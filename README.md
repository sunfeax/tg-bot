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

- Docker and Docker Compose
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))

## Running with Docker

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd tg-bot
   ```

2. Create a `.env` file with your bot token and allowed user IDs:
   ```
   TOKEN="your-telegram-bot-token"
   ALLOWED_USER_IDS="111111111,222222222"
   ```

3. Build and start the bot:
   ```bash
   docker compose up -d --build
   ```

4. View logs:
   ```bash
   docker compose logs -f
   ```

The bot's SQLite database is stored in `./data`, which is mounted into the container so data persists across restarts and rebuilds.

## Configuration

- `TOKEN` — Telegram bot token
- `ALLOWED_USER_IDS` — comma-separated Telegram user IDs allowed to use the bot
- `TZ` — timezone for expense dates, logs and backups (default `Europe/Madrid`)
- `LOG_LEVEL` — logging level (default `INFO`); set `WARNING` to hide routine logs

## Usage

### Adding Expenses
Send a message in the format: `<amount> <category> [comment]`
Examples: `25 food`, `25 food lunch with friends`

### Viewing History
Send `<month>/<year>` to view expense records for that month
Example: `2/2026`

### Deleting Records
Send a message in the format: `<ID> удалить`
Example: `7 удалить`

Send `отмена` to delete your most recent record

### Balance Calculation
The bot automatically calculates the balance between users after each transaction

## Files

- `bot.py` — main bot application
- `Dockerfile`, `docker-compose.yml` — container setup
- `data/` — persisted SQLite database (created automatically)

## Security Notes

- Store your bot token securely in the `.env` file (never commit it)
- Only authorized users (defined via `ALLOWED_USER_IDS`) can interact with the bot
- Database files contain sensitive financial information

## License

This project is open-source and available under the MIT License.
