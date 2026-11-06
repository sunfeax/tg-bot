import { Bot, type Context } from 'grammy';
import { config } from './config/config.ts';
import { BUTTONS, COMMANDS, MESSAGES } from './config/constants.ts';
import { backupHandlers } from './handlers/backup.ts';
import { categoryHandlers } from './handlers/categories.ts';
import { expenseHandlers } from './handlers/expense.ts';
import { recordHandlers } from './handlers/records.ts';
import { reportHandlers } from './handlers/reports.ts';
import { mainKeyboard } from './ui/keyboards.ts';
import { startBackups } from './services/backups.ts';
import { ensureHelpPinned } from './services/pinned-help.ts';

const bot = new Bot(config.token);

bot.use(async (ctx, next) => {
  if (ctx.from && config.allowedUsers.has(ctx.from.id)) return next();
  if (ctx.message) await ctx.reply(MESSAGES.noAccess);
});

const help = (ctx: Context) => ctx.reply(MESSAGES.help, { reply_markup: mainKeyboard });
bot.command(['start', 'help'], help);
bot.hears(BUTTONS.help, help);

bot.use(
  reportHandlers,
  recordHandlers,
  categoryHandlers,
  backupHandlers,
  expenseHandlers,
);

bot.on('message', ctx => ctx.reply(MESSAGES.invalidRequest));

bot.catch(async err => {
  console.error('Update failed:', err.error);
  await err.ctx.reply(MESSAGES.internalError).catch(() => {});
});

await bot.api.setMyCommands(COMMANDS);
for (const userId of config.allowedUsers) {
  await ensureHelpPinned(bot.api, userId).catch(err =>
    console.warn(`Failed to pin help for ${userId}:`, err.message),
  );
}
const backupTimer = startBackups(bot.api);

const stop = () => {
  clearInterval(backupTimer);
  return bot.stop();
};
process.once('SIGINT', stop);
process.once('SIGTERM', stop);

await bot.start({ onStart: () => console.log('Bot started') });
