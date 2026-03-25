#!/usr/bin/env bash
# ============================================================
#  deploy/deploy.sh — wdrożenie na produkcję
#  Uruchom po pierwszym sklonowaniu repo lub przy aktualizacji
# ============================================================
set -euo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# --- Sprawdź .env ---
[[ -f .env ]] || error "Brak pliku .env! Skopiuj .env.example i uzupełnij wartości."
source .env

[[ -z "${POSTGRES_PASSWORD:-}" ]] && error "POSTGRES_PASSWORD nie jest ustawione w .env"
[[ -z "${SECRET_KEY:-}"         ]] && error "SECRET_KEY nie jest ustawione w .env"
[[ -z "${JWT_SECRET_KEY:-}"     ]] && error "JWT_SECRET_KEY nie jest ustawione w .env"

info "=== 1. Pobieranie najnowszego kodu ==="
git pull origin main

info "=== 2. Budowanie obrazów produkcyjnych ==="
docker compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache

info "=== 3. Zatrzymanie starych kontenerów ==="
docker compose -f docker-compose.yml -f docker-compose.prod.yml down --remove-orphans

info "=== 4. Uruchomienie bazy i Redis ==="
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d db redis
info "Czekam na gotowość PostgreSQL..."
sleep 8

info "=== 5. Migracje bazy danych ==="
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
    run --rm backend flask db upgrade

info "=== 6. Seed (jeśli pierwsza instalacja) ==="
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
    run --rm backend flask seed || warn "Seed pominięty (dane już istnieją)"

info "=== 7. Uruchomienie wszystkich usług ==="
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

info "=== 8. Sprawdzenie statusu ==="
sleep 5
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

# Health check
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/api/health || echo "000")
if [[ "$HTTP_CODE" == "200" ]]; then
    info "✓ Health check OK (HTTP $HTTP_CODE)"
else
    warn "Health check zwrócił HTTP $HTTP_CODE — sprawdź logi: make prod-logs"
fi

info ""
info "✓ Wdrożenie zakończone!"
info "  Aplikacja: https://${DOMAIN:-localhost}"
info "  API:       https://${DOMAIN:-localhost}/api/health"
