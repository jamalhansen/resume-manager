import argparse
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

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
