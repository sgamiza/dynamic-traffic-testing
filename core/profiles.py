"""Traffic profile scheduling helpers.

A profile with ``PROFILE_RUNNING_TIME == 0`` is skipped, matching the YAML comment
in ``examples/main_config.example.yaml``.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence


def enabled_profiles(traffic_profile: Mapping[str, Any]) -> list[str]:
    times = traffic_profile.get("PROFILE_RUNNING_TIME") or {}
    sequence: Sequence[str] = traffic_profile.get("PROFILE_RUNNING_SEQ") or []
    enabled = []
    for name in sequence:
        minutes = times.get(name, 0)
        try:
            value = float(minutes)
        except (TypeError, ValueError):
            value = 0
        if value > 0:
            enabled.append(name)
    return enabled


def sequence_duration_minutes(traffic_profile: Mapping[str, Any]) -> float:
    times = traffic_profile.get("PROFILE_RUNNING_TIME") or {}
    return sum(float(times.get(name, 0) or 0) for name in enabled_profiles(traffic_profile))
