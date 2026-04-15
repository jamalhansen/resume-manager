# Resume Manager -- Implementation Plan

> This document is the authoritative spec for the resume-manager CLI tool.
> It is written to be followed by an AI implementer (Gemini) without requiring
> major architectural decisions. All decisions are made here with rationale.

---

## What This Tool Does

A command-line tool that maintains a structured database of professional experience
and generates tailored, branded resume PDFs for specific roles. The AI layer selects
and strategically orders content from the database to match a target role and to
engineer specific interview questions. Output is a PDF rendered from owned HTML/CSS
templates using Jamal's personal brand system.

**Secondary use case (future):** The same database powers bio generation for LinkedIn,
GitHub, speaker profiles, and social media. Same content, different rendering.

---

## Architecture Decisions

### Data store: SQLite at `~/.local/share/resume-manager/resume.db`

All personal data lives outside the repo. The database path resolves in this order:
1. `--db` CLI flag
2. `RESUME_MANAGER_DB` environment variable
3. `~/.local/share/resume-manager/resume.db` (default)

The repo ships with no personal data. Tests use synthetic fixture data in
`tests/fixtures/demo_profile.json`. Demo mode uses the same fixtures.

### Rendering: HTML/CSS + Playwright

Jinja2 templates render experience items to HTML. Playwright converts to PDF.
This lets templates be iterated in CSS without touching rendering logic, and
enables Jamal's brand system (fonts, colors, accent bars) to apply directly.

Two templates ship initially:
- `brand` -- jamalhansen brand system (dark canvas, emerald/gold accents)
- `compact` -- clean two-column layout matching the current EnhancCV visual structure

### LLM integration: multi-provider, generate step only

The LLM is only invoked during `generate`. It acts as:
1. **Curator** -- selects which bullets and skills are relevant for the target role
2. **Strategist** -- identifies which selected items will prompt target interview questions
3. **Rewriter** (optional, `--rewrite` flag) -- lightly rewrites selected bullets to
   fit role vocabulary while preserving the author's voice

Provider abstraction follows the standard pattern (see: transcription-summarizer).
Default provider: `anthropic`. Default model: `claude-sonnet-4-6`.

### Import: EnhancCV PDF + LinkedIn export

The EnhancCV PDF format embeds a UTF-16 JSON blob in the `/ecv-data` PDF metadata
field. This is already proven to work (see extraction notes). LinkedIn exports as
a zip containing `Profile.csv`, `Positions.csv`, `Education.csv`, `Certifications.csv`.

---

## Directory Structure

```
resume-manager/
├── Makefile                    # include $(HOME)/projects/py-tooling/Makefile.common
├── pyproject.toml
├── .python-version
├── README.md
├── resume_manager/
│   ├── __init__.py
│   ├── cli.py                  # argparse entry point
│   ├── db/
│   │   ├── __init__.py
│   │   ├── schema.py           # CREATE TABLE statements + migrations
│   │   └── queries.py          # typed query functions (no raw SQL at call sites)
│   ├── intake/
│   │   ├── __init__.py
│   │   ├── enhancv.py          # EnhancCV PDF importer
│   │   ├── linkedin.py         # LinkedIn zip export importer
│   │   └── chat.py             # chat-based gap-fill intake
│   ├── generate/
│   │   ├── __init__.py
│   │   ├── curator.py          # LLM curator: select + order items for a role
│   │   └── strategist.py       # LLM strategist: map items to interview questions
│   ├── render/
│   │   ├── __init__.py
│   │   ├── renderer.py         # Playwright PDF renderer
│   │   └── templates/
│   │       ├── brand.html.j2   # jamalhansen brand system template
│   │       └── compact.html.j2 # two-column compact template
│   ├── providers/
│   │   ├── __init__.py         # PROVIDERS dict mapping names to classes
│   │   ├── base.py             # abstract BaseProvider
│   │   ├── anthropic_provider.py
│   │   ├── gemini_provider.py
│   │   └── local_provider.py   # Ollama, fetches models from /api/tags
│   └── demo/
│       └── synthetic.py        # loads demo_profile.json, generates demo resume
├── tests/
│   ├── fixtures/
│   │   ├── demo_profile.json   # synthetic personal data (NOT real)
│   │   ├── sample_jd.txt       # synthetic job description for tests
│   │   └── sample_ecv.pdf      # synthetic EnhancCV-format PDF for import tests
│   ├── test_db.py
│   ├── test_enhancv_import.py
│   ├── test_linkedin_import.py
│   ├── test_curator.py
│   ├── test_renderer.py
│   └── test_cli.py
└── output/                     # gitignored -- generated PDFs land here by default
```

---

## Database Schema

```sql
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
```

---

## CLI Interface

Entry point: `resume-manager` (or `rm` alias via Makefile).

All commands support `--db <path>` and `--verbose / -v`. Commands that call an LLM
support `--provider / -p` and `--model / -m`. Commands that write files support
`--dry-run / -n`.

### `resume-manager init`

Set up database. If no `--db` flag, creates at default path. Runs `CREATE TABLE IF
NOT EXISTS` for all tables. Does NOT prompt for personal info -- use `resume-manager
chat --intake` to populate the profile interactively.

```
resume-manager init [--db PATH]
```

### `resume-manager import`

Import from an existing source.

```
resume-manager import --ecv <pdf-path>      # EnhancCV PDF
resume-manager import --linkedin <zip-path> # LinkedIn data export zip
```

**EnhancCV import behavior:**
- Reads `/ecv-data` PDF metadata field, decodes UTF-16 JSON
- Maps ExperienceSection items to `jobs` + `bullets` tables
- Maps TalentSection items to `skills` table
- Maps VolunteerSection items to `volunteer` table
- Maps EducationSection items to `education` table
- Maps header to `profile` table
- On conflict (same company + role + start_date): prompts user to skip, overwrite, or merge

**LinkedIn import behavior:**
- Reads `Positions.csv` -> `jobs` + stub `bullets`
- Reads `Education.csv` -> `education`
- Reads `Certifications.csv` -> `education` (is_certification=1)
- Reads `Profile.csv` -> `profile`
- Does not import LinkedIn connections or messages

### `resume-manager chat`

Interactive LLM-powered chat intake. Two modes:

```
resume-manager chat --intake    # onboarding: populate profile from scratch via conversation
resume-manager chat --gap-fill  # review existing profile and fill missing fields
resume-manager chat --bullets <job-id>  # add/refine bullets for a specific job
```

The chat system prompts operate in "interrogator not generator" mode: the LLM asks
targeted questions to extract information from the user, then converts responses to
structured database records. The LLM does not invent content -- it only extracts and
structures what the user says.

At end of each chat session, show a summary of what was added and ask for confirmation
before writing to the database.

### `resume-manager generate`

Core command. Takes a job description, runs the LLM pipeline, renders a PDF.

```
resume-manager generate <jd-file>
    --template brand|compact     (default: brand)
    --title "VP of Data"         (override headline title; default: auto-inferred from JD)
    --target-questions "Q1" "Q2" (interview questions to engineer toward)
    --sections experience,skills,education,volunteer  (which sections, in order)
    --max-bullets <n>            (per job; default: 3-5 based on recency/relevance)
    --rewrite                    (allow LLM to lightly rewrite bullet language; off by default)
    --output <path>              (default: ./output/resume-YYYYMMDD-<company>.pdf)
    --provider / -p              (default: anthropic)
    --model / -m
    --dry-run / -n               (print selected items, do not render PDF)
    --verbose / -v
```

**Generate pipeline (in order):**

1. Read job description from file (plain text or PDF via Playwright extraction)
2. Load all database content
3. **Curator step** (LLM): Given the job description and all bullets/skills, select the
   most relevant items. Return a ranked list with rationale. Respect `strength` scores
   as a tiebreaker. Produce a selection config JSON.
4. **Strategist step** (LLM): Given the selected items and any `--target-questions`,
   recommend ordering and framing adjustments that will prompt desired interview
   questions. Annotate the selection config with question-mapping.
5. **Rewrite step** (LLM, only if `--rewrite`): For each selected bullet, optionally
   suggest a light rewrite to better fit the role's vocabulary. Show diff to user,
   require confirmation before using rewritten version. Never overwrite the source
   database -- rewrites are ephemeral to the render.
6. **Render step**: Pass selection config to Jinja2 template, render HTML, convert to
   PDF via Playwright.
7. Log the generation run to `resume_log`.

**LLM prompts for curator and strategist are in `generate/prompts/` as `.txt` files
with Jinja2 interpolation.** This keeps prompts editable without touching Python code.

### `resume-manager demo`

Generate a full resume using synthetic data from `tests/fixtures/demo_profile.json`.
Writes to `./output/demo-resume.pdf`. No database required. Safe to share and test
rendering without any personal information.

```
resume-manager demo [--template brand|compact] [--output <path>]
```

### `resume-manager list`

Show database contents in a readable format.

```
resume-manager list jobs
resume-manager list bullets [--job-id <id>]
resume-manager list skills
resume-manager list education
```

### `resume-manager edit`

Open a specific record for editing in `$EDITOR` as YAML, then write back to database.

```
resume-manager edit bullet <id>
resume-manager edit job <id>
resume-manager edit skill <id>
```

### `resume-manager status`

Print database stats: number of jobs, bullets, skills, last generated, etc.

---

## HTML/CSS Templates

### Brand template (`brand.html.j2`)

Uses the jamalhansen brand system. Reference: `~/vaults/BrainSync/brand/brand-system.md`.

```
Colors:
  Background:      #1d1e20 (dark canvas)
  Surface/card:    #2e2e33
  Primary text:    #dadadb
  Secondary text:  #9b9c9d
  Primary accent:  #10b981 (emerald) -- section headers, accent bars
  Secondary accent:#DFD150 (gold)    -- impact metrics, callouts

Fonts (Google Fonts):
  Headings: Plus Jakarta Sans 700/800
  Body:     Inter 400/500
  (No code font needed for resumes)
```

Layout: Single page, two-column (60/40 split). Left column: experience. Right column:
skills, education, volunteer, contact. Name and title in a full-width header zone with
a 3px emerald left accent bar (matching brand carousel style).

Impact metrics (e.g., "$20M savings", "30% reduction") rendered in gold to draw the
interviewer's eye to the exact bullets designed to generate questions.

### Compact template (`compact.html.j2`)

Clean two-column layout matching the visual structure of the current EnhancCV resumes
(similar proportions, no brand colors). Good for conservative roles or ATS submission.
Black and white safe.

---

## LLM Provider Abstraction

Follow the multi-provider pattern documented in the global CLAUDE.md.

```python
# providers/base.py
class BaseProvider(ABC):
    default_model: str
    known_models: list[str]
    models_url: str

    @abstractmethod
    def complete(self, system: str, user: str) -> str: ...
```

```python
# providers/__init__.py
PROVIDERS = {
    "anthropic": AnthropicProvider,
    "gemini":    GeminiProvider,
    "local":     LocalProvider,   # Ollama; fetches installed models from /api/tags
}
```

Default provider: `anthropic`. Default model per provider set in the class.

Each provider catches its own API errors and raises `RuntimeError` with a clear message.
On model-not-found, include `known_models` list and `models_url` in the error.

---

## Personal Data Safety

### What MUST NOT go in the repo

- Real name, email, phone, location, LinkedIn URL in any committed file
- Any imported resume content
- Generated PDFs
- The SQLite database file
- Any `.env` file with real values

### How to enforce this

`.gitignore` must include:
```
output/
*.db
*.pdf
.env
data/
```

`.env.example` ships in repo with placeholder values:
```
RESUME_MANAGER_DB=~/.local/share/resume-manager/resume.db
ANTHROPIC_API_KEY=your-key-here
GEMINI_API_KEY=your-key-here
```

`tests/fixtures/demo_profile.json` uses fully synthetic data:
```json
{
  "name": "Alex Rivera",
  "email": "alex.rivera@example.com",
  "phone": "(555) 000-0000",
  "location": "Austin, Texas",
  ...
}
```

The pre-commit hook (from py-tooling) should add a check that scans staged files for
the real name "Jamal Hansen" and blocks the commit if found outside of `PLAN.md` or
`README.md`.

---

## Testing Requirements

- One test file per module: `test_<module>.py`
- Organized into classes: `class TestEnhancvImport:`
- Mock all LLM calls -- never make real API calls in tests
- Mock Playwright -- test the HTML output, not the PDF render
- Use `tmp_path` fixture for all file I/O
- `tests/fixtures/sample_ecv.pdf` is a synthetic EnhancCV-format PDF with no real data

Run tests: `uv run pytest`

---

## Setup / First Run

### Initial setup (run once)

```bash
cd ~/projects/resume-manager
make          # runs check-hooks, confirms tooling
uv run resume-manager init
```

### Importing existing resumes

```bash
# Import the EnhancCV resumes
uv run resume-manager import --ecv ~/iCloud/Documents/resume/JamalHansenResume.pdf
uv run resume-manager import --ecv ~/iCloud/Documents/resume/chase/Jamal\ Hansen\ Resume.pdf
# (duplicates detected on second import -- merge prompt appears)
```

### Generating a tailored resume

```bash
# Save job description to a text file
uv run resume-manager generate job-description.txt \
    --title "Executive Director, Data Analytics" \
    --template brand \
    --target-questions "Tell me about building a team" "How do you connect data to strategy" \
    --output ./output/resume-director-2026.pdf
```

### Checking output without rendering

```bash
uv run resume-manager generate job-description.txt --dry-run --verbose
```

---

## Implementation Phases

Implement in this order. Each phase should leave the tool in a working state.

### Phase 1: Foundation

1. `uv init` with pyproject.toml
2. `Makefile` with `include $(HOME)/projects/py-tooling/Makefile.common`
3. Run `python3 ~/projects/py-tooling/install_hooks.py --repo .`
4. Run `make check-hooks` and confirm it passes before writing any other code.
   If it fails, fix the hook installation before proceeding. Do not work around it.
5. Make an initial commit: `git init`, stage `Makefile`, `pyproject.toml`, `.gitignore`,
   `.env.example`, then commit. This establishes the hook baseline so all subsequent
   commits run through the hooks correctly.
6. `.gitignore` with all personal data paths
7. `.env.example`
8. `db/schema.py` with all CREATE TABLE statements
9. `resume-manager init` command
10. `resume-manager status` command
11. `uv run pytest` -- confirm all Phase 1 tests pass
12. Commit Phase 1

### Phase 2: Import

1. `intake/enhancv.py` -- EnhancCV PDF importer (decoder is already proven)
2. `intake/linkedin.py` -- LinkedIn zip importer
3. `resume-manager import --ecv` and `--linkedin`
4. Tests for both importers using synthetic fixture files
5. `uv run pytest` -- confirm all tests pass
6. Commit Phase 2

### Phase 3: Providers and Curator

1. `providers/` package with `BaseProvider`, `AnthropicProvider`, `GeminiProvider`, `LocalProvider`
2. `generate/prompts/curator.txt` -- curator system and user prompt templates
3. `generate/curator.py` -- LLM curator logic
4. `generate/prompts/strategist.txt`
5. `generate/strategist.py`
6. Tests with mocked LLM calls
7. `uv run pytest` -- confirm all tests pass
8. Commit Phase 3

### Phase 4: Render

1. `render/templates/compact.html.j2` -- compact two-column template first
2. `render/renderer.py` -- Playwright HTML-to-PDF
3. `render/templates/brand.html.j2` -- brand system template
4. `resume-manager demo` command using synthetic fixtures
5. Tests for HTML output (not PDF)
6. `uv run pytest` -- confirm all tests pass
7. Commit Phase 4

### Phase 5: Generate command + Chat intake

1. Full `resume-manager generate` pipeline wiring phases 3 and 4 together
2. `resume-manager list` commands
3. `resume-manager edit` command
4. `intake/chat.py` -- chat-based gap fill
5. `resume-manager chat` command
6. End-to-end test with dry-run
7. `uv run pytest` -- confirm all tests pass
8. Commit Phase 5

### Phase 6: Polish

1. `resume-manager import` conflict resolution (skip/overwrite/merge prompt)
2. `--rewrite` flag with diff confirmation
3. `resume_log` table population and display
4. README with installation, usage examples, CLI reference, project structure
5. `uv run pytest` -- confirm all tests pass
6. Commit Phase 6 with a summary message covering what the tool does and why

---

## Notes for the Implementer

- Use `uv` for all dependency management. Never use pip directly.
- Use `uv run pytest` to run tests. Confirm all pass before each phase commit.
- Stage specific files rather than `git add -A`.
- The EnhancCV PDF decoder is proven: read `/ecv-data` metadata field, decode as UTF-16,
  parse JSON. The `experience` items have company and role in nested fields -- inspect
  the raw JSON to find them (the earlier extraction missed them).
- Playwright requires `playwright install chromium` after pip install. Add this to the
  Makefile `install` target.
- The brand template fonts (Plus Jakarta Sans, Inter) should be loaded via Google Fonts
  in the HTML `<head>`. Playwright will fetch them during render.
- `interview_questions` and `tags` fields in the database are stored as JSON arrays
  (TEXT column). Serialize/deserialize with `json.loads` / `json.dumps`.
- The `--target-questions` flag in generate is passed to the strategist, not the
  curator. Curator only cares about role relevance. Strategist cares about question
  engineering.
- Keep prompts in `.txt` files with Jinja2 interpolation. This lets prompts be tuned
  without code changes.
