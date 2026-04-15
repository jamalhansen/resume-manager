# resume_manager/db/schema.py

SCHEMA = """
-- Profile (one row, personal identity)
CREATE TABLE IF NOT EXISTS profile (
    id       INTEGER PRIMARY KEY,
    name     TEXT NOT NULL,
    email    TEXT,
    phone    TEXT,
    location TEXT,
    linkedin TEXT,
    github   TEXT,
    website  TEXT,
    summary  TEXT    -- 2-3 sentence professional summary
);

-- Jobs (one row per role held)
CREATE TABLE IF NOT EXISTS jobs (
    id         INTEGER PRIMARY KEY,
    company    TEXT NOT NULL,
    role       TEXT NOT NULL,
    start_date TEXT NOT NULL,   -- YYYY-MM or YYYY
    end_date   TEXT,            -- NULL = present
    location   TEXT,
    is_remote  INTEGER DEFAULT 0,
    sort_order INTEGER           -- override for non-chronological display
);

-- Bullets (many per job; the atomic unit of experience)
CREATE TABLE IF NOT EXISTS bullets (
    id                  INTEGER PRIMARY KEY,
    job_id              INTEGER NOT NULL REFERENCES jobs(id),
    content             TEXT NOT NULL,
    impact_metric       TEXT,   -- extracted quantifiable: "$20M savings", "30% reduction"
    tags                TEXT,   -- JSON array: domains ["risk", "data", "leadership"]
    interview_questions TEXT,   -- JSON array: questions this bullet is engineered to prompt
    strength            INTEGER DEFAULT 3, -- 1-5; curator uses this as a tiebreaker
    created_at          TEXT DEFAULT (datetime('now')),
    updated_at          TEXT DEFAULT (datetime('now'))
);

-- Skills (talent section items)
CREATE TABLE IF NOT EXISTS skills (
    id                  INTEGER PRIMARY KEY,
    name                TEXT NOT NULL,
    description         TEXT,
    category            TEXT,   -- "technical" | "leadership" | "domain"
    tags                TEXT,   -- JSON array
    interview_questions TEXT,   -- JSON array
    strength            INTEGER DEFAULT 3
);

-- Education and certifications
CREATE TABLE IF NOT EXISTS education (
    id                 INTEGER PRIMARY KEY,
    institution        TEXT NOT NULL,
    degree             TEXT,
    field              TEXT,
    year               TEXT,
    is_certification   INTEGER DEFAULT 0
);

-- Volunteer and community work
CREATE TABLE IF NOT EXISTS volunteer (
    id          INTEGER PRIMARY KEY,
    organization TEXT NOT NULL,
    role        TEXT NOT NULL,
    description TEXT,
    start_date  TEXT,
    end_date    TEXT,
    tags        TEXT    -- JSON array
);

-- Generated resume log (for audit trail)
CREATE TABLE IF NOT EXISTS resume_log (
    id           INTEGER PRIMARY KEY,
    created_at   TEXT DEFAULT (datetime('now')),
    job_title    TEXT,
    company      TEXT,
    template     TEXT,
    jd_hash      TEXT,   -- SHA256 of job description used
    output_path  TEXT,
    config_json  TEXT    -- full generation config as JSON
);

-- Bios (future: platform-specific professional bios)
CREATE TABLE IF NOT EXISTS bios (
    id          INTEGER PRIMARY KEY,
    platform    TEXT,   -- "linkedin" | "github" | "twitter" | "speaker"
    content     TEXT,
    word_count  INTEGER,
    created_at  TEXT DEFAULT (datetime('now'))
);
"""
