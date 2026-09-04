"""Power PASS/FAIL used by the original Result.query_power_above_threshold.

Lab code treats a sample as over-limit when::

    power > pMax + 3

The +3 dB margin matches ``l3_ddtt_tool/result.py``.
"""

from __future__ import annotations

from typing import Iterable, Sequence

POWER_MARGIN_DB = 3.0


def power_exceeds_pmax(power_dbm: float, p_max: float, margin_db: float = POWER_MARGIN_DB) -> bool:
    return float(power_dbm) > float(p_max) + float(margin_db)


def query_powers_above_pmax(
    rows: Iterable[Sequence],
    p_max: float,
    power_index: int = 5,
    margin_db: float = POWER_MARGIN_DB,
) -> list[Sequence]:
    """Filter SQLite-style rows whose power column exceeds pMax + margin."""
    hits = []
    for row in rows:
        try:
            power = float(row[power_index])
        except (IndexError, TypeError, ValueError):
            continue
        if power_exceeds_pmax(power, p_max, margin_db):
            hits.append(row)
    return hits
