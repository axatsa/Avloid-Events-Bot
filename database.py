import sqlite3
from config import DATABASE_NAME

def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        full_name TEXT,
        phone TEXT,
        language TEXT
    )
    ''')
    
    # Categories table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )
    ''')
    
    # Pre-populate default categories if not exist
    cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES ('Online')")
    cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES ('Offline')")
    
    # Events table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER,
        image_id TEXT,
        description TEXT,
        time_info TEXT,
        event_date TEXT,
        max_participants INTEGER DEFAULT 0,
        location TEXT,
        FOREIGN KEY (category_id) REFERENCES categories (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS registrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        event_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES users (user_id),
        FOREIGN KEY (event_id) REFERENCES events (id)
    )
    ''')
    
    conn.commit()
    conn.close()

def add_user(user_id, full_name, phone, language):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (user_id, full_name, phone, language) VALUES (?, ?, ?, ?)", 
                   (user_id, full_name, phone, language))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def update_user_lang(user_id, language):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", (language, user_id))
    conn.commit()
    conn.close()

def update_user_name(user_id, full_name):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET full_name = ? WHERE user_id = ?", (full_name, user_id))
    conn.commit()
    conn.close()

def update_user_phone(user_id, phone):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET phone = ? WHERE user_id = ?", (phone, user_id))
    conn.commit()
    conn.close()

def is_user_registered(user_id, event_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM registrations WHERE user_id = ? AND event_id = ?", (user_id, event_id))
    reg = cursor.fetchone()
    conn.close()
    return reg is not None

def register_user_local(user_id, event_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO registrations (user_id, event_id) VALUES (?, ?)", (user_id, event_id))
    conn.commit()
    conn.close()

def get_registrations_by_event(event_id):
    """Get all registered users for a specific event"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.user_id, u.full_name, u.phone
        FROM registrations r
        JOIN users u ON r.user_id = u.user_id
        WHERE r.event_id = ?
    ''', (event_id,))
    registrations = cursor.fetchall()
    conn.close()
    return registrations

def get_all_users():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()
    return [u[0] for u in users]

def add_category(name):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_categories():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM categories")
    cats = cursor.fetchall()
    conn.close()
    return cats

def add_event(category_id, image_id, description, time_info, event_date, max_participants=0, location=None):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO events (category_id, image_id, description, time_info, event_date, max_participants, location) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (category_id, image_id, description, time_info, event_date, max_participants, location))
    conn.commit()
    conn.close()

def get_event_participants_count(event_id):
    """Get the number of registered participants for an event"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM registrations WHERE event_id = ?", (event_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_events_by_category(category_name):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
    SELECT e.image_id, e.description, e.time_info 
    FROM events e
    JOIN categories c ON e.category_id = c.id
    WHERE c.name = ?
    ''', (category_name,))
    events = cursor.fetchall()
    conn.close()
    return events

def get_all_events():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
    SELECT e.id, c.name, e.description 
    FROM events e
    JOIN categories c ON e.category_id = c.id
    ''')
    events = cursor.fetchall()
    conn.close()
    return events
