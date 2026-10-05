"""Web dashboard for real-time diagnostics (HTTP + SSE, stdlib).

`sources` supplies data snapshots from the car (Td5, SLABS, info modules); `server`
serves the dashboard and streams snapshots via Server-Sent Events. There is no demo
mode (ADR-0011): simulated sources live only in ``tests/fake_sources.py``.
"""
from .sources import (
    DataSource,
    InfoDataSource,
    SlabsDataSource,
    Td5DataSource,
)

__all__ = ["DataSource", "Td5DataSource", "SlabsDataSource", "InfoDataSource"]
