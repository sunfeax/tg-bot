from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramForbiddenError
from contextlib import closing
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
BACKUP_DIR = DATA_DIR / "backups"
BACKUP_KEEP = 3

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

TRANSFER_WORDS = {"одолжил", "одолжила", "вернул", "вернула"}

HELP_TEXT = (
  "Не распознана команда. Доступные форматы:\n"
  "• <сумма> <категория> [комментарий] — добавить запись (25 еда пятёрочка)\n"
  "• <сумма> одолжил(а) [комментарий] — вы дали деньги в долг (50 одолжила)\n"
  "• <сумма> вернул(а) [комментарий] — вы вернули долг (50 вернул)\n"
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
        comment TEXT,
        kind TEXT NOT NULL DEFAULT 'expense')'''
    )
    columns = {row[1] for row in conn.execute("PRAGMA table_info(expenses)")}
    if "comment" not in columns:
      conn.execute("ALTER TABLE expenses ADD COLUMN comment TEXT")
    if "kind" not in columns:
      conn.execute("ALTER TABLE expenses ADD COLUMN kind TEXT NOT NULL DEFAULT 'expense'")
    conn.commit()


def backup_db():
  BACKUP_DIR.mkdir(exist_ok=True)
  target = BACKUP_DIR / f"expenses-{datetime.now():%Y-%m-%d}.db"
  if target.exists():
    return
  tmp = target.with_suffix(".tmp")
  with closing(sqlite3.connect(DB_PATH)) as src, closing(sqlite3.connect(tmp)) as dst:
    src.backup(dst)
  tmp.replace(target)
  for old in sorted(BACKUP_DIR.glob("expenses-*.db"))[:-BACKUP_KEEP]:
    old.unlink()
  log.info(f"Бэкап создан: {target.name}")


async def backup_loop():
  while True:
    try:
      await asyncio.to_thread(backup_db)
    except Exception:
      log.exception("Ошибка при создании бэкапа")
    await asyncio.sleep(3600)

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
      kind = "expense"
      if category.lower() in TRANSFER_WORDS:
        category, kind = category.lower(), "transfer"
      await handle_add(message, user_id, username, amount, category, comment, kind)

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
  message: Message, user_id: int, username: str, amount: float, category: str,
  comment: str | None, kind: str,
):
  with sqlite3.connect(DB_PATH) as conn:
    date = message.date.astimezone().strftime('%Y-%m-%d')
    record_id = conn.execute(
      'INSERT INTO expenses (user_id, username, amount, category, date, comment, kind) '
      'VALUES (?, ?, ?, ?, ?, ?, ?)',
      (user_id, username, amount, category, date, comment, kind),
    ).lastrowid
    conn.commit()
  log.info(f"Добавлено id={record_id}: {amount}€ | {describe(category, comment)} | {username}")

  if kind == "expense":
    body = f"{amount:.2f} € | {describe(category, comment)} | {date}"
    await message.answer(f"Трата #{record_id} добавлена\n{body}")
    await notify_other_user(
      user_id,
      f"Новая трата #{record_id} — {username}\n{body}\nВаша половина: {amount / 2:.2f} €",
    )
    return

  if category.startswith("одолж"):
    title, mine, theirs = "Займ", "Вы дали в долг", "Вам дали в долг"
  else:
    title, mine, theirs = "Возврат долга", "Вы вернули", "Вам вернули"
  body = f"{amount:.2f} €{f' ({comment})' if comment else ''} | {date}"
  await message.answer(f"{title} #{record_id} записан\n{mine} {body}")
  await notify_other_user(user_id, f"{title} #{record_id} — {username}\n{theirs} {body}")


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
  body = (
    f"{rec_username} | {rec_amount:.2f} € | "
    f"{describe(rec_category, rec_comment)} | {rec_date}"
  )
  log.info(f"Удалено id={record_id}: {body}")
  await message.answer(f"Запись #{record_id} удалена\n{body}")
  await notify_other_user(user_id, f"Удалена запись #{record_id} — {username}\n{body}")


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
      'SELECT id, username, amount, category, comment, date, kind FROM expenses '
      'WHERE date >= ? AND date < ? ORDER BY id',
      (start_date, end_date),
    ).fetchall()

  if rows:
    user_totals = {}
    for _, name, amount, *_, kind in rows:
      if kind == "expense":
        user_totals[name] = round(user_totals.get(name, 0) + amount, 2)

    history_text = "\n".join(
      f"{rid}. {name} | {amount} € | {describe(category, comment)} | {date}"
      for rid, name, amount, category, comment, date, _ in rows
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


def signed(value: float) -> str:
  return f"{round(value, 2) + 0.0:+.2f} €"


async def balance(user_id: int):
  with sqlite3.connect(DB_PATH) as conn:
    rows = conn.execute(
      "SELECT user_id, kind, SUM(amount) FROM expenses GROUP BY user_id, kind"
    ).fetchall()

  spent = {uid: total for uid, kind, total in rows if kind == "expense"}
  given = {uid: total for uid, kind, total in rows if kind == "transfer"}
  users = set(spent) | set(given)

  if len(users) == 2 and user_id in users:
    other = next(uid for uid in users if uid != user_id)
    expense_part = (spent.get(user_id, 0) - spent.get(other, 0)) / 2
    loan_part = given.get(user_id, 0) - given.get(other, 0)
    msg = f"Ваш баланс: {signed(expense_part + loan_part)}"
    if given:
      msg += (
        f"\n  по общим тратам: {signed(expense_part)}"
        f"\n  по займам: {signed(loan_part)}"
      )
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
  backup_task = asyncio.create_task(backup_loop())
  log.info("Бот запущен")
  try:
    await dp.start_polling(bot)
  finally:
    backup_task.cancel()


if __name__ == "__main__":
  asyncio.run(main())
