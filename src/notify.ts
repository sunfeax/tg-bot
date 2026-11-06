import type { Api, InlineKeyboard } from 'grammy';
import { config } from './config.ts';
import { SUMMARY_DELAY_MS } from './constants.ts';
import { splitMessage } from './format.ts';
import { balanceText, historyText, monthKeyboard } from './report-texts.ts';

export async function sendLong(
  api: Api,
  chatId: number,
  text: string,
  keyboard?: InlineKeyboard,
) {
  const chunks = splitMessage(text);
  for (const [index, chunk] of chunks.entries()) {
    const isLast = index === chunks.length - 1;
    await api.sendMessage(
      chatId,
      chunk,
      isLast && keyboard ? { reply_markup: keyboard } : {},
    );
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
    const now = new Date();
    const month = now.getMonth() + 1;
    const year = now.getFullYear();
    void safeSend(userId, async () => {
      await sendLong(
        api,
        userId,
        historyText(month, year),
        monthKeyboard('hist', month, year),
      );
      await api.sendMessage(userId, balanceText(userId));
    });
  }, SUMMARY_DELAY_MS);
  summaryTimers.set(userId, timer);
}
