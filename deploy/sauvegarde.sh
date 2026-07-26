#!/usr/bin/env bash
# Sauvegarde quotidienne de la base de prospects — l'actif le plus précieux du produit.
# Cron conseillé : 0 2 * * * /opt/datamaturity/deploy/sauvegarde.sh >> /var/log/datamaturity-backup.log 2>&1
set -euo pipefail

DEST="${BACKUP_DIR:-/var/backups/datamaturity}"
STAMP="$(date +%Y%m%d-%H%M)"
mkdir -p "$DEST"

if [[ "${DATABASE_URL:-}" == postgresql* ]]; then
    pg_dump "${DATABASE_URL#postgresql+psycopg://}" | gzip > "$DEST/datamaturity-$STAMP.sql.gz"
else
    SQLITE_PATH="${SQLITE_PATH:-/opt/datamaturity/data/datamaturity.db}"
    sqlite3 "$SQLITE_PATH" ".backup '$DEST/datamaturity-$STAMP.db'"
    gzip -f "$DEST/datamaturity-$STAMP.db"
fi

# Conservation : 30 jours
find "$DEST" -type f -mtime +30 -delete
echo "Sauvegarde terminee : $DEST/datamaturity-$STAMP"
