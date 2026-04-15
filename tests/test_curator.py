from unittest.mock import patch
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
    
    import json
    mock_response_str = json.dumps(mock_response)
    
    with patch("resume_manager.providers.anthropic_provider.AnthropicProvider.complete", return_value=mock_response_str):
        result = curate("Senior Engineer role", "Some experience data")
        assert result["rationale"] == "Test selection"
        assert len(result["jobs"]) == 1
        assert result["jobs"][0]["job_id"] == 1
