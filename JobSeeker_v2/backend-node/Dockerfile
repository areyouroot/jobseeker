FROM oven/bun:1.2.14
WORKDIR /app

COPY package.json bun.lock ./
RUN bun install

COPY . .

EXPOSE 3000
CMD ["bun", "run", "index.ts"]
