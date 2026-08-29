# 🚌 Bus Enterprise DB — Production Setup Guide

PostgreSQL 18 + PostGIS 3.6 + pg_partman production database for the Bus Enterprise Management System.

---

## 📁 Folder Structure

```
bus-enterprise-db/
├── Dockerfile                    # Custom image: postgis:18-3.6 + pg_partman 5.2.4
├── docker-compose.yml            # Production (no ports exposed, Docker Secrets, resource limits)
├── docker-compose.override.yml   # Local dev overrides (auto-applied locally only)
├── .gitignore                    # secrets/, ssl/, backups/ → never committed
├── .github/
│   └── workflows/
│       └── deploy.yml            # GitHub Actions CI/CD pipeline
├── init-sql/
│   └── 01_schema.sql             # Full DB schema (auto-runs on first container start)
├── secrets/                      # NOT in Git
│   └── db_password.txt
├── ssl/                          # NOT in Git
│   ├── server.crt
│   └── server.key
├── backups/                      # NOT in Git
│   └── bus_enterprise_YYYYMMDD_HHMMSS.sql.gz
└── scripts/
    ├── vps_initial_setup.sh
    └── backup.sh
```

---

## 🖥️ Part 1 — Fresh VPS Setup (Ubuntu 22.04)

### 1.1 — SSH into VPS

```bash
ssh root@YOUR_VPS_IP
```

---

### 1.2 — System Update

```bash
apt-get update && apt-get upgrade -y
```

---

### 1.3 — Create Deploy User

```bash
adduser deploy
usermod -aG sudo deploy
mkdir -p /home/deploy/.ssh
cp ~/.ssh/authorized_keys /home/deploy/.ssh/
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys
```

Test from local machine (new terminal):
```bash
ssh deploy@YOUR_VPS_IP
```

---

### 1.4 — Install Docker

```bash
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
usermod -aG docker deploy

docker --version
```

Expected: `Docker version 26.x.x, build ...`

---

### 1.5 — Clone the Repository

```bash
apt-get install -y git
mkdir -p /opt/bus-enterprise-db
cd /opt/bus-enterprise-db
git clone https://github.com/YOUR_ORG/bus-enterprise-db.git .
```

> Replace `YOUR_ORG/bus-enterprise-db` with your actual GitHub repo URL.

---

### 1.6 — Generate DB Password

```bash
mkdir -p /opt/bus-enterprise-db/secrets
chmod 700 /opt/bus-enterprise-db/secrets

openssl rand -base64 32 > /opt/bus-enterprise-db/secrets/db_password.txt
chmod 600 /opt/bus-enterprise-db/secrets/db_password.txt

echo "=== DB Password — SAVE THIS IN A PASSWORD MANAGER ==="
cat /opt/bus-enterprise-db/secrets/db_password.txt
echo "======================================================"
```

> ⚠️ This password cannot be recovered if lost. The DB is initialized with it
> on first container start. Save it immediately.

---

### 1.7 — Generate SSL Certificate

```bash
mkdir -p /opt/bus-enterprise-db/ssl

openssl req -new -x509 -days 365 -nodes \
  -out /opt/bus-enterprise-db/ssl/server.crt \
  -keyout /opt/bus-enterprise-db/ssl/server.key \
  -subj "/C=LK/ST=Western/L=Colombo/O=BusEnterprise/CN=$(curl -s ifconfig.me)"

chmod 644 /opt/bus-enterprise-db/ssl/server.crt
chmod 600 /opt/bus-enterprise-db/ssl/server.key
```

> Self-signed for now (no domain yet). When you get a domain, replace with
> a Let's Encrypt cert and update the CN.

---

### 1.8 — Create Backups Directory

```bash
mkdir -p /opt/bus-enterprise-db/backups
chmod 750 /opt/bus-enterprise-db/backups
```

---

### 1.9 — Start the Container

```bash
cd /opt/bus-enterprise-db
docker compose -f docker-compose.yml up -d --build
```

First build takes 1–2 minutes (compiles pg_partman from source).

Watch logs:
```bash
docker logs -f bus_enterprise_db
```

Wait for:
```
LOG:  database system is ready to accept connections
LOG:  pg_partman master background worker master process initialized
```

Press `Ctrl+C` to stop following.

---

### 1.10 — Verify Everything Works

```bash
# Container healthy?
docker compose -f docker-compose.yml ps

# DB accepting connections?
docker exec bus_enterprise_db pg_isready -U postgres -d bus_enterprise

# Schema loaded? (expect ~22 tables)
docker exec bus_enterprise_db psql -U postgres -d bus_enterprise \
  -c "SELECT COUNT(*) FROM information_schema.tables
      WHERE table_schema IN ('core','biz','fin','system');"

# pg_partman registered?
docker exec bus_enterprise_db psql -U postgres -d bus_enterprise \
  -c "SELECT parent_table, partition_interval, premake FROM partman.part_config;"

# Partitions created?
docker exec bus_enterprise_db psql -U postgres -d bus_enterprise \
  -c "\dt system.audit_logs*"

# PostGIS working?
docker exec bus_enterprise_db psql -U postgres -d bus_enterprise \
  -c "SELECT postgis_full_version();"
```

All 6 pass? DB is fully operational. ✅

---

### 1.11 — Install Daily Backup Cron

```bash
chmod +x /opt/bus-enterprise-db/scripts/backup.sh

cat > /etc/cron.d/bus-enterprise-db-backup << 'EOF'
0 2 * * * root /opt/bus-enterprise-db/scripts/backup.sh >> /var/log/bus-db-backup.log 2>&1
EOF

chmod 644 /etc/cron.d/bus-enterprise-db-backup

# Test manually right now
/opt/bus-enterprise-db/scripts/backup.sh
ls -lh /opt/bus-enterprise-db/backups/
```

Runs daily at 02:00 UTC. Keeps 7 days of backups, older ones deleted automatically.

---

## 🔄 Part 2 — GitHub Actions CI/CD

Every push to `main` automatically:
1. Validates SQL schema against a fresh PostgreSQL CI container
2. Builds and pushes Docker image to GitHub Container Registry (ghcr.io)
3. SSH-deploys to the VPS

### 2.1 — Generate Deploy Key

On the VPS:
```bash
ssh-keygen -t ed25519 -C "github-actions-deploy" \
  -f /root/.ssh/github_deploy_key -N ""

cat /root/.ssh/github_deploy_key.pub >> /root/.ssh/authorized_keys

echo "=== COPY THIS → GitHub Secret: VPS_SSH_KEY ==="
cat /root/.ssh/github_deploy_key
echo "==============================================="
```

---

### 2.2 — Add GitHub Secrets

**GitHub repo → Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Value |
|-------------|-------|
| `VPS_HOST` | Your VPS IP address |
| `VPS_USER` | `root` |
| `VPS_SSH_KEY` | Private key from above (include `-----BEGIN...` and `-----END...` lines) |

---

### 2.3 — Trigger First Deploy

```bash
git add .
git commit -m "chore: initial production setup"
git push origin main
```

**GitHub repo → Actions tab** — watch pipeline run:
- ✅ `validate` — schema SQL tested against clean Postgres
- ✅ `build` — Docker image pushed to ghcr.io
- ✅ `deploy` — VPS pulls new image, container restarted

---

## 💻 Part 3 — Local Development

```bash
# docker-compose.override.yml applies automatically
# Port 5432 exposed, plain password, no resource limits
docker compose up -d --build
```

Connect locally:
```
Host:     localhost
Port:     5432
Database: bus_enterprise
User:     postgres
Password: dev_password_only
```

Reset local DB (wipe all data):
```bash
docker compose down -v
docker compose up -d --build
```

---

## 🔗 Part 4 — Connecting Go Backend

DB container runs on Docker network `bus_enterprise_net`.

In your Go backend's `docker-compose.yml` (separate repo):
```yaml
networks:
  bus_enterprise_net:
    external: true
```

Go DSN:
```
host=bus_db port=5432 dbname=bus_enterprise user=bus_app sslmode=require
```

Create limited app user (run once in psql):
```sql
CREATE USER bus_app WITH PASSWORD 'strong_password_here';
GRANT USAGE ON SCHEMA core, biz, fin TO bus_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA core, biz, fin TO bus_app;
GRANT SELECT ON ALL TABLES IN SCHEMA system TO bus_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA core, biz, fin
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO bus_app;
```

> Never use the `postgres` superuser from the application layer.

---

## 🔒 Part 5 — Security Checklist

| # | Check | Status |
|---|-------|--------|
| 1 | DB port NOT exposed externally | ✅ |
| 2 | Password in Docker Secret, not plaintext in compose | ✅ |
| 3 | `secrets/`, `ssl/`, `backups/` in `.gitignore` | ✅ |
| 4 | App uses limited `bus_app` user, not `postgres` | ⚠️ Setup manually (Part 4) |
| 5 | SSL enabled on DB connections | ✅ Self-signed — replace when domain available |
| 6 | Daily automated backups, 7-day retention | ✅ |
| 7 | Resource limits: 4GB RAM, 2 CPU | ✅ |
| 8 | Container restart policy: `always` | ✅ |
| 9 | GitHub Actions uses deploy key, not password | ✅ |
| 10 | Schema validated in CI before every deploy | ✅ |

---

## 🗄️ Part 6 — Backup & Restore

### Manual Backup
```bash
/opt/bus-enterprise-db/scripts/backup.sh
```

### Restore from Backup
```bash
# List backups
ls -lh /opt/bus-enterprise-db/backups/

# Restore (stop backend first to avoid write conflicts)
gunzip -c /opt/bus-enterprise-db/backups/bus_enterprise_20260701_020000.sql.gz | \
  docker exec -i bus_enterprise_db psql -U postgres -d bus_enterprise
```

---

## 🚑 Part 7 — Troubleshooting

### Container won't start
```bash
docker logs bus_enterprise_db 2>&1 | tail -50
```

### Schema didn't load
```bash
# Check tables exist
docker exec bus_enterprise_db psql -U postgres -d bus_enterprise -c "\dt core.*"

# Check for init errors (Linux)
docker logs bus_enterprise_db 2>&1 | grep -i error

# Check for init errors (Windows PowerShell)
docker logs bus_enterprise_db 2>&1 | Select-String -Pattern "ERROR"
```

### pg_partman not working
```bash
docker exec bus_enterprise_db psql -U postgres -d bus_enterprise -c "\dx"
docker logs bus_enterprise_db 2>&1 | grep -i partman
```

### Disk space check
```bash
df -h /opt/bus-enterprise-db/backups
docker system df
```

### Restart container
```bash
docker compose -f /opt/bus-enterprise-db/docker-compose.yml restart bus_db
```

### Full rebuild (keeps data volume)
```bash
cd /opt/bus-enterprise-db
docker compose -f docker-compose.yml up -d --build
```

---

## 📋 Part 8 — Quick Reference

```bash
# Status
docker compose -f /opt/bus-enterprise-db/docker-compose.yml ps

# Live logs
docker logs -f bus_enterprise_db

# Connect to DB (psql shell)
docker exec -it bus_enterprise_db psql -U postgres -d bus_enterprise

# Manual backup
/opt/bus-enterprise-db/scripts/backup.sh

# Restart
docker compose -f /opt/bus-enterprise-db/docker-compose.yml restart bus_db

# Pull latest code + redeploy
cd /opt/bus-enterprise-db && git pull && \
  docker compose -f docker-compose.yml up -d --build
```

---

## 🗺️ Part 9 — Schema Overview

| Schema | Purpose |
|--------|---------|
| `core` | Drivers, vehicles, passengers, routes, halts, districts, loyalty, seat map |
| `biz` | Trips, bookings, schedules, trip halt IoT logs |
| `fin` | Payments, fare rules, ML analytics fact table |
| `system` | Audit logs (partitioned monthly), notifications |
| `partman` | pg_partman extension — manages audit_log partitions automatically |
| `staging` | OSM import staging area (temporary, pre-review) |

### Key Design Decisions

| Table | Decision | Why |
|-------|----------|-----|
| `system.audit_logs` | Range-partitioned by month via pg_partman | Billions of rows expected; partitioning keeps B-tree small + allows clean archive/drop of old months |
| `biz.trips` | No `actual_seats_available` column | Writing to this column on every booking caused row-lock contention under high concurrency; replaced with `biz.v_trip_seat_inventory` view |
| `biz.bookings` | `uq_trip_seat_lock` partial unique index | Prevents seat double-booking at DB engine level — race condition safe |
| `core.passenger_loyalty` | Satellite table (separate from `core.passengers`) | High-frequency point/tier writes don't compete with identity data row locks |
| `fin.fare_rules` | Directional only (A→B ≠ B→A) | Keeps `fin.calculate_fare()` a single deterministic lookup with no runtime branching |
| `core.halts` | `GEOGRAPHY(POINT, 4326)` not `GEOMETRY` | Correct sphere distances for "nearest halt" queries; GIST index supports `<->` KNN operator for both types anyway |

---

*Last updated: July 2026 | PostgreSQL 18.4 | PostGIS 3.6.4 | pg_partman 5.2.4*
