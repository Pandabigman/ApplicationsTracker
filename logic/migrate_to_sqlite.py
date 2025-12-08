"""
Migration script to transfer data from PostgreSQL to SQLite.
Run this script if you have existing data in PostgreSQL that you want to preserve.

Usage: python migrate_to_sqlite.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Load environment variables for PostgreSQL connection
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

def migrate_data():
    """Migrate data from PostgreSQL to SQLite"""

    # Check if PostgreSQL DATABASE_URL exists
    pg_database_url = os.getenv("DATABASE_URL")
    if not pg_database_url:
        print("No PostgreSQL DATABASE_URL found in .env file.")
        print("Skipping migration. Starting with fresh SQLite database.")
        return

    print("Found PostgreSQL DATABASE_URL. Attempting migration...")

    try:
        # Connect to PostgreSQL
        pg_engine = create_engine(pg_database_url)
        PgSession = sessionmaker(bind=pg_engine)
        pg_session = PgSession()

        # Connect to SQLite
        db_dir = Path(__file__).parent / "data"
        db_dir.mkdir(exist_ok=True)
        sqlite_url = f"sqlite:///{db_dir / 'jobtracker.db'}"
        sqlite_engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
        SqliteSession = sessionmaker(bind=sqlite_engine)
        sqlite_session = SqliteSession()

        # Import models to create tables
        from app.database import Base
        from app.models import Application, JobDetail, Note, ActivityLog, Deadline

        # Create all tables in SQLite
        Base.metadata.create_all(bind=sqlite_engine)
        print("SQLite tables created successfully.")

        # Query all applications from PostgreSQL
        pg_apps = pg_session.execute(
            "SELECT * FROM applications ORDER BY id"
        ).fetchall()

        if not pg_apps:
            print("No applications found in PostgreSQL database.")
            pg_session.close()
            sqlite_session.close()
            return

        print(f"Found {len(pg_apps)} applications in PostgreSQL.")
        print("Migrating data...")

        # Get column names
        column_names = [
            'id', 'company_name', 'position_title', 'job_url', 'location',
            'salary', 'description', 'requirements', 'status', 'date_applied',
            'deadline', 'notes', 'created_at', 'updated_at'
        ]

        migrated_count = 0
        for row in pg_apps:
            # Create dict from row
            app_data = dict(zip(column_names, row))

            # Extract old notes and description/requirements
            old_notes = app_data.pop('notes', None)
            old_description = app_data.pop('description', None)
            old_requirements = app_data.pop('requirements', None)

            # Create new Application (without description/requirements)
            new_app = Application(
                id=app_data['id'],
                company_name=app_data['company_name'],
                position_title=app_data['position_title'],
                job_url=app_data['job_url'],
                location=app_data['location'],
                salary=app_data['salary'],
                status=app_data['status'],
                date_applied=app_data['date_applied'],
                deadline=app_data['deadline'],
                created_at=app_data['created_at'],
                updated_at=app_data['updated_at']
            )
            sqlite_session.add(new_app)
            sqlite_session.flush()  # Get the ID

            # Create JobDetail entry
            if old_description or old_requirements:
                job_detail = JobDetail(
                    application_id=new_app.id,
                    description=old_description,
                    requirements=old_requirements,
                    clean_text_content=None  # Will be populated by new scraping
                )
                sqlite_session.add(job_detail)

            # Create Note entry if old notes exist
            if old_notes:
                note = Note(
                    application_id=new_app.id,
                    content=old_notes
                )
                sqlite_session.add(note)

            # Create activity log for the initial application
            activity = ActivityLog(
                application_id=new_app.id,
                activity_type='application_created',
                description=f'Migrated from PostgreSQL',
                new_value=app_data['status']
            )
            sqlite_session.add(activity)

            migrated_count += 1

        # Commit all changes
        sqlite_session.commit()
        print(f"Successfully migrated {migrated_count} applications to SQLite!")

        # Close sessions
        pg_session.close()
        sqlite_session.close()

        print("\nMigration complete!")
        print(f"SQLite database location: {db_dir / 'jobtracker.db'}")
        print("\nYou can now update your application to use SQLite.")

    except Exception as e:
        print(f"Error during migration: {e}")
        print("\nStarting with fresh SQLite database instead.")
        # Create empty SQLite database
        from app.database import Base, engine
        Base.metadata.create_all(bind=engine)
        print("Fresh SQLite database created.")

if __name__ == "__main__":
    migrate_data()
