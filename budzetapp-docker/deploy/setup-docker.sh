#!/usr/bin/env bash
# ============================================================
#  deploy/setup-docker.sh
#  Instalacja Dockera i Docker Compose na Ubuntu 22.04/24.04
#  Uruchom: bash deploy/setup-docker.sh
# ============================================================
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }

info "=== Instalacja Dockera ==="

# Usuń stare wersje jeśli istnieją
apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

# Dodaj oficjalne repozytorium Docker
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update
apt-get install -y \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    docker-buildx-plugin \
    docker-compose-plugin

info "=== Konfiguracja Dockera ==="

# Autostart po reboocie
systemctl enable docker
systemctl start docker

# Dodaj użytkownika devadmin do grupy docker
# (żeby nie używać sudo przy każdym docker compose)
usermod -aG docker devadmin 2>/dev/null || \
  usermod -aG docker "$SUDO_USER" 2>/dev/null || true

# Konfiguracja daemon.json — limity logów i storage driver
cat > /etc/docker/daemon.json <<'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "live-restore": true
}
EOF

systemctl restart docker

info "=== Weryfikacja ==="
docker --version
docker compose version

info "✓ Docker zainstalowany pomyślnie!"
warn "Wyloguj się i zaloguj ponownie żeby docker działał bez sudo."
warn "Lub uruchom: newgrp docker"
