#!/usr/bin/env bash
set -euo pipefail

DUIX_HOME="${DUIX_HOME:-/opt/duix_avatar_data}"
CLAW_HOME="${CLAW_HOME:-/opt/claw}"
DUIX_REPO_HOME="${DUIX_REPO_HOME:-/opt/duix-avatar}"

info() {
  printf '[info] %s\n' "$*"
}

warn() {
  printf '[warn] %s\n' "$*" >&2
}

need_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    warn "$1 is not installed or not in PATH"
    return 1
  fi
}

info "checking GPU"
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi
else
  warn "nvidia-smi not found. Install NVIDIA driver first."
fi

info "checking Docker"
need_command docker || true
if command -v docker >/dev/null 2>&1; then
  docker --version
  docker compose version || warn "docker compose plugin is not available"
fi

info "checking Docker GPU runtime"
if command -v docker >/dev/null 2>&1; then
  docker info 2>/dev/null | grep -i nvidia || warn "nvidia runtime not found in docker info"
fi

info "creating directories"
sudo mkdir -p "$CLAW_HOME" "$DUIX_REPO_HOME" "$DUIX_HOME/face2face/temp"
sudo chown -R "$USER:$USER" "$CLAW_HOME" "$DUIX_REPO_HOME" "$DUIX_HOME"

info "directories ready"
printf 'CLAW_HOME=%s\n' "$CLAW_HOME"
printf 'DUIX_REPO_HOME=%s\n' "$DUIX_REPO_HOME"
printf 'DUIX_HOME=%s\n' "$DUIX_HOME"

cat <<'NEXT'

Next steps:

1. Clone Duix:
   cd /opt
   git clone https://github.com/duixcom/Duix-Avatar.git duix-avatar

2. Start Duix:
   cd /opt/duix-avatar
   export DUIX_HOME=/opt/duix_avatar_data
   docker compose -f docker-compose-linux.yml up -d

3. Put this project in /opt/claw and start claw:
   cd /opt/claw
   python deploy/duix-gpu/configure_duix.py --mode docker --duix-home /opt/duix_avatar_data
   export DUIX_HOME=/opt/duix_avatar_data
   docker compose -f docker-compose.yml -f deploy/duix-gpu/docker-compose.duix.yml up -d --build

NEXT
