import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "database.db")

conn = sqlite3.connect(DATABASE)
c = conn.cursor()

# Diet plans
c.execute("""
CREATE TABLE IF NOT EXISTS diet_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    fitness_goal TEXT NOT NULL
)
""")

# Member diet plan assignments
c.execute("""
CREATE TABLE IF NOT EXISTS member_diet_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    diet_plan_id INTEGER NOT NULL,
    assigned_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(member_id)
)
""")

conn.commit()
conn.close()
print("Database updated with diet tables (gym app).")
