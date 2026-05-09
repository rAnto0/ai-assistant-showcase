COMPOSE_DEV = docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml
PYTEST_ARGS ?= -q --disable-warnings -r fE
M ?= migration
REV ?= -1
ifneq (,$(wildcard .env.dev))
include .env.dev
export
endif
TEST_POSTGRES_DB ?= $(POSTGRES_DB)_test

.PHONY: run-dev down-dev build-dev logs-dev shell-service-dev compose-dev-command test test-db env-init migrate-head migration migrate-check migration-empty migrate-down migrate-current lint lint-fix format format-check check

# =======
# HELPERS
# =======
define ensure_db
	@echo "Ensuring test database $(1)..."
	@$(COMPOSE_DEV) exec -T postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -tc "SELECT 1 FROM pg_database WHERE datname = '$(1)';" | grep -q 1 || $(COMPOSE_DEV) exec -T postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -c "CREATE DATABASE $(1);"
endef

# ============
# DEV COMMANDS
# ============
run-dev:
	$(COMPOSE_DEV) up -d $(ARGS)

down-dev:
	$(COMPOSE_DEV) down $(ARGS)

build-dev:
	$(COMPOSE_DEV) build $(ARGS)

logs-dev:
	$(COMPOSE_DEV) logs $(SERVICE)

shell-service-dev:
	$(COMPOSE_DEV) exec -it $(SERVICE) sh -lc 'command -v bash >/dev/null 2>&1 && exec bash || exec sh'

compose-dev-command:
	$(COMPOSE_DEV) $(COMMAND)

# =======
# SCRIPTS
# =======
env-init:
	./scripts/init-env.sh

# =================
# DATABASE COMMANDS
# =================
migration:
	$(COMPOSE_DEV) exec -T backend uv run alembic -c pyproject.toml revision --autogenerate -m "$(M)"

migrate-head:
	$(COMPOSE_DEV) exec -T backend uv run alembic -c pyproject.toml upgrade head

migrate-check:
	$(COMPOSE_DEV) exec -T backend uv run alembic -c pyproject.toml check

migration-empty:
	$(COMPOSE_DEV) exec -T backend uv run alembic -c pyproject.toml revision -m "$(M)"

migrate-down:
	$(COMPOSE_DEV) exec -T backend uv run alembic -c pyproject.toml downgrade $(REV)

migrate-current:
	$(COMPOSE_DEV) exec -T backend uv run alembic -c pyproject.toml current

# =============
# TEST COMMANDS
# =============
lint:
	@echo "Running ruff lint..."
	@$(COMPOSE_DEV) exec -T backend uv run --extra dev ruff check .

lint-fix:
	@echo "Running ruff lint with fixes..."
	@$(COMPOSE_DEV) exec -T backend uv run --extra dev ruff check . --fix

format:
	@echo "Running ruff format..."
	@$(COMPOSE_DEV) exec -T backend uv run --extra dev ruff format .

format-check:
	@echo "Checking ruff format..."
	@$(COMPOSE_DEV) exec -T backend uv run --extra dev ruff format --check .

check: lint format-check test

test: test-db
	@echo "Running tests..."
	@$(COMPOSE_DEV) exec -T backend uv run pytest $(PYTEST_ARGS)

test-db:
	$(call ensure_db,$(TEST_POSTGRES_DB))
