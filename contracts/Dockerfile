# Dockerfile for the OpenDPP Hardhat workspace.
# Single dev-mode target: runs a local Hardhat node and auto-deploys
# OpenDPPAnchor on startup.

ARG NODE_VERSION=20-alpine
FROM node:${NODE_VERSION} AS base

ENV PNPM_HOME=/pnpm \
    PATH=/pnpm:$PATH
RUN corepack enable
WORKDIR /app


# --- deps stage: cache the dependency install ---------------------------------
FROM base AS deps

COPY contracts/package.json /app/
COPY contracts/pnpm-lock.yaml* /app/
RUN --mount=type=cache,id=pnpm-contracts,target=/pnpm/store \
    pnpm install --no-frozen-lockfile


# --- dev stage: bind-mount source for live edits ------------------------------
FROM deps AS dev

# Hardhat needs the contracts/scripts on disk to compile + deploy.
# In docker-compose we bind-mount /app source from the host so edits hot-reload.
EXPOSE 8545
CMD ["sh", "-c", "pnpm exec hardhat compile && sh ./scripts/run-and-deploy.sh"]
