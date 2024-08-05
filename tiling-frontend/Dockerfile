FROM docker.io/oven/bun:slim AS base
WORKDIR /usr/src/app

FROM base AS install
RUN mkdir -p /temp/dev
COPY package.json bun.lockb /temp/dev/
RUN cd /temp/dev && bun install

RUN mkdir -p /temp/prod
COPY package.json bun.lockb /temp/prod/
RUN cd /temp/prod && bun install --production

FROM base AS release
COPY --from=install /temp/dev/node_modules node_modules
COPY . .
RUN bun --bun run build
