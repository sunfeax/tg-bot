import { existsSync, mkdirSync, readdirSync, renameSync, unlinkSync } from 'node:fs';
import path from 'node:path';
import { backup } from 'node:sqlite';
import { config } from '../config.ts';
import { BACKUP_FILE_PATTERN, BACKUP_INTERVAL_MS, BACKUP_KEEP } from '../constants.ts';
import { localDate } from '../format.ts';
import { db } from './init.ts';

const backupDir = path.join(config.dataDir, 'backups');

async function backupDb() {
  mkdirSync(backupDir, { recursive: true });
  const target = path.join(backupDir, `expenses-${localDate()}.db`);
  if (existsSync(target)) return;

  const tmp = `${target}.tmp`;
  await backup(db, tmp);
  renameSync(tmp, target);
  console.info(`Backup created: ${path.basename(target)}`);

  const backups = readdirSync(backupDir)
    .filter(name => BACKUP_FILE_PATTERN.test(name))
    .sort();
  for (const old of backups.slice(0, -BACKUP_KEEP)) unlinkSync(path.join(backupDir, old));
}

function runBackup() {
  backupDb().catch(err => console.error('Backup failed:', err));
}

export function startBackups() {
  runBackup();
  return setInterval(runBackup, BACKUP_INTERVAL_MS);
}
