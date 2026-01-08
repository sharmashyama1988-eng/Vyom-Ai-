import sqlite3
import os
import sys
import time
import datetime
import csv

# Ensure database migrations are run
try:
    from vyom.core import history
except ImportError:
    pass # valid if running in a context where imports fail, but standard usage should work

# Configuration
DB_FILE = 'ai_database.db'

# ANSI Colors for CLI
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_db_connection():
    if not os.path.exists(DB_FILE):
        print(f"{Colors.FAIL}Error: Database file '{DB_FILE}' not found.{Colors.ENDC}")
        sys.exit(1)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def format_time(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

# --- ACTIONS ---

def view_dashboard():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Total Users
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        # Total Chats
        cursor.execute("SELECT COUNT(*) FROM chats")
        total_chats = cursor.fetchone()[0]
        
        # Total Messages
        cursor.execute("SELECT COUNT(*) FROM messages")
        total_msgs = cursor.fetchone()[0]
        
        # Gender Distribution
        try:
            cursor.execute("SELECT gender, COUNT(*) FROM users GROUP BY gender")
            gender_stats = cursor.fetchall()
        except:
            gender_stats = []

    print(f"\n{Colors.HEADER}--- SYSTEM DASHBOARD ---{Colors.ENDC}")
    print(f"Total Users:    {Colors.GREEN}{total_users}{Colors.ENDC}")
    print(f"Total Chats:    {Colors.BLUE}{total_chats}{Colors.ENDC}")
    print(f"Total Messages: {Colors.CYAN}{total_msgs}{Colors.ENDC}")
    
    if gender_stats:
        print(f"\n{Colors.BOLD}Gender Distribution:{Colors.ENDC}")
        for g, count in gender_stats:
            label = g if g else "Not Specified"
            print(f"  - {label}: {count}")
    print("-" * 30)

def list_users():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT name, email, gender, created, device_id FROM users ORDER BY created DESC")
            users = cursor.fetchall()
        except sqlite3.OperationalError as e:
            print(f"{Colors.FAIL}Error reading users: {e}{Colors.ENDC}")
            return

    if not users:
        print(f"{Colors.WARNING}No users found.{Colors.ENDC}")
        return

    print(f"\n{Colors.HEADER}{'NAME':<20} | {'EMAIL':<30} | {'GENDER':<15} | {'JOINED':<20} | {'DEVICE ID'}{Colors.ENDC}")
    print("-" * 110)
    
    for u in users:
        name = u['name'][:18] + '..' if len(u['name']) > 18 else u['name']
        email = u['email'][:28] + '..' if len(u['email']) > 28 else u['email']
        gender = u['gender'] if u['gender'] else "N/A"
        joined = format_time(u['created'])
        dev_id = u['device_id']
        
        print(f"{name:<20} | {email:<30} | {gender:<15} | {joined:<20} | {dev_id}")
    print("-" * 110)

def find_user():
    search = input(f"{Colors.BLUE}Enter Name or Email to search: {Colors.ENDC}").strip()
    if not search: return

    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = f"%{search}%"
        cursor.execute("SELECT * FROM users WHERE name LIKE ? OR email LIKE ?", (query, query))
        results = cursor.fetchall()

    if not results:
        print(f"{Colors.WARNING}No matching users found.{Colors.ENDC}")
    else:
        print(f"\n{Colors.GREEN}Found {len(results)} match(es):{Colors.ENDC}")
        for u in results:
            print(f"\nUser:   {Colors.BOLD}{u['name']}{Colors.ENDC}")
            print(f"Email:  {u['email']}")
            print(f"Gender: {u['gender']}")
            print(f"ID:     {u['device_id']}")
            print(f"API Key: {'Yes' if u['api_key'] else 'No'}")
            print(f"Joined: {format_time(u['created'])}")

def delete_user():
    user_id = input(f"{Colors.WARNING}Enter DEVICE ID to delete (or 'c' to cancel): {Colors.ENDC}").strip()
    if user_id.lower() == 'c' or not user_id: return

    with get_db_connection() as conn:
        # Check if exists
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM users WHERE device_id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            print(f"{Colors.FAIL}User not found.{Colors.ENDC}")
            return
            
        confirm = input(f"{Colors.FAIL}Are you sure you want to delete '{user['name']}' and ALL their chats? (yes/no): {Colors.ENDC}")
        if confirm.lower() == 'yes':
            # Enable foreign keys just in case
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Delete
            cursor.execute("DELETE FROM users WHERE device_id = ?", (user_id,))
            conn.commit()
            print(f"{Colors.GREEN}User deleted successfully.{Colors.ENDC}")
        else:
            print("Deletion cancelled.")

def export_csv():
    filename = f"users_export_{int(time.time())}.csv"
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        
        if not rows:
            print("No data to export.")
            return

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Write headers
            writer.writerow([description[0] for description in cursor.description])
            # Write data
            writer.writerows(rows)
    
    print(f"{Colors.GREEN}Successfully exported to {filename}{Colors.ENDC}")

# --- MAIN LOOP ---

def main():
    clear_screen()
    print(f"{Colors.CYAN}")
    print("██╗   ██╗██╗   ██╗ ██████╗ ███╗   ███╗    ██████╗██╗     ██╗")
    print("██║   ██║╚██╗ ██╔╝██╔═══██╗████╗ ████║    ██╔════╝██║     ██║")
    print("██║   ██║ ╚████╔╝ ██║   ██║██╔████╔██║    ██║     ██║     ██║")
    print("╚██╗ ██╔╝  ╚██╔╝  ██║   ██║██║╚██╔╝██║    ██║     ██║     ██║")
    print(" ╚████╔╝    ██║   ╚██████╔╝██║ ╚═╝ ██║    ╚██████╗███████╗██║")
    print("  ╚═══╝     ╚═╝    ╚═════╝ ╚═╝     ╚═╝     ╚═════╝╚══════╝╚═╝")
    print(f"             ADMIN CONTROL PANEL             {Colors.ENDC}")

    while True:
        print(f"\n{Colors.BOLD}Select Action:{Colors.ENDC}")
        print("1. View Dashboard (Stats)")
        print("2. List All Users")
        print("3. Find User (by Name/Email)")
        print("4. Delete User")
        print("5. Export Users to CSV")
        print("q. Exit")
        
        choice = input(f"\n{Colors.BLUE}vyom-admin> {Colors.ENDC}").strip().lower()
        
        if choice == '1':
            view_dashboard()
        elif choice == '2':
            list_users()
        elif choice == '3':
            find_user()
        elif choice == '4':
            delete_user()
        elif choice == '5':
            export_csv()
        elif choice == 'q' or choice == 'exit':
            print("Goodbye.")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
