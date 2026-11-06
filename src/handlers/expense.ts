import { Composer, type Context } from 'grammy';
import { CALLBACK, KIND, LOAN, MESSAGES } from '../config/constants.ts';
import { getCategoryById } from '../db/categories.ts';
import { insertExpense, type NewExpense } from '../db/expenses.ts';
import { takeDraft, saveDraft, type Draft } from '../services/drafts.ts';
import { expenseBody, fullName, loanBody, localDate, money } from '../utils/format.ts';
import { buildCategoryKeyboard, buildDeleteRecordKeyboard } from '../ui/keyboards.ts';
import { notifyOthers, scheduleSummary } from '../services/notify.ts';
import { parseExpense } from '../utils/parse-expense.ts';

export const expenseHandlers = new Composer();

expenseHandlers.on('message:text', async ctx => {
  const parsed = parseExpense(ctx.message.text);
  if (!parsed) return ctx.reply(MESSAGES.invalidRequest);

  const sent = await ctx.reply(
    MESSAGES.chooseCategory(money(parsed.amount), parsed.comment),
    {
      reply_markup: buildCategoryKeyboard(),
    },
  );
  saveDraft(ctx.api, sent.chat.id, sent.message_id, {
    ...parsed,
    userId: ctx.from.id,
    username: fullName(ctx.from),
  });
});

expenseHandlers.callbackQuery(CALLBACK.category, async ctx => {
  const category = getCategoryById(Number(ctx.match[1]));
  if (!category) return ctx.answerCallbackQuery({ text: MESSAGES.categoryNotFound });

  const draft = takeCurrentDraft(ctx);
  if (!draft) return ctx.answerCallbackQuery({ text: MESSAGES.draftNotFound });

  const expense = toExpense(draft, category.name, KIND.expense);
  const id = insertExpense(expense);
  const body = expenseBody(expense);
  console.info(`Added #${id}: ${body} | ${draft.username}`);

  await ctx.editMessageText(MESSAGES.expenseAdded(id, body), {
    reply_markup: buildDeleteRecordKeyboard(id),
  });
  await ctx.answerCallbackQuery();
  await notifyOthers(
    ctx.api,
    draft.userId,
    MESSAGES.expenseNotify(id, draft.username, body, money(draft.amount / 2)),
  );
  scheduleSummary(ctx.api, draft.userId);
});

expenseHandlers.callbackQuery(CALLBACK.loan, async ctx => {
  const draft = takeCurrentDraft(ctx);
  if (!draft) return ctx.answerCallbackQuery({ text: MESSAGES.draftNotFound });

  const isLend = ctx.match[1] === 'lend';
  const expense = toExpense(draft, isLend ? LOAN.lend : LOAN.repay, KIND.transfer);
  const id = insertExpense(expense);
  const body = loanBody(expense);
  console.info(`Added #${id}: ${expense.category} ${body} | ${draft.username}`);

  await ctx.editMessageText(
    isLend ? MESSAGES.loanAdded(id, body) : MESSAGES.repayAdded(id, body),
    { reply_markup: buildDeleteRecordKeyboard(id) },
  );
  await ctx.answerCallbackQuery();
  await notifyOthers(
    ctx.api,
    draft.userId,
    isLend
      ? MESSAGES.loanNotify(id, draft.username, body)
      : MESSAGES.repayNotify(id, draft.username, body),
  );
  scheduleSummary(ctx.api, draft.userId);
});

expenseHandlers.callbackQuery(CALLBACK.cancel, async ctx => {
  takeCurrentDraft(ctx);
  await ctx.editMessageText(MESSAGES.draftCancelled);
  await ctx.answerCallbackQuery();
});

function takeCurrentDraft(ctx: Context) {
  if (ctx.chatId === undefined || ctx.msgId === undefined) return undefined;
  return takeDraft(ctx.chatId, ctx.msgId);
}

function toExpense(draft: Draft, category: string, kind: NewExpense['kind']): NewExpense {
  return {
    userId: draft.userId,
    username: draft.username,
    amount: draft.amount,
    category,
    date: localDate(),
    comment: draft.comment,
    kind,
  };
}
