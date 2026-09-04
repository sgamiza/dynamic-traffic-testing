"""UE IP / PCI consistency check used by TestRunnerBase.validate_ue_ip."""

from __future__ import annotations

from typing import Iterable


def validate_ue_identity(
    config_cellular_ips: Iterable[str],
    config_pcis: Iterable[str],
    observed: Iterable[str],
) -> None:
    expected = set(config_cellular_ips) | set(config_pcis)
    actual = set(observed)
    if expected != actual:
        raise AssertionError(f"UE info do not match. UE info is now: {actual}")
