import type { Api } from 'grammy';
import { DRAFT_TTL_MS, MESSAGES } from './constants.ts';
import type { ParsedExpense } from './parse-expense.ts';

export type Draft = ParsedExpense & { userId: number; username: string };

const drafts = new Map<string, Draft & { timer: NodeJS.Timeout }>();

const key = (chatId: number, messageId: number) => `${chatId}:${messageId}`;

export function saveDraft(api: Api, chatId: number, messageId: number, draft: Draft) {
  const timer = setTimeout(() => {
    drafts.delete(key(chatId, messageId));
    api
      .editMessageText(chatId, messageId, MESSAGES.draftExpired)
      .catch(err => console.warn('Failed to expire draft:', err.message));
  }, DRAFT_TTL_MS);
  drafts.set(key(chatId, messageId), { ...draft, timer });
}

export function takeDraft(chatId: number, messageId: number): Draft | undefined {
  const entry = drafts.get(key(chatId, messageId));
  if (!entry) return undefined;
  clearTimeout(entry.timer);
  drafts.delete(key(chatId, messageId));
  const { timer, ...draft } = entry;
  return draft;
}
