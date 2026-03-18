#!/bin/bash
# Cron Configuration for Audit Logging System
#
# Installation:
# 1. Make this file executable: chmod +x scripts/setup_cron.sh
# 2. Run: ./scripts/setup_cron.sh
#
# Or manually add to crontab:
# crontab -e
# Then paste the cron entries below

# Get the project directory (where this script is located)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Setting up cron jobs for Audit Logging System"
echo "Project directory: $PROJECT_DIR"

# Create temporary cron file
TEMP_CRON=$(mktemp)

# Get existing crontab (if any)
crontab -l > "$TEMP_CRON" 2>/dev/null || true

# Add audit logging cron jobs if not already present
if ! grep -q "audit_rotate.py" "$TEMP_CRON"; then
    echo "" >> "$TEMP_CRON"
    echo "# Audit Logging - Daily log rotation at midnight" >> "$TEMP_CRON"
    echo "0 0 * * * cd $PROJECT_DIR && python scripts/audit_rotate.py --scheduled >> /tmp/audit-rotate.log 2>&1" >> "$TEMP_CRON"
fi

if ! grep -q "audit_verify.py" "$TEMP_CRON"; then
    echo "" >> "$TEMP_CRON"
    echo "# Audit Logging - Weekly integrity check on Sundays at 2 AM" >> "$TEMP_CRON"
    echo "0 2 * * 0 cd $PROJECT_DIR && python scripts/audit_verify.py --verify-all >> /tmp/audit-verify.log 2>&1" >> "$TEMP_CRON"
fi

# Install new crontab
crontab "$TEMP_CRON"

# Clean up
rm "$TEMP_CRON"

echo "✓ Cron jobs installed successfully"
echo ""
echo "Installed cron jobs:"
echo "  - Daily log rotation: 0 0 * * * (midnight)"
echo "  - Weekly integrity check: 0 2 * * 0 (Sunday 2 AM)"
echo ""
echo "To view installed cron jobs: crontab -l"
echo "To remove cron jobs: crontab -e (then delete the audit logging lines)"
echo ""
echo "Log files:"
echo "  - Rotation log: /tmp/audit-rotate.log"
echo "  - Verification log: /tmp/audit-verify.log"
