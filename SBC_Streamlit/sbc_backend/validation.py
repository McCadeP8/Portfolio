from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import pyarrow.parquet as pq

from .datasets import DATASETS, DatasetRepository
from .storage import build_data_manifest


ARCHIVE_PATTERNS = (
    "data_snapshots/shots/nba_shots_20????.parquet",
    "data_snapshots/pbp/pbp_stat_events_20????.parquet",
)


@dataclass(frozen=True)
class ValidationItem:
    dataset: str
    path: str
    status: str
    rows: int = 0
    message: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationReport:
    ok: bool
    items: tuple[ValidationItem, ...]

    @property
    def errors(self) -> tuple[ValidationItem, ...]:
        return tuple(item for item in self.items if item.status == "error")

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": len(self.errors),
            "items": [item.as_dict() for item in self.items],
        }


def _display_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path.resolve()).replace("\\", "/")


def validate_repository(repository: DatasetRepository) -> ValidationReport:
    items: list[ValidationItem] = []
    for name, contract in DATASETS.items():
        path = repository.resolve(contract)
        if path is None:
            items.append(ValidationItem(name, contract.relative_path, "warning", message="dataset not present"))
            continue
        display = _display_path(path, repository.settings.project_root)
        try:
            parquet = pq.ParquetFile(path)
            columns = set(parquet.schema_arrow.names)
            missing = sorted(set(contract.required_columns) - columns)
            if missing:
                items.append(
                    ValidationItem(name, display, "error", parquet.metadata.num_rows, f"missing columns: {', '.join(missing)}")
                )
                continue
            duplicate_message = ""
            if contract.unique_key:
                key_frame = pd.read_parquet(path, columns=list(contract.unique_key), engine="pyarrow")
                duplicates = int(key_frame.duplicated(list(contract.unique_key)).sum())
                if duplicates:
                    duplicate_message = f"{duplicates:,} duplicate key rows"
            status = "warning" if duplicate_message else "ok"
            items.append(ValidationItem(name, display, status, parquet.metadata.num_rows, duplicate_message))
        except Exception as exc:
            items.append(ValidationItem(name, display, "error", message=f"{type(exc).__name__}: {exc}"))

    for pattern in ARCHIVE_PATTERNS:
        for path in repository.parquet_paths(pattern):
            display = _display_path(path, repository.settings.project_root)
            try:
                parquet = pq.ParquetFile(path)
                if parquet.metadata.num_rows <= 0:
                    items.append(ValidationItem(path.stem, display, "warning", message="empty archive"))
                else:
                    items.append(ValidationItem(path.stem, display, "ok", parquet.metadata.num_rows))
            except Exception as exc:
                items.append(ValidationItem(path.stem, display, "error", message=f"{type(exc).__name__}: {exc}"))

    return ValidationReport(ok=not any(item.status == "error" for item in items), items=tuple(items))


def manifest_paths(repository: DatasetRepository) -> list[Path]:
    paths: list[Path] = []
    for contract in DATASETS.values():
        path = repository.resolve(contract)
        if path is not None:
            paths.append(path)
    for pattern in ARCHIVE_PATTERNS:
        paths.extend(repository.parquet_paths(pattern))
    return sorted({path.resolve() for path in paths})


def build_repository_manifest(repository: DatasetRepository, paths: Iterable[Path] | None = None) -> dict[str, Any]:
    return build_data_manifest(paths or manifest_paths(repository), project_root=repository.settings.project_root)
