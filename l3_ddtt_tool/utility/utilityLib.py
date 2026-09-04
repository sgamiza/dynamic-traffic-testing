"""Pure-Python stand-in for the original compiled utility helper.

The original deployment used a compiled extension. This stub keeps the
public API so the rest of the package can be reviewed and unit-tested
without shipping a binary.
"""
from __future__ import annotations

import time
from typing import Tuple

import numpy as np


def delay(delay_s: float) -> None:
    time.sleep(delay_s)


def consecutive_overshot_measure(input_data: np.ndarray, last_pos_value_length: int) -> Tuple[int, np.ndarray]:
    values = np.asarray(input_data, dtype=float).ravel()
    positives = values > 0
    lengths = []
    current = last_pos_value_length
    for flag in positives:
        if flag:
            current += 1
            lengths.append(current)
        else:
            current = 0
            lengths.append(0)
    last = int(lengths[-1]) if lengths else 0
    return last, np.asarray(lengths, dtype=int)


def overlap_check(lastdata: np.ndarray, currentdata: np.ndarray) -> int:
    last = np.asarray(lastdata).ravel()
    current = np.asarray(currentdata).ravel()
    if last.size == 0 or current.size == 0:
        return 0
    max_len = min(last.size, current.size)
    for size in range(max_len, 0, -1):
        if np.array_equal(last[-size:], current[:size]):
            return size
    return 0


def process_array_with_frameLength(
    dataArray: np.ndarray,
    frameLengthMs: float,
    resolutionMs: float,
    duplex: str = "TDD",
) -> Tuple[np.ndarray, np.ndarray, float]:
    data = np.asarray(dataArray, dtype=float).ravel()
    if resolutionMs <= 0:
        raise ValueError("resolutionMs must be > 0")
    section_length = float(frameLengthMs)
    points = max(1, int(round(frameLengthMs / resolutionMs)))
    usable = (data.size // points) * points
    if usable == 0:
        return np.array([]), data, section_length
    frames = data[:usable].reshape(-1, points)
    remain = data[usable:]
    return frames.max(axis=1), remain, section_length
