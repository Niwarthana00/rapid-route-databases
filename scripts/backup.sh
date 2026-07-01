#!/usr/bin/env bash
# scripts/backup.sh
# Daily pg_dump — called by cron, logs to /var/log/bus-db-backup.log
# Keeps 7 days of backups, older ones auto-deleted.

set -euo pipefail

BACKUP_DIR="/opt/bus-enterprise-db/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/bus_enterprise_${TIMESTAMP}.sql.gz"
RETAIN_DAYS=7

echo "[$(date)] Starting backup..."

docker exec bus_enterprise_db \
  pg_dump -U postgres bus_enterprise \
  | gzip > "${BACKUP_FILE}"

echo "[$(date)] Backup written: ${BACKUP_FILE} ($(du -sh "${BACKUP_FILE}" | cut -f1))"

# Remove backups older than RETAIN_DAYS
find "${BACKUP_DIR}" -name "bus_enterprise_*.sql.gz" \
  -mtime +${RETAIN_DAYS} -delete

echo "[$(date)] Old backups cleaned (>${RETAIN_DAYS} days removed)."
echo "[$(date)] Current backups:"
ls -lh "${BACKUP_DIR}"/*.sql.gz 2>/dev/null || echo "  (none)"