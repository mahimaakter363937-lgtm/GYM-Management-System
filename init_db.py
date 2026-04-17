import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "database.db")

def initialize():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # ১. সব টেবিল তৈরি (db_setup.py থেকে)
    c.executescript("""
    CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, phone TEXT, age INTEGER, fitness_goal TEXT,
        username TEXT UNIQUE, password TEXT, fitness_level TEXT
    );
    CREATE TABLE IF NOT EXISTS fitness_profile (
        id INTEGER PRIMARY KEY AUTOINCREMENT, member_id INTEGER,
        height REAL, weight REAL, bmi REAL, fitness_level TEXT
    );
    CREATE TABLE IF NOT EXISTS membership_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT, plan_name TEXT, 
        price REAL, duration_days INTEGER
    );
    CREATE TABLE IF NOT EXISTS memberships (
        id INTEGER PRIMARY KEY AUTOINCREMENT, member_id INTEGER, 
        plan_id INTEGER, start_date TEXT, end_date TEXT
    );
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT, member_id INTEGER, 
        plan_id INTEGER, amount REAL, payment_status TEXT, payment_date TEXT
    );
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT, member_id INTEGER NOT NULL, 
        message TEXT NOT NULL, is_read INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT, member_id INTEGER NOT NULL, 
        subject TEXT NOT NULL, message TEXT NOT NULL, status TEXT DEFAULT 'Pending', 
        admin_reply TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS diet_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, 
        description TEXT NOT NULL, fitness_goal TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS member_diet_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT, member_id INTEGER NOT NULL, 
        diet_plan_id INTEGER NOT NULL, assigned_at TEXT DEFAULT CURRENT_TIMESTAMP, 
        UNIQUE(member_id)
    );
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT, member_id INTEGER NOT NULL, 
        status TEXT NOT NULL, date TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS workouts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, member_id INTEGER NOT NULL, 
        workout_type TEXT NOT NULL, schedule_details TEXT NOT NULL, 
        assigned_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully with all 16 features!")

if __name__ == "__main__":
    initialize()
