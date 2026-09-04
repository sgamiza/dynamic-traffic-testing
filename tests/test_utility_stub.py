import numpy as np
from pathlib import Path

from l3_ddtt_tool.utility.utilityLib import (
    consecutive_overshot_measure,
    overlap_check,
    process_array_with_frameLength,
)


ROOT = Path(__file__).resolve().parents[1]


def test_utility_stub_compiles():
    stub = ROOT / "l3_ddtt_tool" / "utility" / "utilityLib.py"
    compile(stub.read_text(encoding="utf-8"), str(stub), "exec")


def test_consecutive_overshot_measure():
    data = np.array([-1.0, 2.0, 3.0, -4.0, 5.0])
    last, lengths = consecutive_overshot_measure(data, 0)
    assert list(lengths) == [0, 1, 2, 0, 1]
    assert last == 1


def test_overlap_check():
    last = np.array([1, 2, 3, 4])
    current = np.array([3, 4, 5, 6])
    assert overlap_check(last, current) == 2
    assert overlap_check(np.array([]), current) == 0


def test_process_array_with_frame_length():
    data = np.arange(10, dtype=float)
    frames, remain, section = process_array_with_frameLength(data, frameLengthMs=4, resolutionMs=1)
    assert section == 4.0
    assert frames.shape[0] == 2
    assert remain.size == 2
