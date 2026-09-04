import pytest

from core.ue_identity import validate_ue_identity


def test_ue_identity_matches_config():
    validate_ue_identity(
        config_cellular_ips=["127.0.0.1", "127.0.0.1"],
        config_pcis=["271", "272"],
        observed=["127.0.0.1", "271", "272"],
    )


def test_ue_identity_mismatch_raises():
    with pytest.raises(AssertionError, match="UE info do not match"):
        validate_ue_identity(
            config_cellular_ips=["127.0.0.1"],
            config_pcis=["271"],
            observed=["other-ue-ip", "271"],
        )
