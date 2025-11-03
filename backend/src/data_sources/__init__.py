"""Data Sources Layer - Abstraction für verschiedene Datenquellen"""

from .base import DataSource
from .file_loader import FileDataSource

__all__ = ["DataSource", "FileDataSource"]

