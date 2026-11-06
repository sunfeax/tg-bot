import { existsSync, mkdirSync, readdirSync, renameSync, unlinkSync } from 'node:fs';
import path from 'node:path';
import { backup } from 'node:sqlite';
import { config } from '../config/config.ts';
import { BACKUP_FILE_PATTERN, BACKUP_KEEP } from '../config/constants.ts';
import { localDate } from '../utils/format.ts';
import { db } from './init.ts';

export const backupDir = path.join(config.dataDir, 'backups');

export async function createSnapshot(target: string) {
  mkdirSync(path.dirname(target), { recursive: true });
  const tmp = `${target}.tmp`;
  await backup(db, tmp);
  renameSync(tmp, target);
}

export async function dailyBackup() {
  const target = path.join(backupDir, `expenses-${localDate()}.db`);
  if (existsSync(target)) return;

  await createSnapshot(target);
  console.info(`Backup created: ${path.basename(target)}`);

  const backups = readdirSync(backupDir)
    .filter(name => BACKUP_FILE_PATTERN.test(name))
    .sort();
  for (const old of backups.slice(0, -BACKUP_KEEP)) unlinkSync(path.join(backupDir, old));
}
