#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# SynapseAir Production Server Setup
# Run this ONCE after SSH-ing into a fresh Ubuntu 22.04 VM.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

REPO_URL="https://github.com/arehh04/Atlas-ALibaba.git"
APP_DIR="/opt/synapseair"
SSH_DIR="$HOME/.ssh"

echo "═══════════════════════════════════════════════════"
echo "  SynapseAir — Production Server Bootstrap"
echo "═══════════════════════════════════════════════════"

# ── 1. System update ────────────────────────────────────────────────────────
echo "[1/7] Updating system packages..."
sudo apt-get update -qq && sudo apt-get upgrade -y -qq

# ── 2. Install Docker ───────────────────────────────────────────────────────
echo "[2/7] Installing Docker..."
if ! command -v docker &>/dev/null; then
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker "$USER"
  echo "  → Docker installed. You may need to log out/in for group changes."
else
  echo "  → Docker already installed: $(docker --version)"
fi

# Install docker compose plugin
sudo mkdir -p /usr/local/lib/docker/cli-plugins
sudo curl -fsSL "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
echo "  → Docker Compose: $(docker compose version)"

# ── 3. Clone / update repository ────────────────────────────────────────────
echo "[3/7] Setting up repository at $APP_DIR..."
if [ -d "$APP_DIR/.git" ]; then
  cd "$APP_DIR"
  git pull origin main
  echo "  → Repo updated."
else
  sudo mkdir -p "$APP_DIR"
  sudo chown "$USER:$USER" "$APP_DIR"
  git clone "$REPO_URL" "$APP_DIR"
  cd "$APP_DIR"
  echo "  → Repo cloned."
fi

# Work inside travel-recovery-os subdirectory
cd travel-recovery-os

# ── 4. Create production .env ───────────────────────────────────────────────
echo "[4/7] Creating backend/.env..."
if [ ! -f backend/.env ]; then
  cat > backend/.env <<'ENVEOF'
# ── SynapseAir Production Environment ────────────────────────────────────
# Fill in ALL values before running docker compose up.

# DeepSeek LLM (Main Reasoning & Arbiter)
DEEPSEEK_API_KEY=<your-deepseek-key>
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash

# Hermes / OpenRouter LLM Parser
HERMES_API_BASE=https://openrouter.ai/api/v1
HERMES_API_KEY=<your-openrouter-key>
HERMES_MODEL=nvidia/nemotron-3.5-lightning:free

# n8n (optional — leave blank to use in-app HITL mock)
N8N_API_URL=
N8N_API_KEY=
N8N_WEBHOOK_URL=
N8N_CONSENSUS_CALLBACK_URL=http://127.0.0.1:8000/webhook/consensus

# Atlas Sandbox GDS
ATLAS_CLIENT_ID=CTR12752_api_1
ATLAS_CLIENT_SECRET=sandbox-sk-CTR12752_api_1
ATLAS_BASE_URL=https://sandbox.atriptech.com
ATLAS_API_KEY=sandbox-sk-CTR12752_api_1

# Application secrets — GENERATE NEW ONES for production!
SYNAPSE_API_SECRET=<generate-a-random-64-char-hex-string>
JWT_SECRET_KEY=<generate-a-random-64-char-hex-string>
ENVEOF
  echo "  → backend/.env created with placeholders."
  echo "  ⚠️  EDIT THIS FILE NOW: nano $APP_DIR/travel-recovery-os/backend/.env"
else
  echo "  → backend/.env already exists, skipping."
fi

# ── 5. Generate SSH key for GitHub deploys ──────────────────────────────────
echo "[5/7] Setting up SSH key for GitHub Actions..."
mkdir -p "$SSH_DIR"
chmod 700 "$SSH_DIR"
if [ ! -f "$SSH_DIR/id_ed25519_deploy" ]; then
  ssh-keygen -t ed25519 -f "$SSH_DIR/id_ed25519_deploy" -N "" -C "synapseair-deploy"
  echo ""
  echo "═══════════════════════════════════════════════════════════════"
  echo "  ADD THIS PUBLIC KEY TO YOUR GITHUB REPO:"
  echo "  Settings → Secrets and variables → Actions → New secret"
  echo "═══════════════════════════════════════════════════════════════"
  echo ""
  echo "  Secret name: DEPLOY_SSH_KEY"
  echo "  Value: (paste the PRIVATE key below)"
  echo ""
  cat "$SSH_DIR/id_ed25519_deploy"
  echo ""
  echo "  ───────────────────────────────────────────────────────────"
  echo "  Also add this to ~/.ssh/authorized_keys on THIS server:"
  echo "  ───────────────────────────────────────────────────────────"
  cat "$SSH_DIR/id_ed25519_deploy.pub"
  echo ""
  echo "═══════════════════════════════════════════════════════════════"
else
  echo "  → Deploy key already exists."
fi

# Add public key to authorized_keys for SSH access
cat "$SSH_DIR/id_ed25519_deploy.pub" >> "$SSH_DIR/authorized_keys"
chmod 600 "$SSH_DIR/authorized_keys"

# ── 6. Open firewall ports ──────────────────────────────────────────────────
echo "[6/7] Configuring firewall..."
if command -v ufw &>/dev/null; then
  sudo ufw allow 22/tcp    # SSH
  sudo ufw allow 80/tcp    # Frontend (nginx)
  sudo ufw allow 443/tcp   # HTTPS (future)
  sudo ufw allow 8000/tcp  # Backend API
  echo "  → Firewall rules added (22, 80, 443, 8000)."
else
  echo "  → ufw not found; ensure ports 80 and 8000 are open in your cloud NSG."
fi

# ── 7. Initial deploy ───────────────────────────────────────────────────────
echo "[7/7] Starting services..."
docker compose pull 2>/dev/null || true   # pull cached images if available
docker compose up -d --build

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  ✅  SynapseAir is running!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "  Frontend:  http://$(curl -s ifconfig.me 2>/dev/null || echo '<your-server-ip>')"
echo "  Backend:   http://$(curl -s ifconfig.me 2>/dev/null || echo '<your-server-ip>'):8000/health"
echo ""
echo "  Useful commands:"
echo "    cd $APP_DIR/travel-recovery-os"
echo "    docker compose logs -f          # follow logs"
echo "    docker compose restart backend  # restart one service"
echo "    docker compose down             # stop everything"
echo "    docker compose up -d --build    # rebuild and restart"
echo ""
echo "  Next step: add these GitHub Secrets (Settings → Secrets → Actions):"
echo "    DEPLOY_HOST      = $(curl -s ifconfig.me 2>/dev/null || echo '<your-server-public-ip>')"
echo "    DEPLOY_USER      = $(whoami)"
echo "    DEPLOY_SSH_KEY   = (contents of $SSH_DIR/id_ed25519_deploy)"
echo "    DEPLOY_PATH      = $APP_DIR/travel-recovery-os"
echo "═══════════════════════════════════════════════════════════════"
