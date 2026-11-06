import { db } from './init.ts';

export type PinnedHelp = { messageId: number; text: string };

const select = db.prepare(
  'SELECT message_id AS messageId, text FROM pinned_help WHERE user_id = ?',
);
const upsert = db.prepare(
  'INSERT OR REPLACE INTO pinned_help (user_id, message_id, text) VALUES (?, ?, ?)',
);

export function getPinnedHelp(userId: number) {
  return select.get(userId) as PinnedHelp | undefined;
}

export function savePinnedHelp(userId: number, messageId: number, text: string) {
  upsert.run(userId, messageId, text);
}
