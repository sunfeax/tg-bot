import type { User } from 'grammy/types';
import { MAX_MESSAGE_LENGTH } from '../config/constants.ts';
import type { Expense } from '../db/expenses.ts';

export function localDate(date = new Date()) {
  return date.toLocaleDateString('sv-SE');
}

export function money(value: number) {
  return (Math.round(value * 100) / 100 || 0).toFixed(2);
}

export function signed(value: number) {
  const rounded = Math.round(value * 100) / 100 || 0;
  return `${rounded >= 0 ? '+' : ''}${rounded.toFixed(2)} €`;
}

export function describe(category: string, comment: string | null) {
  return comment ? `${category} (${comment})` : category;
}

export function fullName(user: User) {
  return [user.first_name, user.last_name].filter(Boolean).join(' ');
}

export function expenseBody(
  expense: Pick<Expense, 'amount' | 'category' | 'comment' | 'date'>,
) {
  return `${money(expense.amount)} € | ${describe(expense.category, expense.comment)} | ${expense.date}`;
}

export function loanBody(expense: Pick<Expense, 'amount' | 'comment' | 'date'>) {
  return `${money(expense.amount)} €${expense.comment ? ` (${expense.comment})` : ''} | ${expense.date}`;
}

export function historyTable(expenses: Expense[]) {
  const rows = expenses.map(expense => [
    String(expense.id),
    expense.date.slice(5).split('-').reverse().join('.'),
    money(expense.amount),
  ]);
  const headers = ['ID', 'Дата', 'Сумма, €'];
  const widths = headers.map((header, column) =>
    Math.max(header.length, ...rows.map(row => row[column]!.length)),
  );
  const formatRow = (cells: string[]) =>
    cells
      .map((cell, column) =>
        column === 1 ? cell.padEnd(widths[column]!) : cell.padStart(widths[column]!),
      )
      .join(' | ');

  return [
    formatRow(headers),
    widths.map(width => '-'.repeat(width)).join('-+-'),
    ...expenses.flatMap((expense, index) => [
      formatRow(rows[index]!),
      `${expense.username} | ${describe(expense.category, expense.comment)}`,
      '',
    ]),
  ]
    .join('\n')
    .trimEnd();
}

export function monthRange(month: number, year: number) {
  const pad = (value: number) => String(value).padStart(2, '0');
  const next = month === 12 ? { month: 1, year: year + 1 } : { month: month + 1, year };
  return {
    from: `${year}-${pad(month)}-01`,
    to: `${next.year}-${pad(next.month)}-01`,
  };
}

export function shiftMonth(month: number, year: number, delta: number) {
  const index = year * 12 + (month - 1) + delta;
  return { month: (index % 12) + 1, year: Math.floor(index / 12) };
}

export function splitMessage(text: string) {
  const chunks: string[] = [];
  let current = '';
  for (const line of text.split('\n')) {
    const candidate = current ? `${current}\n${line}` : line;
    if (candidate.length <= MAX_MESSAGE_LENGTH) {
      current = candidate;
      continue;
    }
    if (current) chunks.push(current);
    current = line.slice(0, MAX_MESSAGE_LENGTH);
  }
  if (current) chunks.push(current);
  return chunks;
}
