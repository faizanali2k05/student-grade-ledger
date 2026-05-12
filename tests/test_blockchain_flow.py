import os
import shutil
from ledger.db import GradeLedgerDB
from ledger.blockchain import BlockchainEngine
from ledger.models import Grade


def test_block_mining_and_commit():
    test_db_path = "database/test_ledger.db"

    # ensure clean state
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    db = GradeLedgerDB(test_db_path)
    engine = BlockchainEngine(db, difficulty=1)

    # Add 10 grades
    for i in range(10):
        g = Grade(
            student_id=f"S{i}",
            student_name=f"Student {i}",
            course_code=f"CSE{i}",
            grade="A",
            valid_time="Spring 2024"
        )
        success, msg = engine.add_grade(g)
        assert success is True

    # After adding 10, one block should have been mined
    total_blocks = db.get_total_blocks()
    total_txs = db.get_total_transactions()
    assert total_blocks >= 1
    assert total_txs >= 10

    # cleanup
    try:
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
    except Exception:
        pass
