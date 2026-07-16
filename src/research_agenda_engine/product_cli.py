"""Thin product CLI — the locked public command surface.

Commands: ``init`` / ``check`` / ``run`` / ``resume`` / ``status``. Exported publicly as the
``maieusis`` console script. This module must NOT import the private development CLI
(``dev_cli.py``); command handlers keep their heavy imports lazy so the thin CLI never pulls
retired modules. ``scripts/import_closure.py check`` locks this module's command set to the locked
public set (the five above).
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from .assets import asset_root
from .config import RuntimeEnvLoadResult, load_runtime_env
from .io import load_model

app = typer.Typer(
    name="maieusis",
    help="Inspectable scientific question development before analysis.",
    no_args_is_help=True,
)
console = Console()
_RUNTIME_ENV_RESULT: RuntimeEnvLoadResult | None = None


def _project_root() -> Path:
    return asset_root()


def _ensure_runtime_env_loaded(project_root: Path | None = None) -> RuntimeEnvLoadResult:
    global _RUNTIME_ENV_RESULT
    if _RUNTIME_ENV_RESULT is None:
        _RUNTIME_ENV_RESULT = load_runtime_env(project_root=project_root or _project_root())
    return _RUNTIME_ENV_RESULT


@app.callback()
def main() -> None:
    """Load local runtime env files before command execution."""
    _ensure_runtime_env_loaded()


@app.command("check")
def check_cli(
    project: Annotated[Path, typer.Option("--project")] = Path("maieusis.yaml"),
) -> None:
    """Preflight a project config — verify every input, making ZERO paid model/agent calls."""
    from .config import load_runtime_env
    from .schemas.maieusis_project_config import MaieusisProjectConfig
    from .services.preflight import run_preflight

    load_runtime_env(project_root=_project_root())
    config = load_model(project, MaieusisProjectConfig)
    if config.is_demo:
        console.print(f"[yellow]{config.demo_banner}[/yellow]")
    report = run_preflight(
        config,
        home=None,
        probe_dataset_seed=True,
        probe_openalex=True,
    )
    for check in report.checks:
        if check.warning:
            mark = "[yellow]WARN[/yellow]"
        else:
            mark = "[green]OK  [/green]" if check.ok else "[red]FAIL[/red]"
        console.print(f"  {mark} {check.name}: {check.message}")
    console.print(
        "[bold]Estimates:[/bold] " + "; ".join(f"{k}={v}" for k, v in report.estimates.items())
    )
    console.print("[bold]External egress:[/bold]")
    for line in report.egress_disclosure:
        console.print(f"  - {line}")
    if report.ok:
        console.print("[green]Preflight OK — no paid calls made.[/green]")
    else:
        failed = ", ".join(check.name for check in report.failures())
        console.print(f"[red]Preflight FAILED[/red] (no paid calls made): {failed}")
        raise typer.Exit(code=1)


@app.command("run")
def run_cli(
    project: Annotated[Path, typer.Option("--project")] = Path("maieusis.yaml"),
    check_only: Annotated[bool, typer.Option("--check-only")] = False,
) -> None:
    """Develop question families end to end into plan-or-reject dossiers under runs/<id>/.

    ``--check-only`` is read-only. A full run publishes its manifest + README before the zero-paid
    preflight constructs providers, then drives the inspectable product funnel with that same run
    identity.
    """
    from .config import load_runtime_env
    from .schemas.maieusis_project_config import MaieusisProjectConfig
    from .schemas.run_manifest import DiagnosticClass, RunProcessingState
    from .services.orchestration.end_to_end import execute_run_from_config
    from .services.orchestration.run_envelope import (
        initialize_run,
        record_run_failure,
        set_run_state,
    )
    from .services.preflight import run_preflight

    load_runtime_env(project_root=_project_root())
    config = load_model(project, MaieusisProjectConfig)
    if config.is_demo:
        console.print(f"[yellow]{config.demo_banner}[/yellow]")
    # A check-only route is not a scientific run and must not allocate a run root.
    if check_only:
        report = run_preflight(config, home=None, probe_dataset_seed=True)
        if not report.ok:
            failed = ", ".join(check.name for check in report.failures())
            console.print(f"[red]Preflight FAILED[/red] (no paid calls made): {failed}")
            raise typer.Exit(code=1)
        console.print("[green]Preflight OK.[/green]")
        return

    run_context = initialize_run(config.run.output_root)
    try:
        report = run_preflight(config, home=None, probe_dataset_seed=True)
    except Exception:
        record_run_failure(
            run_context,
            code="preflight_exception",
            diagnostic_class=DiagnosticClass.INFRASTRUCTURE,
            public_message="The zero-paid preflight could not complete; no scientific processing began.",
        )
        raise
    if not report.ok:
        failed = ", ".join(check.name for check in report.failures())
        record_run_failure(
            run_context,
            code="preflight_failed",
            diagnostic_class=DiagnosticClass.INPUT,
            public_message="The project did not pass preflight; no scientific processing began.",
        )
        console.print(f"[red]Preflight FAILED[/red] (no paid calls made): {failed}")
        raise typer.Exit(code=1)
    console.print("[green]Preflight OK.[/green]")
    set_run_state(
        run_context,
        RunProcessingState.RUNNING,
        next_action="Scientific processing is running; inspect this README for retained products.",
    )
    try:
        summary_path = execute_run_from_config(config, run_context=run_context)
    except Exception:
        # Direct execution also records faults; this defense covers injected/custom entrypoints.
        from .services.orchestration.run_envelope import load_run_manifest

        if load_run_manifest(run_context.paths).run_state not in {
            RunProcessingState.FAILED,
            RunProcessingState.INCOMPLETE,
        }:
            record_run_failure(run_context, code="run_exception")
        raise
    console.print(f"[green]Run finished.[/green] Summary: {summary_path}")
    _print_presentation_outcome(summary_path.parent)


@app.command("resume")
def resume_cli(
    run_id: Annotated[str, typer.Argument(help="The runs/<id> run to re-enter and finish")],
    project: Annotated[Path, typer.Option("--project")] = Path("maieusis.yaml"),
) -> None:
    """Resume an existing run: REUSE stages proven complete-with-identical-inputs, re-run the rest.

    Same config + preflight as `maieusis run`. The decision set (what was reused and why, with digest
    evidence) is persisted to runs/<id>/receipts/resume-<n>.yaml BEFORE anything executes. A fully
    reused resume makes zero paid calls and zero spawns.
    """
    from .config import load_runtime_env
    from .schemas.maieusis_project_config import MaieusisProjectConfig
    from .services.orchestration.resume import (
        RunArtifactCorruptionError,
        RunLockedError,
        ScientificResumePreflightRequired,
        StaleRunLockError,
        execute_resume_from_config,
    )

    load_runtime_env(project_root=_project_root())
    config = load_model(project, MaieusisProjectConfig)
    if config.is_demo:
        console.print(f"[yellow]{config.demo_banner}[/yellow]")
    try:
        summary_path = execute_resume_from_config(
            config,
            run_id,
            scientific_preflight_complete=False,
        )
    except ScientificResumePreflightRequired:
        from .services.preflight import run_preflight

        report = run_preflight(config, home=None, probe_dataset_seed=True)
        if not report.ok:
            failed = ", ".join(check.name for check in report.failures())
            console.print(f"[red]Preflight FAILED[/red] (no paid calls made): {failed}")
            raise typer.Exit(code=1) from None
        console.print("[green]Preflight OK.[/green]")
        try:
            summary_path = execute_resume_from_config(
                config,
                run_id,
                scientific_preflight_complete=True,
            )
        except (RunArtifactCorruptionError, RunLockedError, StaleRunLockError, ValueError) as exc:
            console.print(f"[red]Resume failed:[/red] {exc}")
            raise typer.Exit(code=1) from exc
    except (RunArtifactCorruptionError, RunLockedError, StaleRunLockError, ValueError) as exc:
        console.print(f"[red]Resume failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    console.print(f"[green]Resume complete.[/green] Summary: {summary_path}")
    _print_presentation_outcome(summary_path.parent)


@app.command("status")
def status_cli(
    run_id: Annotated[str, typer.Argument(help="The runs/<id> run to inspect")],
    project: Annotated[Path, typer.Option("--project")] = Path("maieusis.yaml"),
) -> None:
    """Show what `maieusis resume` would reuse vs re-run (read-only: no lock, no execution, no paid calls).

    Runs the pure resume planner over the persisted receipts/artifacts and prints the per-stage and
    per-family decision table. Input digests are recomputed from the CLI-resolved inputs (inbox PDFs,
    config), exactly as `maieusis resume` would.
    """
    from .config import load_runtime_env
    from .schemas.maieusis_project_config import MaieusisProjectConfig
    from .schemas.resume import PresentationResumeDecisionKind, StageResumeDecisionKind
    from .services.orchestration.end_to_end import effective_family_count
    from .services.orchestration.resume import (
        STAGE_ORDER,
        RunArtifactCorruptionError,
        plan_resume,
    )
    from .services.orchestration.run_envelope import load_run_manifest, render_run_readme
    from .services.orchestration.run_layout import RunPaths, read_stage_receipt

    load_runtime_env(project_root=_project_root())
    config = load_model(project, MaieusisProjectConfig)
    run_root = Path(config.run.output_root) / run_id
    if not run_root.is_dir() or not any(run_root.iterdir()):
        console.print(f"[red]run {run_id!r} not found at {run_root}[/red]")
        raise typer.Exit(code=1)
    paths = RunPaths(root=run_root)
    try:
        manifest = load_run_manifest(paths)
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]Run envelope is unavailable or invalid:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    console.print(render_run_readme(manifest))
    try:
        # Resolve the SAME family cap `maieusis run`/`maieusis resume` used, or a capped run's stage D would be
        # mis-reported as needing re-run (the stage-D config digest is bound to that count).
        plan = plan_resume(config, paths, family_count=effective_family_count(config, 6))
    except RunArtifactCorruptionError as exc:
        console.print(f"[red]Corruption detected:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    except (FileNotFoundError, ValueError):
        console.print("Resume decisions are not available yet; the run inventory above is current.")
        return
    console.print(f"[bold]Run {run_id} — stage state[/bold]")
    for stage in STAGE_ORDER:
        decision = plan.stage_decisions[stage]
        color = "green" if decision.decision == StageResumeDecisionKind.REUSE else "yellow"
        # ``ended_at`` is the receipt's persisted completion time. On a resume it stays UNCHANGED for
        # every REUSE stage (the receipt is not rewritten) — the operator's no-re-pay eyeball check:
        # snapshot it before the kill, compare after resume (REUSE rows identical, re-run rows newer).
        receipt = read_stage_receipt(paths, stage)
        ended = (
            receipt.ended_at.isoformat(timespec="seconds")
            if receipt is not None and receipt.ended_at is not None
            else "-"
        )
        console.print(
            f"  {stage:<14} receipt={decision.receipt_status:<20} "
            f"[{color}]{decision.decision.value:<6}[/{color}] "
            f"ended={ended:<25} {decision.reason.value}"
        )
    if plan.family_decisions:
        console.print("[bold]Back-half families[/bold]")
        for family in plan.family_decisions:
            color = "green" if family.decision == StageResumeDecisionKind.REUSE else "yellow"
            status = family.status_on_disk or "(no record)"
            console.print(
                f"  {family.question_family_id:<28} {status:<32} "
                f"[{color}]{family.decision.value:<6}[/{color}] {family.reason.value}"
            )
    presentation = plan.presentation_decision
    presentation_color = (
        "green" if presentation.decision == PresentationResumeDecisionKind.REUSE else "yellow"
    )
    console.print(
        "[bold]Detailed presentation add-on[/bold]\n"
        f"  [{presentation_color}]{presentation.decision.value}[/{presentation_color}] "
        f"{presentation.reason.value}"
    )
    console.print(
        f"Would reuse {plan.reused_stage_count} stage(s), re-run {plan.rerun_stage_count} stage(s)."
    )


def _print_presentation_outcome(run_root: Path) -> None:
    """Report add-on readiness without changing command success or scientific state."""
    from .schemas.resume import PresentationResumeDecisionKind
    from .services.orchestration.run_layout import RunPaths
    from .services.presentation.materialize import plan_presentation_resume

    try:
        decision = plan_presentation_resume(
            RunPaths(root=run_root), scientific_stage_will_run=False
        )
    except (OSError, ValueError):
        # The command's scientific result remains the primary return contract.  A missing or
        # unreadable add-on pointer is reported as not ready instead of turning presentation into
        # a seventh failure gate (and keeps injected CLI tests honest).
        decision = None
    if decision is not None and decision.decision == PresentationResumeDecisionKind.REUSE:
        console.print("[green]Detailed presentation pages are ready.[/green]")
        return
    console.print(
        "[yellow]Detailed presentation is not ready; scientific run state and compact products "
        "remain unchanged. Run `maieusis resume` to retry the add-on.[/yellow]"
    )


_LAYOUT_EXPLAINER = """\
# Maieusis project layout

`maieusis init` scaffolded this project. Next:

1. Start Codex or Claude Code in this directory. Codex reads `AGENTS.md`; Claude Code reads
   `CLAUDE.md`, which imports the same operating contract.
2. Put lawfully obtained source PDFs in `paperbank.inbox_dir` (default `papers/inbox/`). Keep PDFs,
   datasets, and credentials untracked.
3. Edit `maieusis.yaml` — set the real `dataset.seed.link`, read-only
   `dataset.inspection_runtime.dataset_root`, and distinct Owner/Reviewer providers. When running an
   installed wheel outside its source checkout, also point `source_tree_root` at a clean Maieusis
   source-integrity checkout with HEAD. Keep API keys only in an untracked runtime.env, never in
   this YAML. The coding-host login/subscription is separate from scientific model API credentials.
4. Run `maieusis check --project maieusis.yaml`. It preflights the inputs and reports the estimated
   model calls/planner spawns with ZERO paid calls. Resolve failures, show the report, and ask the
   user before any paid run.
5. After explicit approval, `maieusis run --project maieusis.yaml` develops questions and plans into
   `runs/<id>/` (per-family compact/detailed dossiers + `summary.md`). It does not execute the
   scientific analysis or access confirmation outcomes.
6. Use `maieusis status <run-id>` / `maieusis resume <run-id>` to inspect or finish a run; never
   hand-edit run artifacts to force reuse.

The generated `.claude/agents/` and `.codex/agents/` files define the isolated Dataset Planner role
that Maieusis launches during a run. Do not invoke that role manually before a branch and dialogue
service exist.
"""


def _resolve_bundled(*candidates: str) -> Path | None:
    """Find a bundled asset, trying each relative candidate under the asset root (wheel or source)."""
    root = _project_root()
    for rel in candidates:
        p = root / rel
        if p.exists():
            return p
    return None


@app.command("init")
def init_cli(
    directory: Annotated[Path, typer.Option("--dir")] = Path("."),
) -> None:
    """Scaffold a project config, agent operating files, and dataset-planner role files.

    Idempotent — existing files are left untouched (prints ``skip``). Assets come from the installed
    package (or a source checkout), so this works from a fresh wheel install with no repo present.
    """
    directory.mkdir(parents=True, exist_ok=True)
    materialized: list[tuple[str, Path | None]] = [
        ("maieusis.yaml", _resolve_bundled("examples/maieusis.yaml")),
        (
            ".claude/agents/dataset-planner.md",
            _resolve_bundled(
                "roles/claude/dataset-planner.md", ".claude/agents/dataset-planner.md"
            ),
        ),
        (
            ".codex/agents/dataset-planner.toml",
            _resolve_bundled(
                "roles/codex/dataset-planner.toml", ".codex/agents/dataset-planner.toml"
            ),
        ),
        (
            "AGENTS.md",
            _resolve_bundled("examples/project/AGENTS.template.md"),
        ),
        (
            "CLAUDE.md",
            _resolve_bundled("examples/project/CLAUDE.template.md"),
        ),
    ]
    for dst_rel, src in materialized:
        dst = directory / dst_rel
        if dst.exists():
            console.print(f"  [yellow]skip[/yellow] {dst_rel} (already exists)")
            continue
        if src is None:
            console.print(f"  [red]missing bundled asset for[/red] {dst_rel}")
            raise typer.Exit(code=1)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
        console.print(f"  [green]created[/green] {dst_rel}")

    layout = directory / "PROJECT_LAYOUT.md"
    if not layout.exists():
        layout.write_text(_LAYOUT_EXPLAINER, encoding="utf-8")
        console.print("  [green]created[/green] PROJECT_LAYOUT.md")
    console.print(
        "[green]Project scaffolded.[/green] Next: edit maieusis.yaml, then `maieusis check`."
    )


if __name__ == "__main__":  # `python -m research_agenda_engine.product_cli`
    app()
