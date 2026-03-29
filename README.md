# BudzetApp — Aplikacja do zarządzania budżetem domowym

Projekt edukacyjny. Twórcy nie ponoszą odpowiedzialności za szkody wynikłe z użytkowania.

## Stack techniczny

- **Backend**: Python 3.12 + Flask, PostgreSQL 16, Redis 7
- **Frontend**: HTML/CSS/JS (vanilla, ES modules)
- **Infrastruktura**: Docker Compose, Nginx, Cloudflare Tunnel
- **Email**: Resend.com API
- **CI/CD**: GitHub Actions → SSH przez Tailscale

## Funkcjonalności

- Rejestracja i logowanie z weryfikacją emailem
- Dashboard z wykresami przychodów i wydatków
- Planer budżetu z transakcjami cyklicznymi
- Kalendarz wydarzeń
- Grupy budżetowe (wspólny budżet rodziny/firmy)
- Faktury VAT z generowaniem PDF
- Ciemny motyw
- Reset hasła przez email

## Uruchomienie produkcyjne
```bash
cd /opt/budzetapp
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Migracje bazy danych
```bash
docker exec -u root budzetapp_backend flask db upgrade
```

## Logi
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs backend --tail=50
```

## Zmienne środowiskowe (.env)

| Zmienna | Opis |
|---------|------|
| `SECRET_KEY` | Klucz aplikacji Flask |
| `JWT_SECRET_KEY` | Klucz JWT |
| `DATABASE_URL` | URL bazy PostgreSQL |
| `REDIS_URL` | URL Redis |
| `RESEND_API_KEY` | Klucz API Resend do wysyłki emaili |
| `MAIL_DEFAULT_SENDER` | Adres nadawcy emaili |
| `CORS_ORIGINS` | Dozwolone originy CORS |

## Architektura
```
Cloudflare → Nginx (port 80) → Backend Flask (port 5000)
                             → Frontend (statyczne pliki HTML/JS/CSS)
                             → PostgreSQL (port 5432, tylko localhost)
                             → Redis (port 6379, tylko localhost)
```

## Bezpieczeństwo

- SSH tylko przez Tailscale VPN
- Port 80 i 443 tylko z Cloudflare IP
- Porty 5000 i 3000 zablokowane w UFW
- PostgreSQL i Redis tylko na localhost
- JWT autentykacja
- Weryfikacja emailem przy rejestracji
