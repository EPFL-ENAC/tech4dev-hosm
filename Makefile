install:
	cd backend && make install
	cd frontend && npm install
	test -f .env || cp .env.example .env

lint:
	uvx lefthook run pre-commit --all-files

run-db:
	docker compose up -d

stop-db:
	docker compose down

run-backend:
	cd backend && make run

run-frontend:
	cd frontend && npm run dev

test:
	cd backend && make test

generate-mock-data:
	cd backend && uv run dotenv -f "../.env" run python scripts/generate_mock_data.py
