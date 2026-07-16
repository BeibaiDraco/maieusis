"""Verify the published MC_Maze-S unit-region conversion caveat without analysis."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

EXPECTED = {
    "sub-Jenkins_ses-small_desc-train_behavior+ecephys.nwb": {
        "PMd": 72,
        "M1": 70,
    },
    "sub-Jenkins_ses-small_desc-test_ecephys.nwb": {"PMd": 52, "M1": 55},
}


def _region(unit_id: int) -> str:
    prefix = str(unit_id)[0]
    if prefix == "1":
        return "PMd"
    if prefix == "2":
        return "M1"
    raise ValueError(f"unexpected MC_Maze unit-id prefix: {unit_id}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_root", type=Path)
    args = parser.parse_args()

    try:
        import h5py
    except ImportError as exc:  # pragma: no cover - exercised in the user's NLB environment
        raise SystemExit("install h5py in the read-only NLB inspection environment") from exc

    subject_root = args.dataset_root / "sub-Jenkins"
    for filename, expected in EXPECTED.items():
        path = subject_root / filename
        with h5py.File(path, "r") as handle:
            unit_ids = [int(value) for value in handle["units/id"][()]]
            stored_rows = [int(value) for value in handle["units/electrodes"][()]]
            locations = [
                value.decode() if isinstance(value, bytes) else str(value)
                for value in handle["general/extracellular_ephys/electrodes/location"][()]
            ]

        observed = Counter(_region(unit_id) for unit_id in unit_ids)
        if dict(observed) != expected:
            raise SystemExit(f"{filename}: expected {expected}, observed {dict(observed)}")

        corrected_rows = [
            row + 96 if _region(unit_id) == "M1" else row
            for unit_id, row in zip(unit_ids, stored_rows, strict=True)
        ]
        corrected_locations = Counter(locations[row] for row in corrected_rows)
        if dict(corrected_locations) != expected:
            raise SystemExit(
                f"{filename}: corrected electrode locations {dict(corrected_locations)} "
                f"do not match unit-id regions {expected}"
            )
        print(f"{filename}: PMd={expected['PMd']} M1={expected['M1']} verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
