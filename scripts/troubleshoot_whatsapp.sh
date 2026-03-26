#!/bin/bash

# WhatsApp Watcher Troubleshooting Script
# Helps diagnose and fix common WhatsApp Web loading issues

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                      ║"
echo "║          WhatsApp Watcher - Troubleshooting & Fixes                 ║"
echo "║                                                                      ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if Playwright is installed
echo "🔍 Checking Playwright installation..."
if uv run python -c "import playwright" 2>/dev/null; then
    echo "✅ Playwright is installed"
else
    echo "❌ Playwright not found"
    echo "   Installing Playwright..."
    uv add playwright
    uv run playwright install chromium
    echo "✅ Playwright installed"
fi

# Check if session directory exists
echo ""
echo "🔍 Checking session directory..."
if [ -d ".whatsapp_session" ]; then
    echo "✅ Session directory exists"
    echo "   Size: $(du -sh .whatsapp_session | cut -f1)"

    # Ask if user wants to clear session
    read -p "   Clear session and start fresh? (y/n): " clear_session
    if [ "$clear_session" = "y" ]; then
        echo "   Clearing session..."
        rm -rf .whatsapp_session
        echo "✅ Session cleared"
    fi
else
    echo "ℹ️  No existing session (will create on first run)"
fi

# Check system resources
echo ""
echo "🔍 Checking system resources..."
echo "   Memory: $(free -h | awk '/^Mem:/ {print $3 "/" $2}')"
echo "   Disk: $(df -h . | awk 'NR==2 {print $3 "/" $2 " (" $5 " used)"}')"

# Check if port 3000 is available (sometimes used by Playwright)
echo ""
echo "🔍 Checking ports..."
if lsof -i :3000 >/dev/null 2>&1; then
    echo "⚠️  Port 3000 is in use (may cause issues)"
else
    echo "✅ Port 3000 is available"
fi

# Provide recommendations
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 RECOMMENDATIONS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. TIMEOUT FIXES (Already Applied):"
echo "   ✅ Extended navigation timeout to 2 minutes"
echo "   ✅ Added networkidle wait strategy"
echo "   ✅ Multiple selector fallbacks"
echo "   ✅ Improved browser launch args"
echo ""
echo "2. IF STILL TIMING OUT:"
echo "   • Ensure stable internet connection"
echo "   • Close other browser instances"
echo "   • Try clearing session (see above)"
echo "   • Check if WhatsApp Web is accessible in regular browser"
echo ""
echo "3. COMMON ISSUES:"
echo "   • Browser closes suddenly → Fixed with slow_mo and better args"
echo "   • QR code doesn't appear → Wait longer, check selectors"
echo "   • Session expired → Clear .whatsapp_session/ and re-scan"
echo ""
echo "4. TESTING:"
echo "   Run with verbose output:"
echo "   PLAYWRIGHT_DEBUG=1 uv run python watchers/whatsapp_watcher.py"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Ask if user wants to run the watcher now
read -p "🚀 Run WhatsApp watcher now? (y/n): " run_watcher
if [ "$run_watcher" = "y" ]; then
    echo ""
    echo "Starting WhatsApp watcher..."
    echo "Press Ctrl+C to stop"
    echo ""
    uv run python watchers/whatsapp_watcher.py
fi
