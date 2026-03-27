# ============================================================
#  GITHUB SECRETS — co i gdzie ustawić
#  GitHub → repo → Settings → Secrets and variables → Actions
# ============================================================

## Secrets wymagane przez workflows

### Tailscale
TAILSCALE_AUTHKEY
  Gdzie: tailscale.com → Settings → Keys → Generate auth key
  Opcje: ✅ Reusable  ✅ Ephemeral  ✅ Pre-authorized
  Opis:  Klucz jednorazowy — runner dołącza do VPN na czas joba i znika

### SSH
SSH_PRIVATE_KEY
  Gdzie: skopiuj z serwera po uruchomieniu setup-cicd-server.sh
  Komenda: cat /home/deploy/.ssh/github_actions_key
  Format: cały blok -----BEGIN OPENSSH PRIVATE KEY----- ... -----END-----

SERVER_TAILSCALE_IP
  Gdzie: serwer → tailscale ip -4
  Format: 100.X.X.X

SERVER_USER
  Wartość: deploy
  Opis:    użytkownik stworzony przez setup-cicd-server.sh

### Aplikacja
DOMAIN
  Wartość: twojastrona.pl
  Opis:    używane w health checkach i URL środowiska

POSTGRES_PASSWORD
  Opis: to samo co w .env na serwerze

SECRET_KEY
  Opis: to samo co w .env na serwerze

JWT_SECRET_KEY
  Opis: to samo co w .env na serwerze

## Environments (opcjonalne ale zalecane)
GitHub → Settings → Environments

production
  - Required reviewers: możesz wymagać akceptacji przed deployem
  - Deployment branches: tylko main

staging
  - Deployment branches: tylko dev

## Sprawdzenie czy secrets działają
Po dodaniu secrets możesz przetestować:
  git push origin main
  GitHub → Actions → "CD — deploy na produkcję" → obserwuj logi
