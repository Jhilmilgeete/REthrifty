from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from flask_mail import Mail, Message
from flask_session import Session
import sqlite3
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
import random
from flask import jsonify
import requests
from dotenv import load_dotenv
import string
import secrets
import shutil
import time

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(__file__), '.env')
en_path = os.path.join(os.path.dirname(__file__), '.en')

# Try to load from .env first, then .en
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)
    print(f"Loaded environment from: {env_path}")
elif os.path.exists(en_path):
    load_dotenv(dotenv_path=en_path)
    print(f"Loaded environment from: {en_path}")
else:
    print("No environment file found!")

# Fast2SMS API Configuration
FAST2SMS_API_KEY = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
FAST2SMS_SENDER_ID = "REthrifty"

# Email Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_USERNAME = "rethrifty11@gmail.com"
EMAIL_PASSWORD = "liao wfag szkl miht"

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default-secret-key')

# Configure session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_FILE_DIR'] = os.path.join(os.path.dirname(__file__), 'flask_session')
Session(app)

# Configure Flask-Mail
app.config['MAIL_SERVER'] = SMTP_SERVER
app.config['MAIL_PORT'] = SMTP_PORT
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = EMAIL_USERNAME
app.config['MAIL_PASSWORD'] = EMAIL_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = EMAIL_USERNAME

# Initialize Flask-Mail
mail = Mail(app)

# Additional app configurations
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Database configuration
app.config['DATABASE'] = os.path.join(os.path.dirname(__file__), 'data', 'items.db')
app.config['BACKUP_DIR'] = os.path.join(os.path.dirname(__file__), 'data', 'backups')

# Create necessary directories
os.makedirs(os.path.dirname(app.config['DATABASE']), exist_ok=True)
os.makedirs(app.config['BACKUP_DIR'], exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

def backup_database():
    """Create a backup of the database file with timestamp"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(app.config['BACKUP_DIR'], f'items_backup_{timestamp}.db')
        shutil.copy2(app.config['DATABASE'], backup_path)
        print(f"Database backup created: {backup_path}")
    except Exception as e:
        print(f"Error creating database backup: {str(e)}")

def get_db():
    """Get database connection"""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
        # Enable foreign key constraints
        db.execute('PRAGMA foreign_keys = ON')
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Close database connection"""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize the database with proper error handling"""
    try:
        conn = sqlite3.connect(app.config['DATABASE'])
        c = conn.cursor()
        
        # Enable foreign key constraints
        c.execute('PRAGMA foreign_keys = ON')
        
        # Create tables if they don't exist
        # First create users table
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                profile_picture TEXT,
                is_admin BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        # Create ngos table with all required columns including logo
        c.execute('''
            CREATE TABLE IF NOT EXISTS ngos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT NOT NULL,
                address TEXT NOT NULL,
                description TEXT,
                is_verified BOOLEAN DEFAULT 0,
                verified_at TIMESTAMP,
                verified_by INTEGER,
                logo TEXT  -- Column added to store logo filename
            )
        ''')
        
        # Create items table
        c.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                image_filename TEXT,
                source TEXT NOT NULL,
                price TEXT,
                location TEXT,
                contact_number TEXT,
                user_id INTEGER,
                ngo_id INTEGER,
                status TEXT DEFAULT "active",
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (ngo_id) REFERENCES ngos(id)
            )
        ''')
        
        # Check existing columns for possible migrations
        c.execute("PRAGMA table_info(ngos)")
        ngo_columns = [col[1] for col in c.fetchall()]
        
        # Handle missing columns in existing databases
        if 'logo' not in ngo_columns:
            c.execute('ALTER TABLE ngos ADD COLUMN logo TEXT')
        
        # Create donations table
        c.execute('''
            CREATE TABLE IF NOT EXISTS donations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                donor_name TEXT NOT NULL,
                donor_email TEXT NOT NULL,
                donor_phone TEXT NOT NULL,
                item_name TEXT NOT NULL,
                item_description TEXT,
                item_category TEXT,
                ngo_id INTEGER NOT NULL,
<<<<<<< HEAD
                status TEXT DEFAULT "pending",
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (ngo_id) REFERENCES ngos(id)
            )
        ''')
=======
                user_id INTEGER, -- Link to the user who made the donation
                status TEXT DEFAULT "pending", -- e.g., "pending", "accepted", "rejected", "completed"
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (ngo_id) REFERENCES ngos(id),
                FOREIGN KEY (user_id) REFERENCES users(id) -- Foreign key constraint
            )
        ''')

        # Add user_id column to donations if it doesn't exist
        c.execute("PRAGMA table_info(donations)")
        donations_columns = [col[1] for col in c.fetchall()]
        if 'user_id' not in donations_columns:
            c.execute('ALTER TABLE donations ADD COLUMN user_id INTEGER REFERENCES users(id)')
>>>>>>> 39c4515ded846f8b80ca1a96717b64c5a9c7929c
        
        # Create item_views table
        c.execute('''
            CREATE TABLE IF NOT EXISTS item_views (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES items(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Create admin user if not exists
        c.execute('SELECT id FROM users WHERE username = ? OR email = ?', ('Readmin', 'admin@example.com'))
        existing_admin = c.fetchone()
        
        if existing_admin:
            # Update existing admin user
            admin_password = generate_password_hash('rE@11tH&22')
            c.execute('''
                UPDATE users 
                SET username = ?, email = ?, password = ?, is_admin = 1
                WHERE id = ?
            ''', ('Readmin', 'admin@example.com', admin_password, existing_admin[0]))
        else:
            # Create new admin user
            admin_password = generate_password_hash('rE@11tH&22')
            c.execute('''
                INSERT INTO users (username, email, password, is_admin)
                VALUES (?, ?, ?, 1)
            ''', ('Readmin', 'admin@example.com', admin_password))
        
        conn.commit()
        print("Database initialized successfully")
        
        # Create initial backup
        backup_database()
        
    except sqlite3.Error as e:
        print(f"Database error: {str(e)}")
        raise
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

@app.before_request
def before_request():
    """Create database backup before each request"""
    try:
        backup_database()
    except Exception as e:
        print(f"Error creating backup: {str(e)}")

# Initialize database
init_db()

# In-memory storage for OTPs and pending NGO data (for demo)
pending_ngos = {}

# OTP storage (in production, use a proper database)
otp_store = {}

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def store_otp(email, otp):
    """Store OTP with timestamp"""
    otp_store[email] = {
        'otp': otp,
        'timestamp': datetime.now(),
        'verified': False
    }

def verify_otp(email, otp):
    """Verify OTP and check if it's expired (5 minutes)"""
    if email not in otp_store:
        return False
    
    stored_data = otp_store[email]
    if datetime.now() - stored_data['timestamp'] > timedelta(minutes=5):
        del otp_store[email]
        return False
    
    if stored_data['otp'] == otp:
        stored_data['verified'] = True
        return True
    return False

def send_otp_email(email, otp, purpose='registration'):
    """Send OTP via email using Flask-Mail"""
    try:
        subject = "Your OTP for Registration" if purpose == 'registration' else "Your Password Reset OTP"
        html_content = f"""
        <html>
            <body>
                <h2>{subject}</h2>
                <p>Your One-Time Password (OTP) is: <strong>{otp}</strong></p>
                <p>This OTP is valid for 5 minutes.</p>
                <p>If you didn't request this OTP, please ignore this email.</p>
            </body>
        </html>
        """
        msg = Message(
            subject=subject,
            recipients=[email],
            html=html_content
        )
        mail.send(msg)
        return True, "OTP sent successfully"
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False, str(e)

def send_sms(phone, message):
    """Helper function to send SMS using Fast2SMS API"""
    try:
        if not FAST2SMS_API_KEY:
            print("SMS configuration missing. Please check your .env file.")
            return False, "SMS configuration missing"
            
        url = "https://www.fast2sms.com/dev/bulkV2"
        headers = {
            'authorization': FAST2SMS_API_KEY,
            'Content-Type': "application/x-www-form-urlencoded",
            'Cache-Control': "no-cache"
        }
        
        # Format phone number correctly
        phone = str(phone).strip()
        if phone.startswith('+'):
            phone = phone[1:]
        if phone.startswith('0'):
            phone = phone[1:]
        if not phone.startswith('91'):
            phone = '91' + phone
        
        # Validate phone number length
        if len(phone) != 12:
            return False, f"Invalid phone number length: {phone}"
        
        payload = {
            'sender_id': FAST2SMS_SENDER_ID,
            'message': message,
            'language': 'english',
            'route': 'v3',
            'numbers': phone
        }
        
        response = requests.post(url, data=payload, headers=headers)
        result = response.json()
        
        if result.get('return') == True:
            print(f"SMS sent successfully to {phone}")
            return True, result.get('request_id')
        else:
            error_msg = result.get('message', 'Unknown error')
            print(f"Failed to send SMS: {error_msg}")
            return False, error_msg
            
    except Exception as e:
        print(f"Failed to send SMS: {str(e)}")
        return False, str(e)

def send_email(to_email, subject, message):
    """Send email using Flask-Mail"""
    try:
        msg = Message(
            subject=subject,
            recipients=[to_email],
            html=message
        )
        mail.send(msg)
        return True, "Email sent successfully"
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False, str(e)

@app.route('/')
def index():
    try:
        db = get_db()
        cursor = db.cursor()

        # Get the three most recent items regardless of status
        cursor.execute("""
            SELECT * FROM items 
            ORDER BY created_at DESC 
            LIMIT 3
        """)
        latest_items = cursor.fetchall()

        # === REMOVED CATEGORY FETCHING LOGIC ===

        cursor.close()
        
        # Pass only latest_items to the template
        return render_template('index.html', latest_items=latest_items)
        
    except Exception as e:
        print(f"Error fetching data for index page: {e}")
        # Render with empty latest_items if error
        return render_template('index.html', latest_items=[])

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/ngo-list')
def ngo_list():
    try:
        # {{Add debug print to confirm route is hit}}
        print("Accessing /ngo-list route.")
        cursor = get_db().cursor()
        
        # {{Add debug print before query}}
        print("Executing query: SELECT * FROM ngos WHERE is_verified = 1 ORDER BY name ASC")
        cursor.execute('SELECT * FROM ngos WHERE is_verified = 1 ORDER BY name ASC')
        ngos = cursor.fetchall()
        
        # {{Add debug print after query}}
        print(f"Query returned {len(ngos)} NGOs.")
        # Print the first few NGOs fetched to see their structure and content
        for i, ngo in enumerate(ngos[:5]): # Print details for up to the first 5 NGOs
            # Handle potential missing 'logo' key if column wasn't added properly or ngo row is malformed
            logo_info = ngo['logo'] if 'logo' in ngo.keys() else 'N/A (logo key missing)'
            print(f"  NGO {i+1}: ID={ngo['id']}, Name='{ngo['name']}', Verified={bool(ngo['is_verified'])}, Logo='{logo_info}'")
        
        cursor.close()
        
        return render_template('ngo_list.html', ngos=ngos)
    except Exception as e:
        print(f"Error fetching NGOs in ngo_list route: {e}")
        return render_template('ngo_list.html', ngos=[])

@app.route('/ngo')
def ngo():
    # ... existing code ...
    return render_template('ngo.html')

@app.route('/help')
def help():
    return render_template('help.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Debug print for admin login attempt
        if username == 'Readmin':
            print(f"Attempting admin login for user: {username}, password provided: '{password}'")

        db = get_db()
        cursor = db.cursor()
        
        try:
            # Get user by username
            cursor.execute('SELECT id, password, is_admin FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            
            if username == 'Readmin' and user:
                print(f"Admin user '{username}' found in DB. ID: {user['id']}, Stored Hash: {user['password'][:20]}..., IsAdmin DB: {user['is_admin']}")
            elif username == 'Readmin' and not user:
                print(f"Admin user '{username}' NOT found in DB.")

            if user:
                stored_password_hash = user['password']
                is_admin_from_db = bool(user['is_admin']) # Ensure it's a Python boolean
                
                # Handle scrypt passwords (legacy, admin should ideally not have this if init_db ran)
                if stored_password_hash.startswith('scrypt:'):
                    if username == 'Readmin':
                        print("Admin user has a scrypt hash. Validating and attempting rehash.")
                    # First, check password against the old scrypt hash
                    if check_password_hash(stored_password_hash, password):
                        new_hash = generate_password_hash(password, method='pbkdf2:sha256')
                        cursor.execute('''
                            UPDATE users 
                            SET password = ?, last_login = datetime('now')
                            WHERE id = ?
                        ''', (new_hash, user['id']))
                        db.commit()
                        if username == 'Readmin':
                            print(f"Admin scrypt hash updated to: {new_hash[:20]}...")
                        
                        session.permanent = True
                        session['user_id'] = user['id']
                        session['username'] = username
                        session['is_admin'] = is_admin_from_db 
                        print(f"User {username} logged in successfully (after scrypt rehash and validation). Admin status from DB: {is_admin_from_db}, Set in session: {session['is_admin']}")
                        flash('Logged in successfully!', 'success')
                        return redirect(url_for('index'))
                    else:
                        # Password check failed for scrypt hash
                        if username == 'Readmin':
                            print("Admin scrypt password check FAILED.")
                        # Fall through to the generic error message at the end of the function
                
                # Standard password check (e.g., pbkdf2)
                elif check_password_hash(stored_password_hash, password):
                    cursor.execute('''
                        UPDATE users 
                        SET last_login = datetime('now')
                        WHERE id = ?
                    ''', (user['id'],))
                    db.commit()
                    
                    session.permanent = True
                    session['user_id'] = user['id']
                    session['username'] = username
                    session['is_admin'] = is_admin_from_db
                    
                    if username == 'Readmin':
                        print(f"Admin user {username} logged in successfully (non-scrypt). Admin status from DB: {is_admin_from_db}, Set in session: {session['is_admin']}")
                    else:
                        print(f"User {username} logged in successfully (non-scrypt). Admin status from DB: {is_admin_from_db}, Set in session: {session['is_admin']}")
                    flash('Logged in successfully!', 'success')
                    return redirect(url_for('index'))
                else:
                    # Password check failed for non-scrypt hash
                    if username == 'Readmin':
                        print(f"Admin password check FAILED for non-scrypt hash. Stored hash starts with: {stored_password_hash[:20]}...")
            
            # This part is reached if user is None OR if any password check above failed and didn't return
            print(f"Failed login attempt for username: {username}. User found: {bool(user)}")
            flash('Invalid username or password.', 'error')
            return render_template('login.html')
                
        except sqlite3.Error as e:
            print(f"Database error during login: {str(e)}")
            flash(f'Database error: {str(e)}', 'error')
            return render_template('login.html')
        except Exception as e:
            print(f"An unexpected error occurred during login: {str(e)}")
            flash('An unexpected error occurred. Please try again.', 'error')
            return render_template('login.html')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if 'otp' in request.form:
            # OTP verification step
            email = request.form['email']
            otp = request.form['otp']
            
            if not verify_otp(email, otp):
                flash('Invalid or expired OTP. Please try again.', 'error')
                return render_template('register.html', otp_sent=True, email=email)
            
            # Proceed with registration
            username = request.form['username']
            password = request.form['password']
            confirm_password = request.form['confirm_password']
            
            if not username or not email or not password or not confirm_password:
                flash('All fields are required.', 'error')
                return render_template('register.html', otp_sent=True, email=email)
                
            if password != confirm_password:
                flash('Passwords do not match.', 'error')
                return render_template('register.html', otp_sent=True, email=email)
                
            db = get_db()
            cursor = db.cursor()
            
            try:
                # Check if username or email already exists
                cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
                if cursor.fetchone():
                    flash('Username or email already exists.', 'error')
                    return render_template('register.html', otp_sent=True, email=email)
                
                # Hash the password
                hashed_password = generate_password_hash(password)
                
                # Insert new user with all required fields
                cursor.execute('''
                    INSERT INTO users (username, email, password, created_at, last_login)
                    VALUES (?, ?, ?, datetime('now'), datetime('now'))
                ''', (username, email, hashed_password))
                
                db.commit()
                print(f"User {username} registered successfully")
                
                # Clear OTP data after successful registration
                if email in otp_store:
                    del otp_store[email]
                
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
                
            except sqlite3.Error as e:
                print(f"Database error during registration: {str(e)}")
                flash(f'Database error: {str(e)}', 'error')
                return render_template('register.html', otp_sent=True, email=email)
                
        else:
            # Initial registration step
            email = request.form['email']
            
            # Generate and send OTP
            otp = generate_otp()
            store_otp(email, otp)
            success, message = send_otp_email(email, otp, purpose='registration')
            
            if not success:
                flash(f'Failed to send OTP: {message}', 'error')
                return render_template('register.html')
            
            flash('OTP has been sent to your email. Please check your inbox.', 'success')
            return render_template('register.html', otp_sent=True, email=email)
            
    return render_template('register.html', otp_sent=False)

@app.route('/ngo-register', methods=['GET', 'POST'])
def ngo_register():
    if request.method == 'POST':
        if 'otp' in request.form:
            # OTP verification step
            email = request.form['email']
            otp = request.form['otp']
            
            if not verify_otp(email, otp):
                flash('Invalid or expired OTP. Please try again.', 'error')
                return render_template('ngo_register.html', email=email, show_otp=True)
            
            # Proceed with NGO registration
            name = request.form['name']
            phone = request.form['phone']
            address = request.form['address']
            description = request.form.get('description', '')
            
            if not name or not email or not phone or not address:
                flash('All fields except description are required.', 'error')
                return render_template('ngo_register.html', email=email, show_otp=True)
            
            db = get_db()
            cursor = db.cursor()
            
            # Check if NGO email already exists
            cursor.execute('SELECT id FROM ngos WHERE email = ?', (email,))
            if cursor.fetchone():
                flash('An NGO with this email already exists.', 'error')
                return render_template('ngo_register.html', email=email, show_otp=True)
            
            # Insert new NGO
            cursor.execute('''
                INSERT INTO ngos (name, email, phone, address, description)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, email, phone, address, description))
            db.commit()
            
            # Clear OTP data after successful registration
            if email in otp_store:
                del otp_store[email]
            
            flash('NGO registration successful!', 'success')
            return redirect(url_for('ngo'))
        else:
            # Initial registration step
            email = request.form['email']
            
            # Generate and send OTP
            otp = generate_otp()
            store_otp(email, otp)
            success, message = send_otp_email(email, otp)
            
            if not success:
                flash(f'Failed to send OTP: {message}', 'error')
                return render_template('ngo_register.html')
            
            flash('OTP has been sent to your email. Please check your inbox.', 'success')
            return render_template('ngo_register.html', email=email, show_otp=True)
    
    return render_template('ngo_register.html', show_otp=False)

@app.route('/terms')
def terms():
    return render_template('terms.html')

# Route: Donation Form
@app.route('/donate', methods=['GET', 'POST'])
def donate():
    # Redirect to login if not logged in
    if not session.get('user_id'):
        flash('Please login to access this page.', 'error')
        return redirect(url_for('login'))
<<<<<<< HEAD
    if request.method == 'POST':
        try:
            donor_name = request.form['donor-name']
            donor_email = request.form['donor-email']
            donor_phone = request.form['donor-phone']
=======

    db = get_db()
    cursor = db.cursor()
    
    user_name = ''
    user_email = ''
    # Fetch user details for pre-filling the form (for GET request)
    # and for error re-rendering (in POST request)
    if 'user_id' in session:
        current_user_details = cursor.execute('SELECT username, email FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        if current_user_details:
            user_name = current_user_details['username']
            user_email = current_user_details['email']

    if request.method == 'POST':
        try:
            donor_name_form = request.form['donor-name']
            donor_email_form = request.form['donor-email']
            donor_phone_form = request.form['donor-phone']
>>>>>>> 39c4515ded846f8b80ca1a96717b64c5a9c7929c
            item_name = request.form['item-name']
            item_category = request.form['item-category']
            item_description = request.form['item-description']
            ngo_id = request.form.get('ngo')
            
<<<<<<< HEAD
            if not all([donor_name, donor_email, donor_phone, item_name, item_category, ngo_id]):
                flash('All fields are required.', 'error')
                return redirect(url_for('donate'))
            
            # Format phone number for WhatsApp
            whatsapp_phone = donor_phone.replace('+', '').replace(' ', '')
            
            db = get_db()
            cursor = db.cursor()
            
            # Get NGO details
            cursor.execute('SELECT name, email, phone FROM ngos WHERE id = ?', (ngo_id,))
            ngo = cursor.fetchone()
            if not ngo:
                flash('Selected NGO not found.', 'error')
                return redirect(url_for('donate'))
=======
            if not all([donor_name_form, donor_email_form, donor_phone_form, item_name, item_category, ngo_id]):
                flash('All fields are required.', 'error')
                cursor.execute('SELECT id, name, description FROM ngos WHERE is_verified = 1') # Only verified NGOs
                ngos_list_for_error = cursor.fetchall()
                return render_template('donate.html', ngos=ngos_list_for_error, 
                                       user_name=user_name, user_email=user_email, 
                                       form_data=request.form) # Pass back form data
            
            # Format phone number for WhatsApp
            whatsapp_phone = donor_phone_form.replace('+', '').replace(' ', '')
            
            # Get NGO details
            cursor.execute('SELECT name, email, phone FROM ngos WHERE id = ? AND is_verified = 1', (ngo_id,))
            ngo = cursor.fetchone()
            if not ngo:
                flash('Selected NGO not found or is not verified.', 'error')
                cursor.execute('SELECT id, name, description FROM ngos WHERE is_verified = 1')
                ngos_list_for_error = cursor.fetchall()
                return render_template('donate.html', ngos=ngos_list_for_error, 
                                       user_name=user_name, user_email=user_email, 
                                       form_data=request.form)
>>>>>>> 39c4515ded846f8b80ca1a96717b64c5a9c7929c
            
            ngo_name, ngo_email, ngo_phone = ngo
            
            # Save donation record
            cursor.execute('''
                INSERT INTO donations (donor_name, donor_email, donor_phone, item_name, 
<<<<<<< HEAD
                                     item_description, item_category, ngo_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (donor_name, donor_email, donor_phone, item_name, 
                  item_description, item_category, ngo_id))
=======
                                     item_description, item_category, ngo_id, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (donor_name_form, donor_email_form, donor_phone_form, item_name, 
                  item_description, item_category, ngo_id, session['user_id']))
>>>>>>> 39c4515ded846f8b80ca1a96717b64c5a9c7929c
            
            donation_id = cursor.lastrowid
            db.commit()
            
            # Prepare messages
            ngo_message = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                        <h2 style="color: #2c3e50; text-align: center; margin-bottom: 20px;">🎁 New Donation Alert!</h2>
                        
                        <div style="background-color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
                            <h3 style="color: #2c3e50; margin-bottom: 15px;">Donor Details</h3>
<<<<<<< HEAD
                            <p><strong>Name:</strong> {donor_name}</p>
                            <p><strong>Email:</strong> {donor_email}</p>
                            <p><strong>Phone:</strong> {donor_phone}</p>
=======
                            <p><strong>Name:</strong> {donor_name_form}</p>
                            <p><strong>Email:</strong> {donor_email_form}</p>
                            <p><strong>Phone:</strong> {donor_phone_form}</p>
>>>>>>> 39c4515ded846f8b80ca1a96717b64c5a9c7929c
                            <p><strong>WhatsApp:</strong> <a href="https://wa.me/{whatsapp_phone}" style="color: #25D366; text-decoration: none;">Click to chat on WhatsApp</a></p>
                        </div>

                        <div style="background-color: white; padding: 20px; border-radius: 5px;">
                            <h3 style="color: #2c3e50; margin-bottom: 15px;">Item Details</h3>
                            <p><strong>Name:</strong> {item_name}</p>
                            <p><strong>Category:</strong> {item_category}</p>
                            <p><strong>Description:</strong> {item_description}</p>
                        </div>

                        <div style="text-align: center; margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee;">
                            <p style="color: #666; font-size: 14px;">Please review this donation request and contact the donor if interested.</p>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            donor_message = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                        <h2 style="color: #2c3e50; text-align: center; margin-bottom: 20px;">✨ Thank You for Your Donation!</h2>
                        
                        <div style="background-color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
                            <p style="text-align: center; margin-bottom: 20px;">Your donation details have been sent to <strong>{ngo_name}</strong>.</p>
                            <p style="text-align: center;">They will review your request and contact you if interested.</p>
                        </div>

                        <div style="background-color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
                            <h3 style="color: #2c3e50; margin-bottom: 15px;">Your Item Details</h3>
                            <p><strong>Name:</strong> {item_name}</p>
                            <p><strong>Category:</strong> {item_category}</p>
                            <p><strong>Description:</strong> {item_description}</p>
                        </div>

                        <div style="background-color: white; padding: 20px; border-radius: 5px;">
                            <h3 style="color: #2c3e50; margin-bottom: 15px;">NGO Contact Information</h3>
                            <p><strong>Name:</strong> {ngo_name}</p>
                            <p><strong>Email:</strong> {ngo_email}</p>
                            <p><strong>Phone:</strong> {ngo_phone}</p>
                            <p><strong>WhatsApp:</strong> <a href="https://wa.me/{ngo_phone.replace('+', '').replace(' ', '')}" style="color: #25D366; text-decoration: none;">Click to chat on WhatsApp</a></p>
                        </div>

                        <div style="text-align: center; margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee;">
                            <p style="color: #666; font-size: 14px;">Thank you for choosing to donate through REthrifty!</p>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            # Send emails
            send_email(ngo_email, f"🎁 New Donation Request: {item_name}", ngo_message)
<<<<<<< HEAD
            send_email(donor_email, "✨ Your Donation Request has been Submitted", donor_message)
            
            flash('Donation request submitted successfully! The NGO will contact you soon.', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('donate'))
    
    # For GET request, fetch NGOs to display in the form
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id, name, description FROM ngos')
    ngos = cursor.fetchall()
    db.close()
    
    return render_template('donate.html', ngos=ngos)
=======
            send_email(donor_email_form, "✨ Your Donation Request has been Submitted", donor_message)
            
            flash('Donation request submitted successfully! The NGO will contact you soon.', 'success')
            return redirect(url_for('index')) # Or perhaps redirect to profile page
            
        except Exception as e:
            db.rollback() # Rollback on error
            print(f"Error in /donate POST: {str(e)}") # Log the error
            flash(f'Error submitting donation: {str(e)}', 'error')
            cursor.execute('SELECT id, name, description FROM ngos WHERE is_verified = 1')
            ngos_list_for_error = cursor.fetchall()
            return render_template('donate.html', ngos=ngos_list_for_error, 
                                   user_name=user_name, user_email=user_email, 
                                   form_data=request.form)
    
    # For GET request, fetch NGOs to display in the form
    cursor.execute('SELECT id, name, description FROM ngos WHERE is_verified = 1') # Only verified NGOs
    ngos_list = cursor.fetchall()
    # db.close() # Let app context handle closing
    
    return render_template('donate.html', ngos=ngos_list, user_name=user_name, user_email=user_email)
>>>>>>> 39c4515ded846f8b80ca1a96717b64c5a9c7929c

@app.route('/donation/<int:donation_id>/accept', methods=['POST'])
def accept_donation(donation_id):
    if not session.get('user_id'):
        flash('Please login to accept donations.', 'error')
        return redirect(url_for('login'))
    
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Get donation and NGO details
        cursor.execute('''
            SELECT d.donor_name, d.donor_email, d.donor_phone, d.item_name,
                   n.name, n.email, n.phone
            FROM donations d
            JOIN ngos n ON d.ngo_id = n.id
            WHERE d.id = ?
        ''', (donation_id,))
        
        donation = cursor.fetchone()
        if not donation:
            flash('Donation not found.', 'error')
            return redirect(url_for('index'))
        
        donor_name, donor_email, donor_phone, item_name, ngo_name, ngo_email, ngo_phone = donation
        
        # Update donation status
        cursor.execute('''
            UPDATE donations 
            SET status = 'accepted', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (donation_id,))
        db.commit()
        
        # Format phone numbers for WhatsApp
        donor_whatsapp = donor_phone.replace('+', '').replace(' ', '')
        ngo_whatsapp = ngo_phone.replace('+', '').replace(' ', '')
        
        # Prepare acceptance messages
        donor_message = f"""
        Great News!
        
        {ngo_name} has accepted your donation request for "{item_name}".
        
        NGO Contact Details:
        Name: {ngo_name}
        Email: {ngo_email}
        Phone: {ngo_phone}
        WhatsApp: https://wa.me/{ngo_whatsapp}
        
        Please contact them to arrange the donation pickup/delivery.
        """
        
        ngo_message = f"""
        Donation Accepted
        
        You have accepted the donation request from {donor_name}.
        
        Donor Contact Details:
        Name: {donor_name}
        Email: {donor_email}
        Phone: {donor_phone}
        WhatsApp: https://wa.me/{donor_whatsapp}
        
        Item Details:
        Name: {item_name}
        
        Please contact the donor to arrange pickup/delivery.
        """
        
        # Send acceptance emails
        send_email(donor_email, f"Your Donation has been Accepted by {ngo_name}", donor_message)
        send_email(ngo_email, f"Donation Accepted: {item_name}", ngo_message)
        
        flash('Donation accepted successfully! Both parties have been notified.', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('index'))

# Route: View Items
@app.route('/view')
def view():
    try:
        # Get filter parameters from the request
        category = request.args.get('item-category', '')
        location = request.args.get('location', '')

        db = get_db()
        cursor = db.cursor()
        
        # Start with a base query
        query = '''
            SELECT * FROM items 
            WHERE source = 'sell'
        '''
        params = []

        # Add category filter if provided
        if category:
            query += ' AND category = ?'
            params.append(category)

        # Add location filter if provided
        if location:
            query += ' AND location = ?'
            params.append(location)
            
        # Add order by clause
        query += ' ORDER BY created_at DESC'

        # Execute the query
        cursor.execute(query, params)
        items = cursor.fetchall()
        
        # Pass filter values to the template for pre-filling the form
        return render_template('view_items.html', items=items, selected_category=category, selected_location=location)
    except Exception as e:
        print(f"Error fetching items: {e}")
        return render_template('view_items.html', items=[], selected_category=category, selected_location=location)

@app.route('/items/<int:item_id>')
def item_details(item_id):
    # Check if user is logged in
    if not session.get('user_id'):
        flash('Please login to view item details.', 'error')
        return redirect(url_for('login'))
        
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM items WHERE id = ?', (item_id,))
    item = cursor.fetchone()
    # Insert a view record
    user_id = session.get('user_id')
    cursor.execute('INSERT INTO item_views (item_id, user_id) VALUES (?, ?)', (item_id, user_id))
    db.commit()
    db.close()
    
    if item:
        return render_template('item_details.html', item=item)
    else:
        flash('Item not found!', 'error')
        return redirect(url_for('view'))



@app.route('/sell', methods=['GET', 'POST'])
def sell():
    # Redirect to login if not logged in
    if not session.get('user_id'):
        flash('Please login to access this page.', 'error')
        return redirect(url_for('login'))
    if request.method == 'POST':
        try:
            item_name = request.form['item-name']
            category = request.form['item-category']
            description = request.form['item-description']
            price = request.form['item-price']
            country_code = request.form['country-code']
            contact_number = request.form['contact-number']
            location = request.form['location']
            image = request.files['item-image']

            # Clean and validate phone number
            contact_number = ''.join(filter(str.isdigit, contact_number))
            if not contact_number:
                flash('Please enter a valid phone number', 'error')
                return redirect(url_for('sell'))

            # Clean and validate country code
            country_code = ''.join(filter(str.isdigit, country_code))
            if not country_code:
                flash('Please select a valid country code', 'error')
                return redirect(url_for('sell'))

            # Format full phone number properly
            full_phone = f"+{country_code}{contact_number}"

            image_filename = None
            if image and image.filename:
                if not allowed_file(image.filename):
                    flash('Invalid file type. Only images are allowed.', 'error')
                    return redirect(url_for('sell'))
                
                image_filename = secure_filename(image.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
                image.save(image_path)

            # Save item into database with source 'sell' and price
            db = get_db()
            cursor = db.cursor()
            try:
                cursor.execute('''
                    INSERT INTO items (name, category, description, image_filename, source, price, location, contact_number, user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (item_name, category, description, image_filename, 'sell', price, location, full_phone, session['user_id']))
                db.commit()
                flash('Item listed for sale successfully!', 'success')
            except sqlite3.Error as e:
                flash(f'Database error: {str(e)}', 'error')
                return redirect(url_for('sell'))
            finally:
                db.close()

            return redirect(url_for('view'))

        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('sell'))

    return render_template('sell.html')

@app.route('/logout')
def logout():
    if 'username' in session:
        print(f"User {session['username']} logged out")
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/join-ngo', methods=['GET', 'POST'])
def join_ngo():
    if request.method == 'POST':
        if 'otp' in request.form:
            # OTP verification and NGO registration
            email = request.form['email']
            otp = request.form['otp']
            
            # Verify OTP
            if otp == session.get('ngo_otp') and email == session.get('ngo_email'):
                # Get NGO details from session
                ngo_data = session.get('ngo_data', {})
                
                # Handle image upload
                logo = None
                if 'logo' in request.files:
                    file = request.files['logo']
                    if file and file.filename:
                        filename = secure_filename(file.filename)
                        # Generate unique filename
                        unique_filename = f"ngo_{int(time.time())}_{filename}"
                        file_path = os.path.join('static', 'images', unique_filename)
                        file.save(file_path)
                        logo = unique_filename
                
                # Insert NGO into database with verification status
                cursor = get_db().cursor()
                cursor.execute('''
                    INSERT INTO ngos (name, email, phone, address, description, logo, is_verified)
                    VALUES (?, ?, ?, ?, ?, ?, 0)
                ''', (
                    ngo_data['name'],
                    email,
                    ngo_data['phone'],
                    ngo_data['address'],
                    ngo_data['description'],
                    logo
                ))
                get_db().commit()
                
                # Clear session data
                session.pop('ngo_otp', None)
                session.pop('ngo_email', None)
                session.pop('ngo_data', None)
                
                flash('NGO registration successful! Your application is under review. We will notify you once verified.', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid OTP. Please try again.', 'error')
                return render_template('ngo.html', show_otp=True, email=email)
        else:
            # Initial form submission
            name = request.form['name']
            email = request.form['email']
            phone = request.form['phone']
            address = request.form['address']
            description = request.form['description']
            
            # Store NGO data in session
            session['ngo_data'] = {
                'name': name,
                'phone': phone,
                'address': address,
                'description': description
            }
            
            # Generate and send OTP
            otp = str(random.randint(100000, 999999))
            session['ngo_otp'] = otp
            session['ngo_email'] = email
            
            # Send OTP email
            msg = Message('Your NGO Registration OTP', sender='rethrifty@example.com', recipients=[email])
            msg.body = f'Your OTP for NGO registration is: {otp}'
            mail.send(msg)
            
            return render_template('ngo.html', show_otp=True, email=email)
    
    return render_template('ngo.html', show_otp=False)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not session.get('user_id'):
        flash('Please login to view your profile.', 'error')
        return redirect(url_for('login'))
    
<<<<<<< HEAD
    try:
        db = get_db()
        cursor = db.cursor()
=======
    db = get_db()
    cursor = db.cursor()
    
    try:
>>>>>>> 39c4515ded846f8b80ca1a96717b64c5a9c7929c
        
        if request.method == 'POST':
            # Handle profile update
            new_username = request.form.get('username')
            new_email = request.form.get('email')
<<<<<<< HEAD
            profile_pic = request.files.get('profile_pic')
            
            if profile_pic and profile_pic.filename:
                if not allowed_file(profile_pic.filename):
                    flash('Invalid file type. Only images are allowed.', 'error')
                    return redirect(url_for('profile'))
                
                filename = secure_filename(profile_pic.filename)
                profile_pic_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                profile_pic.save(profile_pic_path)
                
                cursor.execute('''
                    UPDATE users 
                    SET username = ?, email = ?, profile_pic = ?
                    WHERE id = ?
                ''', (new_username, new_email, filename, session['user_id']))
=======
            profile_pic_file = request.files.get('profile_pic')
            
            user_to_update = cursor.execute('SELECT profile_picture FROM users WHERE id = ?', (session['user_id'],)).fetchone()
            current_profile_pic_filename = user_to_update['profile_picture'] if user_to_update else None

            if profile_pic_file and profile_pic_file.filename:
                if not allowed_file(profile_pic_file.filename):
                    flash('Invalid file type. Only images are allowed.', 'error')
                    return redirect(url_for('profile'))
                
                original_filename = secure_filename(profile_pic_file.filename)
                unique_filename = f"{session['user_id']}_{int(time.time())}_{original_filename}"
                profile_pic_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                profile_pic_file.save(profile_pic_path)
                current_profile_pic_filename = unique_filename
                
                cursor.execute('''
                    UPDATE users 
                    SET username = ?, email = ?, profile_picture = ?
                    WHERE id = ?
                ''', (new_username, new_email, current_profile_pic_filename, session['user_id']))
>>>>>>> 39c4515ded846f8b80ca1a96717b64c5a9c7929c
            else:
                cursor.execute('''
                    UPDATE users 
                    SET username = ?, email = ?
                    WHERE id = ?
                ''', (new_username, new_email, session['user_id']))
            
            db.commit()
            flash('Profile updated successfully!', 'success')
<<<<<<< HEAD
=======
            session['username'] = new_username 
>>>>>>> 39c4515ded846f8b80ca1a96717b64c5a9c7929c
            return redirect(url_for('profile'))
        
        # Get user details
        cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
<<<<<<< HEAD
        user = cursor.fetchone()
        
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('index'))
=======
        user_row = cursor.fetchone()
        
        if not user_row:
            flash('User not found.', 'error')
            session.clear() 
            return redirect(url_for('login'))
        
        user_dict = {
            'id': user_row['id'],
            'username': user_row['username'],
            'email': user_row['email'],
            'profile_pic': user_row['profile_picture'], 
            'created_at': user_row['created_at'],
            'is_admin': bool(user_row['is_admin'])
        }
>>>>>>> 39c4515ded846f8b80ca1a96717b64c5a9c7929c
        
        # Get all items for sale by this user
        cursor.execute('''
            SELECT id, name, category, price, status, created_at 
            FROM items 
            WHERE user_id = ? AND source = 'sell'
            ORDER BY created_at DESC
        ''', (session['user_id'],))
        items_for_sale = cursor.fetchall()
        
<<<<<<< HEAD
        # Get all donations by this user (by email) only if user is not an NGO
        donations = []
        if not user['is_admin']:  # Only show donations for regular users, not NGOs
            cursor.execute('''
                SELECT d.id, d.item_name, d.item_category, n.name as ngo_name, 
                       d.status, d.created_at, d.donor_phone
                FROM donations d
                JOIN ngos n ON d.ngo_id = n.id
                WHERE d.donor_email = ?
                ORDER BY d.created_at DESC
            ''', (user[2],))
            donations = cursor.fetchall()
        
        db.close()
        
        user_dict = {
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'created_at': user[4],
            'profile_pic': user[5] if len(user) > 5 else None
        }
=======
        # Get all donations by this user
        donations = []
        if not user_dict['is_admin']: 
            cursor.execute('''
                SELECT d.id, d.item_name, d.item_category, n.name as ngo_name, 
                       d.status, d.created_at, d.donor_phone, d.donor_name, d.donor_email
                FROM donations d
                JOIN ngos n ON d.ngo_id = n.id
                WHERE d.user_id = ? 
                ORDER BY d.created_at DESC
            ''', (session['user_id'],))
            donations = cursor.fetchall()
        
        total_sell = len(items_for_sale)
        total_donation = len(donations)
>>>>>>> 39c4515ded846f8b80ca1a96717b64c5a9c7929c
        
        return render_template('profile.html', 
                             user=user_dict,
                             items_for_sale=items_for_sale,
<<<<<<< HEAD
                             donations=donations)
                             
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('index'))
=======
                             donations=donations,
                             total_sell=total_sell,
                             total_donation=total_donation)
                             
    except Exception as e:
        print(f"Error in /profile: {str(e)}") 
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('index'))
    finally:
        if cursor:
            cursor.close()
        # db connection is closed by teardown_appcontext
>>>>>>> 39c4515ded846f8b80ca1a96717b64c5a9c7929c

@app.route('/donation/delete/<int:donation_id>', methods=['POST'])
def delete_donation(donation_id):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('DELETE FROM donations WHERE id = ?', (donation_id,))
        db.commit()
        db.close()
        flash('Donation deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting donation: {str(e)}', 'error')
    return redirect(url_for('profile'))

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        
        db = get_db()
        cursor = db.cursor()
        
        try:
            # Check if email exists
            cursor.execute('SELECT id, username FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            
            if user:
                # Generate OTP
                otp = generate_otp()
                store_otp(email, otp)
                
                # Send OTP via email with password reset purpose
                success, message = send_otp_email(email, otp, purpose='password_reset')
                
                if success:
                    flash('OTP has been sent to your email. Please check your inbox.', 'success')
                    return render_template('reset_password.html', email=email, show_otp=True)
                else:
                    flash(f'Failed to send OTP: {message}', 'error')
            else:
                flash('No account found with this email address.', 'error')
                
        except sqlite3.Error as e:
            print(f"Database error during forgot password: {str(e)}")
            flash(f'Database error: {str(e)}', 'error')
            
    return render_template('forgot_password.html')

@app.route('/reset-password', methods=['POST'])
def reset_password():
    email = request.form['email']
    otp = request.form['otp']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']
    
    if new_password != confirm_password:
        flash('Passwords do not match.', 'error')
        return render_template('reset_password.html', email=email, show_otp=True)
    
    if not verify_otp(email, otp):
        flash('Invalid or expired OTP. Please try again.', 'error')
        return render_template('reset_password.html', email=email, show_otp=True)
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Hash the new password
        hashed_password = generate_password_hash(new_password)
        
        # Update password in database
        cursor.execute('''
            UPDATE users 
            SET password = ?
            WHERE email = ?
        ''', (hashed_password, email))
        db.commit()
        
        # Clear OTP data after successful password reset
        if email in otp_store:
            del otp_store[email]
        
        flash('Password has been reset successfully. Please login with your new password.', 'success')
        return redirect(url_for('login'))
        
    except sqlite3.Error as e:
        print(f"Database error during password reset: {str(e)}")
        flash(f'Database error: {str(e)}', 'error')
        return render_template('reset_password.html', email=email, show_otp=True)

@app.route('/admin')
def admin():
    # Check if user is admin
    if not session.get('user_id'):
        flash('Please login to access admin panel.', 'error')
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Check if user is admin
        cursor.execute('SELECT is_admin FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()
        
        if not user or not user['is_admin']:
            flash('You do not have permission to access the admin panel.', 'error')
            return redirect(url_for('index'))
        
        # Get pending NGOs
        cursor.execute('SELECT * FROM ngos WHERE is_verified = 0')
        pending_ngos = cursor.fetchall()
        
        # Get all NGOs
        cursor.execute('SELECT * FROM ngos')
        all_ngos = cursor.fetchall()
        
        # Get all users
        cursor.execute('SELECT id, username, email, created_at, last_login FROM users')
        users = cursor.fetchall()
        
        # Get all items
        cursor.execute('''
            SELECT i.*, u.username as seller_name, n.name as ngo_name 
            FROM items i
            LEFT JOIN users u ON i.user_id = u.id
            LEFT JOIN ngos n ON i.ngo_id = n.id
        ''')
        items = cursor.fetchall()
        
        return render_template('admin.html', 
                             pending_ngos=pending_ngos,
                             all_ngos=all_ngos,
                             users=users,
                             items=items)
                             
    except sqlite3.Error as e:
        print(f"Database error in admin panel: {str(e)}")
        flash(f'Database error: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/admin/verify-ngo/<int:ngo_id>', methods=['POST'])
def verify_ngo(ngo_id):
    if not session.get('user_id'):
        flash('Please login to perform this action.', 'error')
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Check if user is admin
        cursor.execute('SELECT is_admin FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()
        
        if not user or not user['is_admin']:
            flash('You do not have permission to perform this action.', 'error')
            return redirect(url_for('index'))
        
        # Update NGO verification status
        cursor.execute('''
            UPDATE ngos 
            SET is_verified = 1, 
                verified_at = datetime('now'),
                verified_by = ?
            WHERE id = ?
        ''', (session['user_id'], ngo_id))
        db.commit()
        
        # Get NGO details for email
        cursor.execute('SELECT name, email FROM ngos WHERE id = ?', (ngo_id,))
        ngo = cursor.fetchone()
        
        if ngo:
            # Send verification email
            send_email(
                ngo['email'],
                "Your NGO has been verified",
                f"""
                <html>
                    <body>
                        <h2>Congratulations!</h2>
                        <p>Your NGO "{ngo['name']}" has been verified by the admin.</p>
                        <p>You can now start receiving donations through our platform.</p>
                    </body>
                </html>
                """
            )
        
        flash('NGO verified successfully!', 'success')
        return redirect(url_for('admin'))
        
    except sqlite3.Error as e:
        print(f"Database error during NGO verification: {str(e)}")
        flash(f'Database error: {str(e)}', 'error')
        return redirect(url_for('admin'))

@app.route('/admin/delete-ngo/<int:ngo_id>', methods=['POST'])
def delete_ngo(ngo_id):
    if not session.get('user_id'):
        flash('Please login to perform this action.', 'error')
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    
    # Check if user is admin
    cursor.execute('SELECT is_admin FROM users WHERE id = ?', (session['user_id'],))
    admin_user = cursor.fetchone()
    
    if not admin_user or not admin_user['is_admin']:
        flash('You do not have permission to perform this action.', 'error')
        # Not closing db here, teardown_appcontext will handle it.
        return redirect(url_for('index'))

    try:
        # Check if the NGO exists
        cursor.execute('SELECT id FROM ngos WHERE id = ?', (ngo_id,))
        ngo_to_delete = cursor.fetchone() 
        if not ngo_to_delete:
            flash('NGO not found.', 'error')
            # Not closing db here, teardown_appcontext will handle it.
            return redirect(url_for('admin')) # Return early

        # Delete related data from other tables (e.g., donations, items)
        cursor.execute('DELETE FROM donations WHERE ngo_id = ?', (ngo_id,))
        cursor.execute('DELETE FROM items WHERE ngo_id = ?', (ngo_id,))

        # Delete the NGO
        cursor.execute('DELETE FROM ngos WHERE id = ?', (ngo_id,))
        db.commit()
        db.close() # Explicitly close on success, following pattern of similar functions
        flash('NGO deleted successfully!', 'success')
        
    except Exception as e: 
        # Log the exception for easier debugging
        print(f"Error deleting NGO (ID: {ngo_id}): {str(e)}")
        flash(f'Error deleting NGO: {str(e)}', 'error')
        # db.close() will be handled by teardown_appcontext if an exception occurs here
        
    return redirect(url_for('admin')) # Common redirect point

@app.route('/items/delete/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    try:
        db = get_db()
        cursor = db.cursor()
        # First, delete all related item_views
        cursor.execute('DELETE FROM item_views WHERE item_id = ?', (item_id,))
        # If you have other tables referencing items, add similar lines here

        # Now delete the item itself
        cursor.execute('DELETE FROM items WHERE id = ?', (item_id,))
        db.commit()
        db.close()
        flash('Item deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting item: {str(e)}', 'error')
    return redirect(url_for('profile'))

# Add delete user and delete ngo routes
@app.route('/users/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    # Check if user is logged in and is an admin
    if not session.get('user_id') or not session.get('is_admin'):
        flash('You do not have permission to delete users.', 'error')
        return redirect(url_for('admin'))

    try:
        db = get_db()
        cursor = db.cursor()

        # Check if the user exists
        cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('admin'))

        # Prevent admin from deleting themselves
        if user_id == session.get('user_id'):
            flash('You cannot delete yourself.', 'error')
            return redirect(url_for('admin'))
        
        print(f"Attempting deletion for user_id: {user_id}")

        # Delete related data from item_views
        cursor.execute('DELETE FROM item_views WHERE user_id = ?', (user_id,))
        print(f"Deleted {cursor.rowcount} rows from item_views for user_id {user_id}")

        # Delete related data from items
        cursor.execute('DELETE FROM items WHERE user_id = ?', (user_id,))
        print(f"Deleted {cursor.rowcount} rows from items for user_id {user_id}")

        # Now attempt to delete the user
        print(f"Attempting final delete from users table for user_id {user_id}")
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        print(f"Deleted {cursor.rowcount} row(s) from users for user_id {user_id}")
        
        db.commit()
        print(f"Committed changes for user deletion ID: {user_id}")

        db.close() # Closing connection here after commit
        flash('User deleted successfully!', 'success')
    except Exception as e:
        # Print the specific error causing the failure
        print(f"Database error during user deletion: {str(e)}") # Log the specific error
        flash(f'Error deleting user: {str(e)}', 'error')
        # Ensure connection is closed even on error if it was opened
        db = getattr(g, '_database', None)
        if db is not None:
            db.close()
            
    return redirect(url_for('admin'))

@app.route('/ngos/delete/<int:ngo_id>', methods=['POST'])
def admin_delete_ngo(ngo_id):
    try:
        db = get_db()
        cursor = db.cursor()

        # Check if the NGO exists
        cursor.execute('SELECT id FROM ngos WHERE id = ?', (ngo_id,))
        ngo = cursor.fetchone()
        if not ngo:
            flash('NGO not found.', 'error')
            return redirect(url_for('admin'))

        # Delete related data from other tables (e.g., donations, items)
        cursor.execute('DELETE FROM donations WHERE ngo_id = ?', (ngo_id,))
        cursor.execute('DELETE FROM items WHERE ngo_id = ?', (ngo_id,))

        # Delete the NGO
        cursor.execute('DELETE FROM ngos WHERE id = ?', (ngo_id,))
        db.commit()
        db.close()
        flash('NGO deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting NGO: {str(e)}', 'error')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)
