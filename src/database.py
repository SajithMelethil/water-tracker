import sqlite3
from datetime import datetime
import os

DB_NAME = 'water_tracker.db'

def create_tables():
    """
    Creates tables if they don't exist and ensures correct structure.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # First, check current table structure
        cursor.execute("PRAGMA table_info(water_intake)")
        current_columns = [col[1] for col in cursor.fetchall()]
        
        required_columns = ['id', 'user_id', 'intake_ml', 'date']
        missing_columns = [col for col in required_columns if col not in current_columns]
        
        if missing_columns:
            print(f"🔄 Table structure incomplete. Missing: {missing_columns}")
            print("🔄 Recreating table with correct structure...")
            
            # Backup existing data if any
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='water_intake_backup'")
            backup_exists = cursor.fetchone()
            
            if not backup_exists:
                cursor.execute("ALTER TABLE water_intake RENAME TO water_intake_backup")
                print("📦 Backed up existing table")
            
            # Create new table with correct structure
            cursor.execute("""
                CREATE TABLE water_intake(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    intake_ml REAL NOT NULL,
                    date TEXT NOT NULL
                )
            """)
            
            # Try to migrate data from backup if it exists
            try:
                cursor.execute("""
                    INSERT INTO water_intake (id, user_id, intake_ml, date)
                    SELECT id, user_id, 0 as intake_ml, date FROM water_intake_backup
                """)
                print("✅ Migrated existing data")
            except:
                print("ℹ️ No data to migrate or migration failed")
            
            # Drop backup table
            cursor.execute("DROP TABLE IF EXISTS water_intake_backup")
            
        else:
            print("✅ Table structure is correct")
        
        conn.commit()
        print("✓ Database tables are ready")
        return True
        
    except sqlite3.Error as e:
        print(f"✗ Database error: {e}")
        return False
    finally:
        if conn:
            conn.close()

def log_intake(user_id, intake_ml):
    """Log water intake for a user"""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        date_today = datetime.today().strftime('%Y-%m-%d')
        
        print(f"📝 Logging: user={user_id}, intake={intake_ml}ml, date={date_today}")
        
        cursor.execute(
            "INSERT INTO water_intake (user_id, intake_ml, date) VALUES(?,?,?)", 
            (user_id, intake_ml, date_today)
        )
        conn.commit()
        print(f"✅ Successfully logged {intake_ml}ml for user {user_id}")
        return True
        
    except sqlite3.Error as e:
        print(f"✗ Error logging intake: {e}")
        return False
    finally:
        if conn:
            conn.close()
    
def get_intake_history(user_id):
    """Get water intake history for a user"""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT date, intake_ml FROM water_intake WHERE user_id = ? ORDER BY date DESC, id DESC", 
            (user_id,)
        )
        records = cursor.fetchall()
        
        print(f"📊 History for {user_id}: {len(records)} records")
        for record in records:
            print(f"  - {record[0]}: {record[1]}ml")
            
        return records
    except sqlite3.Error as e:
        print(f"✗ Error fetching history: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_daily_total(user_id, date=None):
    """Get total water intake for a user on a specific date"""
    conn = None
    try:
        if date is None:
            date = datetime.today().strftime('%Y-%m-%d')
            
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT SUM(intake_ml) FROM water_intake WHERE user_id = ? AND date = ?", 
            (user_id, date)
        )
        total = cursor.fetchone()[0]
        result = total if total else 0
        
        print(f"💧 Daily total for {user_id} on {date}: {result}ml")
        return result
        
    except sqlite3.Error as e:
        print(f"✗ Error getting daily total: {e}")
        return 0
    finally:
        if conn:
            conn.close()

# Test the database when run directly
if __name__ == "__main__":
    print("🧪 Testing database setup...")
    if create_tables():
        # Test with sample data
        print("\n🧪 Testing log functionality...")
        log_intake("test_user", 500)
        log_intake("test_user", 300)
        
        print("\n🧪 Testing history functionality...")
        history = get_intake_history("test_user")
        print(f"Test history: {history}")
        
        print("\n🧪 Testing daily total functionality...")
        total = get_daily_total("test_user")
        print(f"Test daily total: {total}ml")
    else:
        print("❌ Database setup failed")