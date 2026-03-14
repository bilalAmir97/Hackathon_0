# Bronze Tier Setup Guide

Complete setup instructions for the AI Employee Bronze tier implementation.

## Quick Start (5 minutes)

### Step 1: Install Dependencies

```bash
cd Bronze

# Using UV (recommended)
pip install uv
uv pip install -e .

# Or using pip
pip install -e .
```

### Step 2: Verify Installation

```bash
python main.py --help
```

You should see the help message for the AI Employee.

### Step 3: Start the Watcher

```bash
python main.py
```

You should see:
```
============================================================
AI EMPLOYEE - BRONZE TIER
============================================================
Vault Path: /path/to/AI_Employee_Vault
Status: Starting...
============================================================

Starting File System Watcher
Monitoring: /path/to/AI_Employee_Vault/Inbox
File System Watcher is now active
Drop files into the Inbox folder to create action items
Press Ctrl+C to stop
```

### Step 4: Test the System

Open a new terminal and drop a test file:

```bash
cd Bronze
echo "This is a test document for the AI Employee" > AI_Employee_Vault/Inbox/test.txt
```

Check the watcher terminal - you should see:
```
New file detected: test.txt
Processed file: test.txt
Created action file: FILE_2026-02-19T...
```

### Step 5: Process with Claude Code

```bash
cd AI_Employee_Vault
claude
```

Then in Claude Code:
```
Read the file in Needs_Action and tell me what needs to be done
```

## Detailed Setup

### 1. Environment Configuration

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` if needed:
```bash
# Default settings work for most users
VAULT_PATH=./AI_Employee_Vault
CHECK_INTERVAL=60
DRY_RUN=false
LOG_LEVEL=INFO
```

### 2. Obsidian Setup (Optional)

If you want to view the vault in Obsidian:

1. Open Obsidian
2. Click "Open folder as vault"
3. Navigate to `Bronze/AI_Employee_Vault`
4. Click "Open"

You'll now see:
- Dashboard.md - Your AI Employee's status
- Company_Handbook.md - Rules and guidelines
- All folders in the sidebar

### 3. Claude Code Integration

#### Install Claude Code Skills

Copy the process-inbox skill to Claude Code's skills directory:

```bash
# On macOS/Linux
mkdir -p ~/.config/claude-code/skills
cp skills/process-inbox.md ~/.config/claude-code/skills/

# On Windows
mkdir %USERPROFILE%\.config\claude-code\skills
copy skills\process-inbox.md %USERPROFILE%\.config\claude-code\skills\
```

#### Using the Skill

```bash
cd AI_Employee_Vault
claude /process-inbox
```

### 4. Running as a Background Service

#### Using PM2 (Recommended)

```bash
# Install PM2
npm install -g pm2

# Start the watcher
cd Bronze
pm2 start main.py --name ai-employee --interpreter python3

# View logs
pm2 logs ai-employee

# Stop
pm2 stop ai-employee

# Start on system boot
pm2 startup
pm2 save
```

#### Using systemd (Linux)

Create `/etc/systemd/system/ai-employee.service`:

```ini
[Unit]
Description=AI Employee Bronze Tier
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/Bronze
ExecStart=/usr/bin/python3 main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable ai-employee
sudo systemctl start ai-employee
sudo systemctl status ai-employee
```

## Testing the Complete Workflow

### Test 1: File Drop Detection

```bash
# Terminal 1: Start watcher
python main.py

# Terminal 2: Drop a file
echo "Meeting notes from today" > AI_Employee_Vault/Inbox/meeting-notes.txt

# Terminal 1: Should show detection
# Terminal 2: Check action created
ls AI_Employee_Vault/Needs_Action/
```

### Test 2: Claude Code Processing

```bash
cd AI_Employee_Vault
claude
```

In Claude:
```
1. Read all files in Needs_Action
2. Summarize what needs to be done
3. Move the processed file to Done
4. Update Dashboard.md with the activity
```

### Test 3: Multiple Files

```bash
# Drop multiple files
echo "Invoice from client" > AI_Employee_Vault/Inbox/invoice.txt
echo "Project proposal" > AI_Employee_Vault/Inbox/proposal.txt
echo "Bug report" > AI_Employee_Vault/Inbox/bug.txt

# All should be detected and processed
```

## Troubleshooting

### Watcher Not Starting

**Error**: `ModuleNotFoundError: No module named 'watchdog'`

**Solution**:
```bash
pip install watchdog python-dotenv
```

### Files Not Being Detected

**Check 1**: Is the watcher running?
```bash
ps aux | grep main.py
```

**Check 2**: Is the Inbox folder correct?
```bash
ls -la AI_Employee_Vault/Inbox/
```

**Check 3**: File permissions
```bash
chmod 755 AI_Employee_Vault/Inbox/
```

### Claude Code Can't Read Vault

**Issue**: Claude says it can't find files

**Solution**: Make sure you're in the vault directory
```bash
cd AI_Employee_Vault
pwd  # Should show .../Bronze/AI_Employee_Vault
claude
```

### Python Version Issues

**Error**: `requires-python = ">=3.13"`

**Solution**: Check your Python version
```bash
python --version  # Should be 3.13 or higher
```

If you have an older version, install Python 3.13:
```bash
# macOS
brew install python@3.13

# Ubuntu/Debian
sudo apt install python3.13

# Windows
# Download from python.org
```

## Next Steps

Once your Bronze tier is working:

1. **Customize Company_Handbook.md** with your own rules
2. **Add more file types** to the watcher
3. **Create custom Claude Code prompts** for your workflow
4. **Set up scheduled tasks** to process the inbox automatically
5. **Move to Silver tier** by adding Gmail or WhatsApp watchers

## Support

- Check the main [README.md](README.md) for architecture details
- Review the [Hackathon Guide](../Personal%20AI%20Employee%20Hackathon%200_%20Building%20Autonomous%20FTEs%20in%202026.md)
- Join the Wednesday Research Meetings for help

## Verification Checklist

- [ ] Dependencies installed successfully
- [ ] Watcher starts without errors
- [ ] Files dropped in Inbox are detected
- [ ] Action files created in Needs_Action
- [ ] Claude Code can read vault files
- [ ] Dashboard.md and Company_Handbook.md are accessible
- [ ] Files can be moved to Done folder
- [ ] System runs for at least 5 minutes without crashes

Once all items are checked, your Bronze tier is complete! 🎉
