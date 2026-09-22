from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramForbiddenError
from datetime import datetime
from pathlib import Path
import sqlite3
import asyncio
import logging
import os
import re
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "expenses.db"

logging.basicConfig(
  level=os.getenv("LOG_LEVEL", "INFO").upper(),
  format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

ALLOWED_USERS = set(
  int(uid.strip())
  for uid in os.getenv("ALLOWED_USER_IDS", "").split(",")
  if uid.strip()
)

bot = Bot(token=os.getenv("TOKEN"))
dp = Dispatcher(storage=MemoryStorage())

ADD_PATTERN = re.compile(r'^(\d+[.,]?\d*)\s+(\S+)$')
DEL_PATTERN = re.compile(r'^(\d+)\s+удалить$', re.IGNORECASE)
HIST_PATTERN = re.compile(r'^вся\s+история$', re.IGNORECASE)

sqlite3.register_adapter(datetime, lambda d: d.strftime('%Y-%m-%d'))
sqlite3.register_converter("timestamp", lambda s: datetime.strptime(s.decode(), '%Y-%m-%d'))


def init_db():
  with sqlite3.connect(DB_PATH) as conn:
    conn.execute(
      '''CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        date TEXT NOT NULL)'''
    )
    conn.commit()

summary_timers: dict[int, asyncio.Task] = {}

MAX_MSG_LEN = 4096


async def send_long(user_id: int, text: str):
  for i in range(0, max(len(text), 1), MAX_MSG_LEN):
    await bot.send_message(user_id, text[i:i + MAX_MSG_LEN])


async def _send_summary(user_id: int):
  await asyncio.sleep(1.5)
  await history(user_id)
  await balance(user_id)


def schedule_summary(user_id: int):
  task = summary_timers.get(user_id)
  if task and not task.done():
    task.cancel()
  summary_timers[user_id] = asyncio.create_task(_send_summary(user_id))


@dp.message()
async def handle_all_messages(message: Message):
  if not message.text:
    await message.answer("Бот принимает только текстовые сообщения.")
    return

  if message.from_user.id not in ALLOWED_USERS:
    await message.answer("У вас нет доступа к этому боту.")
    return

  user_id = message.from_user.id
  username = message.from_user.full_name
  text = message.text.strip()

  log.info(f"[{username} | {user_id}] {text!r}")

  try:
    if DEL_PATTERN.match(text):
      record_id = int(DEL_PATTERN.match(text).group(1))
      await handle_delete(message, user_id, username, record_id)

    elif HIST_PATTERN.match(text):
      await full_history(user_id)
      return

    elif ADD_PATTERN.match(text):
      m = ADD_PATTERN.match(text)
      amount = float(m.group(1).replace(",", "."))
      category = m.group(2)
      await handle_add(message, user_id, username, amount, category)

    else:
      await message.answer(
        "Не распознана команда. Доступные форматы:\n"
        "• <сумма> <категория> — добавить запись (25 еда)\n"
        "• <id> удалить — удалить запись (7 удалить)\n"
        "• вся история — показать все записи"
      )
      return

  except Exception as e:
    log.exception(f"Ошибка при обработке сообщения от {username}: {e}")
    await message.answer("Произошла внутренняя ошибка. Попробуйте ещё раз.")
    return

  for uid in ALLOWED_USERS:
    schedule_summary(uid)


async def handle_add(message: Message, user_id: int, username: str, amount: float, category: str):
  with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()
    date = datetime.now().strftime('%Y-%m-%d')
    cursor.execute(
      'INSERT INTO expenses (user_id, username, amount, category, date) VALUES (?, ?, ?, ?, ?)',
      (user_id, username, amount, category, date),
    )
    conn.commit()
  log.info(f"Добавлено: {amount}€ | {category} | {username}")
  await message.answer(f"Запись добавлена: {amount} € с пометкой {category}.")
  await notify_other_user(
    user_id,
    f"Пользователь {username} добавил запись: {amount:.2f} € с пометкой '{category}'.",
  )


async def handle_delete(message: Message, user_id: int, username: str, record_id: int):
  with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()
    cursor.execute(
      "SELECT username, amount, category, date FROM expenses WHERE id = ?",
      (record_id,),
    )
    row = cursor.fetchone()
    if not row:
      await message.answer(f"Запись с id {record_id} не найдена.")
      return
    rec_username, rec_amount, rec_category, rec_date = row
    cursor.execute("DELETE FROM expenses WHERE id = ?", (record_id,))
    conn.commit()
  log.info(f"Удалено id={record_id}: {rec_amount}€ | {rec_category} | {rec_username}")
  await message.answer(
    f"Запись #{record_id} удалена: {rec_amount} € | {rec_category} | {rec_date}."
  )
  await notify_other_user(
    user_id,
    f"Пользователь {username} удалил запись #{record_id}: "
    f"{rec_amount:.2f} € | {rec_category} | {rec_date}.",
  )


async def history(user_id: int):
  with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()
    today = datetime.now()
    start_date = today.replace(day=1).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')
    cursor.execute(
      'SELECT id, username, amount, category, date FROM expenses '
      'WHERE date BETWEEN ? AND ? ORDER BY id',
      (start_date, end_date),
    )
    rows = cursor.fetchall()

  user_totals = {}
  for row in rows:
    user_totals[row[1]] = round(user_totals.get(row[1], 0) + row[2], 2)

  history_text = "\n".join([f"{r[0]}. {r[1]} | {r[2]} € | {r[3]} | {r[4]}" for r in rows])
  totals_text = "\n".join([f"{u}: {t} €" for u, t in user_totals.items()])

  try:
    await bot.send_message(
      user_id,
      f"История расходов:\n\n{history_text}\n\nСумма трат за месяц:\n{totals_text}",
    )
  except TelegramForbiddenError:
    log.warning(f"Бот заблокирован пользователем {user_id}")


async def full_history(user_id: int):
  with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, amount, category, date FROM expenses ORDER BY id")
    rows = cursor.fetchall()

  if not rows:
    await bot.send_message(user_id, "История расходов пуста.")
    return

  all_history = "\n".join([f"{r[0]}. {r[1]} | {r[2]} € | {r[3]} | {r[4]}" for r in rows])
  try:
    await send_long(user_id, f"Вся история расходов:\n\n{all_history}")
  except TelegramForbiddenError:
    log.warning(f"Бот заблокирован пользователем {user_id}")
  except Exception as e:
    log.exception(f"Ошибка отправки полной истории пользователю {user_id}: {e}")


async def balance(user_id: int):
  with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, SUM(amount) FROM expenses GROUP BY user_id")
    rows = cursor.fetchall()

  user_expenses = {row[0]: row[1] for row in rows}

  if len(user_expenses) == 2:
    total = sum(user_expenses.values())
    each_share = total / 2
    bal = user_expenses.get(user_id, 0) - each_share
    msg = f"Ваш баланс составляет: {'+' if bal >= 0 else ''}{bal:.2f} €"
  else:
    msg = "Баланс можно рассчитать только для двух пользователей."

  try:
    await bot.send_message(user_id, msg)
  except TelegramForbiddenError:
    log.warning(f"Бот заблокирован пользователем {user_id}")


async def notify_other_user(sender_id: int, text: str):
  other = next((uid for uid in ALLOWED_USERS if uid != sender_id), None)
  if other is None:
    return
  try:
    await bot.send_message(chat_id=other, text=text)
  except TelegramForbiddenError:
    log.warning(f"Бот заблокирован пользователем {other}")


async def main():
  init_db()
  log.info("Бот запущен")
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
