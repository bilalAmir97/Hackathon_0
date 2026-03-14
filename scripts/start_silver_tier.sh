#!/bin/bash
# Silver Tier Quickstart Script
# Starts Gmail watcher and approval executor

set -e

echo "=========================================="
echo "Silver Tier - Gmail Watcher + Approval"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    echo "   Copy .env.example to .env and configure it"
    exit 1
fi

# Check if token.json exists
if [ ! -f "token.json" ]; then
    echo "⚠️  Warning: token.json not found"
    echo "   Run: python test_gmail_oauth.py"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if credentials.json exists
if [ ! -f "credentials.json" ]; then
    echo "❌ Error: credentials.json not found"
    echo "   Download from Google Cloud Console"
    exit 1
fi

# Validate vault structure
echo "📁 Validating vault structure..."
python -c "from watchers.gmail_state import validate_vault_structure; validate_vault_structure('./AI_Employee_Vault')" || exit 1
echo ""

# Check for PM2
USE_PM2=false
if command -v pm2 &> /dev/null; then
    echo "✅ PM2 detected"
    read -p "Use PM2 for process management? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        USE_PM2=true
    fi
fi

echo ""
echo "Starting Silver Tier services..."
echo ""

if [ "$USE_PM2" = true ]; then
    # Start with PM2
    echo "🚀 Starting with PM2..."

    # Stop existing processes if any
    pm2 delete gmail-watcher 2>/dev/null || true
    pm2 delete approval-executor 2>/dev/null || true

    # Start Gmail watcher
    pm2 start python --name gmail-watcher -- -m watchers.gmail_watcher

    # Start approval executor
    pm2 start python --name approval-executor -- -m scripts.approval_executor

    # Save PM2 configuration
    pm2 save

    echo ""
    echo "✅ Services started with PM2"
    echo ""
    echo "Useful commands:"
    echo "  pm2 list                    # View running processes"
    echo "  pm2 logs gmail-watcher      # View watcher logs"
    echo "  pm2 logs approval-executor  # View executor logs"
    echo "  pm2 stop all                # Stop all processes"
    echo "  pm2 restart all             # Restart all processes"
    echo "  pm2 delete all              # Remove all processes"
    echo ""

else
    # Start without PM2 (foreground)
    echo "🚀 Starting in foreground mode..."
    echo "   Press Ctrl+C to stop both services"
    echo ""

    # Trap Ctrl+C to kill both processes
    trap 'echo ""; echo "⏹️  Stopping services..."; kill $WATCHER_PID $EXECUTOR_PID 2>/dev/null; exit 0' INT TERM

    # Start Gmail watcher in background
    python -m watchers.gmail_watcher &
    WATCHER_PID=$!
    echo "✅ Gmail watcher started (PID: $WATCHER_PID)"

    # Wait a moment
    sleep 2

    # Start approval executor in background
    python -m scripts.approval_executor &
    EXECUTOR_PID=$!
    echo "✅ Approval executor started (PID: $EXECUTOR_PID)"

    echo ""
    echo "📊 Services running:"
    echo "   Gmail Watcher:      PID $WATCHER_PID"
    echo "   Approval Executor:  PID $EXECUTOR_PID"
    echo ""
    echo "Press Ctrl+C to stop"
    echo ""

    # Wait for both processes
    wait $WATCHER_PID $EXECUTOR_PID
fi
