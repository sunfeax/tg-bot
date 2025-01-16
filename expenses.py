import sqlite3

conn = sqlite3.connect('expenses.db')  # Файл базы данных
cursor = conn.cursor()

# cursor.execute('''
#     UPDATE expenses
#     SET date = DATE(date);
# ''')

# Вывести данные
cursor.execute("SELECT * FROM expenses;")

# Получение всех результатов
rows = cursor.fetchall()

# Вывод данных в терминал
for row in rows:
    print(row)

conn.commit()
conn.close()