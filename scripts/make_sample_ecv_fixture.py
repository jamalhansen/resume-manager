#!/usr/bin/env python3
"""Regenerate tests/fixtures/sample_ecv.pdf.

The file was referenced by tests/test_cli.py but never committed, so
test_cli_import_ecv and test_cli_generate_dry_run always failed with
FileNotFoundError. This script builds a minimal PDF carrying the same
'/ecv-data' metadata EnhancCV's real export uses, so it exercises
resume_manager.intake.enhancv.extract_enhancv_data's actual decode path.

That decode path has a real quirk worth documenting here since nothing else
does: pypdf round-trips a metadata string containing at least one non-ASCII
character correctly, but for a *pure-ASCII* JSON payload it silently returns
garbage from `raw.encode('latin1').decode('utf-16')` (no exception -- the
byte-pair reinterpretation just succeeds on nonsense). extract_enhancv_data
depends on the UnicodeEncodeError from a non-ASCII character to fall back to
the raw string, so this fixture's summary field deliberately includes an
em dash. A pure-ASCII payload would need extract_enhancv_data itself fixed,
not just a new fixture.

Run from the repo root: uv run scripts/make_sample_ecv_fixture.py
"""
import json
from pathlib import Path

from pypdf import PdfWriter

OUT_PATH = Path(__file__).parent.parent / "tests" / "fixtures" / "sample_ecv.pdf"

PAYLOAD = {
    "header": {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "555-1234",
        "location": "Remote",
        "links": [
            {"title": "LinkedIn", "url": "https://linkedin.com/in/janedoe"},
        ],
        # Em dash is deliberate -- see module docstring.
        "summary": "Senior engineer — test fixture profile.",
    },
    "sections": [
        {
            "type": "ExperienceSection",
            "items": [
                {
                    "company": {"text": "Tech Corp"},
                    "role": {"text": "Senior Engineer"},
                    "startDate": "2020-01",
                    "endDate": "2023-01",
                    "location": "Remote",
                    "description": [
                        {"text": "Led a team of 5 to deliver X."},
                        {"text": "Improved performance by 30%."},
                    ],
                }
            ],
        },
        {
            "type": "TalentSection",
            "items": [{"text": "Python"}, {"text": "SQL"}],
        },
        {
            "type": "EducationSection",
            "items": [
                {
                    "institution": "State University",
                    "degree": "B.S.",
                    "field": "Computer Science",
                    "year": "2019",
                }
            ],
        },
    ],
}


def main() -> None:
    data_str = json.dumps(PAYLOAD, ensure_ascii=False)

    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.add_metadata({"/ecv-data": data_str})

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("wb") as f:
        writer.write(f)

    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
