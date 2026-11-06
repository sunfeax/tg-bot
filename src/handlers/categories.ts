import { Composer, type Context } from 'grammy';
import { CALLBACK, CATEGORY_NAME_MAX_LENGTH, MESSAGES, PROMPTS } from '../constants.ts';
import {
  addCategory,
  deleteCategory,
  getCategories,
  getCategoryById,
} from '../db/categories.ts';
import { buildDeleteCategoryKeyboard } from '../keyboards.ts';
import { forceReply, isReplyTo } from '../prompts.ts';

export const categoryHandlers = new Composer();

categoryHandlers.command('addcat', ctx => {
  const name = ctx.match.trim();
  if (!name) {
    return ctx.reply(PROMPTS.addCategory, forceReply(PROMPTS.addCategoryPlaceholder));
  }
  return addByInput(ctx, name);
});

categoryHandlers
  .on('message:text')
  .filter(isReplyTo(PROMPTS.addCategory), ctx => addByInput(ctx, ctx.message.text));

function addByInput(ctx: Context, input: string) {
  const name = input.trim();
  if (!name || name.length > CATEGORY_NAME_MAX_LENGTH) {
    return ctx.reply(MESSAGES.invalidCategoryName);
  }
  return ctx.reply(
    addCategory(name) ? MESSAGES.categoryAdded(name) : MESSAGES.categoryExists(name),
  );
}

categoryHandlers.command('delcat', ctx =>
  ctx.reply(MESSAGES.chooseCategoryToDelete, {
    reply_markup: buildDeleteCategoryKeyboard(),
  }),
);

categoryHandlers.callbackQuery(CALLBACK.deleteCategory, async ctx => {
  const category = getCategoryById(Number(ctx.match[1]));
  if (!category) return ctx.answerCallbackQuery({ text: MESSAGES.categoryNotFound });
  if (getCategories().length === 1) {
    return ctx.answerCallbackQuery({ text: MESSAGES.lastCategory });
  }

  deleteCategory(category.id);
  console.info(`Category deleted: ${category.name}`);
  await ctx.editMessageText(MESSAGES.categoryDeleted(category.name));
  await ctx.answerCallbackQuery();
});

categoryHandlers.callbackQuery(CALLBACK.closeMenu, async ctx => {
  await ctx.editMessageText(MESSAGES.menuClosed);
  await ctx.answerCallbackQuery();
});
