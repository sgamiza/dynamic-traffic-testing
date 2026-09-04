from pathlib import Path

import pytest

from core.config import DdttConfigError, load_ddtt_config, validate_ddtt_config

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "main_config.example.yaml"


def test_example_yaml_loads_and_validates():
    config = load_ddtt_config(EXAMPLE)
    assert config["pMax"] == 40
    assert config["POWER_SENSOR_IP1"] == "127.0.0.1"
    assert "PROFILE_RUNNING_SEQ" in config["TRAFICC_PROFILE"]
    assert len(config["UE_AND_CELL_INFOS"]) >= 1


def test_missing_pmax_raises():
    config = load_ddtt_config(EXAMPLE)
    del config["pMax"]
    with pytest.raises(DdttConfigError, match="pMax"):
        validate_ddtt_config(config)


def test_empty_ue_list_raises():
    config = load_ddtt_config(EXAMPLE)
    config["UE_AND_CELL_INFOS"] = []
    with pytest.raises(DdttConfigError, match="UE_AND_CELL_INFOS"):
        validate_ddtt_config(config)


def test_non_mapping_yaml_raises(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text("- just a list\n", encoding="utf-8")
    with pytest.raises(DdttConfigError, match="mapping"):
        load_ddtt_config(path)
