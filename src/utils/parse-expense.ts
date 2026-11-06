import { AMOUNT_PATTERN } from '../config/constants.ts';

export interface ParsedExpense {
  amount: number;
  comment: string | null;
}

export function parseExpense(text: string): ParsedExpense | null {
  const trimmed = text.trim();
  const spaceIndex = trimmed.search(/\s/);
  const rawAmount = spaceIndex === -1 ? trimmed : trimmed.slice(0, spaceIndex);
  const rawComment = spaceIndex === -1 ? '' : trimmed.slice(spaceIndex).trim();

  if (!AMOUNT_PATTERN.test(rawAmount)) return null;

  const amount = Number(rawAmount.replace(',', '.'));
  if (amount <= 0) return null;

  return { amount, comment: rawComment || null };
}
