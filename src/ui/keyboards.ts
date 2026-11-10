import { InlineKeyboard } from 'grammy';
import { BUTTONS, CALLBACK } from '../config/constants.ts';
import { getCategories } from '../db/categories.ts';

function categoryButtons(prefix: string) {
  const keyboard = new InlineKeyboard();
  for (const [index, category] of getCategories().entries()) {
    keyboard.text(category.name, `${prefix}:${category.id}`);
    if (index % 2 === 1) keyboard.row();
  }
  return keyboard.row();
}

export function buildCategoryKeyboard() {
  return categoryButtons('cat')
    .text(BUTTONS.lend, 'loan:lend')
    .text(BUTTONS.repay, 'loan:repay')
    .row()
    .text(BUTTONS.cancel, CALLBACK.cancel);
}

export function buildDeleteCategoryKeyboard() {
  return categoryButtons('delcat').text(BUTTONS.close, CALLBACK.closeMenu);
}

export function buildDeleteRecordKeyboard(id: number) {
  return new InlineKeyboard().text(BUTTONS.delete, `del:${id}`);
}
