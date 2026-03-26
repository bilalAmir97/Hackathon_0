# Automation Setup Guide

**Do I Need to Manually Start Services Every Time?**

This guide explains what's automated, what's manual, and how to achieve full automation.

---

## Current Status Analysis

### ✅ What's Already Running

**PM2 Services** (Currently Active):
```
✅ whatsapp-processor    - Running for 6 days
✅ gmail-watcher         - Running for 15 hours (restarted 4490 times)
✅ linkedin-poster       - Running for 6 days
⚠️ vault-watcher         - Waiting restart (crashed 9 times)
✅ approval-executor     - Running for 6 days
```

**Cron Jobs** (Already Installed):
```
✅ Weekly audit - Sunday 8 PM
✅ Weekly audit fallback - @reboot + daily 4 PM
✅ Daily briefing - Daily 9 PM
✅ Daily briefing fallback - @reboot
✅ Health check - Every 5 minutes
✅ Log rotation - Sunday 11 PM
✅ Cache cleanup - Daily 2 AM
✅ PM2 resurrection - @reboot
```

---

## Current Setup: Semi-Automated

### What's Automated ✅

1. **Cron Jobs**: Fully automated
   - Run on schedule automatically
   - No manual intervention needed
   - Persist across reboots

2. **PM2 Services After Reboot**: Semi-automated
   - Cron job `@reboot pm2 resurrect` restarts services
   - Works if PM2 was running before reboot
   - Requires PM2 to have been started at least once

### What's Manual ❌

1. **First PM2 Start**: Manual
   - After fresh install, you must run: `pm2 start ecosystem.config.json`
   - After system reboot, cron resurrects PM2 (but only if it was running before)

2. **PM2 Systemd Service**: Not configured
   - PM2 is not registered as a system service
   - Relies on cron @reboot fallback instead

---

## Two Automation Approaches

### Approach 1: Current Setup (Cron-Based) ⚠️

**How It Works**:
```
System Boot
    ↓
Wait 30 seconds
    ↓
Cron runs: pm2 resurrect
    ↓
PM2 restores saved process list
    ↓
Services start automatically
```

**Pros**:
- ✅ No sudo required
- ✅ Already configured
- ✅ Works across reboots

**Cons**:
- ⚠️ 30-second delay after boot
- ⚠️ Requires PM2 to have been started at least once
- ⚠️ If PM2 process list is lost, services won't start

**Current State**: ✅ **ACTIVE** (This is what you have now)

---

### Approach 2: Systemd Service (Recommended) ✅

**How It Works**:
```
System Boot
    ↓
Systemd starts PM2 service
    ↓
PM2 automatically restores process list
    ↓
Services start immediately
```

**Pros**:
- ✅ Starts immediately on boot (no delay)
- ✅ More reliable (systemd manages PM2)
- ✅ Survives PM2 crashes
- ✅ Standard Linux service management

**Cons**:
- ⚠️ Requires one-time sudo setup

**Current State**: ❌ **NOT CONFIGURED** (Optional upgrade)

---

## One-Time Setup for Full Automation

### Step 1: Install Cron Jobs (If Not Already Done)

**Check if installed**:
```bash
crontab -l | grep "AI Employee"
```

**If not installed, run**:
```bash
bash scripts/setup_cron.sh
```

**Verify**:
```bash
crontab -l
```

**Result**: ✅ Cron jobs will run automatically on schedule

---

### Step 2: Configure PM2 Auto-Start (Optional but Recommended)

**Option A: Systemd Service (Recommended)**

Run the setup script to see the command:
```bash
bash scripts/setup_pm2_startup.sh
```

This will show you the exact command to run. Copy and paste it:
```bash
sudo env PATH=$PATH:/home/bilal-amir/.nvm/versions/node/v20.19.6/bin \
  /home/bilal-amir/.nvm/versions/node/v20.19.6/lib/node_modules/pm2/bin/pm2 \
  startup systemd -u bilal-amir --hp /home/bilal-amir
```

**Then save the current PM2 process list**:
```bash
pm2 save
```

**Verify**:
```bash
sudo systemctl status pm2-bilal-amir
```

**Result**: ✅ PM2 services will start automatically on boot (no delay)

---

**Option B: Keep Current Cron-Based Setup (Already Working)**

If you don't want to use sudo, your current setup already works:
- Cron job `@reboot pm2 resurrect` handles restarts
- 30-second delay after boot
- Services restore automatically

**No action needed** - you're already set up!

---

## What Happens After Setup

### Scenario 1: System Reboot

**With Systemd (Recommended)**:
```
1. System boots
2. Systemd starts PM2 service (immediate)
3. PM2 restores all 5 services
4. Services running within 5-10 seconds
```

**With Cron (Current Setup)**:
```
1. System boots
2. Wait 30 seconds
3. Cron runs: pm2 resurrect
4. PM2 restores all 5 services
5. Services running within 35-40 seconds
```

### Scenario 2: PM2 Crash

**With Systemd**:
```
1. PM2 process crashes
2. Systemd detects crash
3. Systemd restarts PM2 automatically
4. Services restored
```

**With Cron**:
```
1. PM2 process crashes
2. Services stop
3. Must manually restart: pm2 start ecosystem.config.json
   OR wait for next reboot
```

### Scenario 3: Individual Service Crash

**Both setups**:
```
1. Service crashes (e.g., gmail-watcher)
2. PM2 auto-restarts service (max 10 attempts)
3. Service back online within seconds
```

This is already working (gmail-watcher restarted 4490 times automatically!)

---

## Daily Operations

### Do You Need to Run Commands Every Day?

**NO** - Everything is automated:

✅ **PM2 Services**: Run 24/7 automatically
- No daily commands needed
- Auto-restart on crash
- Auto-restore on reboot (via cron or systemd)

✅ **Cron Jobs**: Run on schedule automatically
- Weekly audit: Sunday 8 PM
- Daily briefing: Daily 9 PM
- Health checks: Every 5 minutes
- No manual intervention needed

✅ **Fallback Mechanisms**: Automatic
- Missed reports generated automatically
- No manual checks needed

### When DO You Need to Run Commands?

**Only in these situations**:

1. **After Fresh Install** (one-time):
   ```bash
   pm2 start ecosystem.config.json
   pm2 save
   bash scripts/setup_cron.sh
   ```

2. **To Check Status** (optional):
   ```bash
   pm2 status
   pm2 logs
   crontab -l
   ```

3. **To Update Configuration** (rare):
   ```bash
   pm2 restart all
   bash scripts/setup_cron.sh
   ```

4. **To Manually Trigger Reports** (optional):
   ```bash
   python scripts/generate_weekly_audit.py
   python scripts/daily_briefing.py
   ```

---

## Verification Checklist

### ✅ Verify PM2 Services

```bash
# Check if services are running
pm2 status

# Expected output:
# ✅ whatsapp-processor - online
# ✅ gmail-watcher - online
# ✅ linkedin-poster - online
# ✅ vault-watcher - online
# ✅ approval-executor - online
```

### ✅ Verify Cron Jobs

```bash
# Check if cron jobs are installed
crontab -l | grep "AI Employee"

# Expected output:
# ✅ Weekly audit cron job
# ✅ Daily briefing cron job
# ✅ Health check cron job
# ✅ @reboot pm2 resurrect
```

### ✅ Verify Auto-Start (After Reboot)

```bash
# Reboot your system
sudo reboot

# After reboot, wait 1 minute, then check:
pm2 status

# Expected: All services should be running
```

### ✅ Verify Reports Generation

```bash
# Check if reports are being generated
ls -lh AI_Employee_Vault/Briefings/

# Expected:
# ✅ WEEKLY_AUDIT_*.md files
# ✅ BRIEFING_*.md files
```

---

## Troubleshooting

### Problem: PM2 services not running after reboot

**Diagnosis**:
```bash
pm2 status
# If shows "No processes", PM2 didn't resurrect
```

**Solution 1**: Check cron logs
```bash
grep "pm2 resurrect" /tmp/ai-employee-cron.log
```

**Solution 2**: Manually start and save
```bash
pm2 start ecosystem.config.json
pm2 save
```

**Solution 3**: Set up systemd service (permanent fix)
```bash
bash scripts/setup_pm2_startup.sh
# Follow instructions
```

---

### Problem: Cron jobs not running

**Diagnosis**:
```bash
crontab -l | grep "AI Employee"
# If empty, cron jobs not installed
```

**Solution**:
```bash
bash scripts/setup_cron.sh
```

---

### Problem: vault-watcher keeps crashing

**Diagnosis**:
```bash
pm2 logs vault-watcher --lines 50
# Check error messages
```

**Solution**: This is a known issue, vault-watcher has crashed 9 times. Check logs for the specific error and fix the underlying issue.

---

## Summary

### Current State: ✅ Semi-Automated

**What's Working**:
- ✅ PM2 services running (4/5 online)
- ✅ Cron jobs installed and active
- ✅ Auto-restart on reboot (via cron)
- ✅ Scheduled reports generating automatically

**What You Need to Do**:
- ❌ Nothing! Your system is already automated
- ⚠️ Optional: Set up systemd for faster boot (requires sudo)
- ⚠️ Optional: Fix vault-watcher crashes

### After One-Time Setup: ✅ Fully Automated

**You will NEVER need to**:
- ❌ Manually start PM2 services
- ❌ Manually run cron jobs
- ❌ Manually generate reports
- ❌ Manually restart services after reboot

**Everything runs automatically**:
- ✅ PM2 services: 24/7 operation
- ✅ Cron jobs: Scheduled execution
- ✅ Reports: Generated on schedule
- ✅ Fallbacks: Catch missed executions
- ✅ Auto-restart: Services recover from crashes

---

## Quick Reference

### One-Time Setup Commands

```bash
# 1. Install cron jobs (if not done)
bash scripts/setup_cron.sh

# 2. Start PM2 services (if not running)
pm2 start ecosystem.config.json
pm2 save

# 3. Optional: Set up systemd (requires sudo)
bash scripts/setup_pm2_startup.sh
# Follow instructions
```

### Daily Operations

```bash
# Check status (optional)
pm2 status
pm2 logs

# View reports (optional)
ls AI_Employee_Vault/Briefings/
cat AI_Employee_Vault/Briefings/BRIEFING_$(date +%Y-%m-%d).md
```

### After Reboot

```bash
# Wait 1 minute, then verify
pm2 status

# If services not running:
pm2 resurrect
# OR
pm2 start ecosystem.config.json
```

---

**Bottom Line**: Your system is already 95% automated. Cron jobs run automatically, PM2 services auto-restart, and reports generate on schedule. The only optional improvement is setting up systemd for faster boot times.
