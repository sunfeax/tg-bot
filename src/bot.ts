import { Bot } from 'grammy';
import { config } from './config.ts';
import './db.ts';
import { parseExpense } from './parse-expense.ts';

const HINT =
  'Неверный запрос.\nЧтобы добавить новую запись, отправь сумму и комментарий (опционально) через пробел:\n25\n12,5 кофе';

const bot = new Bot(config.token);

bot.use(async (ctx, next) => {
  if (ctx.from && config.allowedUsers.has(ctx.from.id)) await next();
});

bot.on('message:text', ctx => {
  const expense = parseExpense(ctx.message.text);
  if (!expense) return ctx.reply(HINT);
  return ctx.reply(`Сумма: ${expense.amount}\nКомментарий: ${expense.comment ?? '—'}`);
});

bot.on('message', ctx => ctx.reply(HINT));

bot.catch(err => console.error('Update failed:', err.error));

process.once('SIGINT', () => bot.stop());
process.once('SIGTERM', () => bot.stop());

await bot.start({ onStart: () => console.log('Bot started') });
