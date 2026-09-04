"""SQLite result store mirroring ``l3_ddtt_tool.database.DeviceDB`` without pandas."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Optional


class ResultsDB:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._conn = sqlite3.connect(self.path)
        self._cursor = self._conn.cursor()
        self._create_table()

    def _create_table(self) -> None:
        self._cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS data (
                id INTEGER PRIMARY KEY,
                pid INTEGER NOT NULL,
                ip TEXT NOT NULL,
                profile TEXT NOT NULL,
                bandwidth TEXT NOT NULL,
                power FLOAT NOT NULL,
                comment TEXT,
                timestamp TEXT DEFAULT (datetime('now', 'localtime'))
            )
            """
        )
        self._conn.commit()

    def insert_data(
        self,
        pid: str,
        ip: str,
        profile: str,
        bandwidth: str,
        power: float,
        comment: Optional[str] = None,
    ) -> None:
        if comment is not None:
            sql = (
                "INSERT INTO data (pid, ip, profile, bandwidth, power, comment) "
                "VALUES (?, ?, ?, ?, ?, ?)"
            )
            params: tuple[Any, ...] = (pid, ip, profile, bandwidth, power, comment)
        else:
            sql = "INSERT INTO data (pid, ip, profile, bandwidth, power) VALUES (?, ?, ?, ?, ?)"
            params = (pid, ip, profile, bandwidth, power)
        self._cursor.execute(sql, params)
        self._conn.commit()

    def query_data(self) -> list[tuple]:
        self._cursor.execute("SELECT * FROM data")
        return self._cursor.fetchall()

    def update_bandwidth(self, profile: str, new_bandwidth: str) -> None:
        self._cursor.execute(
            "UPDATE data SET bandwidth = ? WHERE profile = ?",
            (new_bandwidth, profile),
        )
        self._conn.commit()

    def delete_profile(self, profile: str) -> None:
        self._cursor.execute("DELETE FROM data WHERE profile = ?", (profile,))
        self._conn.commit()

    def close(self) -> None:
        self._cursor.close()
        self._conn.close()

    def __enter__(self) -> "ResultsDB":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
