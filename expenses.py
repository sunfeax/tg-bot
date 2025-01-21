import sqlite3

conn = sqlite3.connect('expenses.db')  # Файл базы данных
cursor = conn.cursor()

cursor.execute("SELECT * FROM expenses;")

cursor.execute("SELECT * FROM expenses;")

rows = cursor.fetchall()
for row in rows:
    print(row)

conn.commit()
conn.close()