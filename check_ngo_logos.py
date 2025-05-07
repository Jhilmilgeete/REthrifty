import sqlite3
import os

# Database configuration
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'items.db')

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

if __name__ == '__main__':
    conn = None
    try:
        print(f"Attempting to connect to database at: {DATABASE_PATH}")
        if not os.path.exists(DATABASE_PATH):
            print(f"ERROR: Database file not found at {DATABASE_PATH}")
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, name, logo, is_verified FROM ngos ORDER BY id")
            ngos = cursor.fetchall()
            
            if ngos:
                print("\nNGO Information:")
                print("-" * 60)
                for ngo in ngos:
                    print(f"ID: {ngo['id']}, Name: {ngo['name']}, Logo: {ngo['logo']}, Verified: {bool(ngo['is_verified'])}")
                print("-" * 60)
            else:
                print("No NGOs found in the database.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if conn:
            conn.close()
