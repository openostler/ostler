"""Web dashboard for real-time diagnostics (HTTP + SSE, stdlib).

`sources` supplies data snapshots (Mock for UI dev, Td5 for the car); `server`
serves the dashboard and streams snapshots via Server-Sent Events.
"""
from .sources import (
    DataSource,
    InfoDataSource,
    MockDataSource,
    MockSlabsDataSource,
    SlabsDataSource,
    Td5DataSource,
    mock_bcu_signals,
)

__all__ = [
    "DataSource", "MockDataSource", "Td5DataSource",
    "SlabsDataSource", "MockSlabsDataSource", "InfoDataSource",
    "mock_bcu_signals",
]
