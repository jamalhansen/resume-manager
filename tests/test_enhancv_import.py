import pytest
from pathlib import Path
from resume_manager.db import init_db, get_connection
from resume_manager.intake.enhancv import import_enhancv

def test_import_enhancv(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    conn = get_connection(db_path)
    
    pdf_path = Path("tests/fixtures/sample_ecv.pdf")
    if not pdf_path.exists():
        pytest.skip("Fixture sample_ecv.pdf not found")
        
    import_enhancv(pdf_path, conn)
    
    cursor = conn.cursor()
    
    # Check profile
    cursor.execute("SELECT name, email FROM profile")
    profile = cursor.fetchone()
    assert profile[0] == "Jane Doe"
    assert profile[1] == "jane@example.com"
    
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
    
    # Check skills
    cursor.execute("SELECT name FROM skills")
    skills = [row[0] for row in cursor.fetchall()]
    assert "Python" in skills
    assert "SQL" in skills
    
    conn.close()
