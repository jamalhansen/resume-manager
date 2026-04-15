import sqlite3
import os
from pathlib import Path
from .schema import SCHEMA

DEFAULT_DB_PATH = Path("~/.local/share/resume-manager/resume.db").expanduser()

def get_db_path(override_path=None):
    if override_path:
        return Path(override_path)
    env_path = os.getenv("RESUME_MANAGER_DB")
    if env_path:
        return Path(env_path).expanduser()
    return DEFAULT_DB_PATH

def init_db(db_path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()

def get_connection(db_path):
    return sqlite3.connect(db_path)
