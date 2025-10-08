# fix_database.py
import sqlite3
import os

DB_NAME = 'water_tracker.db'

def fix_database():
    """Add the missing intake_ml column to the existing table"""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        print("🔧 Fixing database structure...")
        
        # Check current columns
        cursor.execute("PRAGMA table_info(water_intake)")
        current_columns = [col[1] for col in cursor.fetchall()]
        print(f"Current columns: {current_columns}")
        
        # Add the missing intake_ml column
        if 'intake_ml' not in current_columns:
            print("➕ Adding missing 'intake_ml' column...")
            cursor.execute("ALTER TABLE water_intake ADD COLUMN intake_ml REAL")
            conn.commit()
            print("✅ Successfully added 'intake_ml' column")
        else:
            print("✅ 'intake_ml' column already exists")
        
        # Verify the fix
        cursor.execute("PRAGMA table_info(water_intake)")
        fixed_columns = [col[1] for col in cursor.fetchall()]
        print(f"Fixed columns: {fixed_columns}")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Error fixing database: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_database()