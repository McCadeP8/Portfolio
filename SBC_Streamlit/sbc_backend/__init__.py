"""Backend services for SBC Streamlit.

The package deliberately has no Streamlit dependency.  UI code may cache the
small results returned by these services, while ingestion jobs can use the
same storage and provider contracts from a scheduler or command line.
"""

from .config import BackendSettings, LiveMode
from .datasets import DatasetRepository, get_repository

__all__ = ["BackendSettings", "DatasetRepository", "LiveMode", "get_repository"]
