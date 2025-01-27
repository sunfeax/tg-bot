import sqlite3

conn = sqlite3.connect('expenses.db')  # Файл базы данных
cursor = conn.cursor()

# Переименование старой таблицы
cursor.execute("ALTER TABLE expenses RENAME TO old_expenses;")

# Удаление старой таблицы
cursor.execute("DROP TABLE IF EXISTS expenses;")

cursor.execute("""
CREATE TABLE expenses (
    id INTEGER AUTOINCREMENT PRIMARY KEY,
    user_id INTEGER,
    username TEXT,
    amount REAL,
    category TEXT,
    date TEXT
);
""")

# Копирование данных обратно
cursor.execute("""
INSERT INTO expenses (id, user_id, username, amount, category, date)
SELECT id, user_id, username, amount, category, date
FROM old_expenses;
""")

# Удаление старой таблицы
cursor.execute("DROP TABLE old_expenses;")

cursor.execute("SELECT * FROM old_expenses;")

rows = cursor.fetchall()
for row in rows:
    print(row)

conn.commit()
conn.close()