#!/usr/bin/env bash
# scripts/vps_initial_setup.sh
# Run ONCE on a fresh VPS to set up everything needed before GitHub Actions
# can deploy. After this runs, all subsequent deploys happen automatically
# via the GitHub Actions workflow.
#
# Usage: (as root or sudo user on the VPS)
#   git clone https://github.com/YOUR_ORG/bus-enterprise-db.git /opt/bus-enterprise-db
#   cd /opt/bus-enterprise-db
#   chmod +x scripts/vps_initial_setup.sh
#   sudo ./scripts/vps_initial_setup.sh

set -euo pipefail

echo "=== [1/6] Installing Docker ==="
apt-get update -q
apt-get install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
  > /etc/apt/sources.list.d/docker.list
apt-get update -q
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
systemctl enable docker
systemctl start docker
echo "Docker installed: $(docker --version)"

echo "=== [2/6] Creating secrets ==="
mkdir -p /opt/bus-enterprise-db/secrets
chmod 700 /opt/bus-enterprise-db/secrets

if [ ! -f /opt/bus-enterprise-db/secrets/db_password.txt ]; then
  openssl rand -base64 32 > /opt/bus-enterprise-db/secrets/db_password.txt
  chmod 600 /opt/bus-enterprise-db/secrets/db_password.txt
  echo "Generated new DB password -> /opt/bus-enterprise-db/secrets/db_password.txt"
  echo "IMPORTANT: Save this password somewhere safe (password manager)."
  echo "Password: $(cat /opt/bus-enterprise-db/secrets/db_password.txt)"
else
  echo "secrets/db_password.txt already exists, skipping."
fi

echo "=== [3/6] Generating self-signed SSL cert ==="
mkdir -p /opt/bus-enterprise-db/ssl
if [ ! -f /opt/bus-enterprise-db/ssl/server.crt ]; then
  openssl req -new -x509 -days 365 -nodes \
    -out /opt/bus-enterprise-db/ssl/server.crt \
    -keyout /opt/bus-enterprise-db/ssl/server.key \
    -subj "/C=LK/ST=Western/L=Colombo/O=BusEnterprise/CN=localhost"
  chmod 644 /opt/bus-enterprise-db/ssl/server.crt
  chmod 600 /opt/bus-enterprise-db/ssl/server.key
  echo "Self-signed SSL cert generated."
  echo "NOTE: Replace with a real cert (Let's Encrypt) before going live."
else
  echo "SSL certs already exist, skipping."
fi

echo "=== [4/6] Creating backups directory ==="
mkdir -p /opt/bus-enterprise-db/backups
chmod 750 /opt/bus-enterprise-db/backups

echo "=== [5/6] Setting up daily backup cron ==="
cat > /etc/cron.d/bus-enterprise-db-backup << 'CRON'
0 2 * * * root /opt/bus-enterprise-db/scripts/backup.sh >> /var/log/bus-db-backup.log 2>&1
CRON
chmod 644 /etc/cron.d/bus-enterprise-db-backup
echo "Backup cron installed (daily 02:00 UTC)."

echo "=== [6/6] Initial build + start ==="
cd /opt/bus-enterprise-db
docker compose -f docker-compose.yml up -d --build

echo ""
echo "=== Setup complete ==="
echo "Add these to GitHub repo (Settings > Secrets > Actions):"
echo "  VPS_HOST    = $(curl -s ifconfig.me)"
echo "  VPS_USER    = $(whoami)"
echo "  VPS_SSH_KEY = (your deploy key private key)"