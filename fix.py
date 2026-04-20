import psycopg2

# আপনার দেওয়া External URL
db_url = "postgresql://gym_management_sysytem_user:BwEXWlC4wYVEwA1dyChnmsDT34si490y@dpg-d7grhlb7uimc73cv2sk0-a.virginia-postgres.render.com/gym_management_sysytem"

try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    # টেবিল তৈরি করা
    cur.execute("""
    CREATE TABLE IF NOT EXISTS members (
        id SERIAL PRIMARY KEY,
        name TEXT,
        phone TEXT,
        age INTEGER,
        fitness_goal TEXT,
        username TEXT UNIQUE,
        password TEXT
    );
    """)
    conn.commit()
    print("✅ Success! Tables created in the database.")
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    conn.close()
