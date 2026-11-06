import { Bot } from "grammy";
import { config } from "./config.ts";
import "./db.ts";

const bot = new Bot(config.token);

bot.use(async (ctx, next) => {
  if (ctx.from && config.allowedUsers.has(ctx.from.id)) await next();
});

bot.catch((err) => console.error("Update failed:", err.error));

process.once("SIGINT", () => bot.stop());
process.once("SIGTERM", () => bot.stop());

await bot.start({ onStart: () => console.log("Bot started") });
