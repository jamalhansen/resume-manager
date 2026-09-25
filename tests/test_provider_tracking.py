"""LLM calls are logged once, by llm-gateway-service, attributed via resolve_provider's
tool_name. The tool itself must not write its own processing_log row for them."""

import json
import os
from unittest.mock import patch

import duckdb
from local_first_common.testing import MockProvider

from resume_manager.generate import curator, strategist


def _resume_manager_rows() -> int:
    path = os.environ["LOCAL_FIRST_TRACKING_DB"]
    if not os.path.exists(path):
        return 0
    con = duckdb.connect(path)
    try:
        tables = {t[0] for t in con.execute("SHOW TABLES").fetchall()}
        if "processing_log" not in tables:
            return 0
        return con.execute(
            "SELECT count(*) FROM processing_log WHERE tool_name = 'resume-manager'"
        ).fetchone()[0]
    finally:
        con.close()


def test_curate_resolves_provider_with_tool_name():
    mock = MockProvider(response=json.dumps({"rationale": "r", "jobs": [], "skills": []}))
    with patch.object(curator, "resolve_provider", return_value=mock) as resolve:
        curator.curate("some JD", {"jobs": []})
    assert resolve.call_args.kwargs["tool_name"] == "resume-manager"


def test_strategize_resolves_provider_with_tool_name():
    mock = MockProvider(
        response=json.dumps({"recommendations": "x", "ordered_jobs": [], "question_mappings": []})
    )
    with patch.object(strategist, "resolve_provider", return_value=mock) as resolve:
        strategist.strategize({"jobs": []}, ["a question"])
    assert resolve.call_args.kwargs["tool_name"] == "resume-manager"


def test_llm_calls_are_not_double_logged_by_the_tool():
    before = _resume_manager_rows()
    curator.curate(
        "some JD", {"jobs": []},
        provider=MockProvider(response=json.dumps({"rationale": "r", "jobs": [], "skills": []})),
    )
    assert _resume_manager_rows() == before
