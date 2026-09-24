import json

from local_first_common.testing import MockProvider

from resume_manager.generate.curator import curate


def test_curate_mocked():
    mock_response = {
        "rationale": "Test selection",
        "jobs": [
            {
                "job_id": 1,
                "bullets": [10, 11],
                "rationale": "Relevant"
            }
        ],
        "skills": [
            {
                "skill_id": 1,
                "rationale": "Key skill"
            }
        ]
    }

    provider = MockProvider(response=json.dumps(mock_response))
    result = curate("Senior Engineer role", "Some experience data", provider=provider)
    assert result["rationale"] == "Test selection"
    assert len(result["jobs"]) == 1
    assert result["jobs"][0]["job_id"] == 1
    assert provider.calls  # the curator prompt was actually sent
