"""Citation contexts read by a subscription coding agent, verified by the host.

WHY THIS REPLACES A REGEX. `extract_citation_contexts` finds the citation marker with a regex and
then GUESSES the role with a twelve-line keyword ladder ("dataset" -> dataset_precedent; "method" or
"model" or "analysis" -> method_precedent; "however"/"unknown"/"remain" -> unresolved_tension; else
`other`). Measured across the live corpus: **950 cited works produced 54 contexts (5.7%)**, and
**49 of those 54 (90.7%) fell through to `other`** -- a usable role for 0.5% of cited works. In a
climate paper the word "model" appears in nearly every sentence, and it is checked before "however",
so the ladder fights itself.

That matters because `cited_roles_correct` -- a gate criterion that decides whether a paper keeps
its formation trace -- has no other ground truth. Operator ruling: deterministic code is a guard at
a special juncture; it cannot make a scientific judgement and must not play language games.

WHY A SUBSCRIPTION AGENT AND NOT AN API CALL. Reading citation contexts means reading the paper.
Live bodies run to a median 187 kB and a maximum 516 kB, 4.2 MB for a 20-paper corpus, against a
gate that already windows at 250 kB -- so the API route means many large-input calls, which is the
exact shape that truncated five live gate replies. An agent reads the files; nothing is stuffed into
a prompt. It is billed against a subscription rather than per token, and one spawn covers the whole
corpus.

WHAT THE HOST DOES NOT DELEGATE. The agent proposes; the host verifies, and every check here is
structural rather than lexical:

- the cited work must be one this paper actually cites;
- the quoted sentence must appear VERBATIM in the paper body (whitespace-normalised), which is what
  makes fabrication impossible rather than merely discouraged;
- the host -- not the agent -- locates the containing block, so `source_span_id`, `page` and
  `section` are provenance the agent cannot invent;
- the role must be a declared `CitationContextRole` member.

An entry failing any of these is dropped and counted. A paper whose file is missing or unreadable
yields no contexts and says so. Nothing here can end a run.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ...io import dump_data, load_data
from ...provenance import stable_hash
from ...schemas.cited_literature import CitationContext, CitationContextRole, CitedWorkRef
from ...schemas.paper_ingest import BlockType, ParsedPaper, ParsedPaperBlock

#: The agent writes one file per paper here; the host reads only from this directory.
CONTEXTS_DIRNAME = "citation_contexts"
TASK_FILENAME = "citation_context_task.yaml"

#: Given a prepared workspace, drive the agent. Injected so the host logic is testable without a
#: subprocess and so a live run and a test exercise the same verification code.
AgentSpawn = Callable[[Path], None]


class CitationContextAgentReport(BaseModel):
    """What the agent proposed and what survived verification, per run."""

    model_config = ConfigDict(extra="forbid")

    papers_requested: int = 0
    papers_answered: int = 0
    proposed: int = 0
    accepted: int = 0
    rejected_unknown_work: int = 0
    rejected_quote_not_found: int = 0
    #: An unrecognised role is DEFAULTED, never a rejection: the sentence is the evidence.
    role_defaulted: int = 0
    notes: list[str] = Field(default_factory=list)

    @property
    def rejected(self) -> int:
        return self.rejected_unknown_work + self.rejected_quote_not_found


def _normalized(text: str) -> str:
    return " ".join(text.split())


def _body_blocks(parsed: ParsedPaper) -> list[ParsedPaperBlock]:
    """Body only: a citation context found in the reference list is the reference, not a use."""
    return [
        block
        for block in parsed.blocks
        if block.block_type != BlockType.REFERENCE
        and "reference" not in block.section_title.lower()
        and "bibliography" not in block.section_title.lower()
    ]


#: A quote shorter than this is too weak an anchor to trust; a sentence expanded around it is
#: what the reader and the reviewer actually get.
MIN_ANCHOR_CHARS = 20
#: How far either side of the anchor the host will look for sentence boundaries.
SENTENCE_WINDOW_CHARS = 400


def _expand_to_sentence(haystack: str, start: int, end: int) -> str:
    """Grow an anchor out to its sentence boundaries in the SOURCE text.

    The agent points; the host extracts. Measured on the first live run: asked to copy the citing
    sentence, the agent returned mechanical substrings -- "reach Earth's surface (1, 2)." and
    "trate to successively lower altitudes (4-6)", the second a word cut in half. They pass a
    verbatim check and carry none of the author's reason, which is the entire point of a citation
    context.

    Making the agent copy more carefully would cost turns and still not be reliable. Growing the
    anchor here costs nothing, cannot invent text, and turns an easy job for the agent into a clean
    sentence for the reader.
    """
    left = max(
        haystack.rfind(". ", max(0, start - SENTENCE_WINDOW_CHARS), start),
        haystack.rfind("\n", max(0, start - SENTENCE_WINDOW_CHARS), start),
    )
    right_stop = min(len(haystack), end + SENTENCE_WINDOW_CHARS)
    right = haystack.find(". ", end, right_stop)
    if right == -1:
        right = haystack.find("\n", end, right_stop)
    return haystack[
        (left + 2 if left != -1 else 0) : (right + 1 if right != -1 else right_stop)
    ].strip()


def _locate(quote: str, blocks: Sequence[ParsedPaperBlock]) -> tuple[ParsedPaperBlock, str] | None:
    """The block containing this anchor verbatim, plus the sentence grown around it.

    Whitespace-normalised on both sides because a parser may rewrap a line; nothing else is
    relaxed. This is the check that makes a fabricated quote impossible rather than merely
    discouraged, and it is also what supplies provenance the agent never gets to assert.
    """
    needle = _normalized(quote)
    if len(needle) < MIN_ANCHOR_CHARS:
        return None
    for block in blocks:
        flat = _normalized(block.text)
        at = flat.find(needle)
        if at != -1:
            return block, _expand_to_sentence(flat, at, at + len(needle))
    return None


def write_task(
    workspace: Path,
    *,
    papers: Mapping[str, Sequence[CitedWorkRef]],
    body_paths: Mapping[str, Path],
) -> Path:
    """The agent's instructions and inputs: paths to read, works to look for."""
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / CONTEXTS_DIRNAME).mkdir(exist_ok=True)
    task = {
        "task": (
            "For each paper below, read its text file and find the places where it cites the "
            "listed works. For each place, copy roughly a dozen words VERBATIM from the file "
            "around the citation -- just enough to point at it unambiguously. Do NOT try to copy a "
            "whole sentence or tidy it up: the host grows your anchor out to its sentence "
            "boundaries in the original, so a short exact fragment is worth more than a long "
            "approximate one. Authors usually say why they are citing something right there "
            '("following X", "in contrast to X", "X showed that"), so the surrounding sentence '
            "carries the reason without you having to classify anything.\n"
            "Write one file per paper at "
            f"{CONTEXTS_DIRNAME}/<paper_id>.yaml with a top-level `contexts` list of "
            "{cited_work_id, quote}. A work cited in several places gets several entries -- that "
            "is expected and useful, not a problem to resolve, and no entry is more correct than "
            "another. There is nothing to classify and no taxonomy to fit: the sentence is the "
            "whole answer. Skip anything you cannot find; "
            "this does not need to be exhaustive or exact, and a short honest list beats a long "
            "invented one. Do not re-read a file to double-check a quote: copy it once and move "
            "on, because the host checks every quote against the file and silently drops any that "
            "does not match."
        ),
        "papers": [
            {
                "paper_id": paper_id,
                "text_file": str(body_paths[paper_id]),
                "cited_works": [
                    {
                        "cited_work_id": work.cited_work_id,
                        "authors": work.authors[:3],
                        "year": work.year,
                        "title": work.title,
                        "local_reference_index": work.local_reference_index,
                    }
                    for work in works
                ],
            }
            for paper_id, works in papers.items()
            if paper_id in body_paths
        ],
    }
    path = workspace / TASK_FILENAME
    dump_data(task, path)
    return path


def _read_proposals(workspace: Path, paper_id: str) -> list[Mapping[str, Any]]:
    path = workspace / CONTEXTS_DIRNAME / f"{paper_id}.yaml"
    if not path.is_file():
        return []
    try:
        payload = load_data(path)
    except Exception:  # noqa: BLE001 - an unreadable answer is no answer, never a run failure
        return []
    if not isinstance(payload, Mapping):
        return []
    entries = payload.get("contexts")
    return (
        [entry for entry in entries if isinstance(entry, Mapping)]
        if isinstance(entries, list)
        else []
    )


def verify_paper(
    *,
    paper_id: str,
    parsed: ParsedPaper,
    cited_works: Sequence[CitedWorkRef],
    proposals: Sequence[Mapping[str, Any]],
    report: CitationContextAgentReport,
) -> list[CitationContext]:
    """Turn one paper's proposals into contexts the host can stand behind."""
    known = {work.cited_work_id for work in cited_works}
    blocks = _body_blocks(parsed)
    seen: set[tuple[str, str]] = set()
    contexts: list[CitationContext] = []

    for entry in proposals:
        report.proposed += 1
        work_id = str(entry.get("cited_work_id") or "")
        if work_id not in known:
            report.rejected_unknown_work += 1
            continue
        located = _locate(str(entry.get("quote") or ""), blocks)
        if located is None:
            report.rejected_quote_not_found += 1
            continue
        block, sentence = located
        # NOT ASKED FOR, and accepted only if volunteered. The answer is the sentence: an author
        # who cites something almost always says why in the same breath ("following X", "in
        # contrast to X", "X showed that"), so the sentence already carries the reason. Making an
        # agent choose from an eight-member taxonomy costs turns, invites an argument about which
        # label fits, and adds no evidence -- and the same taxonomy applied by a keyword ladder is
        # what produced `other` for 49 of 54 live contexts. `OTHER` here means "not classified",
        # which is honest, and the reviewer reads the sentence.
        raw_role = str(entry.get("role") or "").strip().lower()
        try:
            role = CitationContextRole(raw_role) if raw_role else CitationContextRole.OTHER
        except ValueError:
            role = CitationContextRole.OTHER
            report.role_defaulted += 1

        local_context = sentence
        key = (work_id, local_context)
        if key in seen:
            continue
        seen.add(key)
        contexts.append(
            CitationContext(
                context_id=f"cc-{stable_hash((work_id, block.block_id, local_context))[:12]}",
                cited_work_id=work_id,
                source_span_id=block.block_id,
                page=block.page_number,
                section=block.section_title,
                local_context=local_context,
                inferred_role=role,
            )
        )
    report.accepted += len(contexts)
    return contexts


def extract_citation_contexts_with_agent(
    *,
    workspace: Path,
    spawn: AgentSpawn,
    parsed_by_paper: Mapping[str, ParsedPaper],
    cited_works_by_paper: Mapping[str, Sequence[CitedWorkRef]],
    body_paths: Mapping[str, Path],
    max_parallel: int = 4,
) -> tuple[dict[str, list[CitationContext]], CitationContextAgentReport]:
    """One short session PER PAPER, several at a time; the host verifies every proposal.

    Per paper rather than per corpus, and concurrent, because the work is embarrassingly parallel
    and a single long session was the slow part: one measured spawn over two papers ran past ten
    minutes, and one paper alone took 302 seconds. Papers do not inform each other -- a citation in
    paper A tells you nothing about paper B -- so there is no reason to serialise them.

    A per-paper session is also the honest failure unit. One paper whose agent times out, crashes
    or writes nothing costs that paper its contexts and nothing else; before, it could take the
    whole corpus with it.
    """
    report = CitationContextAgentReport(papers_requested=len(cited_works_by_paper))
    paper_ids = [
        pid for pid in cited_works_by_paper if pid in body_paths and pid in parsed_by_paper
    ]

    def _one(paper_id: str) -> tuple[str, list[Mapping[str, Any]], str]:
        """Prepare, spawn and read back a single paper in its own workspace."""
        cell = workspace / paper_id
        write_task(
            cell,
            papers={paper_id: cited_works_by_paper[paper_id]},
            body_paths={paper_id: body_paths[paper_id]},
        )
        try:
            spawn(cell)
        except Exception as exc:  # noqa: BLE001 - one paper's failure is one paper's, never the run's
            return paper_id, [], f"{paper_id}: agent spawn failed ({type(exc).__name__})"
        return paper_id, _read_proposals(cell, paper_id), ""

    proposals_by_paper: dict[str, list[Mapping[str, Any]]] = {}
    if paper_ids:
        with ThreadPoolExecutor(max_workers=max(1, min(max_parallel, len(paper_ids)))) as pool:
            for paper_id, proposals, note in pool.map(_one, paper_ids):
                proposals_by_paper[paper_id] = proposals
                if note:
                    report.notes.append(note)

    contexts: dict[str, list[CitationContext]] = {}
    for paper_id, works in cited_works_by_paper.items():
        proposals = proposals_by_paper.get(paper_id, [])
        parsed = parsed_by_paper.get(paper_id)
        if proposals:
            report.papers_answered += 1
        contexts[paper_id] = (
            verify_paper(
                paper_id=paper_id,
                parsed=parsed,
                cited_works=works,
                proposals=proposals,
                report=report,
            )
            if parsed is not None
            else []
        )
    return contexts, report


def claude_code_spawn(
    *,
    executable: str = "claude",
    max_turns: int = 60,
    timeout_seconds: float = 1_800.0,
    permission_mode: str = "dontAsk",
    allowed_tools: Sequence[str] = ("Read", "Write", "Glob", "Grep"),
) -> AgentSpawn:
    """One headless `claude -p` session over the prepared workspace.

    Bounded the same way the planner spawn is -- a turn cap plus a hard wall-clock timeout, no
    dollar budget, because this is subscription-billed rather than per-token. The whole corpus is
    one session: the papers are files the agent opens, so a 4.2 MB corpus costs no prompt at all.

    Deliberately thin. It writes nothing itself and reads nothing back: the workspace is the entire
    contract, and every proposal it produces is verified against the paper before it becomes a
    context. A spawn that fails, times out or never runs is zero contexts, which the caller already
    treats as an honest outcome.

    `--permission-mode` and `--allowedTools` are not optional and were found the hard way. Without
    them a live spawn ran 397 seconds over two real papers and wrote NOTHING: the transcript said
    "Wrote citation_contexts/probe.yaml -- pending your permission to save", and in `-p` there is
    nobody to approve it. `dontAsk` is the same mode the planner runner has always used. The tool
    list is the minimum this task needs -- read the papers, write the answers -- and deliberately
    excludes Bash: this job never needs a shell.
    """
    import subprocess

    def spawn(workspace: Path) -> None:
        argv = [
            executable,
            "-p",
            (
                f"Read {TASK_FILENAME} in this directory and carry out the task it describes. "
                f"Write your answers under {CONTEXTS_DIRNAME}/ and nothing else."
            ),
            "--max-turns",
            str(max_turns),
            "--add-dir",
            str(workspace),
            "--permission-mode",
            permission_mode,
            "--allowedTools",
            ",".join(allowed_tools),
        ]
        proc = subprocess.Popen(
            argv,
            cwd=str(workspace),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        try:
            proc.communicate(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            import os
            import signal

            os.killpg(proc.pid, signal.SIGKILL)
            proc.communicate()
            raise

    return spawn
