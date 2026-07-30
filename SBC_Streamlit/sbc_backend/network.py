from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import json
from pathlib import Path
import time
from typing import Any

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .storage import atomic_write_json, atomic_write_parquet


DEFAULT_USER_AGENT = "SBCFBL-Data/1.0 (+https://github.com/)"


def resilient_session(*, retries: int = 4, backoff_factor: float = 0.8) -> requests.Session:
    retry = Retry(
        total=retries,
        connect=retries,
        read=retries,
        status=retries,
        backoff_factor=backoff_factor,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "HEAD"}),
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=8, pool_maxsize=8)
    session = requests.Session()
    session.headers.update({"User-Agent": DEFAULT_USER_AGENT, "Accept": "application/json,text/csv,*/*"})
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def cache_is_fresh(path: Path, ttl_seconds: int) -> bool:
    return path.exists() and time.time() - path.stat().st_mtime <= max(0, ttl_seconds)


@dataclass
class CachedHttpClient:
    timeout_seconds: int = 30
    retries: int = 4

    def __post_init__(self) -> None:
        self.session = resilient_session(retries=self.retries)

    def get_json(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        cache_path: Path | None = None,
        ttl_seconds: int = 0,
        allow_stale_on_error: bool = True,
    ) -> dict[str, Any]:
        if cache_path and cache_is_fresh(cache_path, ttl_seconds):
            return json.loads(cache_path.read_text(encoding="utf-8"))
        try:
            response = self.session.get(url, params=params, timeout=self.timeout_seconds)
            response.raise_for_status()
            payload = response.json()
            if cache_path:
                atomic_write_json(payload, cache_path)
            return payload
        except Exception:
            if allow_stale_on_error and cache_path and cache_path.exists():
                return json.loads(cache_path.read_text(encoding="utf-8"))
            raise

    def get_csv_snapshot(
        self,
        url: str,
        *,
        cache_path: Path,
        ttl_seconds: int = 86_400,
        allow_stale_on_error: bool = True,
        row_group_size: int = 50_000,
        **read_csv_kwargs: Any,
    ) -> pd.DataFrame:
        if cache_is_fresh(cache_path, ttl_seconds):
            return pd.read_parquet(cache_path)
        try:
            response = self.session.get(url, timeout=self.timeout_seconds)
            response.raise_for_status()
            frame = pd.read_csv(BytesIO(response.content), **read_csv_kwargs)
            atomic_write_parquet(frame, cache_path, row_group_size=row_group_size)
            return frame
        except Exception:
            if allow_stale_on_error and cache_path.exists():
                return pd.read_parquet(cache_path)
            raise
