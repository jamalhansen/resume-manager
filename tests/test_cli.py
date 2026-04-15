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

def test_cli_generate_dry_run(tmp_path, monkeypatch, capsys):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("RESUME_MANAGER_DB", str(db_path))
    
    # Init and import
    with patch.object(sys, 'argv', ['resume-manager', 'init']):
        main()
    ecv_path = Path("tests/fixtures/sample_ecv.pdf")
    with patch.object(sys, 'argv', ['resume-manager', 'import', '--ecv', str(ecv_path)]):
        main()
        
    jd_file = tmp_path / "jd.txt"
    jd_file.write_text("Senior Engineer role at Tech Corp")
    
    # Mock curator
    mock_selection = {
        "rationale": "Selected best items",
        "jobs": [{"job_id": 1, "bullets": [1]}],
        "skills": []
    }
    
    with patch("resume_manager.generate.curator.curate", return_value=mock_selection):
        with patch.object(sys, 'argv', ['resume-manager', 'generate', str(jd_file), '--dry-run']):
            main()
            
    captured = capsys.readouterr()
    assert "Dry run: Selection details" in captured.out
    assert "Selected best items" in captured.out
