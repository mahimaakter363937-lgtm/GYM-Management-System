import os
import psycopg2

def initialize():
    # Render থেকে DATABASE_URL নিয়ে আসা
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if not DATABASE_URL:
        print("❌ No DATABASE_URL found. Please set it in Render Environment Variables.")
        return

    # url-এ postgres:// থাকলে সেটাকে postgresql:// করে নেওয়া
    url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    try:
        conn = psycopg2.connect(url)
        c = conn.cursor()

        # ১. সব টেবিল তৈরি (PostgreSQL সিনট্যাক্স অনুযায়ী SERIAL ব্যবহার করে)
        c.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id SERIAL PRIMARY KEY, 
            name TEXT, phone TEXT, age INTEGER, fitness_goal TEXT,
            username TEXT UNIQUE, password TEXT, fitness_level TEXT
        );
        CREATE TABLE IF NOT EXISTS fitness_profile (
            id SERIAL PRIMARY KEY, member_id INTEGER,
            height REAL, weight REAL, bmi REAL, fitness_level TEXT
        );
        CREATE TABLE IF NOT EXISTS membership_plans (
            id SERIAL PRIMARY KEY, plan_name TEXT, 
            price REAL, duration_days INTEGER
        );
        CREATE TABLE IF NOT EXISTS memberships (
            id SERIAL PRIMARY KEY, member_id INTEGER, 
            plan_id INTEGER, start_date TEXT, end_date TEXT
        );
        CREATE TABLE IF NOT EXISTS payments (
            id SERIAL PRIMARY KEY, member_id INTEGER, 
            plan_id INTEGER, amount REAL, payment_status TEXT, payment_date TEXT
        );
        CREATE TABLE IF NOT EXISTS notifications (
            id SERIAL PRIMARY KEY, member_id INTEGER NOT NULL, 
            message TEXT NOT NULL, is_read INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS feedback (
            id SERIAL PRIMARY KEY, member_id INTEGER NOT NULL, 
            subject TEXT NOT NULL, message TEXT NOT NULL, status TEXT DEFAULT 'Pending', 
            admin_reply TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS diet_plans (
            id SERIAL PRIMARY KEY, name TEXT NOT NULL, 
            description TEXT NOT NULL, fitness_goal TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS member_diet_plans (
            id SERIAL PRIMARY KEY, member_id INTEGER UNIQUE NOT NULL, 
            diet_plan_id INTEGER NOT NULL, assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS attendance (
            id SERIAL PRIMARY KEY, member_id INTEGER NOT NULL, 
            status TEXT NOT NULL, date TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS workouts (
            id SERIAL PRIMARY KEY, member_id INTEGER NOT NULL, 
            workout_type TEXT NOT NULL, schedule_details TEXT NOT NULL, 
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS progress (
            id SERIAL PRIMARY KEY, member_id INTEGER, 
            weight REAL, bmi REAL, date TEXT
        );
        """)
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully on PostgreSQL with all 16 features!")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")

if __name__ == "__main__":
    initialize()
