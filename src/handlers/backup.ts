import { Composer } from 'grammy';
import { sendBackup } from '../services/backups.ts';

export const backupHandlers = new Composer();

backupHandlers.command('backup', ctx => sendBackup(ctx.api, ctx.chat.id));
