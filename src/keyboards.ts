import { InlineKeyboard } from 'grammy';
import { MESSAGES } from './constants.ts';
import { getCategories } from './db/categories.ts';

export function buildCategoryKeyboard() {
  const categories = getCategories();
  const keyboard = new InlineKeyboard();
  for (const [index, category] of categories.entries()) {
    keyboard.text(category.name, `categoryId:${category.id}`);
    if (index % 2 === 1) keyboard.row();
  }
  keyboard.row().text(MESSAGES.cancel, 'cancel');
  return keyboard;
}
