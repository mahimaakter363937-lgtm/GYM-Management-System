import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

# Create members table
c.execute('''
CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT,
    age INTEGER,
    fitness_goal TEXT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
''')

# Create fitness_profile table
c.execute('''
CREATE TABLE IF NOT EXISTS fitness_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER UNIQUE,
    height REAL,
    weight REAL,
    bmi REAL,
    fitness_level TEXT,
    FOREIGN KEY (member_id) REFERENCES members(id)
)
''')

# Create membership_plans table
c.execute('''
CREATE TABLE IF NOT EXISTS membership_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_name TEXT,
    duration_days INTEGER,
    price REAL
)
''')

# Insert default plans if not exists
c.execute("SELECT COUNT(*) FROM membership_plans")
if c.fetchone()[0] == 0:
    plans = [
        ('Monthly', 30, 50.0),
        ('Quarterly', 90, 140.0),
        ('Yearly', 365, 500.0)
    ]
    c.executemany("INSERT INTO membership_plans (plan_name, duration_days, price) VALUES (?,?,?)", plans)

# Create memberships table
c.execute('''
CREATE TABLE IF NOT EXISTS memberships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER UNIQUE,
    plan_id INTEGER,
    start_date TEXT,
    end_date TEXT,
    FOREIGN KEY (member_id) REFERENCES members(id),
    FOREIGN KEY (plan_id) REFERENCES membership_plans(id)
)
''')

conn.commit()
conn.close()
print("Database setup completed successfully!")