.PHONY: help up down restart logs build rebuild ps shell-api shell-web migrate seed test test-api test-web lint lint-api lint-web fmt-api gen-types clean nuke

# Default target: print help.
help:
	@echo "OpenDPP — common tasks (everything runs in docker compose)"
	@echo ""
	@echo "  make up         Start the full stack (postgres + api + web)"
	@echo "  make down       Stop the stack (keeps the db volume)"
	@echo "  make restart    Restart api + web"
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
	@echo "  make shell-api  Open a shell in the api container"
	@echo "  make shell-web  Open a shell in the web container"
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

clean:
	docker compose down

nuke:
	docker compose down -v
