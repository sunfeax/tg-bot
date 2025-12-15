import os
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from datetime import datetime
import sqlite3
import asyncio
import dotenv
import logging

dotenv.load_dotenv()

logging.basicConfig(
    level = logging.INFO,
    format = "%(asctime)s - %(levelname)s - %(message)s",
    handlers = [logging.FileHandler("bot.log", encoding="utf-8"),
                logging.StreamHandler()])

TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

ALLOWED_USERS = {660558578, 432192596}
session_messages = []
pending_reports = set()
DELETE_KEYWORDS = {"delete", "remove"}
HISTORY_KEYWORDS = {"history"}

sqlite3.register_adapter(datetime, lambda d: d.strftime('%Y-%m-%d'))
sqlite3.register_converter("timestamp", lambda s: datetime.strptime(s.decode(), '%Y-%m-%d'))

@dp.message()
async def handle_all_messages(message: Message):

    if message.from_user.id not in ALLOWED_USERS:
        await message.answer("You do not have access to this bot.")
        return

    user_id = message.from_user.id
    username = message.from_user.full_name
    text = message.text.strip()

    logging.info(f"User {user_id} sent message: {message.text}")

    session_messages.append(message)

    parts = text.split()

    if len(parts) != 2:
        await message.answer("Invalid format. Required: <amount category> (25 food) or <ID delete> (7 delete).")
        return

    command = parts[1].lower()
    skip_auto_report = parts == ["all", "history"]

    try:
        conn = sqlite3.connect('expenses.db')
        cursor = conn.cursor()

        if command not in DELETE_KEYWORDS and command not in HISTORY_KEYWORDS:
            amount = float(parts[0].replace(",", "."))
            category = parts[1]
            date = message.date.strftime('%Y-%m-%d')
            cursor.execute('''
                INSERT INTO expenses (user_id, username, amount, category, date)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, amount, category, date))
            conn.commit()
            conn.close()
            await message.answer(f"Entry added: {amount} € under {category}.")
            await notify_other_user(user_id, amount, category, message)

        elif command in DELETE_KEYWORDS:
            id = int(parts[0])
            cursor.execute("DELETE FROM expenses WHERE id = ?;", (id,))
            await message.answer(f"Entry with id {id} was deleted.")
            conn.commit()
            conn.close()

    except ValueError:
        await message.answer("An error occurred. Use: <amount category> (10 pharmacy) or <id delete> (25 delete).")

    if message.from_user.id not in pending_reports and not skip_auto_report:
        pending_reports.add(message.from_user.id)
        await asyncio.sleep(0.4)
        await history(user_id)
        await balance(user_id)
        pending_reports.remove(message.from_user.id)


async def history(user_id: int):
    conn = sqlite3.connect('expenses.db')
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

    await bot.send_message(user_id, f"Expense History:\n\n{history}\n\nMonthly Spending Totals:\n{totals_text}")
    

async def balance(user_id: int):

    conn = sqlite3.connect('expenses.db')
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
        balance_message = f"Your balance is: {'+' if balance >= 0 else ''}{balance:.2f} €"
    else:
        balance_message = "Balance can only be calculated for two users."
    await bot.send_message(user_id, balance_message)


async def notify_other_user(user_id: int, amount: float, category: str, message):
    next_user_id = next(uid for uid in ALLOWED_USERS if uid != user_id)
    username = message.from_user.full_name
    await bot.send_message(
        chat_id = next_user_id,
        text = f"User {username} added a record: {amount:.2f} € under '{category}'."
    )
    await balance(next_user_id)


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
