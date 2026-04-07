import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "database.db")

conn = sqlite3.connect(DATABASE)
c = conn.cursor()

# Members
c.execute("""
CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    phone TEXT,
    age INTEGER,
    fitness_goal TEXT,
    username TEXT UNIQUE,
    password TEXT
)
""")

# Fitness profile
c.execute("""
CREATE TABLE IF NOT EXISTS fitness_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER,
    height REAL,
    weight REAL,
    bmi REAL,
    fitness_level TEXT
)
""")

# Membership plans
c.execute("""
CREATE TABLE IF NOT EXISTS membership_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_name TEXT,
    price REAL,
    duration_days INTEGER
)
""")

# Memberships
c.execute("""
CREATE TABLE IF NOT EXISTS memberships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER,
    plan_id INTEGER,
    start_date TEXT,
    end_date TEXT
)
""")

# Payments (MODULE 2)
c.execute("""
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER,
    plan_id INTEGER,
    amount REAL,
    payment_status TEXT,
    payment_date TEXT
)
""")

conn.commit()
conn.close()
