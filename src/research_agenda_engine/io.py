from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypeVar

import yaml
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def load_data(path: str | Path) -> Any:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        return yaml.safe_load(text)
    if path.suffix.lower() == ".json":
        return json.loads(text)
    raise ValueError(f"Unsupported file type: {path}")


def load_model(path: str | Path, model_type: type[T]) -> T:
    return model_type.model_validate(load_data(path))


def dump_data(value: Any, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json", exclude_none=True)
    elif isinstance(value, list):
        value = [
            v.model_dump(mode="json", exclude_none=True) if isinstance(v, BaseModel) else v
            for v in value
        ]

    if path.suffix.lower() in {".yaml", ".yml"}:
        path.write_text(
            yaml.safe_dump(value, sort_keys=False, allow_unicode=True), encoding="utf-8"
        )
    elif path.suffix.lower() == ".json":
        path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {path}")
    return path
