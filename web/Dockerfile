# Multi-stage Dockerfile for the OpenDPP web viewer.
# Build targets:
#   --target dev   → next dev with source mounted at runtime
#   --target prod  → next build → standalone runtime

ARG NODE_VERSION=20-alpine
FROM node:${NODE_VERSION} AS base

ENV PNPM_HOME=/pnpm \
    PATH=/pnpm:$PATH
RUN corepack enable
WORKDIR /app


# --- deps stage: cache the dependency install ---------------------------------
FROM base AS deps

COPY web/package.json web/pnpm-lock.yaml web/pnpm-workspace.yaml /app/
RUN --mount=type=cache,id=pnpm,target=/pnpm/store \
    pnpm install --frozen-lockfile


# --- dev stage: bind-mount source for hot reload ------------------------------
FROM deps AS dev

# Schemas are bind-mounted at /schemas; gen-types.mjs reads them on `predev`.
EXPOSE 3000
CMD ["pnpm", "dev", "--port", "3000", "--hostname", "0.0.0.0"]


# --- build stage: full source + production build ------------------------------
FROM deps AS build

COPY web/ /app/
COPY schemas/ /schemas/
RUN pnpm gen:types && pnpm build


# --- prod stage: minimal runtime image (next standalone) ----------------------
FROM node:${NODE_VERSION} AS prod

ENV NODE_ENV=production \
    PORT=3000 \
    HOSTNAME=0.0.0.0
WORKDIR /app

# Standalone build copies only the necessary deps and runtime files.
COPY --from=build /app/.next/standalone /app/
COPY --from=build /app/.next/static /app/.next/static
COPY --from=build /app/public /app/public

EXPOSE 3000
CMD ["node", "server.js"]
