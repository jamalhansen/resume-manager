"""The command-line contract: what resume-manager prints and exits with, as golden output.

A change of CLI framework must not change it. Runs the installed script against a temp
database; LLM-backed and PDF-rendering paths are covered by their own tests, not here.
Re-record deliberately with RECORD_CLI_CONTRACT=1.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

GOLDEN = Path(__file__).parent / "golden" / "cli_contract.json"
SCRIPT = Path(sys.executable).parent / "resume-manager"
ECV = Path(__file__).parent / "fixtures" / "sample_ecv.pdf"

SEQUENCE = [
    ["status"],
    ["list", "jobs"],
    ["generate", "{T}/jd.txt", "--dry-run"],
    ["-v", "init"],
    ["status"],
    ["import", "--ecv", "{E}"],
    ["--verbose", "import", "--ecv", "{E}"],
    ["status"],
    ["list", "jobs"],
    ["list", "bullets"],
    ["list", "bullets", "--job-id", "1"],
    ["list", "skills"],
    ["list", "education"],
    ["list", "logs"],
    ["list", "nothing"],
    ["list", "bullets", "--job-id", "x"],
    ["edit", "job"],
    ["edit", "job", "999"],
    ["edit", "job", "1"],
    ["edit", "profile"],
    ["edit", "unknown"],
    ["generate", "{T}/missing-jd.txt", "--dry-run"],
    ["generate", "{T}/jd.txt", "--template", "fancy"],
    ["--db", "{T}/other.db", "status"],
    ["--db", "{T}/other.db", "init"],
    ["--db", "{T}/other.db", "status"],
    ["demo", "--template", "fancy"],
    ["bogus"],
    [],
]


def _results(tmp: Path) -> list[dict]:
    (tmp / "jd.txt").write_text("A job description.")
    env = {**os.environ, "RESUME_MANAGER_DB": str(tmp / "resume.db"), "EDITOR": "true",
           "LOCAL_FIRST_TRACKING_DB": str(tmp / "tracking.duckdb")}
    out = []
    for argv in SEQUENCE:
        args = [a.replace("{T}", str(tmp)).replace("{E}", str(ECV)) for a in argv]
        proc = subprocess.run([str(SCRIPT), *args], capture_output=True, text=True, env=env, cwd=tmp, check=False)
        norm = lambda t: t.replace(str(tmp), "<TMP>").replace(str(ECV.parent), "<FIXTURES>")
        result = {"argv": argv, "exit": proc.returncode}
        if argv and proc.returncode != 2:  # usage errors and bare help: only the exit code is contract
            result["stdout"] = norm(proc.stdout)
            result["stderr"] = norm(proc.stderr)
        out.append(result)
    return out


def test_cli_contract(tmp_path):
    results = _results(tmp_path)
    if os.environ.get("RECORD_CLI_CONTRACT"):
        GOLDEN.parent.mkdir(exist_ok=True)
        GOLDEN.write_text(json.dumps(results, indent=2) + "\n")
        pytest.skip("recorded")
    assert results == json.loads(GOLDEN.read_text())
