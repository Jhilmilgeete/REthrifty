import sqlite3
import os
from datetime import datetime

# Database configuration (mirroring app.py)
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'items.db')

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    # Enable foreign key constraints
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def add_ngo(name, email, phone, address, description, logo=None, is_verified=1):
    """Adds a new NGO to the database."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if NGO email already exists
        cursor.execute('SELECT id FROM ngos WHERE email = ?', (email,))
        existing_ngo = cursor.fetchone()

        if existing_ngo:
            print(f"NGO with email {email} already exists. Skipping.")
            return False

        cursor.execute('''
            INSERT INTO ngos (name, email, phone, address, description, logo, is_verified, verified_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, email, phone, address, description, logo, is_verified, datetime.now() if is_verified else None))
        conn.commit()
        print(f"NGO '{name}' added successfully.")
        return True
    except sqlite3.Error as e:
        print(f"Database error while adding NGO '{name}': {e}")
        if conn:
            conn.rollback() # Rollback changes on error
        return False
    except Exception as e:
        print(f"An unexpected error occurred while adding NGO '{name}': {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # Ensure the database and table exist (similar to init_db but minimal for this script)
    if not os.path.exists(DATABASE_PATH):
        print(f"Database file not found at {DATABASE_PATH}. Please run the main app first to initialize the database.")
    else:
        # {{The following block needed to be indented under the 'else' statement}}
        sample_ngos = [
            {
                "name": "Helping Hands Foundation",
                "email": "contact@helpinghands.org",
                "phone": "+1-555-0100",
                "address": "123 Charity Lane, Anytown, ST 12345",
                "description": "Dedicated to providing support and resources to underprivileged communities.",
                "logo": None, 
                "is_verified": 1
            },
            {
                "name": "Green Earth Initiative",
                "email": "info@greenearth.org",
                "phone": "+1-555-0101",
                "address": "456 Eco Drive, Greenville, ST 67890",
                "description": "Focused on environmental conservation and promoting sustainable practices.",
                "logo": None,
                "is_verified": 1
            },
            {
                "name": "Children's Future Fund",
                "email": "support@childrenfuture.org",
                "phone": "+1-555-0102",
                "address": "789 Hope Avenue, Kidstown, ST 13579",
                "description": "Working towards a brighter future for children through education and healthcare.",
                "logo": None,
                "is_verified": 1
            },
            {
                "name": "Tech for Tomorrow",
                "email": "connect@techfortomorrow.org",
                "phone": "+1-555-0103",
                "address": "101 Innovation Drive, Future City, ST 24680",
                "description": "Bridging the digital divide by providing technology education and resources to underserved populations.",
                "logo": None,
                "is_verified": 1
            },
            {
                "name": "Art & Soul Collective",
                "email": "create@artsoul.org",
                "phone": "+1-555-0104",
                "address": "202 Inspiration Street, Artville, ST 11223",
                "description": "Fostering creativity and community through art programs and workshops.",
                "logo": None,
                "is_verified": 1
            },
            # {{New NGOs added below}}
            {
                "name": "Healthy Futures Alliance",
                "email": "info@healthyfutures.org",
                "phone": "+1-555-0105",
                "address": "303 Wellness Way, Healthburg, ST 35791",
                "description": "Promoting health and wellness through community programs and medical aid.",
                "logo": None,
                "is_verified": 1
            },
            {
                "name": "Wildlife Guardian Society",
                "email": "protect@wildlifeguardian.org",
                "phone": "+1-555-0106",
                "address": "404 Sanctuary Road, Wildlands, ST 46802",
                "description": "Dedicated to the protection of endangered species and their habitats.",
                "logo": None,
                "is_verified": 1
            }
        ]

        added_count = 0
        for ngo_data in sample_ngos:
            if add_ngo(
                name=ngo_data["name"],
                email=ngo_data["email"],
                phone=ngo_data["phone"],
                address=ngo_data["address"],
                description=ngo_data["description"],
                logo=ngo_data["logo"],
                is_verified=ngo_data["is_verified"]
            ):
                added_count += 1
        
        print(f"\nFinished adding NGOs. {added_count} new NGOs were added.")