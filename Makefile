.PHONY: help up down restart refresh-web logs build rebuild ps shell-api shell-web shell-hardhat migrate seed test test-api test-web test-contracts lint lint-api lint-web fmt-api gen-types compile-contracts deploy-contract-amoy clean nuke

# Default target: print help.
help:
	@echo "OpenDPP — common tasks (everything runs in docker compose)"
	@echo ""
	@echo "  make up         Start the full stack (postgres + api + web)"
	@echo "  make down       Stop the stack (keeps the db volume)"
	@echo "  make restart    Restart api + web"
	@echo "  make refresh-web  Clear the web container's .next cache + restart (fixes stale Turbopack import maps after adding files)"
	@echo "  make build      Build images"
	@echo "  make rebuild    Rebuild images from scratch and restart"
	@echo "  make logs       Tail logs from all services"
	@echo "  make ps         List running services"
	@echo ""
	@echo "  make migrate    Apply Alembic migrations"
	@echo "  make seed       Load seed products"
	@echo "  make test       Run pytest inside the api container"
	@echo "  make lint       Run ruff + tsc"
	@echo "  make gen-types  Regenerate TS types from textile-dpp.v1.json"
	@echo ""
	@echo "  make shell-api       Open a shell in the api container"
	@echo "  make shell-web       Open a shell in the web container"
	@echo "  make shell-hardhat   Open a shell in the hardhat container"
	@echo ""
	@echo "  make compile-contracts          Recompile Solidity"
	@echo "  make test-contracts             Run Hardhat contract tests"
	@echo "  make deploy-contract-amoy       Deploy OpenDPPAnchor to Polygon Amoy (needs DEPLOYER_PRIVATE_KEY)"
	@echo ""
	@echo "  make clean      docker compose down (keeps volumes)"
	@echo "  make nuke       docker compose down -v (drops the db volume)"
	@echo ""
	@echo "  Host ports:  web 3030  ·  api 8080  ·  postgres 5433"

up:
	docker compose up -d
	@echo ""
	@echo "  web → http://localhost:3030"
	@echo "  api → http://localhost:8080/docs"
	@echo "  pg  → localhost:5433"

down:
	docker compose stop

restart:
	docker compose restart api web

# Clears the anonymous /app/.next volume's contents in place — needed
# whenever a new file under web/ doesn't show up in Turbopack's import
# map after a plain restart. Cheaper than --force-recreate (which would
# also blow away node_modules and trigger a full pnpm install).
refresh-web:
	docker compose exec web sh -c 'cd /app/.next && find . -mindepth 1 -delete' || true
	docker compose restart web

build:
	docker compose build

rebuild:
	docker compose build --no-cache
	docker compose up -d

logs:
	docker compose logs -f

ps:
	docker compose ps

migrate:
	docker compose exec api alembic upgrade head

seed:
	docker compose exec api python /seed/load_seed.py

test: test-api

test-api:
	docker compose exec api pytest

test-web:
	docker compose exec web pnpm exec tsc --noEmit

lint: lint-api lint-web

lint-api:
	docker compose exec api ruff check src/ tests/

lint-web:
	docker compose exec web pnpm exec tsc --noEmit

fmt-api:
	docker compose exec api ruff format src/ tests/

gen-types:
	docker compose exec web pnpm gen:types

shell-api:
	docker compose exec api bash

shell-web:
	docker compose exec web sh

shell-hardhat:
	docker compose exec hardhat sh

compile-contracts:
	docker compose exec hardhat pnpm exec hardhat compile

test-contracts:
	docker compose exec hardhat pnpm exec hardhat test

deploy-contract-amoy:
	docker compose exec -e DEPLOYER_PRIVATE_KEY=$${DEPLOYER_PRIVATE_KEY:?missing} \
	                    -e AMOY_RPC_URL=$${AMOY_RPC_URL:-https://rpc-amoy.polygon.technology} \
		hardhat pnpm exec hardhat run scripts/deploy.ts --network amoy

clean:
	docker compose down

nuke:
	docker compose down -v
