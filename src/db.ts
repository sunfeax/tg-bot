import { mkdirSync } from 'node:fs';
import path from 'node:path';
import { DatabaseSync } from 'node:sqlite';
import { config } from './config.ts';

mkdirSync(config.dataDir, { recursive: true });

export const db = new DatabaseSync(path.join(config.dataDir, 'expenses.db'));

db.exec(`
  CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    date TEXT NOT NULL,
    comment TEXT,
    kind TEXT NOT NULL DEFAULT 'expense'
  );
  CREATE TABLE IF NOT EXISTS pinned_help (
    user_id INTEGER PRIMARY KEY,
    message_id INTEGER NOT NULL,
    text TEXT NOT NULL
  );
  CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
  );
`);

const DEFAULT_CATEGORIES = ['Еда', 'Транспорт', 'Дом', 'Развлечения', 'Другое'];

const { count } = db.prepare('SELECT COUNT(*) AS count FROM categories').get() as {
  count: number;
};

if (count === 0) {
  const insert = db.prepare('INSERT INTO categories (name) VALUES (?)');
  for (const name of DEFAULT_CATEGORIES) insert.run(name);
}
