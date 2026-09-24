import json


def insert_profile(conn, name, email=None, phone=None, location=None, linkedin=None, github=None, website=None, summary=None):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM profile LIMIT 1")
    existing = cursor.fetchone()
    if existing:
        cursor.execute("""
            UPDATE profile SET name=?, email=?, phone=?, location=?, linkedin=?, github=?, website=?, summary=?
            WHERE id=?
        """, (name, email, phone, location, linkedin, github, website, summary, existing[0]))
        conn.commit()
        return existing[0]
    else:
        cursor.execute("""
            INSERT INTO profile (name, email, phone, location, linkedin, github, website, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, email, phone, location, linkedin, github, website, summary))
        conn.commit()
        return cursor.lastrowid

def upsert_job(conn, company, role, start_date, end_date=None, location=None, is_remote=0, sort_order=None):
    cursor = conn.cursor()
    # Check if job exists (company + role + start_date)
    cursor.execute("""
        SELECT id FROM jobs WHERE company = ? AND role = ? AND start_date = ?
    """, (company, role, start_date))
    existing = cursor.fetchone()
    if existing:
        job_id = existing[0]
        cursor.execute("""
            UPDATE jobs SET end_date = ?, location = ?, is_remote = ?, sort_order = ?
            WHERE id = ?
        """, (end_date, location, is_remote, sort_order, job_id))
    else:
        cursor.execute("""
            INSERT INTO jobs (company, role, start_date, end_date, location, is_remote, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (company, role, start_date, end_date, location, is_remote, sort_order))
        job_id = cursor.lastrowid
    conn.commit()
    return job_id

def insert_bullet(conn, job_id, content, impact_metric=None, tags=None, interview_questions=None, strength=3):
    cursor = conn.cursor()
    tags_json = json.dumps(tags) if tags else None
    questions_json = json.dumps(interview_questions) if interview_questions else None
    
    cursor.execute("""
        INSERT INTO bullets (job_id, content, impact_metric, tags, interview_questions, strength)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (job_id, content, impact_metric, tags_json, questions_json, strength))
    conn.commit()
    return cursor.lastrowid

def insert_skill(conn, name, description=None, category=None, tags=None, interview_questions=None, strength=3):
    cursor = conn.cursor()
    tags_json = json.dumps(tags) if tags else None
    questions_json = json.dumps(interview_questions) if interview_questions else None
    
    cursor.execute("""
        INSERT INTO skills (name, description, category, tags, interview_questions, strength)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, description, category, tags_json, questions_json, strength))
    conn.commit()
    return cursor.lastrowid

def insert_education(conn, institution, degree=None, field=None, year=None, is_certification=0):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO education (institution, degree, field, year, is_certification)
        VALUES (?, ?, ?, ?, ?)
    """, (institution, degree, field, year, is_certification))
    conn.commit()
    return cursor.lastrowid

def insert_volunteer(conn, organization, role, description=None, start_date=None, end_date=None, tags=None):
    cursor = conn.cursor()
    tags_json = json.dumps(tags) if tags else None
    cursor.execute("""
        INSERT INTO volunteer (organization, role, description, start_date, end_date, tags)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (organization, role, description, start_date, end_date, tags_json))
    conn.commit()
    return cursor.lastrowid

def get_all_content(conn):
    cursor = conn.cursor()
    
    # Profile
    cursor.execute("SELECT * FROM profile LIMIT 1")
    profile_row = cursor.fetchone()
    profile = {}
    if profile_row:
        columns = [d[0] for d in cursor.description]
        profile = dict(zip(columns, profile_row))
    
    # Jobs and bullets
    cursor.execute("SELECT * FROM jobs ORDER BY start_date DESC")
    job_rows = cursor.fetchall()
    jobs = []
    job_columns = [d[0] for d in cursor.description]
    for row in job_rows:
        job = dict(zip(job_columns, row))
        cursor.execute("SELECT * FROM bullets WHERE job_id = ?", (job['id'],))
        bullet_rows = cursor.fetchall()
        bullet_columns = [d[0] for d in cursor.description]
        job['bullets'] = [dict(zip(bullet_columns, b)) for b in bullet_rows]
        jobs.append(job)
    
    # Skills
    cursor.execute("SELECT * FROM skills")
    skill_rows = cursor.fetchall()
    skill_columns = [d[0] for d in cursor.description]
    skills = [dict(zip(skill_columns, s)) for s in skill_rows]
    
    # Education
    cursor.execute("SELECT * FROM education")
    edu_rows = cursor.fetchall()
    edu_columns = [d[0] for d in cursor.description]
    education = [dict(zip(edu_columns, e)) for e in edu_rows]
    
    return {
        "profile": profile,
        "jobs": jobs,
        "skills": skills,
        "education": education
    }

def log_resume_generation(conn, job_title, company, template, jd_hash, output_path, config_json):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO resume_log (job_title, company, template, jd_hash, output_path, config_json)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (job_title, company, template, jd_hash, output_path, config_json))
    conn.commit()
    return cursor.lastrowid
