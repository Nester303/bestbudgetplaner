# BudzetApp

Aplikacja webowa do zarządzania budżetem domowym z kalendarzem.

## Stack

| Warstwa | Technologia |
|---------|-------------|
| Backend | Python 3.12 + Flask |
| Baza    | PostgreSQL 16 |
| Cache   | Redis 7 |
| Frontend | HTML / CSS / JS |
| Serwer  | Nginx |
| Deploy  | Docker Compose |
| Sieć    | Tailscale VPN + Cloudflare Tunnel |
| CI/CD   | GitHub Actions |

---

## Szybki start (development)

```bash
# 1. Sklonuj repo
git clone https://github.com/TWOJ_GITHUB/budzetapp.git
cd budzetapp

# 2. Zmienne środowiskowe
cp .env.example .env
# edytuj .env — uzupełnij hasła

# 3. Uruchom
make dev

# 4. Migracje i seed (osobny terminal)
make migrate
make seed

# Aplikacja działa na http://localhost
# API: http://localhost/api/health
```

---

## Struktura gałęzi

```
main   ──────────────────────────────────→  produkcja (autodeploy)
         ↑ merge PR
dev    ──────────────────────────────────→  staging (autodeploy)
         ↑ merge feature branches
feature/nazwa-funkcji  (tworzysz lokalnie, PR → dev)
hotfix/opis            (PR → main i dev)
```

### Workflow dla nowej funkcji

```bash
git checkout dev
git pull origin dev
git checkout -b feature/moja-funkcja

# ... kodowanie ...

git add .
git commit -m "feat: opis zmiany"
git push origin feature/moja-funkcja
# → otwórz Pull Request do dev na GitHubie
```

### Konwencja commitów

```
feat:     nowa funkcja
fix:      naprawa błędu
refactor: refaktoryzacja bez zmiany funkcjonalności
test:     dodanie/zmiana testów
docs:     dokumentacja
chore:    zmiany konfiguracji, CI, zależności
```

---

## Dostępne komendy

```bash
make help          # pełna lista komend
make dev           # uruchom development
make test          # uruchom testy
make migrate       # migracje bazy
make shell-be      # bash w kontenerze backendu
make shell-db      # psql w PostgreSQL
make backup-db     # backup bazy danych
make prod          # uruchom produkcję
```

---

## CI/CD

| Trigger | Workflow | Cel |
|---------|----------|-----|
| push / PR → `dev` | CI testy | weryfikacja |
| push → `dev`  | CD staging | autodeploy staging |
| push / PR → `main` | CI testy | weryfikacja |
| push → `main` | CD produkcja | autodeploy prod z rollbackiem |

GitHub Actions łączy się z serwerem przez **Tailscale VPN** → SSH.

Wymagane GitHub Secrets — patrz `deploy/GITHUB_SECRETS.md`.
