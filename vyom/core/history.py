# d:/ai/history.py
import os
import sqlite3
import time
import uuid
import json
from contextlib import contextmanager

# --- CONSTANTS ---
DB_FILE = os.path.join(os.getcwd(), 'ai_database.db')
LEGACY_USERS_FILE = os.path.join(os.getcwd(), 'users', 'users.json')

# --- DATABASE SETUP ---

@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def _initialize_database():
    """Initializes the database tables if they don't exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # User table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                device_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                created REAL NOT NULL,
                api_key TEXT
            )
        ''')
        # Chats table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chats (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                created REAL NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (device_id) ON DELETE CASCADE
            )
        ''')
        # Messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp REAL NOT NULL,
                FOREIGN KEY (chat_id) REFERENCES chats (id) ON DELETE CASCADE
            )
        ''')
        
        # --- MIGRATION: Add api_key column if missing ---
        try:
            cursor.execute("SELECT api_key FROM users LIMIT 1")
        except sqlite3.OperationalError:
            # Column doesn't exist, add it
            print("Migrating Database: Adding api_key column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN api_key TEXT")

        # --- MIGRATION: Add gender column if missing ---
        try:
            cursor.execute("SELECT gender FROM users LIMIT 1")
        except sqlite3.OperationalError:
            print("Migrating Database: Adding gender column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN gender TEXT")

        # --- MIGRATION: Add default_engine and default_model columns if missing ---
        try:
            cursor.execute("SELECT default_engine FROM users LIMIT 1")
        except sqlite3.OperationalError:
            print("Migrating Database: Adding default_engine column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN default_engine TEXT")
        try:
            cursor.execute("SELECT default_model FROM users LIMIT 1")
        except sqlite3.OperationalError:
            print("Migrating Database: Adding default_model column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN default_model TEXT")

        # --- MIGRATION: Add api_keys column (JSON) if missing ---
        try:
            cursor.execute("SELECT api_keys FROM users LIMIT 1")
        except sqlite3.OperationalError:
            print("Migrating Database: Adding api_keys column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN api_keys TEXT")

        # --- MIGRATION: Add device info columns if missing ---
        for col in ["last_device", "last_os", "last_seen_platform", "last_location", "lat", "lon"]:
            try:
                cursor.execute(f"SELECT {col} FROM users LIMIT 1")
            except sqlite3.OperationalError:
                print(f"Migrating Database: Adding {col} column to users table...")
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
        
        conn.commit()
        # Check if migration is needed
        if os.path.exists(LEGACY_USERS_FILE):
            _migrate_legacy_data(conn)


def _migrate_legacy_data(conn):
    """
    Migrates data from the old JSON file to the new SQLite database.
    This is designed to be idempotent.
    """
    print("Checking for legacy data to migrate...")
    try:
        with open(LEGACY_USERS_FILE, 'r', encoding='utf-8') as f:
            legacy_users = json.load(f)
    except (IOError, json.JSONDecodeError):
        print("Could not read legacy users file or file is empty.")
        # Once migration is done or failed, rename the file to prevent re-running
        os.rename(LEGACY_USERS_FILE, LEGACY_USERS_FILE + '.migrated')
        return

    cursor = conn.cursor()
    for user_id, user_data in legacy_users.items():
        try:
            # 1. Migrate User
            cursor.execute(
                "INSERT OR IGNORE INTO users (device_id, name, email, created) VALUES (?, ?, ?, ?)",
                (user_id, user_data.get('name', ''), user_data.get('email', ''), user_data.get('created', time.time()))
            )

            # 2. Migrate Chats and Messages
            for chat_data in user_data.get('chats', []):
                chat_id = chat_data.get('id')
                if not chat_id: continue

                cursor.execute(
                    "INSERT OR IGNORE INTO chats (id, user_id, title, created) VALUES (?, ?, ?, ?)",
                    (chat_id, user_id, chat_data.get('title', 'Imported Chat'), time.time())
                )

                for msg_entry in chat_data.get('messages', []):
                    # Simple parsing for "role: content" format
                    role, content = "assistant", msg_entry
                    if isinstance(msg_entry, str) and ': ' in msg_entry:
                        parts = msg_entry.split(': ', 1)
                        if len(parts) == 2 and parts[0].lower() in ['user', 'assistant', 'system']:
                            role, content = parts
                    
                    cursor.execute(
                        "INSERT INTO messages (chat_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                        (chat_id, role, content, time.time())
                    )
        except sqlite3.IntegrityError as e:
            print(f"Skipping duplicate entry for user {user_id}: {e}")
        except Exception as e:
            print(f"An error occurred during migration for user {user_id}: {e}")


    conn.commit()
    print("Data migration completed.")
    # Rename the old file to prevent this from running again
    try:
        os.rename(LEGACY_USERS_FILE, LEGACY_USERS_FILE + '.migrated')
        print(f"Renamed legacy user file to {LEGACY_USERS_FILE}.migrated")
    except OSError as e:
        print(f"Could not rename legacy user file: {e}")


# --- PUBLIC API ---

def get_user(device_id):
    """Retrieves a single user's data, excluding their chats.

    Returns parsed `api_keys` (dict) if present and maintains backwards compatibility with `api_key`.
    """
    if not device_id:
        return None
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT device_id, name, email, created, api_key, api_keys, gender, default_engine, default_model FROM users WHERE device_id = ?", (device_id,))
        row = cursor.fetchone()
        if not row:
            return None
        user = dict(row)
        # Parse api_keys JSON if present
        api_keys_raw = user.get('api_keys')
        try:
            import json
            user['api_keys'] = json.loads(api_keys_raw) if api_keys_raw else {}
        except Exception:
            user['api_keys'] = {}
        return user if user else None

def save_user_api_key(device_id, api_key):
    """Updates the user's personal API Key (legacy single key)."""
    if not device_id: return False
    with get_db_connection() as conn:
        res = conn.execute(
            "UPDATE users SET api_key = ? WHERE device_id = ?",
            (api_key, device_id)
        )
        conn.commit()
        return res.rowcount > 0


def save_user_api_keys(device_id, keys: dict):
    """Saves multiple named API keys as JSON in the `api_keys` column."""
    if not device_id or not isinstance(keys, dict):
        return False
    import json
    keys_json = json.dumps(keys)
    with get_db_connection() as conn:
        res = conn.execute(
            "UPDATE users SET api_keys = ? WHERE device_id = ?",
            (keys_json, device_id)
        )
        conn.commit()
        return res.rowcount > 0


def save_user_preferences(device_id, default_engine=None, default_model=None):
    """Saves user's default engine/model preferences."""
    if not device_id: return False
    with get_db_connection() as conn:
        # Build dynamic update
        updates = []
        params = []
        if default_engine is not None:
            updates.append("default_engine = ?")
            params.append(default_engine)
        if default_model is not None:
            updates.append("default_model = ?")
            params.append(default_model)
        if not updates:
            return False
        params.append(device_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE device_id = ?"
        res = conn.execute(query, params)
        conn.commit()
        return res.rowcount > 0

def register_user(device_id, name, email, gender=None):
    """Creates or updates a user's registration data."""
    if not all([device_id, name, email]):
        return None, "device_id, name and email are required"

    # Email Validation
    import re
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return None, "Invalid email address format"

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT device_id FROM users WHERE device_id = ?", (device_id,))
        exists = cursor.fetchone()

        if not exists:
            # Create new user
            conn.execute(
                "INSERT INTO users (device_id, name, email, created, gender) VALUES (?, ?, ?, ?, ?)",
                (device_id, name, email, time.time(), gender)
            )
            # Create a default chat for the new user
            new_chat_id = "chat-" + str(uuid.uuid4())
            conn.execute(
                "INSERT INTO chats (id, user_id, title, created) VALUES (?, ?, ?, ?)",
                (new_chat_id, device_id, "Welcome Chat", time.time())
            )
        else:
            # Update existing user
            if gender:
                conn.execute(
                    "UPDATE users SET name = ?, email = ?, gender = ? WHERE device_id = ?",
                    (name, email, gender, device_id)
                )
            else:
                conn.execute(
                    "UPDATE users SET name = ?, email = ? WHERE device_id = ?",
                    (name, email, device_id)
                )
        conn.commit()

    return get_user(device_id), None


def get_chat_sessions(device_id):
    """Returns a list of all chat sessions for a user (id and title)."""
    if not device_id:
        return []
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, title FROM chats WHERE user_id = ? ORDER BY created DESC",
            (device_id,)
        )
        chats = cursor.fetchall()
        return [dict(chat) for chat in chats]

def start_new_chat(device_id):
    """Creates a new, empty chat for the user and returns it."""
    if not device_id:
        return None
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT device_id FROM users WHERE device_id = ?", (device_id,))
        if not cursor.fetchone():
            return None # User must exist
        
        new_chat = {
            "id": "chat-" + str(uuid.uuid4()),
            "title": "New Chat",
            "created": time.time()
        }
        conn.execute(
            "INSERT INTO chats (id, user_id, title, created) VALUES (?, ?, ?, ?)",
            (new_chat['id'], device_id, new_chat['title'], new_chat['created'])
        )
        conn.commit()
        # Add messages key for compatibility with existing frontend if needed
        new_chat['messages'] = []
        return new_chat


def get_chat_history(device_id, chat_id):
    """Gets the messages for a specific chat session."""
    if not all([device_id, chat_id]):
        return None
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Ensure the chat belongs to the user
        cursor.execute(
            "SELECT 1 FROM chats WHERE id = ? AND user_id = ?",
            (chat_id, device_id)
        )
        if not cursor.fetchone():
            return None # Chat doesn't exist or doesn't belong to the user
            
        cursor.execute(
            "SELECT role, content, timestamp FROM messages WHERE chat_id = ? ORDER BY timestamp ASC",
            (chat_id,)
        )
        # Return structured data
        return [dict(row) for row in cursor.fetchall()]


def add_to_chat_history(device_id, chat_id, entry, role=None):
    """Adds a message to a specific chat session."""
    if not all([device_id, chat_id]):
        return False
        
    content = entry
    # If role is not provided, try to parse it from the entry string for backward compatibility
    if not role and isinstance(entry, str) and ': ' in entry:
        parts = entry.split(': ', 1)
        if len(parts) == 2 and parts[0].lower() in ['user', 'assistant', 'system', 'vyom ai']:
            parsed_role = parts[0].lower()
            if parsed_role == 'vyom ai': parsed_role = 'assistant'
            role, content = parsed_role, parts[1]
    
    if not role: 
        role = 'assistant'

    with get_db_connection() as conn:
        cursor = conn.cursor()
        # 1. Verify chat exists and belongs to the user
        cursor.execute("SELECT title, (SELECT COUNT(*) FROM messages WHERE chat_id=?) FROM chats WHERE id = ? AND user_id = ?", (chat_id, chat_id, device_id))
        result = cursor.fetchone()

        if not result:
            return False # Chat not found or access denied

        chat_title, message_count = result

        # 2. Insert the new message
        conn.execute(
            "INSERT INTO messages (chat_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (chat_id, role, content, time.time())
        )

        # 3. If this is the first user message, generate a title
        if message_count == 0 and role == 'user':
            # Simple title generation from the first few words of the content
            title = ' '.join(str(content).split()[:5])
            if len(str(content).split()) > 5:
                title += "..."
            conn.execute("UPDATE chats SET title = ? WHERE id = ?", (title, chat_id))
            
        conn.commit()
        return True


def rename_chat(device_id, chat_id, new_title):
    """Renames a specific chat session."""
    if not all([device_id, chat_id, new_title]):
        return False
    with get_db_connection() as conn:
        res = conn.execute(
            "UPDATE chats SET title = ? WHERE id = ? AND user_id = ?",
            (new_title, chat_id, device_id)
        )
        conn.commit()
        return res.rowcount > 0


def delete_chat(device_id, chat_id):
    """Deletes a specific chat session."""
    if not all([device_id, chat_id]):
        return False
        
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check how many chats the user has
        cursor.execute("SELECT COUNT(*) FROM chats WHERE user_id = ?", (device_id,))
        chat_count = cursor.fetchone()[0]

        # Prevent deleting the last chat
        if chat_count <= 1:
            # Instead of deleting, just clear its messages
            conn.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
            conn.execute("UPDATE chats SET title = 'New Chat' WHERE id = ?", (chat_id,))
            conn.commit()
            return True # Indicate an operation was performed

        # If more than one chat exists, proceed with deletion
        res = conn.execute(
            "DELETE FROM chats WHERE id = ? AND user_id = ?",
            (chat_id, device_id)
        )
        conn.commit()
        return res.rowcount > 0


def delete_all_chats(device_id):
    """Deletes ALL chat history for a specific device ID."""
    if not device_id: return False
    with get_db_connection() as conn:
        # We'll just delete all chats and create one new one.
        # The CASCADE foreign key will handle deleting all messages.
        conn.execute("DELETE FROM chats WHERE user_id = ?", (device_id,))
        
        # Create a new default chat
        new_chat_id = "chat-" + str(uuid.uuid4())
        conn.execute(
            "INSERT INTO chats (id, user_id, title, created) VALUES (?, ?, ?, ?)",
            (new_chat_id, device_id, "Welcome Back", time.time())
        )
        conn.commit()
    return True

def find_user_by_email(email):
    """Finds a user by their email address."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None

def link_device_to_user(old_id, new_id):
    """
    Merges an existing user account (old_id) into the current device session (new_id).
    Preserves the new_id so the browser session stays valid.
    """
    if not old_id or not new_id or old_id == new_id:
        return

    with get_db_connection() as conn:
        # 1. Get Old User Data
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE device_id = ?", (old_id,))
        old_user = cursor.fetchone()
        
        if not old_user: return # Should not happen

        # 2. Check if New Device ID exists (e.g. Guest session)
        cursor.execute("SELECT * FROM users WHERE device_id = ?", (new_id,))
        new_user = cursor.fetchone()

        # 3. Migrate User Data
        if new_user:
            # Overwrite guest data with the logged-in user's data
            # We keep 'created' from the old user to show account age
            conn.execute('''
                UPDATE users 
                SET name=?, email=?, api_key=?, api_keys=?, gender=?, default_engine=?, default_model=?, created=?
                WHERE device_id=?
            ''', (
                old_user['name'], old_user['email'], old_user['api_key'], 
                old_user['api_keys'], old_user['gender'], old_user['default_engine'], 
                old_user['default_model'], old_user['created'],
                new_id
            ))
        else:
            # Create new record for new_id with old data
            conn.execute('''
                INSERT INTO users (device_id, name, email, created, api_key, api_keys, gender, default_engine, default_model)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                new_id, old_user['name'], old_user['email'], old_user['created'],
                old_user['api_key'], old_user['api_keys'], old_user['gender'],
                old_user['default_engine'], old_user['default_model']
            ))

        # 4. Migrate Chats
        # Move all chats from old_id to new_id
        conn.execute("UPDATE chats SET user_id = ? WHERE user_id = ?", (new_id, old_id))

        # 5. Delete Old User Record
        # (Chats are already moved, so we can safely delete the user)
        conn.execute("DELETE FROM users WHERE device_id = ?", (old_id,))
        
        conn.commit()

def update_user(device_id, data):
    """Updates a user's record with provided data dictionary."""
    if not device_id or not data:
        return False
    
    with get_db_connection() as conn:
        # Build dynamic update query
        keys = data.keys()
        set_clause = ", ".join([f"{key} = ?" for key in keys])
        values = list(data.values())
        values.append(device_id)
        
        query = f"UPDATE users SET {set_clause} WHERE device_id = ?"
        try:
            res = conn.execute(query, values)
            conn.commit()
            return res.rowcount > 0
        except sqlite3.OperationalError as e:
            print(f"Error updating user: {e}")
            return False

def get_all_users():
    """Returns a list of all registered users."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        return [dict(row) for row in cursor.fetchall()]

# --- INITIALIZATION ---
_initialize_database()
