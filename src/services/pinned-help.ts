import type { Api } from 'grammy';
import { MESSAGES } from '../config/constants.ts';
import { getPinnedHelp, savePinnedHelp } from '../db/pinned-help.ts';

export async function ensureHelpPinned(api: Api, userId: number) {
  const saved = getPinnedHelp(userId);
  const pinned = (await api.getChat(userId)).pinned_message;

  if (saved && pinned?.message_id === saved.messageId) {
    if (saved.text === MESSAGES.help) return;
    await api.editMessageText(userId, saved.messageId, MESSAGES.help);
    savePinnedHelp(userId, saved.messageId, MESSAGES.help);
    console.info(`Help updated for ${userId}`);
    return;
  }

  const sent = await api.sendMessage(userId, MESSAGES.help, {
    reply_markup: { remove_keyboard: true },
    disable_notification: true,
  });
  await api.pinChatMessage(userId, sent.message_id, { disable_notification: true });
  savePinnedHelp(userId, sent.message_id, MESSAGES.help);
  console.info(`Help pinned for ${userId}`);
}
