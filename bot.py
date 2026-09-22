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

ADD_PATTERN = re.compile(r'^(\d+[.,]?\d*)\s+(\S+)(?:\s+(.+))?$', re.DOTALL)
DEL_PATTERN = re.compile(r'^(\d+)\s+удалить$', re.IGNORECASE)
UNDO_PATTERN = re.compile(r'^отмена$', re.IGNORECASE)
MONTH_PATTERN = re.compile(r'^(\d{1,2})/(\d{4})$')

HELP_TEXT = (
  "Не распознана команда. Доступные форматы:\n"
  "• <сумма> <категория> [комментарий] — добавить запись (25 еда пятёрочка)\n"
  "• <id> удалить — удалить запись (7 удалить)\n"
  "• отмена — удалить свою последнюю запись\n"
  "• <месяц>/<год> — история за месяц (2/2026)"
)

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
        date TEXT NOT NULL,
        comment TEXT)'''
    )
    columns = {row[1] for row in conn.execute("PRAGMA table_info(expenses)")}
    if "comment" not in columns:
      conn.execute("ALTER TABLE expenses ADD COLUMN comment TEXT")
    conn.commit()

summary_timers: dict[int, asyncio.Task] = {}

MAX_MSG_LEN = 4096


def describe(category: str, comment: str | None) -> str:
  return f"{category} ({comment})" if comment else category


async def send_long(user_id: int, text: str):
  for i in range(0, max(len(text), 1), MAX_MSG_LEN):
    await bot.send_message(user_id, text[i:i + MAX_MSG_LEN])


async def _send_summary(user_id: int):
  await asyncio.sleep(1.5)
  now = datetime.now()
  await history(user_id, now.month, now.year)
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
    if m := DEL_PATTERN.match(text):
      await handle_delete(message, user_id, username, int(m.group(1)))

    elif UNDO_PATTERN.match(text):
      await handle_undo(message, user_id, username)

    elif m := MONTH_PATTERN.match(text):
      month, year = int(m.group(1)), int(m.group(2))
      if not 1 <= month <= 12:
        await message.answer("Месяц должен быть от 1 до 12.")
      else:
        await history(user_id, month, year)
      return

    elif m := ADD_PATTERN.match(text):
      amount = float(m.group(1).replace(",", "."))
      category = m.group(2)
      comment = m.group(3).strip() if m.group(3) else None
      await handle_add(message, user_id, username, amount, category, comment)

    else:
      await message.answer(HELP_TEXT)
      return

  except Exception as e:
    log.exception(f"Ошибка при обработке сообщения от {username}: {e}")
    await message.answer("Произошла внутренняя ошибка. Попробуйте ещё раз.")
    return

  for uid in ALLOWED_USERS:
    schedule_summary(uid)


async def handle_add(
  message: Message, user_id: int, username: str, amount: float, category: str, comment: str | None
):
  with sqlite3.connect(DB_PATH) as conn:
    date = datetime.now().strftime('%Y-%m-%d')
    conn.execute(
      'INSERT INTO expenses (user_id, username, amount, category, date, comment) '
      'VALUES (?, ?, ?, ?, ?, ?)',
      (user_id, username, amount, category, date, comment),
    )
    conn.commit()
  what = describe(category, comment)
  log.info(f"Добавлено: {amount}€ | {what} | {username}")
  await message.answer(f"Запись добавлена: {amount} € | {what}.")
  await notify_other_user(
    user_id,
    f"Пользователь {username} добавил запись: {amount:.2f} € | {what}.",
  )


async def handle_delete(message: Message, user_id: int, username: str, record_id: int):
  with sqlite3.connect(DB_PATH) as conn:
    row = conn.execute(
      "SELECT username, amount, category, comment, date FROM expenses WHERE id = ?",
      (record_id,),
    ).fetchone()
    if not row:
      await message.answer(f"Запись с id {record_id} не найдена.")
      return
    rec_username, rec_amount, rec_category, rec_comment, rec_date = row
    conn.execute("DELETE FROM expenses WHERE id = ?", (record_id,))
    conn.commit()
  what = describe(rec_category, rec_comment)
  log.info(f"Удалено id={record_id}: {rec_amount}€ | {what} | {rec_username}")
  await message.answer(f"Запись #{record_id} удалена: {rec_amount} € | {what} | {rec_date}.")
  await notify_other_user(
    user_id,
    f"Пользователь {username} удалил запись #{record_id}: "
    f"{rec_amount:.2f} € | {what} | {rec_date}.",
  )


async def handle_undo(message: Message, user_id: int, username: str):
  with sqlite3.connect(DB_PATH) as conn:
    (last_id,) = conn.execute(
      "SELECT MAX(id) FROM expenses WHERE user_id = ?", (user_id,)
    ).fetchone()
  if last_id is None:
    await message.answer("У вас нет записей для отмены.")
    return
  await handle_delete(message, user_id, username, last_id)


async def history(user_id: int, month: int, year: int):
  start_date = f"{year:04d}-{month:02d}-01"
  end_date = f"{year + month // 12:04d}-{month % 12 + 1:02d}-01"
  with sqlite3.connect(DB_PATH) as conn:
    rows = conn.execute(
      'SELECT id, username, amount, category, comment, date FROM expenses '
      'WHERE date >= ? AND date < ? ORDER BY id',
      (start_date, end_date),
    ).fetchall()

  if rows:
    user_totals = {}
    for _, name, amount, *_ in rows:
      user_totals[name] = round(user_totals.get(name, 0) + amount, 2)

    history_text = "\n".join(
      f"{rid}. {name} | {amount} € | {describe(category, comment)} | {date}"
      for rid, name, amount, category, comment, date in rows
    )
    totals_text = "\n".join(f"{u}: {t} €" for u, t in user_totals.items())
    text = (
      f"История расходов за {month}/{year}:\n\n{history_text}\n\n"
      f"Сумма трат за месяц:\n{totals_text}"
    )
  else:
    text = f"За {month}/{year} записей нет."

  try:
    await send_long(user_id, text)
  except TelegramForbiddenError:
    log.warning(f"Бот заблокирован пользователем {user_id}")


async def balance(user_id: int):
  with sqlite3.connect(DB_PATH) as conn:
    rows = conn.execute("SELECT user_id, SUM(amount) FROM expenses GROUP BY user_id").fetchall()

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
