# WhatsApp Watcher - Windows Setup Instructions

## Current Status
- ✅ Implementation complete (watchers/whatsapp_watcher.py)
- ✅ All automated tests pass
- ❌ WhatsApp Web blocks automation in WSL2

## Run from Windows PowerShell

### 1. Install Python Dependencies
```powershell
cd D:\Bilal\Bilal\Bilal_Data\Hackathon\Hackathon_0
pip install playwright
playwright install chromium
```

### 2. Run the Watcher
```powershell
# Dry-run mode (no files created)
python watchers/whatsapp_watcher.py --dry-run

# Production mode
python watchers/whatsapp_watcher.py
```

### 3. What to Expect
1. Chrome browser window opens
2. WhatsApp Web loads with QR code
3. Scan QR code with your phone
4. Watcher monitors for priority messages
5. Creates action files in AI_Employee_Vault/Needs_Action/

## Why Windows Instead of WSL2?
- WhatsApp Web detects WSL2 automation more aggressively
- Windows has native GUI support
- Better success rate bypassing bot detection

## Testing Checklist
- [ ] Browser opens successfully
- [ ] QR code appears
- [ ] Scan QR code with phone
- [ ] Send test message with "urgent" keyword
- [ ] Verify action file created in Needs_Action/
- [ ] Check logs in AI_Employee_Vault/Logs/

## If Still Blocked
WhatsApp may still detect automation. Alternative approaches:
1. Use WhatsApp Business API (official, no automation detection)
2. Manual monitoring (human reviews WhatsApp periodically)
3. Different automation tool (Selenium with better stealth)
