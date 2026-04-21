import sqlite3
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "database.db")

def update_tables():
    """
    এই ফাংশনটি ডাটাবেজে মাহিমা এবং রিচির মডিউলের জন্য নতুন টেবিল এবং কলাম তৈরি করে।
    """
    conn = None
    try:
        # ডাটাবেজ কানেকশন তৈরি
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        print(f"Connecting to database at: {DATABASE}")

        # ==========================================
        # ১. মেম্বার টেবিল আপডেট (রিচি'র মডিউল ১ ও ৩)
        # ==========================================
        try:
           
            c.execute("ALTER TABLE members ADD COLUMN fitness_level TEXT")
            print("✅ Added 'fitness_level' column to members table.")
        except sqlite3.OperationalError:
 
            print("ℹ️ 'fitness_level' column already exists.")

        # ==========================================
        # ২. ডায়েট প্ল্যান টেবিল (মাহিমা'র মডিউল ৩)
        # ==========================================
        
        
        c.execute("""
        CREATE TABLE IF NOT EXISTS diet_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            fitness_goal TEXT NOT NULL
        )
        """)

        
        c.execute("""
        CREATE TABLE IF NOT EXISTS member_diet_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id INTEGER NOT NULL,
            diet_plan_id INTEGER NOT NULL,
            assigned_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(member_id),
            FOREIGN KEY (member_id) REFERENCES members (id),
            FOREIGN KEY (diet_plan_id) REFERENCES diet_plans (id)
        )
        """)

        # ==========================================
        #  Attendence- Richy (Module3)
        # ==========================================

        # প্রতিদিনের মেম্বারদের উপস্থিতি (Present/Absent) সংরক্ষণের জন্য টেবিল
        c.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id INTEGER NOT NULL,
            status TEXT NOT NULL, -- 'Present' অথবা 'Absent'
            date TEXT NOT NULL,    -- তারিখ (YYYY-MM-DD)
            FOREIGN KEY (member_id) REFERENCES members (id)
        )
        ''')
        
        # ==========================================
        #  Workout shedule- Richy (Module3)
        # ==========================================


        c.execute('''
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id INTEGER NOT NULL,
            workout_type TEXT NOT NULL,      -- যেমন: Cardio, Strength, Yoga
            schedule_details TEXT NOT NULL,  -- ওয়ার্কআউটের বিস্তারিত বিবরণ
            assigned_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (member_id) REFERENCES members (id)
        )
        ''')
        
        conn.commit()
        print("✅ Success: All tables and columns for Richie and Mahima are ready!")

    except sqlite3.Error as e:
        print(f"❌ Database Error: {e}")
    
    finally:
        
        if conn:
            conn.close()

if __name__ == '__main__':
    update_tables()