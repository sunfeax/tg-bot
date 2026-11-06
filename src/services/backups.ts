import { existsSync, readFileSync, unlinkSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { InputFile, type Api } from 'grammy';
import { config } from '../config/config.ts';
import { BACKUP_INTERVAL_MS, BACKUP_SENT_MARKER, MESSAGES } from '../config/constants.ts';
import { backupDir, createSnapshot, dailyBackup } from '../db/backup.ts';
import { localDate } from '../utils/format.ts';

const markerPath = path.join(backupDir, BACKUP_SENT_MARKER);

export async function sendBackup(api: Api, chatId: number) {
  const date = localDate();
  const snapshot = path.join(backupDir, `snapshot-${Date.now()}.db`);
  await createSnapshot(snapshot);
  try {
    await api.sendDocument(chatId, new InputFile(snapshot, `expenses-${date}.db`), {
      caption: MESSAGES.backupCaption(date),
      disable_notification: true,
    });
  } finally {
    unlinkSync(snapshot);
  }
}

async function sendMonthlyBackup(api: Api) {
  const ownerId = config.allowedUsers.values().next().value;
  const month = localDate().slice(0, 7);
  const lastSent = existsSync(markerPath) ? readFileSync(markerPath, 'utf8') : '';
  if (ownerId === undefined || lastSent === month) return;

  await sendBackup(api, ownerId);
  writeFileSync(markerPath, month);
  console.info(`Monthly backup sent to ${ownerId}`);
}

function runBackups(api: Api) {
  dailyBackup()
    .then(() => sendMonthlyBackup(api))
    .catch(err => console.error('Backup failed:', err));
}

export function startBackups(api: Api) {
  runBackups(api);
  return setInterval(() => runBackups(api), BACKUP_INTERVAL_MS);
}
