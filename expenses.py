import sqlite3
import os

# Полный путь к базе данных
db_path = os.path.abspath('expenses.db')
print(f"Путь к базе данных: {db_path}")

# Подключение к базе данных
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Проверка данных
cursor.execute("SELECT * FROM expenses")
rows = cursor.fetchall()

# Вывод данных
for row in rows:
    print(row)

conn.close()