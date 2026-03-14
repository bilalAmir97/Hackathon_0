#!/bin/bash
# Scheduled Tasks for AI Employee
# Add these to your crontab: crontab -e

# ============================================================
# CONTINUOUS WATCHERS (Managed by PM2 - Always Running)
# ============================================================
# These are handled by PM2, not cron
# - WhatsApp Watcher (every 30s)
# - WhatsApp Processor (every 30s)
# - Gmail Watcher (every 2 minutes)

# ============================================================
# SCHEDULED TASKS (Run at specific times)
# ============================================================

# Daily Morning Briefing (8:00 AM every day)
# 0 8 * * * cd /mnt/d/Bilal/Bilal/Bilal_Data/Hackathon/Hackathon_0 && /usr/bin/uv run python scripts/daily_briefing.py >> /tmp/daily-briefing.log 2>&1

# Weekly Business Audit (Sunday 11:00 PM)
# 0 23 * * 0 cd /mnt/d/Bilal/Bilal/Bilal_Data/Hackathon/Hackathon_0 && /usr/bin/uv run python scripts/weekly_audit.py >> /tmp/weekly-audit.log 2>&1

# Process Pending Approvals (Every hour)
# 0 * * * * cd /mnt/d/Bilal/Bilal/Bilal_Data/Hackathon/Hackathon_0 && /usr/bin/uv run python scripts/approval_executor.py >> /tmp/approval-executor.log 2>&1

# Rotate Logs (Daily at midnight)
# 0 0 * * * cd /mnt/d/Bilal/Bilal/Bilal_Data/Hackathon/Hackathon_0 && bash scripts/rotate_logs.sh >> /tmp/log-rotation.log 2>&1

# Health Check (Every 5 minutes)
# */5 * * * * cd /mnt/d/Bilal/Bilal/Bilal_Data/Hackathon/Hackathon_0 && /usr/bin/uv run python scripts/health_check.py >> /tmp/health-check.log 2>&1

# Backup Vault (Daily at 2:00 AM)
# 0 2 * * * cd /mnt/d/Bilal/Bilal/Bilal_Data/Hackathon/Hackathon_0 && bash scripts/backup_vault.sh >> /tmp/backup.log 2>&1

# ============================================================
# INSTALLATION INSTRUCTIONS
# ============================================================
# 1. Make this file executable:
#    chmod +x scripts/cron_schedule.sh
#
# 2. Edit your crontab:
#    crontab -e
#
# 3. Add the lines you want (uncomment by removing #)
#
# 4. Verify cron jobs:
#    crontab -l
#
# 5. Check cron logs:
#    grep CRON /var/log/syslog  (Linux)
#    tail -f /tmp/*.log          (Your logs)

# ============================================================
# CRON TIME FORMAT
# ============================================================
# * * * * * command
# │ │ │ │ │
# │ │ │ │ └─── Day of week (0-7, 0 and 7 = Sunday)
# │ │ │ └───── Month (1-12)
# │ │ └─────── Day of month (1-31)
# │ └───────── Hour (0-23)
# └─────────── Minute (0-59)
#
# Examples:
# 0 8 * * *     = 8:00 AM every day
# */5 * * * *   = Every 5 minutes
# 0 23 * * 0    = 11:00 PM every Sunday
# 0 0 1 * *     = Midnight on 1st of every month
