from core.judgment import POWER_MARGIN_DB, power_exceeds_pmax, query_powers_above_pmax


def test_margin_matches_lab_code():
    assert POWER_MARGIN_DB == 3.0
    assert power_exceeds_pmax(43.1, p_max=40) is True
    assert power_exceeds_pmax(43.0, p_max=40) is False
    assert power_exceeds_pmax(40.0, p_max=40) is False


def test_query_filters_sqlite_style_rows():
    rows = [
        (1, 9616, "127.0.0.1", "profile_100", "10", 44.0, None, "ts"),
        (2, 9616, "127.0.0.1", "profile_50", "10", 41.0, None, "ts"),
        (3, 9616, "127.0.0.1", "profile_30", "10", -13.0, None, "ts"),
    ]
    hits = query_powers_above_pmax(rows, p_max=40)
    assert [row[3] for row in hits] == ["profile_100"]
