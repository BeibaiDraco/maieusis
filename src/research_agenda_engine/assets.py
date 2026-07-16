from __future__ import annotations

import os
from pathlib import Path


class AssetResolutionError(FileNotFoundError):
    """Raised when a built-in or user-supplied project asset cannot be found."""


def source_checkout_root() -> Path | None:
    """Return the repository root when running from a source checkout."""
    candidate = Path(__file__).resolve().parents[2]
    if (candidate / "pyproject.toml").exists() and (candidate / "prompts").exists():
        return candidate
    return None


def builtin_asset_root() -> Path:
    """Location populated inside built wheels by Hatch force-include."""
    return Path(__file__).resolve().parent / "_builtin"


def asset_root() -> Path:
    """Resolve the canonical root for bundled prototype assets.

    Resolution order:
    1. explicit ``MAIEUSIS_PROJECT_ROOT``;
    2. the current working directory when it looks like a source checkout;
    3. this package's source checkout root;
    4. wheel-bundled assets.
    """
    env = os.getenv("MAIEUSIS_PROJECT_ROOT")
    if env:
        root = Path(env).expanduser().resolve()
        if not root.exists():
            raise AssetResolutionError(f"MAIEUSIS_PROJECT_ROOT does not exist: {root}")
        return root

    cwd = Path.cwd().resolve()
    if (cwd / "pyproject.toml").exists() and (cwd / "prompts").exists():
        return cwd

    checkout = source_checkout_root()
    if checkout is not None:
        return checkout

    bundled = builtin_asset_root()
    if bundled.exists():
        return bundled
    raise AssetResolutionError(
        "Could not locate Maieusis assets. Set MAIEUSIS_PROJECT_ROOT to a source "
        "checkout or reinstall a wheel that includes built-in assets."
    )


def resolve_asset(path: str | Path) -> Path:
    """Resolve an explicit path, falling back to a path under :func:`asset_root`."""
    candidate = Path(path).expanduser()
    if candidate.exists():
        return candidate.resolve()
    if candidate.is_absolute():
        raise AssetResolutionError(candidate)
    fallback = asset_root() / candidate
    if fallback.exists():
        import os as _os

        trace_path = _os.getenv("MAIEUSIS_TRACE_ASSETS")
        if trace_path and "prompts/" in candidate.as_posix():
            with open(trace_path, "a", encoding="utf-8") as _fh:
                _fh.write(candidate.as_posix() + "\n")
        return fallback.resolve()
    raise AssetResolutionError(
        f"Asset not found at '{candidate}' or '{fallback}'. Supply an explicit path."
    )
