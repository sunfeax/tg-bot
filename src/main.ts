import { Bot } from 'grammy';
import { config } from './config.ts';
import { MESSAGES } from './constants.ts';
import { buildCategoryKeyboard } from './keyboards.ts';
import { parseExpense } from './parse-expense.ts';

const bot = new Bot(config.token);

bot.use(async (ctx, next) => {
  if (ctx.from && config.allowedUsers.has(ctx.from.id)) await next();
});

bot.on('message:text', ctx => {
  const expense = parseExpense(ctx.message.text);
  if (!expense) return ctx.reply(MESSAGES.invalidRequest);
  return ctx.reply(MESSAGES.chooseCategory, {
    reply_markup: buildCategoryKeyboard(),
  });
});

bot.on('message', ctx => ctx.reply(MESSAGES.invalidRequest));

bot.catch(err => console.error('Update failed:', err.error));

process.once('SIGINT', () => bot.stop());
process.once('SIGTERM', () => bot.stop());

await bot.start({ onStart: () => console.log('Bot started') });
