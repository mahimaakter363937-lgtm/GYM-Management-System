import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "database.db")

conn = sqlite3.connect(DATABASE)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("--- MEMBERS TABLE ---")
rows = cursor.execute("SELECT id, name, username FROM members").fetchall()
for row in rows:
    print(f"ID: {row['id']}, Name: {row['name']}, Username: {row['username']}")

conn.close()
