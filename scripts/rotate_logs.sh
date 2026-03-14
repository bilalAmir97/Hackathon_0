#!/bin/bash
# Log Rotation Script for Silver Tier
# Compresses logs older than 7 days and deletes logs older than 30 days

set -e

# Configuration
VAULT_PATH="${VAULT_PATH:-./AI_Employee_Vault}"
LOGS_DIR="${VAULT_PATH}/Logs"
COMPRESS_DAYS=7
DELETE_DAYS=30

echo "=========================================="
echo "Log Rotation - Silver Tier"
echo "=========================================="
echo ""
echo "Logs directory: ${LOGS_DIR}"
echo "Compress logs older than: ${COMPRESS_DAYS} days"
echo "Delete logs older than: ${DELETE_DAYS} days"
echo ""

# Check if logs directory exists
if [ ! -d "${LOGS_DIR}" ]; then
    echo "❌ Error: Logs directory not found: ${LOGS_DIR}"
    exit 1
fi

# Count files before rotation
TOTAL_FILES=$(find "${LOGS_DIR}" -name "*.json" -type f | wc -l)
echo "📊 Found ${TOTAL_FILES} log files"
echo ""

# Compress logs older than 7 days
echo "🗜️  Compressing logs older than ${COMPRESS_DAYS} days..."
COMPRESSED=0

find "${LOGS_DIR}" -name "*.json" -type f -mtime +${COMPRESS_DAYS} ! -name "*.gz" | while read -r logfile; do
    if [ -f "${logfile}" ]; then
        gzip "${logfile}"
        echo "   Compressed: $(basename "${logfile}")"
        COMPRESSED=$((COMPRESSED + 1))
    fi
done

if [ ${COMPRESSED} -eq 0 ]; then
    echo "   No files to compress"
fi
echo ""

# Delete compressed logs older than 30 days
echo "🗑️  Deleting compressed logs older than ${DELETE_DAYS} days..."
DELETED=0

find "${LOGS_DIR}" -name "*.json.gz" -type f -mtime +${DELETE_DAYS} | while read -r logfile; do
    if [ -f "${logfile}" ]; then
        rm "${logfile}"
        echo "   Deleted: $(basename "${logfile}")"
        DELETED=$((DELETED + 1))
    fi
done

if [ ${DELETED} -eq 0 ]; then
    echo "   No files to delete"
fi
echo ""

# Calculate disk space saved
COMPRESSED_SIZE=$(find "${LOGS_DIR}" -name "*.json.gz" -type f -exec du -ch {} + | grep total$ | awk '{print $1}')
UNCOMPRESSED_SIZE=$(find "${LOGS_DIR}" -name "*.json" -type f -exec du -ch {} + | grep total$ | awk '{print $1}')

echo "📊 Summary:"
echo "   Uncompressed logs: ${UNCOMPRESSED_SIZE:-0}"
echo "   Compressed logs:   ${COMPRESSED_SIZE:-0}"
echo "   Total files:       $(find "${LOGS_DIR}" -type f | wc -l)"
echo ""

# Create rotation log entry
ROTATION_LOG="${LOGS_DIR}/.rotation_history.json"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "{\"timestamp\":\"${TIMESTAMP}\",\"compressed\":${COMPRESSED},\"deleted\":${DELETED}}" >> "${ROTATION_LOG}"

echo "✅ Log rotation complete"
echo ""
echo "💡 Tip: Add this script to cron for automatic rotation:"
echo "   0 2 * * * cd $(pwd) && ./scripts/rotate_logs.sh >> /var/log/log_rotation.log 2>&1"
