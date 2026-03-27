# ============================================================
#  Makefile — skróty dla codziennej pracy
#  Użycie: make <komenda>
# ============================================================

.PHONY: help dev prod down logs shell-backend shell-db migrate seed \
        test lint fresh-db backup-db restore-db build-prod

# Domyślna komenda — pokaż pomoc
help:
	@echo ""
	@echo "  BudzetApp — dostępne komendy:"
	@echo ""
	@echo "  DEVELOPMENT"
	@echo "  make dev          — uruchom wszystkie kontenery (dev)"
	@echo "  make down         — zatrzymaj i usuń kontenery"
	@echo "  make logs         — śledź logi wszystkich kontenerów"
	@echo "  make logs-be      — logi backendu"
	@echo "  make logs-db      — logi PostgreSQL"
	@echo ""
	@echo "  BAZA DANYCH"
	@echo "  make migrate      — utwórz i uruchom migracje (flask db upgrade)"
	@echo "  make migration m='opis' — nowa migracja (flask db migrate)"
	@echo "  make seed         — wypełnij bazę domyślnymi kategoriami"
	@echo "  make fresh-db     — usuń bazę i zacznij od nowa (⚠ usuwa dane)"
	@echo "  make backup-db    — dump bazy do pliku backup/"
	@echo ""
	@echo "  SHELL / DEBUG"
	@echo "  make shell-be     — bash w kontenerze backendu"
	@echo "  make shell-db     — psql w kontenerze PostgreSQL"
	@echo "  make flask-shell  — interaktywny Flask shell (ipython)"
	@echo ""
	@echo "  PRODUKCJA"
	@echo "  make prod         — uruchom stack produkcyjny"
	@echo "  make build-prod   — zbuduj obrazy produkcyjne"
	@echo ""

# ---- DEV ----
dev:
	docker compose up --build

dev-d:
	docker compose up --build -d

down:
	docker compose down

down-v:
	docker compose down -v    # usuwa też volumes (⚠ dane!)

logs:
	docker compose logs -f --tail=100

logs-be:
	docker compose logs -f --tail=100 backend

logs-db:
	docker compose logs -f --tail=100 db

# ---- BAZA DANYCH ----
migrate:
	docker compose exec backend flask db upgrade

migration:
	docker compose exec backend flask db migrate -m "$(m)"

seed:
	docker compose exec backend flask seed

fresh-db:
	@echo "⚠  Usuwam bazę danych i zaczynam od nowa..."
	docker compose down -v
	docker compose up -d db
	sleep 3
	docker compose up -d backend
	sleep 3
	$(MAKE) migrate
	$(MAKE) seed
	@echo "✓  Świeża baza gotowa."

backup-db:
	@mkdir -p backup
	docker compose exec -T db pg_dump \
	  -U $${POSTGRES_USER:-budzetapp_user} \
	  $${POSTGRES_DB:-budzetapp_db} \
	  | gzip > backup/db_$$(date +%Y%m%d_%H%M%S).sql.gz
	@echo "✓  Backup zapisany w backup/"

restore-db:
	@echo "Użycie: make restore-db FILE=backup/db_20260324_120000.sql.gz"
	gunzip -c $(FILE) | docker compose exec -T db psql \
	  -U $${POSTGRES_USER:-budzetapp_user} \
	  $${POSTGRES_DB:-budzetapp_db}

# ---- SHELL ----
shell-be:
	docker compose exec backend bash

shell-db:
	docker compose exec db psql \
	  -U $${POSTGRES_USER:-budzetapp_user} \
	  -d $${POSTGRES_DB:-budzetapp_db}

flask-shell:
	docker compose exec backend flask shell

# ---- TESTY ----
test:
	docker compose exec backend pytest tests/ -v --tb=short

test-cov:
	docker compose exec backend pytest tests/ --cov=app --cov-report=term-missing

# ---- LINT ----
lint:
	docker compose exec backend python -m flake8 app/ --max-line-length=100
	docker compose exec backend python -m mypy app/ --ignore-missing-imports

# ---- PRODUKCJA ----
prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

build-prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml build

prod-logs:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f --tail=200

prod-down:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down
