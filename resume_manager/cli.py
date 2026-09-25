import json
import os
from enum import Enum
from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv
from local_first_common.tracking import register_tool

from .db import get_connection, get_db_path, init_db

_TOOL = register_tool("resume-manager")

app = typer.Typer(help="Resume Manager CLI", add_completion=False)


class Template(str, Enum):
    brand = "brand"
    compact = "compact"


class ListTable(str, Enum):
    jobs = "jobs"
    bullets = "bullets"
    skills = "skills"
    education = "education"
    logs = "logs"


class EditTable(str, Enum):
    job = "job"
    bullet = "bullet"
    skill = "skill"
    profile = "profile"


@app.callback(invoke_without_command=True)
def _root(
    ctx: typer.Context,
    db: Annotated[str | None, typer.Option("--db", help="Path to SQLite database")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose output")] = False,
) -> None:
    """Resume Manager CLI."""
    load_dotenv()
    ctx.obj = {"db_path": get_db_path(db), "verbose": verbose}
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command("init")
def init_cmd(
    ctx: typer.Context,
) -> None:
    """Initialize the database"""
    db_path = ctx.obj["db_path"]
    if ctx.obj['verbose']:
        print(f"Initializing database at {db_path}")
    init_db(db_path)
    print(f"Database initialized at {db_path}")



@app.command("status")
def status_cmd(
    ctx: typer.Context,
) -> None:
    """Show database status"""
    db_path = ctx.obj["db_path"]
    if not db_path.exists():
        print(f"Database does not exist at {db_path}. Run 'init' first.")
        raise typer.Exit()

    conn = get_connection(db_path)
    cursor = conn.cursor()

    print(f"Database: {db_path}")
    
    tables = ["profile", "jobs", "bullets", "skills", "education", "volunteer", "resume_log"]
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table.capitalize()}: {count} records")
    
    conn.close()



@app.command("import")
def import__cmd(
    ctx: typer.Context,
    ecv: Annotated[str | None, typer.Option("--ecv", help="Path to EnhancCV PDF")] = None,
    linkedin: Annotated[str | None, typer.Option("--linkedin", help="Path to LinkedIn data export zip")] = None,
) -> None:
    """Import from an existing source"""
    db_path = ctx.obj["db_path"]
    if not db_path.exists():
        print(f"Database does not exist at {db_path}. Run 'init' first.")
        raise typer.Exit()
        
    conn = get_connection(db_path)
    
    if ecv:
        from .intake.enhancv import import_enhancv
        if ctx.obj['verbose']:
            print(f"Importing EnhancCV PDF from {ecv}")
        import_enhancv(Path(ecv), conn)
        print(f"Imported from {ecv}")
        
    if linkedin:
        from .intake.linkedin import import_linkedin
        if ctx.obj['verbose']:
            print(f"Importing LinkedIn zip from {linkedin}")
        import_linkedin(Path(linkedin), conn)
        print(f"Imported from {linkedin}")
        
    conn.close()



@app.command("demo")
def demo_cmd(
    ctx: typer.Context,
    template: Annotated[Template, typer.Option("--template", help="Template to use")] = Template.brand,
    output: Annotated[str | None, typer.Option("--output", help="Output path")] = None,
) -> None:
    """Generate a demo resume"""
    from .render.renderer import render
    
    fixture_path = Path(__file__).parent.parent / "tests" / "fixtures" / "demo_profile.json"
    with open(fixture_path) as f:
        data = json.load(f)
        
    output_path = output or "output/demo-resume.pdf"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating demo resume using {template.value} template...")
    render(template.value, data, output_path)
    print(f"Demo resume generated at {output_path}")



@app.command("generate", context_settings={"allow_extra_args": True})
def generate_cmd(
    ctx: typer.Context,
    jd_file: Annotated[str, typer.Argument(help="Path to job description file")],
    template: Annotated[Template, typer.Option("--template", help="Template to use")] = Template.brand,
    title: Annotated[str | None, typer.Option("--title", help="Override headline title")] = None,
    target_questions: Annotated[
        list[str] | None,
        typer.Option("--target-questions", help="Interview questions to engineer toward (one or more values)"),
    ] = None,
    output: Annotated[str | None, typer.Option("--output", help="Output path")] = None,
    provider: Annotated[str, typer.Option("--provider", "-p", help="LLM provider")] = "anthropic",
    model: Annotated[str | None, typer.Option("--model", "-m", help="LLM model")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", "-n", help="Print selected items, do not render PDF")] = False,
) -> None:
    """Generate a tailored resume"""
    # `--target-questions "q1" "q2"` (several values after one flag) keeps working:
    # values after the first land in ctx.args.
    if ctx.args:
        if not target_questions:
            typer.echo(f"Error: unexpected arguments: {' '.join(ctx.args)}", err=True)
            raise typer.Exit(2)
        target_questions = [*target_questions, *ctx.args]
    db_path = ctx.obj["db_path"]
    if not db_path.exists():
        print(f"Database does not exist at {db_path}. Run 'init' first.")
        raise typer.Exit()
        
    conn = get_connection(db_path)
    
    # 1. Read JD
    if not Path(jd_file).exists():
        print(f"Error: Job description file not found: {jd_file}")
        raise typer.Exit()
    with open(jd_file) as f:
        jd = f.read()
        
    # 2. Load all content
    from .db.queries import get_all_content
    all_content = get_all_content(conn)
    
    # 3. Curator
    from .generate.curator import curate, filter_content
    print("Curating experience items...")
    selection = curate(jd, all_content, provider_name=provider, model=model)
    
    if ctx.obj['verbose']:
        print("Selection rationale:", selection.get("rationale"))
        
    # 4. Strategist (if target questions)
    filtered_content = filter_content(all_content, selection)
    if target_questions:
        from .generate.strategist import strategize
        print("Engineering for target questions...")
        strategy = strategize(selection, target_questions, provider_name=provider, model=model)
        if ctx.obj['verbose']:
            print("Strategy:", strategy.get("recommendations"))
        # TODO: Apply strategy reordering to filtered_content
        
    # 5. Render
    if dry_run:
        print("Dry run: Selection details")
        print(json.dumps(selection, indent=2))
    else:
        from .render.renderer import render
        output_path = output or f"output/resume-{Path(jd_file).stem}.pdf"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        print(f"Rendering resume using {template.value} template...")
        render(template.value, filtered_content, output_path)
        print(f"Resume generated at {output_path}")
        
        # 6. Log
        import hashlib
        jd_hash = hashlib.sha256(jd.encode()).hexdigest()
        from .db.queries import log_resume_generation
        log_resume_generation(
            conn,
            job_title=title or "Tailored Resume",
            company=Path(jd_file).stem,
            template=template.value,
            jd_hash=jd_hash,
            output_path=str(output_path),
            config_json=json.dumps(selection)
        )
        
    conn.close()



@app.command("list")
def list_cmd(
    ctx: typer.Context,
    table: Annotated[ListTable, typer.Argument(help="Table to list")],
    job_id: Annotated[int | None, typer.Option("--job-id", help="Filter bullets by job ID")] = None,
) -> None:
    """List database contents"""
    db_path = ctx.obj["db_path"]
    if not db_path.exists():
        print(f"Database does not exist at {db_path}. Run 'init' first.")
        raise typer.Exit()
        
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    if table.value == "jobs":
        cursor.execute("SELECT id, company, role, start_date FROM jobs ORDER BY start_date DESC")
        for row in cursor.fetchall():
            print(f"[{row[0]}] {row[1]} - {row[2]} ({row[3]})")
            
    elif table.value == "bullets":
        if job_id:
            cursor.execute("SELECT id, content FROM bullets WHERE job_id = ?", (job_id,))
        else:
            cursor.execute("SELECT id, job_id, content FROM bullets")
        for row in cursor.fetchall():
            if job_id:
                print(f"[{row[0]}] {row[1]}")
            else:
                print(f"[{row[0]}] (Job {row[1]}) {row[2]}")
                
    elif table.value == "skills":
        cursor.execute("SELECT id, name, category FROM skills")
        for row in cursor.fetchall():
            print(f"[{row[0]}] {row[1]} ({row[2]})")
            
    elif table.value == "education":
        cursor.execute("SELECT id, institution, degree, year FROM education")
        for row in cursor.fetchall():
            print(f"[{row[0]}] {row[1]} - {row[2]} ({row[3]})")
            
    elif table.value == "logs":
        cursor.execute("SELECT id, created_at, job_title, company FROM resume_log ORDER BY created_at DESC")
        for row in cursor.fetchall():
            print(f"[{row[0]}] {row[1]} - {row[2]} ({row[3]})")
            
    conn.close()



@app.command("edit")
def edit_cmd(
    ctx: typer.Context,
    kind: Annotated[EditTable, typer.Argument(help="Table to edit")],
    record_id: Annotated[int | None, typer.Argument(help="ID of the record to edit")] = None,
) -> None:
    """Edit a specific record"""
    db_path = ctx.obj["db_path"]
    if not db_path.exists():
        print(f"Database does not exist at {db_path}. Run 'init' first.")
        raise typer.Exit()
        
    import subprocess
    import tempfile

    import yaml
    
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    table_map = {
        "job": "jobs",
        "bullet": "bullets",
        "skill": "skills",
        "profile": "profile"
    }
    table = table_map[kind.value]
    
    if kind.value == "profile":
        cursor.execute(f"SELECT * FROM {table} LIMIT 1")
    else:
        if not record_id:
            print(f"Error: ID required to edit {kind.value}")
            raise typer.Exit()
        cursor.execute(f"SELECT * FROM {table} WHERE id = ?", (record_id,))
        
    row = cursor.fetchone()
    if not row:
        print(f"No record found in {table}")
        raise typer.Exit()
        
    columns = [d[0] for d in cursor.description]
    data = dict(zip(columns, row))
    
    # Open in editor
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w+", delete=False) as tf:
        yaml.dump(data, tf, default_flow_style=False)
        temp_path = tf.name
        
    editor = os.getenv("EDITOR", "vi")
    subprocess.run([editor, temp_path], check=False)  # a nonzero editor exit (e.g. user aborted) shouldn't crash the CLI
    
    # Read back
    with open(temp_path) as f:
        updated_data = yaml.safe_load(f)
        
    if updated_data == data:
        print("No changes made.")
        os.unlink(temp_path)
        raise typer.Exit()
        
    # Update
    update_cols = [c for c in columns if c != "id"]
    set_clause = ", ".join([f"{c} = ?" for c in update_cols])
    values = [updated_data.get(c) for c in update_cols]
    
    if kind.value == "profile":
        cursor.execute(f"UPDATE {table} SET {set_clause} WHERE id = ?", values + [data['id']])
    else:
        cursor.execute(f"UPDATE {table} SET {set_clause} WHERE id = ?", values + [record_id])
        
    conn.commit()
    print(f"Updated {kind.value} record.")
    os.unlink(temp_path)
    conn.close()



@app.command("chat")
def chat_cmd(
    ctx: typer.Context,
    intake: Annotated[bool, typer.Option("--intake", help="Populate profile from scratch")] = False,
    gap_fill: Annotated[bool, typer.Option("--gap-fill", help="Fill missing fields")] = False,
    bullets: Annotated[int | None, typer.Option("--bullets", help="Add/refine bullets for a specific job ID")] = None,
) -> None:
    """Interactive LLM-powered chat intake"""
    db_path = ctx.obj["db_path"]
    if not db_path.exists():
        print(f"Database does not exist at {db_path}. Run 'init' first.")
        raise typer.Exit()
        
    conn = get_connection(db_path)
    from .intake.chat import run_chat
    
    mode = "intake" if intake else "gap-fill" if gap_fill else "bullets"
    run_chat(mode, conn)
    conn.close()



if __name__ == "__main__":
    app()
