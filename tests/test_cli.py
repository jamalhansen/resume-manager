from pathlib import Path
from resume_manager.cli import main
import sys
from unittest.mock import patch

def test_cli_init(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("RESUME_MANAGER_DB", str(db_path))
    
    with patch.object(sys, 'argv', ['resume-manager', 'init']):
        main()
        
    assert db_path.exists()

def test_cli_import_ecv(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("RESUME_MANAGER_DB", str(db_path))
    
    # Init first
    with patch.object(sys, 'argv', ['resume-manager', 'init']):
        main()
        
    ecv_path = Path("tests/fixtures/sample_ecv.pdf")
    with patch.object(sys, 'argv', ['resume-manager', 'import', '--ecv', str(ecv_path)]):
        main()
        
    # Check if data was imported
    from resume_manager.db import get_connection
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM profile")
    assert cursor.fetchone()[0] == "Jane Doe"
    conn.close()

def test_cli_status(tmp_path, monkeypatch, capsys):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("RESUME_MANAGER_DB", str(db_path))
    
    with patch.object(sys, 'argv', ['resume-manager', 'init']):
        main()
        
    with patch.object(sys, 'argv', ['resume-manager', 'status']):
        main()
        
    captured = capsys.readouterr()
    assert "Database:" in captured.out
    assert "Profile: 0 records" in captured.out
