from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from resume_manager.cli import app

runner = CliRunner()


def main_with(args):
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output
    print(result.output, end="")


def test_cli_init(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("RESUME_MANAGER_DB", str(db_path))
    
    main_with(['init'])
        
    assert db_path.exists()

def test_cli_import_ecv(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("RESUME_MANAGER_DB", str(db_path))
    
    # Init first
    main_with(['init'])
        
    ecv_path = Path("tests/fixtures/sample_ecv.pdf")
    main_with(['import', '--ecv', str(ecv_path)])
        
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
    
    main_with(['init'])
        
    main_with(['status'])
        
    captured = capsys.readouterr()
    assert "Database:" in captured.out
    assert "Profile: 0 records" in captured.out

def test_cli_generate_dry_run(tmp_path, monkeypatch, capsys):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("RESUME_MANAGER_DB", str(db_path))
    
    # Init and import
    main_with(['init'])
    ecv_path = Path("tests/fixtures/sample_ecv.pdf")
    main_with(['import', '--ecv', str(ecv_path)])
        
    jd_file = tmp_path / "jd.txt"
    jd_file.write_text("Senior Engineer role at Tech Corp")
    
    # Mock curator
    mock_selection = {
        "rationale": "Selected best items",
        "jobs": [{"job_id": 1, "bullets": [1]}],
        "skills": []
    }
    
    with patch("resume_manager.generate.curator.curate", return_value=mock_selection):
        main_with(["generate", str(jd_file), "--dry-run"])

    captured = capsys.readouterr()
    assert "Dry run: Selection details" in captured.out
    assert "Selected best items" in captured.out


def test_several_target_questions_after_one_flag(tmp_path, monkeypatch):
    """argparse's nargs="+" syntax still works: --target-questions "q1" "q2"."""
    monkeypatch.setenv("RESUME_MANAGER_DB", str(tmp_path / "test.db"))
    main_with(["init"])
    jd = tmp_path / "jd.txt"
    jd.write_text("JD")
    seen = {}
    with patch("resume_manager.generate.curator.curate", return_value={"jobs": [], "skills": []}), \
         patch("resume_manager.generate.strategist.strategize",
               side_effect=lambda sel, qs, **kw: seen.setdefault("qs", qs) and {"recommendations": ""}):
        main_with(["generate", str(jd), "--dry-run", "--target-questions", "Why us?", "Biggest win?"])
    assert seen["qs"] == ["Why us?", "Biggest win?"]


def test_stray_arguments_are_a_usage_error(tmp_path, monkeypatch):
    monkeypatch.setenv("RESUME_MANAGER_DB", str(tmp_path / "test.db"))
    result = runner.invoke(app, ["generate", "jd.txt", "extra", "--dry-run"])
    assert result.exit_code == 2
