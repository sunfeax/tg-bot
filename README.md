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

- Docker and Docker Compose (for deployment)
- Node.js 24+ (for local development)
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

## Local Development

```bash
npm install
npm run dev        # runs src/main.ts with --watch and loads .env
npm run typecheck  # type checking only, Node runs TypeScript directly
```

## Configuration

- `TOKEN` — Telegram bot token
- `ALLOWED_USER_IDS` — comma-separated Telegram user IDs allowed to use the bot
- `TZ` — timezone for expense dates and backups (default `Europe/Madrid`)

## Usage

Send an amount with an optional comment, e.g. `25` or `12,5 coffee`. The bot replies with category buttons:

- pick a category to save an expense (it counts half toward the balance);
- **🤝 Одолжил** — you lent money to the other user, **💸 Вернул** — you paid back a loan (loans count in full and are excluded from monthly spending totals);
- unanswered drafts expire after 10 minutes.

Every saved record has a 🗑 button to delete it. The other user gets a notification for each new or deleted record, and the author receives the current month history and balance after every change.

On startup the bot pins a help message in each user's chat and edits it in place when the text changes.

Bottom keyboard: history and per-category statistics for the current month (both with ◀️ ▶️ month navigation), balance, help, undo your last record.

Commands:

- `<month>/<year>` — history for a month, e.g. `2/2026`
- `/del` — delete a record by id (the bot asks for the id, or pass it directly: `/del 7`)
- `/undo` — delete your last record
- `/addcat` — add a category (asks for the name), `/delcat` — delete one (existing records keep their category)
- `/history`, `/stats`, `/balance`, `/help`

The database is backed up hourly to `data/backups/` (one file per day, last 3 kept).

## Files

- `src/main.ts` — entry point: access check, handler wiring, startup
- `src/config/` — environment config and all texts, buttons, callback patterns and settings
- `src/db/` — schema, queries, backups
- `src/handlers/` — expense input, records, reports, categories
- `src/services/` — drafts, notifications, report texts, pinned help
- `src/ui/` — keyboards and reply prompts
- `src/utils/` — formatting and expense parsing
- `Dockerfile`, `docker-compose.yml` — container setup
- `data/` — persisted SQLite database (created automatically)

## Security Notes

- Store your bot token securely in the `.env` file (never commit it)
- Only authorized users (defined via `ALLOWED_USER_IDS`) can interact with the bot
- Database files contain sensitive financial information

## License

This project is open-source and available under the MIT License.
