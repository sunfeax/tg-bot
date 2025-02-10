from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from datetime import datetime
import sqlite3
import asyncio

bot = Bot(token='7809031263:AAFM3oVlukcyaxydu-tQme4c3imS-wqqKNc')
dp = Dispatcher(storage=MemoryStorage())

ALLOWED_USERS = {660558578, 432192596}
session_messages = []
pending_reports = set()

sqlite3.register_adapter(datetime, lambda d: d.strftime('%Y-%m-%d'))
sqlite3.register_converter("timestamp", lambda s: datetime.strptime(s.decode(), '%Y-%m-%d'))

@dp.message()
async def handle_all_messages(message: Message):

    if message.from_user.id not in ALLOWED_USERS:
        await message.answer("У вас нет доступа к этому боту.")
        return

    user_id = message.from_user.id
    username = message.from_user.full_name
    text = message.text.strip()

    session_messages.append(message)

    try:
        parts = text.split()

        if len(parts) != 2:
            await message.answer("Неверный формат. Требуется: <сумма категория> (25 еда) или <ID удалить> (7 удалить).")
            return
        
        conn = sqlite3.connect(r'C:\Users\Vladi\Desktop\dich\python\tg_bot-1\expenses.db')
        cursor = conn.cursor()

        # Добавление записи
        if parts[1].lower() != "удалить" and parts[1].lower() != "история":
            amount = float(parts[0].replace(",", "."))
            category = parts[1]
            date = message.date.strftime('%Y-%m-%d')
            cursor.execute('''
                INSERT INTO expenses (user_id, username, amount, category, date)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, amount, category, date))
            conn.commit()
            conn.close()
            await message.answer(f"Запись добавлена: {amount} € с пометкой {category}.")
            await notify_other_user(user_id, amount, category, message)

        # Удаление записи
        elif parts[1].lower() == "удалить":
            id = int(parts[0])
            cursor.execute("DELETE FROM expenses WHERE id = ?;", (id,))
            await message.answer(f"Запись с id {id} была удалена.")
            conn.commit()
            conn.close()

        # Просмотр всей истории
        elif parts == ["вся", "история"]:
            conn = sqlite3.connect('expenses.db')
            cursor.execute("SELECT * FROM expenses ORDER BY id;")
            rows = cursor.fetchall()
            for row in rows:
                all_history = "\n".join([f"{row[0]}. {row[2]} € | {row[3]} | {row[4]}| {row[5]}" for row in rows])
            await bot.send_message(user_id, f"История расходов:\n\n{all_history}")
            conn.close()

    except ValueError:
        await message.answer("Произошла ошибка. Используйте: <сумма категория> (10 аптека) или <id удалить> (25 удалить).")

    if message.from_user.id not in pending_reports and ["вся", "история"] != parts:
        pending_reports.add(message.from_user.id)
        await asyncio.sleep(0.4)
        await history(user_id)
        await balance(user_id)
        pending_reports.remove(message.from_user.id)


async def history(user_id: int):
    conn = sqlite3.connect(r'C:\Users\Vladi\Desktop\dich\python\tg_bot-1\expenses.db')
    cursor = conn.cursor()

    today = datetime.now()
    start_date = today.replace(day=1).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')
    query = '''
        SELECT id, username, amount, category, date 
        FROM expenses 
        WHERE date BETWEEN ? AND ?
        ORDER BY id
    '''
    params = (start_date, end_date)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    user_totals = {}
    for row in rows:
        user = row[1]
        amount = row[2]
        user_totals[user] = round(user_totals.get(user, 0) + amount, 2)
    history = "\n".join([f"{row[0]}. {row[1]} | {row[2]} € | {row[3]} | {row[4]}" for row in rows])
    totals_text = "\n".join([f"{user}: {total} €" for user, total in user_totals.items()])

    await bot.send_message(user_id, f"История расходов:\n\n{history}\n\nСумма трат за месяц:\n{totals_text}")
    

async def balance(user_id: int):

    conn = sqlite3.connect(r'C:\Users\Vladi\Desktop\dich\python\tg_bot-1\expenses.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT user_id, SUM(amount) as total_amount
        FROM expenses
        GROUP BY user_id
    ''')
    rows = cursor.fetchall()
    user_expenses = {row[0]: row[1] for row in rows}
    conn.close()

    if len(user_expenses) == 2:
        total_expenses = sum(user_expenses.values())
        each_share = total_expenses / 2
        balance = user_expenses.get(user_id, 0) - each_share
        balance_message = f"Ваш баланс составляет: {'+' if balance >= 0 else ''}{balance:.2f} €"
    else:
        balance_message = "Баланс можно рассчитать только для двух пользователей."
    await bot.send_message(user_id, balance_message)


async def notify_other_user(user_id: int, amount: float, category: str, message):
    next_user_id = next(uid for uid in ALLOWED_USERS if uid != user_id)
    username = message.from_user.full_name
    await bot.send_message(
        chat_id = next_user_id,
        text = f"Пользователь {username} добавил запись: {amount:.2f} € с пометкой '{category}'."
    )
    await balance(next_user_id)


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())