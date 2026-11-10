import { Composer, type Context } from 'grammy';
import { CALLBACK, MESSAGES, PROMPTS } from '../config/constants.ts';
import { deleteExpense, getExpense } from '../db/expenses.ts';
import { expenseBody, fullName } from '../utils/format.ts';
import { notifyOthers, scheduleSummary } from '../services/notify.ts';
import { forceReply, isReplyTo } from '../ui/prompts.ts';

export const recordHandlers = new Composer();

recordHandlers.command('del', ctx => {
  const arg = ctx.match.trim();
  if (!arg) {
    return ctx.reply(PROMPTS.deleteRecord, forceReply(PROMPTS.deleteRecordPlaceholder));
  }
  return deleteByInput(ctx, arg);
});

recordHandlers
  .on('message:text')
  .filter(isReplyTo(PROMPTS.deleteRecord), ctx => deleteByInput(ctx, ctx.message.text));

recordHandlers.callbackQuery(CALLBACK.deleteRecord, async ctx => {
  const text = await removeExpense(ctx, Number(ctx.match[1]));
  await ctx.editMessageText(text);
  await ctx.answerCallbackQuery();
});

async function deleteByInput(ctx: Context, input: string) {
  const id = Number(input.trim());
  if (!Number.isInteger(id) || id <= 0) return ctx.reply(MESSAGES.invalidId);
  await ctx.reply(await removeExpense(ctx, id));
}

async function removeExpense(ctx: Context, id: number) {
  const expense = getExpense(id);
  if (!expense || !ctx.from) return MESSAGES.recordNotFound(id);

  deleteExpense(id);
  const body = `${expense.username} | ${expenseBody(expense)}`;
  console.info(`Deleted #${id}: ${body}`);

  await notifyOthers(
    ctx.api,
    ctx.from.id,
    MESSAGES.recordDeletedNotify(id, fullName(ctx.from), body),
  );
  scheduleSummary(ctx.api, ctx.from.id);
  return MESSAGES.recordDeleted(id, body);
}
