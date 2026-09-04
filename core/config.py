"""YAML loader and required-field checks for DDTT main config."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import yaml

REQUIRED_TOP_LEVEL = (
    "POWER_SENSOR_IP1",
    "POWER_SENSOR_IP2",
    "POWER_SENSOR_PROFILE1",
    "POWER_SENSOR_PROFILE2",
    "BBU_IP",
    "pMax",
    "TRAFICC_PROFILE",
    "UE_AND_CELL_INFOS",
)

REQUIRED_TRAFFIC = (
    "SERVER_IP",
    "TECHNOLOGY",
    "CARRIER_BW",
    "PROFILE_RUNNING_TIME",
    "PROFILE_RUNNING_SEQ",
)

REQUIRED_POWER_PROFILE = ("freq_ps", "bandwidth_ps", "loss_ps", "att_ps")


class DdttConfigError(ValueError):
    """Raised when a DDTT YAML config is missing required fields."""


def load_ddtt_config(path: str | Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        try:
            data = yaml.safe_load(handle)
        except yaml.YAMLError as exc:
            raise DdttConfigError(f"invalid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise DdttConfigError("DDTT config must be a YAML mapping")
    validate_ddtt_config(data)
    return data


def validate_ddtt_config(config: Mapping[str, Any]) -> None:
    missing = [key for key in REQUIRED_TOP_LEVEL if key not in config]
    if missing:
        raise DdttConfigError(f"missing top-level keys: {missing}")

    p_max = config["pMax"]
    if not isinstance(p_max, (int, float)):
        raise DdttConfigError("pMax must be a number")

    for profile_key in ("POWER_SENSOR_PROFILE1", "POWER_SENSOR_PROFILE2"):
        profile = config[profile_key]
        if not isinstance(profile, Mapping):
            raise DdttConfigError(f"{profile_key} must be a mapping")
        missing_profile = [key for key in REQUIRED_POWER_PROFILE if key not in profile]
        if missing_profile:
            raise DdttConfigError(f"{profile_key} missing {missing_profile}")

    traffic = config["TRAFICC_PROFILE"]
    if not isinstance(traffic, Mapping):
        raise DdttConfigError("TRAFICC_PROFILE must be a mapping")
    missing_traffic = [key for key in REQUIRED_TRAFFIC if key not in traffic]
    if missing_traffic:
        raise DdttConfigError(f"TRAFICC_PROFILE missing {missing_traffic}")

    infos = config["UE_AND_CELL_INFOS"]
    if not isinstance(infos, list) or not infos:
        raise DdttConfigError("UE_AND_CELL_INFOS must be a non-empty list")
    for index, item in enumerate(infos):
        for field in ("cell_pci", "cell_ssb", "ue_ip", "ue_port"):
            if field not in item:
                raise DdttConfigError(f"UE_AND_CELL_INFOS[{index}] missing {field}")
