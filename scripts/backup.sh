#!/bin/sh
set -e
STAMP=$(date +%Y%m%d_%H%M%S)
FILE="/backups/ascend_${STAMP}.sql"
HOST="${POSTGRES_HOST:-db}"
USER="${POSTGRES_USER:-ascend}"
DB="${POSTGRES_DB:-ascend}"

echo "Creating backup: $FILE"
pg_dump -h "$HOST" -U "$USER" -d "$DB" --no-owner --no-acl -f "$FILE"
echo "Backup done: $FILE"

# keep 14 days
find /backups -name 'ascend_*.sql' -mtime +14 -delete 2>/dev/null || true
