# Resume Manager

A command-line tool that maintains a structured database of professional experience and generates tailored, branded resume PDFs for specific roles.

## Features

- **Structured Data**: Store jobs, bullets, skills, and education in a local SQLite database.
- **AI-Powered Curation**: Automatically selects the most relevant content for a specific job description.
- **Branded Rendering**: Generates beautiful PDFs using HTML/CSS templates via Playwright.
- **Import**: Easily import existing data from EnhancCV PDFs or LinkedIn data exports.
- **Interactive Editing**: Edit records directly in your favorite text editor.

## Installation

1. Clone the repository.
2. Install dependencies using `uv`:
   ```bash
   uv sync
   ```
3. Install Playwright browsers:
   ```bash
   make install-playwright
   ```
4. Initialize the database:
   ```bash
   uv run resume-manager init
   ```

## Usage

### Import Data

```bash
uv run resume-manager import --ecv path/to/resume.pdf
uv run resume-manager import --linkedin path/to/linkedin-export.zip
```

### Generate a Resume

```bash
uv run resume-manager generate job-description.txt --template brand
```

### Manage Data

```bash
uv run resume-manager list jobs
uv run resume-manager list skills
uv run resume-manager edit job 1
```

### Demo Mode

Test the rendering with synthetic data:
```bash
uv run resume-manager demo --template brand
```

## Configuration

Set the database path via environment variable:
```bash
export RESUME_MANAGER_DB=~/.local/share/resume-manager/resume.db
```

Set LLM API keys in a `.env` file:
```
ANTHROPIC_API_KEY=your-key
GEMINI_API_KEY=your-key
```

## License

MIT
