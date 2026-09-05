import sys
import os

# Add backend directory to sys.path so we can import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.database.connection import engine

def run_migration():
    print("--- PHASE 19 MIGRATION ---")
    
    with engine.connect() as conn:
        # Check if column exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='teaching_sessions' AND column_name='state_data';
        """))
        
        column_exists = result.scalar() is not None
        
        if column_exists:
            print("Column 'state_data' already exists. Skipping DDL.")
        else:
            print("Adding 'state_data' JSON column to 'teaching_sessions' table...")
            # We use JSON rather than JSONB to be safe across different pg versions/configurations though JSONB is usually better
            conn.execute(text("ALTER TABLE teaching_sessions ADD COLUMN state_data JSON;"))
            conn.commit()
            print("Column 'state_data' added successfully.")
            
        # Verify
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='teaching_sessions' AND column_name='state_data';
        """))
        if result.scalar() is None:
            print("ERROR: Verification failed. Column does not exist.")
            sys.exit(1)
        else:
            print("Verification passed. Column is present.")

if __name__ == "__main__":
    run_migration()
