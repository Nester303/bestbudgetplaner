#!/usr/bin/env bash
# ============================================================
#  deploy/setup-cicd-server.sh
#  Przygotuj serwer do odbierania deployów z GitHub Actions
#  Uruchom RAZ na serwerze jako devadmin (sudo)
# ============================================================
set -euo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info() { echo -e "${GREEN}[INFO]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }

# --- Zmienne — dostosuj przed uruchomieniem ---
REPO_URL="https://github.com/TWOJ_GITHUB/NAZWA_REPO.git"
DEPLOY_DIR="/opt/budzetapp"
STAGING_DIR="/opt/budzetapp-staging"
DEPLOY_USER="deploy"     # dedykowany user do deployów (nie devadmin)
# -----------------------------------------------

info "=== 1. Tworzenie użytkownika deploy ==="
if ! id "$DEPLOY_USER" &>/dev/null; then
    adduser --system --group --shell /bin/bash --home /home/$DEPLOY_USER $DEPLOY_USER
    # Dodaj do grupy docker (żeby mógł uruchamiać docker compose)
    usermod -aG docker $DEPLOY_USER
    info "Użytkownik '$DEPLOY_USER' utworzony"
else
    warn "Użytkownik '$DEPLOY_USER' już istnieje — pomijam"
fi

info "=== 2. Generowanie klucza SSH dla GitHub Actions ==="
DEPLOY_KEY_PATH="/home/$DEPLOY_USER/.ssh/authorized_keys"
mkdir -p "/home/$DEPLOY_USER/.ssh"
chmod 700 "/home/$DEPLOY_USER/.ssh"

# Wygeneruj parę kluczy (bez hasła — używana przez GitHub Actions)
if [[ ! -f "/home/$DEPLOY_USER/.ssh/github_actions_key" ]]; then
    ssh-keygen -t ed25519 \
        -C "github-actions-deploy@$(hostname)" \
        -f "/home/$DEPLOY_USER/.ssh/github_actions_key" \
        -N ""

    # Dodaj klucz publiczny do authorized_keys
    cat "/home/$DEPLOY_USER/.ssh/github_actions_key.pub" >> "$DEPLOY_KEY_PATH"
    chmod 600 "$DEPLOY_KEY_PATH"
    chown -R $DEPLOY_USER:$DEPLOY_USER "/home/$DEPLOY_USER/.ssh"
    info "Para kluczy wygenerowana"
else
    warn "Klucz już istnieje — pomijam generowanie"
fi

echo ""
echo "============================================================"
echo "  SKOPIUJ ten klucz PRYWATNY do GitHub Secret SSH_PRIVATE_KEY:"
echo "============================================================"
cat "/home/$DEPLOY_USER/.ssh/github_actions_key"
echo "============================================================"
echo ""

info "=== 3. Klonowanie repozytorium ==="
if [[ ! -d "$DEPLOY_DIR/.git" ]]; then
    mkdir -p "$DEPLOY_DIR"
    git clone "$REPO_URL" "$DEPLOY_DIR"
    chown -R $DEPLOY_USER:$DEPLOY_USER "$DEPLOY_DIR"
    info "Repo sklonowane do $DEPLOY_DIR"
else
    warn "Repo już istnieje w $DEPLOY_DIR — pomijam"
fi

# Staging
if [[ ! -d "$STAGING_DIR/.git" ]]; then
    mkdir -p "$STAGING_DIR"
    git clone -b dev "$REPO_URL" "$STAGING_DIR" 2>/dev/null || \
        git clone "$REPO_URL" "$STAGING_DIR"
    chown -R $DEPLOY_USER:$DEPLOY_USER "$STAGING_DIR"
    info "Staging repo sklonowane do $STAGING_DIR"
fi

info "=== 4. Uprawnienia deploy usera do katalogów ==="
chown -R $DEPLOY_USER:$DEPLOY_USER "$DEPLOY_DIR" "$STAGING_DIR"

info "=== 5. Sudo bez hasła dla docker compose (deploy user) ==="
SUDOERS_FILE="/etc/sudoers.d/deploy-docker"
cat > "$SUDOERS_FILE" <<EOF
# Pozwól deploy userowi uruchamiać docker compose bez hasła
$DEPLOY_USER ALL=(ALL) NOPASSWD: /usr/bin/docker, /usr/local/bin/docker
EOF
chmod 440 "$SUDOERS_FILE"
visudo -c -f "$SUDOERS_FILE" && info "Sudoers OK" || { rm "$SUDOERS_FILE"; warn "Błąd sudoers!"; }

info "=== 6. .env na serwerze ==="
if [[ ! -f "$DEPLOY_DIR/.env" ]]; then
    cp "$DEPLOY_DIR/.env.example" "$DEPLOY_DIR/.env"
    warn "Skopiowano .env.example → .env"
    warn "⚠  Uzupełnij $DEPLOY_DIR/.env przed pierwszym deployem!"
fi

info ""
info "✓ Serwer gotowy do odbierania deployów!"
info ""
info "Następne kroki:"
info "  1. Uzupełnij $DEPLOY_DIR/.env"
info "  2. Dodaj GitHub Secrets (patrz niżej)"
info "  3. Push do main → automatyczny deploy"
