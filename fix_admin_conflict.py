import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "database.db")

conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

print("--- Renaming member 'admin' to 'biva' ---")
cursor.execute("UPDATE members SET username='biva' WHERE username='admin' AND id=10")
conn.commit()

if cursor.rowcount > 0:
    print("SUCCESS: Renamed username from 'admin' to 'biva' for ID 10.")
else:
    print("FAILED: No member found with username 'admin' and ID 10 (or already renamed).")

conn.close()
