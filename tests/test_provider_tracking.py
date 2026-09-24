"""resume-manager had its own copy of the provider abstraction (BaseProvider,
AnthropicProvider, GeminiProvider, LocalProvider) instead of using
local_first_common.providers -- no fallback, no tracking, no MockProvider.
Migrated 2026-09-24; these confirm curate()/strategize() now log to the
fleet's processing_log like every other tool."""

import json
import os

import duckdb
from local_first_common.testing import MockProvider

from resume_manager.generate.curator import curate
from resume_manager.generate.strategist import strategize


def _tracking_db():
    return duckdb.connect(os.environ["LOCAL_FIRST_TRACKING_DB"])


def test_curate_logs_a_processing_run():
    provider = MockProvider(response=json.dumps({"rationale": "r", "jobs": [], "skills": []}))
    curate("some JD", {"jobs": []}, provider=provider)

    row = _tracking_db().execute(
        "SELECT tool_name, model, provider, success FROM processing_log "
        "WHERE tool_name = 'resume-manager' ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    assert row == ("resume-manager", "mock", "mock", True)


def test_curate_logs_a_failed_run_on_bad_json():
    provider = MockProvider(response="not json at all")

    try:
        curate("some JD", {"jobs": []}, provider=provider)
    except ValueError:
        pass

    row = _tracking_db().execute(
        "SELECT success FROM processing_log WHERE tool_name = 'resume-manager' ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    assert row == (False,)


def test_strategize_logs_a_processing_run():
    provider = MockProvider(response=json.dumps({"recommendations": "x", "ordered_jobs": [], "question_mappings": []}))
    strategize({"jobs": []}, ["a question"], provider=provider)

    row = _tracking_db().execute(
        "SELECT tool_name, success FROM processing_log WHERE tool_name = 'resume-manager' ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    assert row == ("resume-manager", True)
