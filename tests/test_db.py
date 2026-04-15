from pathlib import Path
from resume_manager.db import init_db, get_connection, get_db_path

def test_init_db(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    assert db_path.exists()

    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    # Check if tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    expected_tables = ["profile", "jobs", "bullets", "skills", "education", "volunteer", "resume_log", "bios"]
    for table in expected_tables:
        assert table in tables
    
    conn.close()

def test_get_db_path_env(monkeypatch):
    monkeypatch.setenv("RESUME_MANAGER_DB", "/tmp/env_test.db")
    assert get_db_path() == Path("/tmp/env_test.db")

def test_get_db_path_override():
    assert get_db_path("/tmp/override.db") == Path("/tmp/override.db")
