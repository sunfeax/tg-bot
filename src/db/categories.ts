import { db } from './init.ts';

export type Category = { id: number; name: string };

const selectCategories = db.prepare('SELECT id, name FROM categories ORDER BY id');
const selectCategoryById = db.prepare('SELECT id, name FROM categories WHERE id = ?');
const insertCategory = db.prepare('INSERT OR IGNORE INTO categories (name) VALUES (?)');
const deleteCategoryById = db.prepare('DELETE FROM categories WHERE id = ?');

export function getCategories() {
  return selectCategories.all() as Category[];
}

export function getCategoryById(id: number) {
  return selectCategoryById.get(id) as Category | undefined;
}

export function addCategory(name: string) {
  return insertCategory.run(name).changes > 0;
}

export function deleteCategory(id: number) {
  deleteCategoryById.run(id);
}
