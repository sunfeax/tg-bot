# Telegram Expense Tracker Bot

A Telegram bot for tracking shared expenses between users. The bot allows authorized users to log expenses, view spending history, and calculate balances for shared costs.

## Features

- Track expenses with amounts and categories
- View monthly expense history
- Calculate shared balances between users
- Notification system for expense updates
- Delete specific expense records
- View complete expense history

## Requirements

- Python 3.7+
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd telegram-expense-tracker
   ```

2. Install required packages:
   ```bash
   pip install aiogram python-dotenv
   ```

3. Create a `.env` file with your bot token:
   ```
   TOKEN="your-telegram-bot-token"
   ```

4. Run the bot:
   ```bash
   python hiu.py
   ```

## Configuration

1. Edit the `ALLOWED_USERS` set in `hiu.py` with the Telegram user IDs of authorized users:
   ```python
   ALLOWED_USERS = {user_id_1, user_id_2}
   ```

2. The bot uses SQLite for data storage. The database file (`expenses.db`) will be created automatically.

## Usage

### Adding Expenses
Send a message in the format: `<amount> <category>`
Example: `25 food`

### Viewing History
Send `вся история` to view all expense records for the current month

### Deleting Records
Send a message in the format: `<ID> удалить`
Example: `7 удалить`

### Balance Calculation
The bot automatically calculates the balance between users after each transaction

## Files

- `hiu.py` - Main bot application
- `expenses.py` - Utility script to view database contents
- `expenses.db` - SQLite database file (created automatically)
- `run_bot.vbs` - Windows VBScript to run the bot
- `run-bot.bat` - Windows batch file to run the bot

## Security Notes

- Store your bot token securely in the `.env` file
- Only authorized users (defined in `ALLOWED_USERS`) can interact with the bot
- Database files contain sensitive financial information

## License

This project is open-source and available under the MIT License.