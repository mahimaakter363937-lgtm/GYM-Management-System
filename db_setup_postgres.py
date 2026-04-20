import psycopg2

def setup_postgres():
    try:
        conn = psycopg2.connect(
            dbname="your_db_name",
            user="postgres",
            password="your_password",
            host="localhost"
        )
        c = conn.cursor()

        # ১. Members Table (Richy ও অন্যদের মডিউলের কলামসহ)
        c.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id SERIAL PRIMARY KEY,
            name TEXT,
            phone TEXT,
            age INTEGER,
            fitness_goal TEXT,
            fitness_level TEXT,
            username TEXT UNIQUE,
            password TEXT
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
            plan_name TEXT,
            price FLOAT,
            duration_days INTEGER
        )
        """)

        # ৪. Memberships
        c.execute("""
        CREATE TABLE IF NOT EXISTS memberships (
            id SERIAL PRIMARY KEY,
            member_id INTEGER REFERENCES members(id),
            plan_id INTEGER REFERENCES membership_plans(id),
            start_date DATE DEFAULT CURRENT_DATE,
            end_date DATE
        )
        """)

        # ৫. Payments
        c.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id SERIAL PRIMARY KEY,
            member_id INTEGER REFERENCES members(id),
            plan_id INTEGER REFERENCES membership_plans(id),
            amount FLOAT,
            payment_status TEXT,
            payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # ৬. Notifications (Biva's Module)
        c.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id SERIAL PRIMARY KEY,
            member_id INTEGER REFERENCES members(id),
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # ৭. Feedback (Biva's Module)
        c.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id SERIAL PRIMARY KEY,
            member_id INTEGER REFERENCES members(id),
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            admin_reply TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # ৮. Diet Plans (Mahima's Module)
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
            member_id INTEGER UNIQUE REFERENCES members(id),
            diet_plan_id INTEGER REFERENCES diet_plans(id),
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # ৯. Attendance (Richy's Module)
        c.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id SERIAL PRIMARY KEY,
            member_id INTEGER REFERENCES members(id),
            status TEXT NOT NULL,
            date DATE NOT NULL
        )
        """)

        # ১০. Workouts (Richy/Zadid)
        c.execute("""
        CREATE TABLE IF NOT EXISTS workouts (
            id SERIAL PRIMARY KEY,
            member_id INTEGER REFERENCES members(id),
            workout_type TEXT NOT NULL,
            schedule_details TEXT NOT NULL,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()
        print("✅ PostgreSQL Database initialized successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    setup_postgres()
