.PHONY: help install db-up db-down db-logs migrate seed dev test lint fmt clean

help:
	@echo "OpenDPP — common tasks"
	@echo ""
	@echo "  make install   Install API dependencies via uv"
	@echo "  make db-up     Start Postgres in docker compose"
	@echo "  make db-down   Stop Postgres"
	@echo "  make migrate   Apply Alembic migrations"
	@echo "  make seed      Load seed products and DPPs"
	@echo "  make dev       Run the FastAPI dev server on :8000"
	@echo "  make test      Run pytest"
	@echo "  make lint      Run ruff check"
	@echo "  make fmt       Run ruff format"

install:
	cd api && uv sync

db-up:
	docker compose up -d postgres
	@echo "waiting for postgres..."
	@until docker exec opendpp-postgres pg_isready -U opendpp -d opendpp >/dev/null 2>&1; do sleep 1; done
	@echo "postgres ready"

db-down:
	docker compose down

db-logs:
	docker compose logs -f postgres

migrate:
	cd api && uv run alembic upgrade head

seed:
	cd api && uv run python ../seed/load_seed.py

dev:
	cd api && uv run uvicorn opendpp.main:app --reload --host 0.0.0.0 --port 8000

test:
	cd api && uv run pytest

lint:
	cd api && uv run ruff check src/ tests/

fmt:
	cd api && uv run ruff format src/ tests/

clean:
	docker compose down -v
	rm -rf api/.venv api/__pycache__ api/src/opendpp/__pycache__
