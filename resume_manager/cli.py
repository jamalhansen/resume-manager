import argparse
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from .db import get_db_path, init_db, get_connection

def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Resume Manager CLI")
    parser.add_argument("--db", help="Path to SQLite database")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # init
    subparsers.add_parser("init", help="Initialize the database")

    # status
    subparsers.add_parser("status", help="Show database status")

    # import
    import_parser = subparsers.add_parser("import", help="Import from an existing source")
    import_parser.add_argument("--ecv", help="Path to EnhancCV PDF")
    import_parser.add_argument("--linkedin", help="Path to LinkedIn data export zip")

    # demo
    demo_parser = subparsers.add_parser("demo", help="Generate a demo resume")
    demo_parser.add_argument("--template", default="brand", choices=["brand", "compact"], help="Template to use")
    demo_parser.add_argument("--output", help="Output path")

    # generate
    gen_parser = subparsers.add_parser("generate", help="Generate a tailored resume")
    gen_parser.add_argument("jd_file", help="Path to job description file")
    gen_parser.add_argument("--template", default="brand", choices=["brand", "compact"], help="Template to use")
    gen_parser.add_argument("--title", help="Override headline title")
    gen_parser.add_argument("--target-questions", nargs="+", help="Interview questions to engineer toward")
    gen_parser.add_argument("--output", help="Output path")
    gen_parser.add_argument("--provider", "-p", default="anthropic", help="LLM provider")
    gen_parser.add_argument("--model", "-m", help="LLM model")
    gen_parser.add_argument("--dry-run", "-n", action="store_true", help="Print selected items, do not render PDF")

    # list
    list_parser = subparsers.add_parser("list", help="List database contents")
    list_parser.add_argument("table", choices=["jobs", "bullets", "skills", "education", "logs"], help="Table to list")
    list_parser.add_argument("--job-id", type=int, help="Filter bullets by job ID")

    # edit
    edit_parser = subparsers.add_parser("edit", help="Edit a specific record")
    edit_parser.add_argument("table", choices=["job", "bullet", "skill", "profile"], help="Table to edit")
    edit_parser.add_argument("id", type=int, nargs="?", help="ID of the record to edit")

    # chat
    chat_parser = subparsers.add_parser("chat", help="Interactive LLM-powered chat intake")
    chat_parser.add_argument("--intake", action="store_true", help="Populate profile from scratch")
    chat_parser.add_argument("--gap-fill", action="store_true", help="Fill missing fields")
    chat_parser.add_argument("--bullets", type=int, help="Add/refine bullets for a specific job ID")

    args = parser.parse_args()

    db_path = get_db_path(args.db)

    if args.command == "init":
        if args.verbose:
            print(f"Initializing database at {db_path}")
        init_db(db_path)
        print(f"Database initialized at {db_path}")

    elif args.command == "status":
        if not db_path.exists():
            print(f"Database does not exist at {db_path}. Run 'init' first.")
            return

        conn = get_connection(db_path)
        cursor = conn.cursor()

        print(f"Database: {db_path}")
        
        tables = ["profile", "jobs", "bullets", "skills", "education", "volunteer", "resume_log"]
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table.capitalize()}: {count} records")
        
        conn.close()

    elif args.command == "import":
        if not db_path.exists():
            print(f"Database does not exist at {db_path}. Run 'init' first.")
            return
            
        conn = get_connection(db_path)
        
        if args.ecv:
            from .intake.enhancv import import_enhancv
            if args.verbose:
                print(f"Importing EnhancCV PDF from {args.ecv}")
            import_enhancv(Path(args.ecv), conn)
            print(f"Imported from {args.ecv}")
            
        if args.linkedin:
            from .intake.linkedin import import_linkedin
            if args.verbose:
                print(f"Importing LinkedIn zip from {args.linkedin}")
            import_linkedin(Path(args.linkedin), conn)
            print(f"Imported from {args.linkedin}")
            
        conn.close()

    elif args.command == "demo":
        from .render.renderer import render
        
        fixture_path = Path(__file__).parent.parent / "tests" / "fixtures" / "demo_profile.json"
        with open(fixture_path) as f:
            data = json.load(f)
            
        output_path = args.output or "output/demo-resume.pdf"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        print(f"Generating demo resume using {args.template} template...")
        render(args.template, data, output_path)
        print(f"Demo resume generated at {output_path}")

    elif args.command == "generate":
        if not db_path.exists():
            print(f"Database does not exist at {db_path}. Run 'init' first.")
            return
            
        conn = get_connection(db_path)
        
        # 1. Read JD
        if not Path(args.jd_file).exists():
            print(f"Error: Job description file not found: {args.jd_file}")
            return
        with open(args.jd_file) as f:
            jd = f.read()
            
        # 2. Load all content
        from .db.queries import get_all_content
        all_content = get_all_content(conn)
        
        # 3. Curator
        from .generate.curator import curate, filter_content
        print("Curating experience items...")
        selection = curate(jd, all_content, provider_name=args.provider, model=args.model)
        
        if args.verbose:
            print("Selection rationale:", selection.get("rationale"))
            
        # 4. Strategist (if target questions)
        filtered_content = filter_content(all_content, selection)
        if args.target_questions:
            from .generate.strategist import strategize
            print("Engineering for target questions...")
            strategy = strategize(selection, args.target_questions, provider_name=args.provider, model=args.model)
            if args.verbose:
                print("Strategy:", strategy.get("recommendations"))
            # TODO: Apply strategy reordering to filtered_content
            
        # 5. Render
        if args.dry_run:
            print("Dry run: Selection details")
            print(json.dumps(selection, indent=2))
        else:
            from .render.renderer import render
            output_path = args.output or f"output/resume-{Path(args.jd_file).stem}.pdf"
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            print(f"Rendering resume using {args.template} template...")
            render(args.template, filtered_content, output_path)
            print(f"Resume generated at {output_path}")
            
            # 6. Log
            import hashlib
            jd_hash = hashlib.sha256(jd.encode()).hexdigest()
            from .db.queries import log_resume_generation
            log_resume_generation(
                conn,
                job_title=args.title or "Tailored Resume",
                company=Path(args.jd_file).stem,
                template=args.template,
                jd_hash=jd_hash,
                output_path=str(output_path),
                config_json=json.dumps(selection)
            )
            
        conn.close()

    elif args.command == "list":
        if not db_path.exists():
            print(f"Database does not exist at {db_path}. Run 'init' first.")
            return
            
        conn = get_connection(db_path)
        cursor = conn.cursor()
        
        if args.table == "jobs":
            cursor.execute("SELECT id, company, role, start_date FROM jobs ORDER BY start_date DESC")
            for row in cursor.fetchall():
                print(f"[{row[0]}] {row[1]} - {row[2]} ({row[3]})")
                
        elif args.table == "bullets":
            if args.job_id:
                cursor.execute("SELECT id, content FROM bullets WHERE job_id = ?", (args.job_id,))
            else:
                cursor.execute("SELECT id, job_id, content FROM bullets")
            for row in cursor.fetchall():
                if args.job_id:
                    print(f"[{row[0]}] {row[1]}")
                else:
                    print(f"[{row[0]}] (Job {row[1]}) {row[2]}")
                    
        elif args.table == "skills":
            cursor.execute("SELECT id, name, category FROM skills")
            for row in cursor.fetchall():
                print(f"[{row[0]}] {row[1]} ({row[2]})")
                
        elif args.table == "education":
            cursor.execute("SELECT id, institution, degree, year FROM education")
            for row in cursor.fetchall():
                print(f"[{row[0]}] {row[1]} - {row[2]} ({row[3]})")
                
        elif args.table == "logs":
            cursor.execute("SELECT id, created_at, job_title, company FROM resume_log ORDER BY created_at DESC")
            for row in cursor.fetchall():
                print(f"[{row[0]}] {row[1]} - {row[2]} ({row[3]})")
                
        conn.close()

    elif args.command == "edit":
        if not db_path.exists():
            print(f"Database does not exist at {db_path}. Run 'init' first.")
            return
            
        import yaml
        import tempfile
        import subprocess
        
        conn = get_connection(db_path)
        cursor = conn.cursor()
        
        table_map = {
            "job": "jobs",
            "bullet": "bullets",
            "skill": "skills",
            "profile": "profile"
        }
        table = table_map[args.table]
        
        if args.table == "profile":
            cursor.execute(f"SELECT * FROM {table} LIMIT 1")
        else:
            if not args.id:
                print(f"Error: ID required to edit {args.table}")
                return
            cursor.execute(f"SELECT * FROM {table} WHERE id = ?", (args.id,))
            
        row = cursor.fetchone()
        if not row:
            print(f"No record found in {table}")
            return
            
        columns = [d[0] for d in cursor.description]
        data = dict(zip(columns, row))
        
        # Open in editor
        with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w+", delete=False) as tf:
            yaml.dump(data, tf, default_flow_style=False)
            temp_path = tf.name
            
        editor = os.getenv("EDITOR", "vi")
        subprocess.run([editor, temp_path])
        
        # Read back
        with open(temp_path) as f:
            updated_data = yaml.safe_load(f)
            
        if updated_data == data:
            print("No changes made.")
            os.unlink(temp_path)
            return
            
        # Update
        update_cols = [c for c in columns if c != "id"]
        set_clause = ", ".join([f"{c} = ?" for c in update_cols])
        values = [updated_data.get(c) for c in update_cols]
        
        if args.table == "profile":
            cursor.execute(f"UPDATE {table} SET {set_clause} WHERE id = ?", values + [data['id']])
        else:
            cursor.execute(f"UPDATE {table} SET {set_clause} WHERE id = ?", values + [args.id])
            
        conn.commit()
        print(f"Updated {args.table} record.")
        os.unlink(temp_path)
        conn.close()

    elif args.command == "chat":
        if not db_path.exists():
            print(f"Database does not exist at {db_path}. Run 'init' first.")
            return
            
        conn = get_connection(db_path)
        from .intake.chat import run_chat
        
        mode = "intake" if args.intake else "gap-fill" if args.gap_fill else "bullets"
        run_chat(mode, conn)
        conn.close()

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
