from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import socket
import time
from typing import Any, Iterable, Sequence
from uuid import uuid4

import pandas as pd
import pyarrow.parquet as pq


class LockUnavailable(RuntimeError):
    pass


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _temporary_sibling(target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    return target.with_name(f".{target.name}.{uuid4().hex}.tmp")


def atomic_write_parquet(
    frame: pd.DataFrame,
    target: str | Path,
    *,
    row_group_size: int = 50_000,
    compression: str = "zstd",
) -> Path:
    destination = Path(target)
    temporary = _temporary_sibling(destination)
    try:
        frame.to_parquet(
            temporary,
            index=False,
            engine="pyarrow",
            compression=compression,
            row_group_size=max(1_000, int(row_group_size)),
        )
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()
    return destination


def atomic_write_json(payload: Any, target: str | Path) -> Path:
    destination = Path(target)
    temporary = _temporary_sibling(destination)
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, default=str)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()
    return destination


def atomic_write_text(value: str, target: str | Path) -> Path:
    destination = Path(target)
    temporary = _temporary_sibling(destination)
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()
    return destination


def read_parquet_files(
    paths: Sequence[str | Path],
    *,
    columns: Sequence[str] | None = None,
    filters: list[tuple[str, str, Any]] | None = None,
) -> pd.DataFrame:
    existing = [Path(path) for path in paths if Path(path).exists()]
    if not existing:
        return pd.DataFrame(columns=list(columns or []))
    try:
        if len(existing) == 1:
            return pd.read_parquet(existing[0], columns=list(columns) if columns else None, filters=filters, engine="pyarrow")
        dataset = pq.ParquetDataset([str(path) for path in existing], filters=filters)
        return dataset.read(columns=list(columns) if columns else None).to_pandas()
    except (TypeError, ValueError, OSError):
        # Older archives can have harmless schema drift. Reading each file keeps
        # selective filters while allowing Arrow to reconcile at concat time.
        frames = [
            pd.read_parquet(path, columns=list(columns) if columns else None, filters=filters, engine="pyarrow")
            for path in existing
        ]
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=list(columns or []))


@dataclass(frozen=True)
class ParquetMetadata:
    path: str
    rows: int
    columns: int
    row_groups: int
    bytes: int
    modified_at: str
    sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "rows": self.rows,
            "columns": self.columns,
            "row_groups": self.row_groups,
            "bytes": self.bytes,
            "modified_at": self.modified_at,
            "sha256": self.sha256,
        }


def file_sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def parquet_metadata(path: Path, relative_to: Path | None = None) -> ParquetMetadata:
    parquet = pq.ParquetFile(path)
    stat = path.stat()
    display_path = str(path.relative_to(relative_to)) if relative_to and path.is_relative_to(relative_to) else str(path)
    return ParquetMetadata(
        path=display_path.replace("\\", "/"),
        rows=parquet.metadata.num_rows,
        columns=parquet.metadata.num_columns,
        row_groups=parquet.metadata.num_row_groups,
        bytes=stat.st_size,
        modified_at=datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        sha256=file_sha256(path),
    )


def build_data_manifest(paths: Iterable[Path], *, project_root: Path) -> dict[str, Any]:
    entries = [parquet_metadata(path, project_root).as_dict() for path in sorted(set(paths)) if path.exists()]
    return {
        "schema_version": 1,
        "generated_at": utc_now_iso(),
        "datasets": entries,
        "totals": {
            "files": len(entries),
            "rows": sum(entry["rows"] for entry in entries),
            "bytes": sum(entry["bytes"] for entry in entries),
        },
    }


class FileLock(AbstractContextManager["FileLock"]):
    """Small cross-platform lock based on atomic lock-file creation."""

    def __init__(self, path: str | Path, *, stale_after_seconds: int = 6 * 60 * 60):
        self.path = Path(path)
        self.stale_after_seconds = stale_after_seconds
        self._acquired = False

    def acquire(self) -> "FileLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists() and time.time() - self.path.stat().st_mtime > self.stale_after_seconds:
            self.path.unlink()
        payload = json.dumps(
            {
                "pid": os.getpid(),
                "host": socket.gethostname(),
                "created_at": utc_now_iso(),
            },
            sort_keys=True,
        ).encode("utf-8")
        try:
            descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise LockUnavailable(f"Another refresh is already using {self.path}") from exc
        try:
            os.write(descriptor, payload)
        finally:
            os.close(descriptor)
        self._acquired = True
        return self

    def release(self) -> None:
        if self._acquired and self.path.exists():
            self.path.unlink()
        self._acquired = False

    def __enter__(self) -> "FileLock":
        return self.acquire()

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.release()
