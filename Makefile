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

reset-db:
	docker compose down --volumes
	docker compose up -d

run-backend:
	cd backend && make run

run-frontend:
	cd frontend && bash -c 'trap "exit 0" INT TERM HUP; while true; do npm run dev; code=$$?; if [ "$$code" -eq 0 ] || [ "$$code" -ge 128 ]; then break; fi; echo "npm run dev exited unexpectedly (code $$code), restarting..."; sleep 1; done'

run-all:
	make run-db && trap 'kill "$${backend_pid}" "$${frontend_pid}" 2>/dev/null; make stop-db' INT TERM HUP && { make run-backend & backend_pid=$$!; make run-frontend & frontend_pid=$$!; wait; }

test:
	cd backend && make test

generate-mock-data:
	cd backend && uv run dotenv -f "../.env" run python scripts/generate_mock_data.py

generate-tiles:
	cd backend && uv run dotenv -f "../.env" run python scripts/generate_tiles.py $(filter-out $@,$(MAKECMDGOALS))

get-all-pitch-angles:
	cd backend && uv run dotenv -f "../.env" run python scripts/get_all_pitch_angles.py

%:
	@:
