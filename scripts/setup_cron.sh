#!/bin/bash
# Cron Setup Script for AI Employee System
#
# Sets up automated tasks:
# - Weekly business audit (Sunday 8 PM)
# - Health checks (every 5 minutes)
# - Log rotation (weekly)
#
# Usage: bash scripts/setup_cron.sh

set -e

echo "=================================================="
echo "AI Employee System - Cron Setup"
echo "=================================================="
echo ""

# Get the absolute path to the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_PATH=$(which python3 || which python)

echo "Project Directory: $PROJECT_DIR"
echo "Python Path: $PYTHON_PATH"
echo ""

# Check if cron is available
if ! command -v crontab &> /dev/null; then
    echo "❌ Error: crontab command not found"
    echo "   Install cron: sudo apt-get install cron"
    exit 1
fi

# Create cron jobs file
CRON_FILE="/tmp/ai_employee_cron.txt"

cat > "$CRON_FILE" << CRONEOF
# AI Employee System - Automated Tasks
# Generated: $(date)
# Project: $PROJECT_DIR

# Weekly Business Audit - Every Sunday at 8 PM
0 20 * * 0 cd $PROJECT_DIR && $PYTHON_PATH scripts/generate_weekly_audit.py --days 7 >> $PROJECT_DIR/logs/weekly_audit.log 2>&1

# Health Check - Every 5 minutes
*/5 * * * * cd $PROJECT_DIR && $PYTHON_PATH scripts/health_check.py >> $PROJECT_DIR/logs/health_check.log 2>&1

# Log Rotation - Every Sunday at 11 PM
0 23 * * 0 cd $PROJECT_DIR && find $PROJECT_DIR/AI_Employee_Vault/Logs -name "*.jsonl" -mtime +90 -delete >> $PROJECT_DIR/logs/log_rotation.log 2>&1

# Cache Cleanup - Daily at 2 AM
0 2 * * * cd $PROJECT_DIR && find $PROJECT_DIR/.data_cache -name "*.json" -mtime +1 -delete >> $PROJECT_DIR/logs/cache_cleanup.log 2>&1

CRONEOF

echo "📋 Cron jobs to be installed:"
echo "---------------------------------------------------"
cat "$CRON_FILE"
echo "---------------------------------------------------"
echo ""

# Backup existing crontab
echo "💾 Backing up existing crontab..."
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null || true

# Install new cron jobs
echo "📥 Installing cron jobs..."
(crontab -l 2>/dev/null | grep -v "AI Employee System" || true; cat "$CRON_FILE") | crontab -

# Verify installation
echo ""
echo "✅ Cron jobs installed successfully!"
echo ""
echo "📋 Current crontab:"
echo "---------------------------------------------------"
crontab -l | grep -A 10 "AI Employee System" || echo "No AI Employee cron jobs found"
echo "---------------------------------------------------"
echo ""

# Create log directory
mkdir -p "$PROJECT_DIR/logs"

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Verify cron service is running: sudo service cron status"
echo "  2. Check logs in: $PROJECT_DIR/logs/"
echo "  3. Test manually: python scripts/generate_weekly_audit.py"
echo ""
echo "To remove cron jobs: crontab -e (then delete AI Employee lines)"
echo ""
