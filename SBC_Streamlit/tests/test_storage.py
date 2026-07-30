from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from sbc_backend.storage import FileLock, LockUnavailable, atomic_write_parquet


class StorageTests(unittest.TestCase):
    def test_atomic_parquet_uses_bounded_row_groups(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "frame.parquet"
            atomic_write_parquet(pd.DataFrame({"value": range(2_501)}), path, row_group_size=1_000)
            self.assertEqual(pd.read_parquet(path)["value"].tolist(), list(range(2_501)))
            self.assertEqual(pq.ParquetFile(path).metadata.num_row_groups, 3)
            self.assertEqual(list(path.parent.glob("*.tmp")), [])

    def test_lock_rejects_a_second_writer(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "refresh.lock"
            with FileLock(path):
                with self.assertRaises(LockUnavailable):
                    FileLock(path).acquire()
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
