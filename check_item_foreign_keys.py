import sqlite3
import os

# Database configuration (mirroring app.py)
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'items.db')

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    # Enable foreign key constraints
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

if __name__ == '__main__':
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("PRAGMA foreign_key_list(items)")
        foreign_keys = cursor.fetchall()

        if foreign_keys:
            print("Foreign Keys referencing 'items' table:")
            for fk in foreign_keys:
                print(f"  Table: {fk['table']}, From: {fk['from']}, To: {fk['to']}, On Update: {fk['on_update']}, On Delete: {fk['on_delete']}, Match: {fk['match']}")
        else:
            print("No foreign keys referencing 'items' table found.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if conn:
            conn.close()