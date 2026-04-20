import psycopg2
import os

def setup_postgres():
    conn = None
    try:
        # ১. কানেকশন সেটআপ: 
        # রেন্ডার থেকে পাওয়া 'External Database URL' আপনার পিসির এনভায়রনমেন্টে সেট থাকলে সেটি নেবে, 
        # না থাকলে আপনি সরাসরি এখানে স্ট্রিং হিসেবে দিতে পারেন।
        
        # আপনার রেন্ডার ড্যাশবোর্ড থেকে পাওয়া 'External Database URL' নিচে দিন
        external_url = "আপনার_EXTERNAL_DATABASE_URL_এখানে_দিন" 
        
        print("⏳ Connecting to PostgreSQL...")
        conn = psycopg2.connect(postgresql://gym_management_sysytem_user:BwEXWlC4wYVEwA1dyChnmsDT34si490y@dpg-d7grhlb7uimc73cv2sk0-a.virginia-postgres.render.com/gym_management_sysytem)
        c = conn.cursor()

        # ১. Members Table
        c.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT,
            age INTEGER,
            fitness_goal TEXT,
            fitness_level TEXT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """)

        # ২. Fitness Profile
        c.execute("""
        CREATE TABLE IF NOT EXISTS fitness_profile (
            id SERIAL PRIMARY KEY,
            member_id INTEGER REFERENCES members(id) ON DELETE CASCADE,
            height FLOAT,
            weight FLOAT,
            bmi FLOAT,
            fitness_level TEXT
        )
        """)

        # ৩. Membership Plans
        c.execute("""
        CREATE TABLE IF NOT EXISTS membership_plans (
            id SERIAL PRIMARY KEY,
            plan_name TEXT NOT NULL,
            price FLOAT NOT NULL,
            duration_days INTEGER NOT NULL
        )
        """)

        # ৪. Memberships
        c.execute("""
        CREATE TABLE IF NOT EXISTS memberships (
            id SERIAL PRIMARY KEY,
            member_id INTEGER REFERENCES members(id) ON DELETE CASCADE,
            plan_id INTEGER REFERENCES membership_plans(id) ON DELETE SET NULL,
            start_date DATE DEFAULT CURRENT_DATE,
            end_date DATE
        )
        """)

        # ৫. Payments
        c.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id SERIAL PRIMARY KEY,
            member_id INTEGER REFERENCES members(id) ON DELETE CASCADE,
            plan_id INTEGER REFERENCES membership_plans(id),
            amount FLOAT NOT NULL,
            payment_status TEXT DEFAULT 'Pending',
            payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # ৬. Notifications
        c.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id SERIAL PRIMARY KEY,
            member_id INTEGER REFERENCES members(id) ON DELETE CASCADE,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # ৭. Feedback
        c.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id SERIAL PRIMARY KEY,
            member_id INTEGER REFERENCES members(id) ON DELETE CASCADE,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            admin_reply TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # ৮. Diet Plans
        c.execute("""
        CREATE TABLE IF NOT EXISTS diet_plans (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            fitness_goal TEXT NOT NULL
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS member_diet_plans (
            id SERIAL PRIMARY KEY,
            member_id INTEGER UNIQUE REFERENCES members(id) ON DELETE CASCADE,
            diet_plan_id INTEGER REFERENCES diet_plans(id) ON DELETE SET NULL,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # ৯. Attendance
        c.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id SERIAL PRIMARY KEY,
            member_id INTEGER REFERENCES members(id) ON DELETE CASCADE,
            status TEXT NOT NULL,
            date DATE NOT NULL DEFAULT CURRENT_DATE
        )
        """)

        # ১০. Workouts
        c.execute("""
        CREATE TABLE IF NOT EXISTS workouts (
            id SERIAL PRIMARY KEY,
            member_id INTEGER REFERENCES members(id) ON DELETE CASCADE,
            workout_type TEXT NOT NULL,
            schedule_details TEXT NOT NULL,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()
        print("✅ PostgreSQL Database initialized successfully on Render!")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    setup_postgres()
