install:
	cd backend && make install
	cd frontend && npm install
	test -f .env || cp .env.example .env

lint:
	uvx lefthook run pre-commit --all-files

run-backend:
	cd backend && make run

run-frontend:
	cd frontend && npm run dev

test:
	cd backend && make test
