import { Composer, type Context } from 'grammy';
import { CALLBACK, MESSAGES, MONTH_PATTERN } from '../config/constants.ts';
import { splitMessage } from '../utils/format.ts';
import { sendLong } from '../services/notify.ts';
import {
  balanceText,
  historyText,
  monthKeyboard,
  statsText,
} from '../services/report-texts.ts';

export const reportHandlers = new Composer();

reportHandlers.command('history', currentMonthHistory);

reportHandlers.hears(MONTH_PATTERN, ctx => {
  const month = Number(ctx.match[1]);
  const year = Number(ctx.match[2]);
  if (month < 1 || month > 12) return ctx.reply(MESSAGES.invalidMonth);
  return sendHistory(ctx, month, year);
});

reportHandlers.callbackQuery(CALLBACK.history, async ctx => {
  const year = Number(ctx.match[1]);
  const month = Number(ctx.match[2]);
  const text = historyText(month, year);
  const keyboard = monthKeyboard('hist', month, year);

  if (splitMessage(text).length === 1) {
    await ctx
      .editMessageText(text, { reply_markup: keyboard })
      .catch(err => console.warn('Failed to edit history:', err.message));
  } else {
    await sendHistory(ctx, month, year);
  }
  await ctx.answerCallbackQuery();
});

reportHandlers.command('stats', currentMonthStats);

reportHandlers.callbackQuery(CALLBACK.stats, async ctx => {
  const year = Number(ctx.match[1]);
  const month = Number(ctx.match[2]);
  await ctx
    .editMessageText(statsText(month, year), {
      reply_markup: monthKeyboard('stats', month, year),
    })
    .catch(err => console.warn('Failed to edit stats:', err.message));
  await ctx.answerCallbackQuery();
});

reportHandlers.command('balance', balance);

function currentMonthHistory(ctx: Context) {
  const now = new Date();
  return sendHistory(ctx, now.getMonth() + 1, now.getFullYear());
}

function currentMonthStats(ctx: Context) {
  const now = new Date();
  const month = now.getMonth() + 1;
  const year = now.getFullYear();
  return ctx.reply(statsText(month, year), {
    reply_markup: monthKeyboard('stats', month, year),
  });
}

function sendHistory(ctx: Context, month: number, year: number) {
  if (ctx.chatId === undefined) return;
  return sendLong(
    ctx.api,
    ctx.chatId,
    historyText(month, year),
    monthKeyboard('hist', month, year),
  );
}

function balance(ctx: Context) {
  if (!ctx.from) return;
  return ctx.reply(balanceText(ctx.from.id));
}
