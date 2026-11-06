FROM node:24-slim

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --omit=dev

COPY src ./src

ENV NODE_ENV=production
ENV DATA_DIR=/app/data
ENV TZ=Europe/Madrid
VOLUME ["/app/data"]

CMD ["node", "src/bot.ts"]
