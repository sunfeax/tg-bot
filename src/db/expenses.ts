import { KIND } from '../config/constants.ts';
import { db } from './init.ts';

export type Kind = (typeof KIND)[keyof typeof KIND];

export type Expense = {
  id: number;
  userId: number;
  username: string;
  amount: number;
  category: string;
  date: string;
  comment: string | null;
  kind: Kind;
};

export type NewExpense = Omit<Expense, 'id'>;

const COLUMNS = 'id, user_id AS userId, username, amount, category, date, comment, kind';

const insert = db.prepare(
  'INSERT INTO expenses (user_id, username, amount, category, date, comment, kind) VALUES (?, ?, ?, ?, ?, ?, ?)',
);
const selectById = db.prepare(`SELECT ${COLUMNS} FROM expenses WHERE id = ?`);
const deleteById = db.prepare('DELETE FROM expenses WHERE id = ?');
const selectLastIdByUser = db.prepare(
  'SELECT MAX(id) AS id FROM expenses WHERE user_id = ?',
);
const selectByPeriod = db.prepare(
  `SELECT ${COLUMNS} FROM expenses WHERE date >= ? AND date < ? ORDER BY id`,
);
const selectCategoryTotals = db.prepare(
  `SELECT category, SUM(amount) AS total FROM expenses
   WHERE kind = 'expense' AND date >= ? AND date < ?
   GROUP BY category ORDER BY total DESC`,
);
const selectTotals = db.prepare(
  'SELECT user_id AS userId, kind, SUM(amount) AS total FROM expenses GROUP BY user_id, kind',
);

export function insertExpense(expense: NewExpense) {
  const { userId, username, amount, category, date, comment, kind } = expense;
  const result = insert.run(userId, username, amount, category, date, comment, kind);
  return Number(result.lastInsertRowid);
}

export function getExpense(id: number) {
  return selectById.get(id) as Expense | undefined;
}

export function deleteExpense(id: number) {
  deleteById.run(id);
}

export function getLastExpenseId(userId: number) {
  return (selectLastIdByUser.get(userId) as { id: number | null }).id;
}

export function getExpensesByPeriod(from: string, to: string) {
  return selectByPeriod.all(from, to) as Expense[];
}

export function getTotals() {
  return selectTotals.all() as { userId: number; kind: Kind; total: number }[];
}

export function getCategoryTotals(from: string, to: string) {
  return selectCategoryTotals.all(from, to) as { category: string; total: number }[];
}
