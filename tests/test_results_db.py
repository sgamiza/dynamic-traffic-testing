from core.judgment import query_powers_above_pmax
from core.results_db import ResultsDB


def test_insert_query_update_delete(tmp_path):
    db_path = tmp_path / "result.db"
    with ResultsDB(db_path) as db:
        db.insert_data("9616", "127.0.0.1", "profile_100", "10", 44.2)
        db.insert_data("9616", "127.0.0.1", "profile_50", "10", 12.0, comment="ok")
        rows = db.query_data()
        assert len(rows) == 2
        assert rows[0][3] == "profile_100"
        assert rows[1][6] == "ok"

        db.update_bandwidth("profile_50", "20")
        updated = [row for row in db.query_data() if row[3] == "profile_50"][0]
        assert updated[4] == "20"

        db.delete_profile("profile_50")
        left = db.query_data()
        assert len(left) == 1
        assert left[0][3] == "profile_100"

        over = query_powers_above_pmax(left, p_max=40)
        assert len(over) == 1
