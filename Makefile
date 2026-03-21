.PHONY: up down seed logs build test lint

up:
	docker compose up -d --build

down:
	docker compose down

seed:
	docker compose exec backend python -m app.db.seed.seed_all

logs:
	docker compose logs -f

build:
	docker compose build --no-cache

test:
	cd backend && pytest tests/ -v

lint:
	cd backend && ruff check app/ && ruff format --check app/
