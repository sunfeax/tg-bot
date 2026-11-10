import type { Api, InlineKeyboard } from 'grammy';
import { config } from '../config/config.ts';
import { SUMMARY_DELAY_MS } from '../config/constants.ts';
import { splitMessage } from '../utils/format.ts';
import { balanceText } from './report-texts.ts';

export async function sendLong(
  api: Api,
  chatId: number,
  text: string,
  keyboard?: InlineKeyboard,
  monospace = false,
) {
  const chunks = splitMessage(text);
  for (const [index, chunk] of chunks.entries()) {
    const isLast = index === chunks.length - 1;
    await api.sendMessage(chatId, chunk, {
      ...(isLast && keyboard ? { reply_markup: keyboard } : {}),
      ...(monospace
        ? { entities: [{ type: 'pre' as const, offset: 0, length: chunk.length }] }
        : {}),
    });
  }
}

async function safeSend(chatId: number, send: () => Promise<unknown>) {
  try {
    await send();
  } catch (err) {
    console.warn(`Failed to send message to ${chatId}:`, (err as Error).message);
  }
}

export async function notifyOthers(api: Api, senderId: number, text: string) {
  for (const userId of config.allowedUsers) {
    if (userId !== senderId) await safeSend(userId, () => api.sendMessage(userId, text));
  }
}

const summaryTimers = new Map<number, NodeJS.Timeout>();

export function scheduleSummary(api: Api, userId: number) {
  clearTimeout(summaryTimers.get(userId));
  const timer = setTimeout(() => {
    summaryTimers.delete(userId);
    void safeSend(userId, () => api.sendMessage(userId, balanceText(userId)));
  }, SUMMARY_DELAY_MS);
  summaryTimers.set(userId, timer);
}
