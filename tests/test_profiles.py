from core.profiles import enabled_profiles, sequence_duration_minutes


def test_zero_runtime_profiles_are_skipped():
    traffic = {
        "PROFILE_RUNNING_TIME": {
            "profile_100": 25,
            "profile_idle": 0,
            "profile_50": 20,
        },
        "PROFILE_RUNNING_SEQ": ["profile_100", "profile_idle", "profile_50"],
    }
    assert enabled_profiles(traffic) == ["profile_100", "profile_50"]
    assert sequence_duration_minutes(traffic) == 45


def test_unknown_sequence_name_is_skipped():
    traffic = {
        "PROFILE_RUNNING_TIME": {"profile_100": 10},
        "PROFILE_RUNNING_SEQ": ["profile_100", "not_defined"],
    }
    assert enabled_profiles(traffic) == ["profile_100"]
