import psycopg2
import os

# ⚠️ PASTE YOUR RENDER "EXTERNAL DATABASE URL" HERE
DB_URL = "postgresql://gym_management_sysytem_user:BwEXWlC4wYVEwA1dyChnmsDT34si490y@dpg-d7grhlb7uimc73cv2sk0-a.virginia-postgres.render.com/gym_management_sysytem"

def create_tables():
    print("Connecting to database...")
    conn = psycopg2.connect(DB_URL)
    c = conn.cursor()

    # 1. Members
    c.execute("""
    CREATE TABLE IF NOT EXISTS members (
        id SERIAL PRIMARY KEY,
        name TEXT,
        phone TEXT,
        age INTEGER,
        fitness_goal TEXT,
        username TEXT UNIQUE,
        password TEXT,
        fitness_level TEXT
    )
    """)

    # 2. Fitness profile
    c.execute("""
    CREATE TABLE IF NOT EXISTS fitness_profile (
        id SERIAL PRIMARY KEY,
        member_id INTEGER REFERENCES members(id),
        height REAL,
        weight REAL,
        bmi REAL,
        fitness_level TEXT
    )
    """)

    # 3. Membership plans
    c.execute("""
    CREATE TABLE IF NOT EXISTS membership_plans (
        id SERIAL PRIMARY KEY,
        plan_name TEXT,
        price REAL,
        duration_days INTEGER
    )
    """)

    # 4. Memberships
    c.execute("""
    CREATE TABLE IF NOT EXISTS memberships (
        id SERIAL PRIMARY KEY,
        member_id INTEGER REFERENCES members(id),
        plan_id INTEGER REFERENCES membership_plans(id),
        start_date TEXT,
        end_date TEXT
    )
    """)

    # 5. Payments
    c.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id SERIAL PRIMARY KEY,
        member_id INTEGER REFERENCES members(id),
        plan_id INTEGER REFERENCES membership_plans(id),
        amount REAL,
        payment_status TEXT,
        payment_date TEXT
    )
    """)

    # 6. Notifications
    c.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id SERIAL PRIMARY KEY,
        member_id INTEGER NOT NULL REFERENCES members(id),
        message TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 7. Feedback
    c.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id SERIAL PRIMARY KEY,
        member_id INTEGER NOT NULL REFERENCES members(id),
        subject TEXT NOT NULL,
        message TEXT NOT NULL,
        status TEXT DEFAULT 'Pending',
        admin_reply TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 8. Diet Plans
    c.execute("""
    CREATE TABLE IF NOT EXISTS diet_plans (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        fitness_goal TEXT NOT NULL
    )
    """)

    # 9. Member Diet Plans
    c.execute("""
    CREATE TABLE IF NOT EXISTS member_diet_plans (
        id SERIAL PRIMARY KEY,
        member_id INTEGER UNIQUE NOT NULL REFERENCES members(id),
        diet_plan_id INTEGER NOT NULL REFERENCES diet_plans(id),
        assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 10. Attendance
    c.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id SERIAL PRIMARY KEY,
        member_id INTEGER NOT NULL REFERENCES members(id),
        status TEXT NOT NULL,
        date TEXT NOT NULL
    )
    """)

    # 11. Workouts
    c.execute("""
    CREATE TABLE IF NOT EXISTS workouts (
        id SERIAL PRIMARY KEY,
        member_id INTEGER NOT NULL REFERENCES members(id),
        workout_type TEXT NOT NULL,
        schedule_details TEXT NOT NULL,
        assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()
    print("✅ Success: All PostgreSQL tables are created and ready!")

if __name__ == '__main__':
    create_tables()