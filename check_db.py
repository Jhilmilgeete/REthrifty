import sqlite3

def check_database():
    try:
        # Connect to the database
        conn = sqlite3.connect('items.db')
        cursor = conn.cursor()
        
        # Check if the items table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='items'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("Items table exists!")
            # Get table structure
            cursor.execute("PRAGMA table_info(items)")
            columns = cursor.fetchall()
            print("\nTable Structure:")
            for column in columns:
                print(f"Column: {column[1]}, Type: {column[2]}")
            
            # Get all items
            cursor.execute("SELECT * FROM items")
            items = cursor.fetchall()
            print("\nItems in database:")
            for item in items:
                print(item)
        else:
            print("Items table does not exist!")
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_database() 