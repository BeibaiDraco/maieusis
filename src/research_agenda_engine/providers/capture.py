"""Raw paid-leaf capture (6-H1b D3) — additive, default-off, operator-enabled for live runs.

When ``MAIEUSIS_CAPTURE_DIR`` is set (env), every paid-leaf request/response is teed raw to
``<dir>/<seam>/<NNNN>-{request,response}.json`` with a provenance stamp, so a live run's real
external shapes can seed the replay corpus (the 6-H2 live-capture checkpoint depends on this). When
the env var is unset the hooks are a no-op — ZERO behavior change — so tests/CI never capture.

Secrets are redacted before anything is written: Authorization/api-key/token headers and
``api_key=``/``key=``/``token=`` query params are masked, so a capture directory never holds a key.
Capture is best-effort: a write error (bad ``MAIEUSIS_CAPTURE_DIR``) is swallowed narrowly (OSError only) so
it can never crash a paid run it was only observing.
"""

from __future__ import annotations

import json
import os
import re
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

CAPTURE_ENV = "MAIEUSIS_CAPTURE_DIR"

_MASK = "REDACTED"
_SECRET_HEADER = re.compile(r"(?i)(authorization|api[_-]?key|x-api-key|token|secret|cookie)")
_SECRET_QUERY_KEY = re.compile(r"(?i)(api_?key|key|token|secret|access_token|mailto)")
_CAPTURE_FILENAME = re.compile(
    r"^(\d+)-(?:request|response|parse_failure|transport_failure)\.json$"
)
_counter_lock = threading.Lock()


@dataclass(frozen=True)
class CaptureReceipt:
    destination: Path
    occurrence: int
    provenance: dict[str, Any]


def capture_dir() -> Path | None:
    raw = os.getenv(CAPTURE_ENV, "").strip()
    return Path(raw) if raw else None


def capture_enabled() -> bool:
    return capture_dir() is not None


def _redact_url(url: str) -> str:
    parts = urlsplit(url)
    if not parts.query:
        return url
    scrubbed = [
        (key, _MASK if _SECRET_QUERY_KEY.fullmatch(key) else value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
    ]
    return urlunsplit(parts._replace(query=urlencode(scrubbed)))


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            # A credential is always a STRING. `_SECRET_HEADER` matches any key containing "token",
            # which is right for `auth_token` and wrong for `usage.output_tokens` -- and it masked
            # the latter in all 123 session captures of the 2026-07-31 leg, leaving no way to tell
            # how close a reply ran to its ceiling. That is the one number a truncation postmortem
            # needs. Narrowing the pattern instead would be worse: `\btoken\b` stops matching
            # `auth_token` too, because `_` is a word character.
            if (
                isinstance(key, str)
                and _SECRET_HEADER.search(key)
                and not isinstance(item, bool | int | float)
            ):
                out[key] = _MASK
            elif key == "url" and isinstance(item, str):
                out[key] = _redact_url(item)
            else:
                out[key] = _redact(item)
        return out
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, str) and value.startswith(("http://", "https://")):
        return _redact_url(value)
    return value


def capture_paid_leaf(
    seam: str, *, request: dict[str, Any], response: Any, model: str = ""
) -> CaptureReceipt | None:
    """Tee a paid-leaf exchange when MAIEUSIS_CAPTURE_DIR is set; a no-op otherwise. Best-effort."""
    root = capture_dir()
    if root is None:
        return None
    try:
        receipt = _reserve_capture(root, seam=seam, request=request, model=model)
        with (receipt.destination / f"{receipt.occurrence:04d}-response.json").open(
            "x", encoding="utf-8"
        ) as handle:
            handle.write(
                json.dumps(
                    {"provenance": receipt.provenance, "response": _redact(response)},
                    indent=2,
                    default=str,
                )
            )
        return receipt
    except OSError:
        # Observability tee must never crash the run it is watching (bad MAIEUSIS_CAPTURE_DIR, full disk).
        return None


def capture_paid_leaf_failure(
    seam: str,
    *,
    request: dict[str, Any],
    error: BaseException,
    provider: str,
    model: str = "",
    failure_kind: str = "unclassified",
    attempts: int = 1,
) -> CaptureReceipt | None:
    """Persist a failed paid call without persisting provider text or response bytes.

    Successful capture has always reserved an occurrence only *after* the transport returned. A
    transport exception therefore left no request identity at all. This sibling reserves the same
    redacted request envelope and pairs it with a finite marker: enough to identify the failed leaf
    and classify it, but never the exception message/body, request id, or partial model output.

    One call should be made for the final exception of one logical ``send``. Provider adapters own
    retry semantics and pass the final attempt count here.
    """

    root = capture_dir()
    if root is None:
        return None
    try:
        receipt = _reserve_capture(root, seam=seam, request=request, model=model)
        status = int(getattr(error, "status_code", 0) or 0)
        marker = {
            "provenance": receipt.provenance,
            "transport_failure": True,
            "provider": provider,
            "model": model,
            "failure_kind": failure_kind,
            "error_type": type(error).__name__,
            "http_status": status or None,
            "attempts": max(1, int(attempts)),
        }
        (receipt.destination / f"{receipt.occurrence:04d}-transport_failure.json").write_text(
            json.dumps(marker, indent=2), encoding="utf-8"
        )
        return receipt
    except OSError:
        return None


def _reserve_capture(
    root: Path, *, seam: str, request: dict[str, Any], model: str
) -> CaptureReceipt:
    """Reserve one append-only occurrence by writing its redacted request first."""

    seam_slug = re.sub(r"[^A-Za-z0-9._-]+", "_", seam)
    dest = root / seam_slug
    dest.mkdir(parents=True, exist_ok=True)
    # The request file is the reservation record. Scan disk (not process memory) so a new
    # ``resume`` process appends after existing captures, and use exclusive create so concurrent
    # processes cannot claim the same occurrence. Slug-colliding seam names intentionally share
    # one on-disk sequence because they share one destination directory.
    with _counter_lock:
        occurrence = _next_disk_occurrence(dest)
        while True:
            stamp = {
                "seam": seam,
                "model": model,
                "captured_at": datetime.now(UTC).isoformat(),
                "occurrence": occurrence,
            }
            try:
                with (dest / f"{occurrence:04d}-request.json").open(
                    "x", encoding="utf-8"
                ) as handle:
                    handle.write(
                        json.dumps(
                            {"provenance": stamp, "request": _redact(request)},
                            indent=2,
                            default=str,
                        )
                    )
                break
            except FileExistsError:
                occurrence += 1
    return CaptureReceipt(destination=dest, occurrence=occurrence, provenance=stamp)


def _next_disk_occurrence(destination: Path) -> int:
    maximum = 0
    for path in destination.iterdir():
        match = _CAPTURE_FILENAME.fullmatch(path.name)
        if match:
            maximum = max(maximum, int(match.group(1)))
    return maximum + 1


def capture_parse_failure(receipt: CaptureReceipt | None, error: BaseException) -> None:
    """Mark an SDK parse failure without persisting exception text that may echo model output."""
    if receipt is None:
        return
    try:
        (receipt.destination / f"{receipt.occurrence:04d}-parse_failure.json").write_text(
            json.dumps(
                {
                    "provenance": receipt.provenance,
                    "parse_failure": True,
                    "error_type": type(error).__name__,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    except OSError:
        return


def raw_response_body(raw_response: Any) -> Any:
    """Read a vendor raw-response body before its SDK parse/post-parser runs."""
    http_response = getattr(raw_response, "http_response", raw_response)
    json_method = getattr(http_response, "json", None)
    if callable(json_method):
        try:
            return json_method()
        except (TypeError, ValueError, json.JSONDecodeError):
            pass
    text = getattr(http_response, "text", "")
    return {"raw_text": str(text)}
