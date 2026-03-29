# BudzetApp — Aplikacja do zarządzania budżetem domowym

> ⚠️ Projekt edukacyjny. Twórcy nie ponoszą odpowiedzialności za szkody wynikłe z użytkowania.

## Stack techniczny

- **Backend**: Python 3.12 + Flask, PostgreSQL 16, Redis 7
- **Frontend**: HTML/CSS/JS (vanilla, ES modules)
- **Infrastruktura**: Docker Compose, Nginx, Cloudflare Tunnel
- **Email**: Resend.com API
- **CI/CD**: GitHub Actions → SSH przez Tailscale VPN

## Funkcjonalności

- Rejestracja i logowanie z weryfikacją emailem
- Reset hasła przez email
- Dashboard z wykresami przychodów i wydatków
- Planer budżetu z transakcjami cyklicznymi
- Kalendarz wydarzeń
- Grupy budżetowe (wspólny budżet rodziny/firmy)
- Faktury VAT z generowaniem PDF i danymi sprzedawcy
- Ciemny motyw
- Walidacja siły hasła

## Uruchomienie
```bash
cp .env.example .env
# Uzupełnij zmienne w .env
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
docker exec -u root budzetapp_backend flask db upgrade
```

## Przydatne komendy
```bash
# Logi backendu
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs backend --tail=50

# Migracje bazy
docker exec -u root budzetapp_backend flask db migrate -m "opis"
docker exec -u root budzetapp_backend flask db upgrade

# Restart wszystkiego
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --force-recreate

# Seed danych testowych
docker exec -u root budzetapp_backend flask seed
```

## Zmienne środowiskowe

| Zmienna | Opis |
|---------|------|
| `SECRET_KEY` | Klucz aplikacji Flask |
| `JWT_SECRET_KEY` | Klucz JWT |
| `DATABASE_URL` | URL bazy PostgreSQL |
| `REDIS_URL` | URL Redis |
| `RESEND_API_KEY` | Klucz API Resend |
| `MAIL_DEFAULT_SENDER` | Adres nadawcy emaili |
| `CORS_ORIGINS` | Dozwolone originy CORS |
| `FRONTEND_URL` | URL frontendu |

## Architektura
```
Internet → Cloudflare → Nginx (80) → Backend Flask (5000)
                                   → Frontend statyczny
                      PostgreSQL (5432, localhost only)
                      Redis (6379, localhost only)
```

## Bezpieczeństwo

- SSH tylko przez Tailscale VPN
- Port 80/443 tylko z Cloudflare IP
- Porty 5000/3000 zablokowane w UFW
- PostgreSQL i Redis niedostępne z zewnątrz
- JWT autentykacja z blacklistą tokenów w Redis
- Weryfikacja emailem przy rejestracji
