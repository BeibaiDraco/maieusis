"""Host the scientific-dialogue MCP server in-process for a spawned agent.

The locked transport (probe-confirmed): the runner hosts the dialogue MCP server itself,
in its OWN process, on a background uvicorn thread bound to ``127.0.0.1:<free-port>``, and passes
an inline ``--mcp-config`` HTTP entry to the spawned ``claude -p``. The spawned agent reaches it
through its runtime MCP client (which is NOT confined by Claude's native Bash sandbox — the
sandbox scopes to Bash subprocesses only, verified by probe). The **real Question Owner API call
happens inside this host process** (full network, API key present here), never inside the agent
spawn (which has paid/API-key env stripped). The agent only ever talks to ``localhost``.

Scope is deliberately narrow: MCP carries owner dialogue + read context/state only. Inspection
evidence and the terminal plan/rejection still travel as files (the direct-file contract), so the
shared ``RealPlannerHost`` Collect path is unchanged.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

import contextlib
import json
import socket
import threading
import time
from types import TracebackType
from typing import TYPE_CHECKING

from ...mcp import build_server_app

if TYPE_CHECKING:
    from ...mcp import ScientificDialogueServer

# Client-side MCP server name (the key in ``--mcp-config``). Claude derives tool names as
# ``mcp__<server_name>__<tool_name>``; keep it delimiter-safe (no underscores) so that split is
# unambiguous. Confirmed reachable by the transport probe.
DIALOGUE_MCP_SERVER_NAME = "maieusisdialogue"

# The only dialogue tools the spawned agent may call. Evidence / plan / rejection / feasibility
# tools are intentionally excluded — those artifacts stay files (direct-file contract).
DIALOGUE_MCP_TOOL_NAMES: tuple[str, ...] = (
    "branch_get_context",
    "branch_get_state",
    "branch_submit_clarification_request",
    "branch_ask_question_owner",
    "branch_submit_operationalization",
)

_STREAMABLE_HTTP_PATH = "/mcp"
_BIND_TIMEOUT_SECONDS = 20.0
_STOP_JOIN_TIMEOUT_SECONDS = 10.0
_MAX_BIND_ATTEMPTS = 5


def _bind_localhost_socket(host: str) -> socket.socket:
    """Bind a fresh localhost socket to an ephemeral port and return it STILL OPEN.

    Note: an earlier ``_free_localhost_port`` bound ``:0``, read the port, then CLOSED the socket,
    leaving a TOCTOU window before uvicorn re-bound that port — under N-family parallelism two
    families could receive the same port and one uvicorn bind would fail. Holding the bound socket
    from allocation until it is handed to uvicorn (``Server.run(sockets=[sock])``) keeps the port
    reserved the whole time, so concurrent servers can never collide.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((host, 0))
    except OSError:
        sock.close()
        raise
    return sock


def dialogue_mcp_config_json(url: str, *, server_name: str = DIALOGUE_MCP_SERVER_NAME) -> str:
    """The inline ``--mcp-config`` JSON pointing the agent at the localhost HTTP dialogue server."""
    return json.dumps({"mcpServers": {server_name: {"type": "http", "url": url}}})


def dialogue_allowed_tool_names(*, server_name: str = DIALOGUE_MCP_SERVER_NAME) -> list[str]:
    """The ``mcp__<server>__<tool>`` names to add to ``--allowedTools`` in dialogue mode."""
    return [f"mcp__{server_name}__{tool}" for tool in DIALOGUE_MCP_TOOL_NAMES]


class LocalDialogueMcpServer:
    """Serve a ``ScientificDialogueServer`` over localhost streamable-HTTP on a bg thread.

    Use as a context manager around the agent spawn::

        with LocalDialogueMcpServer(service) as dialogue:
            argv = runner.build_command(..., mcp_config_json=dialogue.mcp_config_json, ...)
            ...spawn...
        # server stopped on exit

    The owner provider lives inside ``service`` (this process), so the owner API key is never
    forwarded to the agent subprocess.
    """

    def __init__(
        self,
        service: ScientificDialogueServer,
        *,
        server_name: str = DIALOGUE_MCP_SERVER_NAME,
        host: str = "127.0.0.1",
        port: int | None = None,
    ) -> None:
        self.service = service
        self.server_name = server_name
        self.host = host
        # Auto-allocated ports hold their bound socket (see `_bind_localhost_socket`); an explicitly
        # supplied port keeps the legacy no-socket path (used by config/url-only unit tests).
        self._socket: socket.socket | None = None
        if port is not None:
            self.port = port
        else:
            self._socket = _bind_localhost_socket(host)
            self.port = int(self._socket.getsockname()[1])
        self._server: object | None = None
        self._thread: threading.Thread | None = None

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}{_STREAMABLE_HTTP_PATH}"

    @property
    def mcp_config_json(self) -> str:
        return dialogue_mcp_config_json(self.url, server_name=self.server_name)

    @property
    def allowed_tool_names(self) -> list[str]:
        return dialogue_allowed_tool_names(server_name=self.server_name)

    def start(self) -> LocalDialogueMcpServer:
        # Double-insurance retry (commander-approved): holding the socket already makes a collision
        # essentially impossible, so a retry only guards against a transient bind failure — and only
        # when the port is auto-allocated (an explicit port is never silently changed).
        attempts = _MAX_BIND_ATTEMPTS if self._socket is not None else 1
        last_exc: Exception | None = None
        for attempt in range(attempts):
            try:
                return self._start_once()
            except (RuntimeError, TimeoutError, OSError) as exc:
                last_exc = exc
                self._server = None
                self._thread = None
                if self._socket is not None and attempt + 1 < attempts:
                    with contextlib.suppress(OSError):
                        self._socket.close()
                    self._socket = _bind_localhost_socket(self.host)
                    self.port = int(self._socket.getsockname()[1])
        assert last_exc is not None
        raise last_exc

    def _start_once(self) -> LocalDialogueMcpServer:
        import uvicorn

        app = build_server_app(self.service).streamable_http_app()
        config = uvicorn.Config(
            app,
            host=self.host,
            port=self.port,
            log_level="warning",
            lifespan="on",
        )
        server = uvicorn.Server(config)
        self._server = server
        held = self._socket

        def _serve() -> None:
            # Hand the pre-bound socket to uvicorn so it never re-binds the port (no TOCTOU window).
            if held is not None:
                server.run(sockets=[held])
            else:
                server.run()

        thread = threading.Thread(target=_serve, name="maieusis-dialogue-mcp", daemon=True)
        self._thread = thread
        thread.start()

        deadline = time.time() + _BIND_TIMEOUT_SECONDS
        while time.time() < deadline:
            if getattr(server, "started", False):
                return self
            if not thread.is_alive():
                raise RuntimeError("dialogue MCP server thread exited before binding")
            time.sleep(0.05)
        self.stop()
        raise TimeoutError(
            f"dialogue MCP server did not bind {self.host}:{self.port} within "
            f"{_BIND_TIMEOUT_SECONDS}s"
        )

    def stop(self) -> None:
        server = self._server
        if server is not None:
            server.should_exit = True  # type: ignore[attr-defined]
        thread = self._thread
        if thread is not None:
            thread.join(timeout=_STOP_JOIN_TIMEOUT_SECONDS)
        sock = self._socket
        if sock is not None:
            # uvicorn may already have closed the handed-off socket on shutdown; closing twice is fine.
            with contextlib.suppress(OSError):
                sock.close()
        self._socket = None
        self._server = None
        self._thread = None

    def __enter__(self) -> LocalDialogueMcpServer:
        return self.start()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.stop()
