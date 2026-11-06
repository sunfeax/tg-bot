import { db } from './init.ts';

export type Category = { id: number; name: string };

const selectCategories = db.prepare('SELECT id, name FROM categories ORDER BY id');

export function getCategories() {
  return selectCategories.all() as Category[];
}
