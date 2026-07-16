#!/bin/sh
set -e
FILE="$1"
if [ -z "$FILE" ]; then
  echo "Usage: ./scripts/restore.sh backups/ascend_YYYYMMDD_HHMMSS.sql"
  exit 1
fi
HOST="${POSTGRES_HOST:-db}"
USER="${POSTGRES_USER:-ascend}"
DB="${POSTGRES_DB:-ascend}"

echo "Restoring from $FILE"
psql -h "$HOST" -U "$USER" -d "$DB" -f "$FILE"
echo "Restore completed"
