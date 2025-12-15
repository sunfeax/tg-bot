# Expense Sharing Telegram Bot

Minimal Telegram bot built with `aiogram` that logs shared expenses to SQLite, keeps both participants in sync, and calculates a simple split balance.

## Features
- Access restricted to the Telegram user IDs listed in `ALLOWED_USERS` inside `bot.py`.
- Add expenses with an amount and category; data is stored in `expenses.db`.
- Delete expenses by row ID.
- Sends the current month's expense history and per-user totals after each interaction.
- Notifies the other allowed user when an expense is added and shows their updated balance.
- Computes a split balance when exactly two users are being tracked.

## Requirements
- Python 3.10+
- Packages: `aiogram`, `python-dotenv` (SQLite is part of the standard library).
- A SQLite database file `expenses.db` that contains an `expenses` table.

### Database schema
Create the table once before running the bot:

```sql
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    date TEXT NOT NULL
);
```

## Setup
1) Install dependencies:
```bash
pip install aiogram python-dotenv
```
2) Create a `.env` file in the project root and set your bot token:
```env
TOKEN=1234567890:ABCDEF_your_token_here
```
3) Update `ALLOWED_USERS` in `bot.py` with the numeric Telegram user IDs allowed to interact with the bot.

## Running the bot
- Start the bot from the project directory:
```bash
python bot.py
```
- Optional: adjust and use `run-bot.bat` on Windows if you prefer starting it in the background.

## Usage
- Add an expense: `<amount> <category>`  
  Example: `25.50 groceries`
- Delete an expense by ID: `<id> delete`  
  Example: `7 delete`
- After each message, the bot replies with the current month's expense history and your balance. Balance calculations only occur when two distinct users are present in the data.

## Utilities
- `expenses.py` prints all rows from `expenses.db` to the console for quick inspection.
- Logs are written to `bot.log`.
