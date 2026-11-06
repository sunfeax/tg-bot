import { InlineKeyboard } from 'grammy';
import { BUTTONS, KIND, MESSAGES, STATS_BAR_LENGTH } from './constants.ts';
import { getCategoryTotals, getExpensesByPeriod, getTotals } from './db/expenses.ts';
import { money, monthRange, recordLine, shiftMonth, signed } from './format.ts';

export function historyText(month: number, year: number) {
  const { from, to } = monthRange(month, year);
  const expenses = getExpensesByPeriod(from, to);
  if (expenses.length === 0) return MESSAGES.historyEmpty(month, year);

  const totals = new Map<string, number>();
  for (const expense of expenses) {
    if (expense.kind !== KIND.expense) continue;
    totals.set(expense.username, (totals.get(expense.username) ?? 0) + expense.amount);
  }

  return [
    MESSAGES.historyTitle(month, year),
    '',
    ...expenses.map(recordLine),
    '',
    MESSAGES.historyTotals,
    ...[...totals].map(([username, total]) => `${username}: ${money(total)} €`),
  ].join('\n');
}

export function monthKeyboard(prefix: 'hist' | 'stats', month: number, year: number) {
  const prev = shiftMonth(month, year, -1);
  const next = shiftMonth(month, year, 1);
  return new InlineKeyboard()
    .text(BUTTONS.prevMonth, `${prefix}:${prev.year}-${prev.month}`)
    .text(`${month}/${year}`, `${prefix}:${year}-${month}`)
    .text(BUTTONS.nextMonth, `${prefix}:${next.year}-${next.month}`);
}

export function statsText(month: number, year: number) {
  const { from, to } = monthRange(month, year);
  const totals = getCategoryTotals(from, to);
  if (totals.length === 0) return MESSAGES.statsEmpty(month, year);

  const sum = totals.reduce((acc, { total }) => acc + total, 0);
  const lines = totals.map(({ category, total }) => {
    const share = total / sum;
    const filled = Math.round(share * STATS_BAR_LENGTH);
    const bar = '█'.repeat(filled) + '░'.repeat(STATS_BAR_LENGTH - filled);
    return `${bar} ${Math.round(share * 100)}%\n${category} — ${money(total)} €`;
  });

  const prev = shiftMonth(month, year, -1);
  const prevRange = monthRange(prev.month, prev.year);
  const prevSum = getCategoryTotals(prevRange.from, prevRange.to).reduce(
    (acc, { total }) => acc + total,
    0,
  );

  const result = [
    MESSAGES.statsTitle(month, year),
    '',
    lines.join('\n\n'),
    '',
    MESSAGES.statsTotal(money(sum)),
  ];
  if (prevSum > 0) {
    const change = Math.round(((sum - prevSum) / prevSum) * 100);
    const arrow = change > 0 ? '📈' : change < 0 ? '📉' : '➖';
    result.push(
      MESSAGES.statsCompare(arrow, `${change > 0 ? '+' : ''}${change}`, money(prevSum)),
    );
  }
  return result.join('\n');
}

export function balanceText(userId: number) {
  const spent = new Map<number, number>();
  const given = new Map<number, number>();
  for (const { userId: id, kind, total } of getTotals()) {
    (kind === KIND.expense ? spent : given).set(id, total);
  }

  const users = new Set([...spent.keys(), ...given.keys()]);
  const other = [...users].find(id => id !== userId);
  if (users.size !== 2 || !users.has(userId) || other === undefined) {
    return MESSAGES.balanceUnavailable;
  }

  const expensePart = ((spent.get(userId) ?? 0) - (spent.get(other) ?? 0)) / 2;
  const loanPart = (given.get(userId) ?? 0) - (given.get(other) ?? 0);
  const text = MESSAGES.balance(signed(expensePart + loanPart));
  return given.size > 0
    ? text + MESSAGES.balanceDetails(signed(expensePart), signed(loanPart))
    : text;
}
