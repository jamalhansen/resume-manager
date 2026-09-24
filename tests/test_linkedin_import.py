from pathlib import Path

import pytest

from resume_manager.db import get_connection, init_db
from resume_manager.intake.linkedin import import_linkedin


def test_import_linkedin(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    conn = get_connection(db_path)
    
    zip_path = Path("tests/fixtures/sample_linkedin.zip")
    if not zip_path.exists():
        pytest.skip("Fixture sample_linkedin.zip not found")
        
    import_linkedin(zip_path, conn)
    
    cursor = conn.cursor()
    
    # Check profile
    cursor.execute("SELECT name, email, linkedin FROM profile")
    profile = cursor.fetchone()
    assert profile[0] == "Jane Doe"
    assert profile[1] == "jane@example.com"
    assert profile[2] == "https://linkedin.com/in/janedoe"
    
    # Check jobs
    cursor.execute("SELECT company, role FROM jobs")
    job = cursor.fetchone()
    assert job[0] == "Tech Corp"
    assert job[1] == "Senior Engineer"
    
    # Check bullets
    cursor.execute("SELECT content FROM bullets")
    bullets = [row[0] for row in cursor.fetchall()]
    assert "Led a team of 5 to deliver X." in bullets
    assert "Improved performance by 30%." in bullets
    
    conn.close()
