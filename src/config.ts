import path from "node:path";

const token = process.env.TOKEN;
if (!token) throw new Error("TOKEN is not set");

export const config = {
  token,
  allowedUsers: new Set(
    (process.env.ALLOWED_USER_IDS ?? "")
      .split(",")
      .map((id) => id.trim())
      .filter(Boolean)
      .map(Number),
  ),
  dataDir: process.env.DATA_DIR ?? path.resolve("data"),
};
