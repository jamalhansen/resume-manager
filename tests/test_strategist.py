import json

from local_first_common.testing import MockProvider

from resume_manager.generate.strategist import strategize


def test_strategize_mocked():
    mock_response = {
        "recommendations": "Lead with team growth",
        "ordered_jobs": [{"job_id": 123, "bullets": [789, 456], "framing": "Emphasize team growth"}],
        "question_mappings": [{"question": "Tell me about building a team", "supporting_bullet_ids": [789]}],
    }

    provider = MockProvider(response=json.dumps(mock_response))
    result = strategize(
        {"jobs": [{"job_id": 123, "bullets": [789, 456]}], "skills": []},
        ["Tell me about building a team"],
        provider=provider,
    )
    assert result["recommendations"] == "Lead with team growth"
    assert result["ordered_jobs"][0]["job_id"] == 123
    assert provider.calls
