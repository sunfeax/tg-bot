import os
import sqlite3
from pathlib import Path

DATA_DIR = Path(os.getenv("DATA_DIR", Path(__file__).resolve().parent))
DB_PATH = DATA_DIR / "expenses.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT * FROM expenses;")

rows = cursor.fetchall()
for row in rows:
    print(row)

conn.close()
