import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "database.db")

conn = sqlite3.connect(DATABASE)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("--- Checking for 'admin' username in members table ---")
row = cursor.execute("SELECT id, name, username FROM members WHERE username='admin'").fetchone()
if row:
    print(f"FOUND: ID: {row['id']}, Name: {row['name']}, Username: {row['username']}")
else:
    print("NOT FOUND")

conn.close()
