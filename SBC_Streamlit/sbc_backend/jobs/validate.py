from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..config import BackendSettings
from ..datasets import DatasetRepository
from ..storage import atomic_write_json
from ..validation import build_repository_manifest, validate_repository


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate SBC data contracts and build the data catalog.")
    parser.add_argument("--no-write", action="store_true", help="Validate without updating metadata files.")
    args = parser.parse_args()

    settings = BackendSettings.from_env(Path(__file__).resolve().parents[2])
    repository = DatasetRepository(settings)
    report = validate_repository(repository)
    manifest = build_repository_manifest(repository)
    payload = {"validation": report.as_dict(), "manifest": manifest}
    if not args.no_write:
        atomic_write_json(report.as_dict(), settings.metadata_root / "validation.json")
        atomic_write_json(manifest, settings.metadata_root / "data_manifest.json")
    print(json.dumps(payload, indent=2, default=str))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
