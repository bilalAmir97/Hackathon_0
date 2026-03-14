#!/bin/bash
"""
AI Employee Management Script

Easy control of all AI Employee services.
"""

set -e

PROJECT_DIR="/mnt/d/Bilal/Bilal/Bilal_Data/Hackathon/Hackathon_0"
cd "$PROJECT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_header() {
    echo ""
    echo "============================================================"
    echo "  $1"
    echo "============================================================"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if PM2 is installed
check_pm2() {
    if ! command -v pm2 &> /dev/null; then
        print_error "PM2 is not installed"
        echo "Install with: npm install -g pm2"
        exit 1
    fi
}

# Start all services
start_services() {
    print_header "Starting AI Employee Services"

    check_pm2

    # Stop any existing instances first
    pm2 delete all 2>/dev/null || true

    # Start services from ecosystem config
    pm2 start ecosystem.config.json

    print_success "All services started"
    pm2 status
}

# Stop all services
stop_services() {
    print_header "Stopping AI Employee Services"

    check_pm2
    pm2 stop all

    print_success "All services stopped"
}

# Restart all services
restart_services() {
    print_header "Restarting AI Employee Services"

    check_pm2
    pm2 restart all

    print_success "All services restarted"
    pm2 status
}

# Show service status
show_status() {
    print_header "AI Employee Status"

    check_pm2
    pm2 status

    echo ""
    echo "Logs location:"
    echo "  WhatsApp Watcher: /tmp/whatsapp-watcher-out.log"
    echo "  WhatsApp Processor: /tmp/whatsapp-processor-out.log"
    echo "  Gmail Watcher: /tmp/gmail-watcher-out.log"
}

# Show logs
show_logs() {
    print_header "AI Employee Logs"

    if [ -z "$2" ]; then
        # Show all logs
        pm2 logs --lines 50
    else
        # Show specific service logs
        pm2 logs "$2" --lines 50
    fi
}

# Run health check
run_health_check() {
    print_header "Running Health Check"

    uv run python scripts/health_check.py
}

# Generate daily briefing
generate_briefing() {
    print_header "Generating Daily Briefing"

    uv run python scripts/daily_briefing.py
}

# Setup PM2 startup
setup_startup() {
    print_header "Setting Up Auto-Start on Boot"

    check_pm2

    # Save current PM2 process list
    pm2 save

    # Generate startup script
    pm2 startup

    print_success "Auto-start configured"
    print_warning "You may need to run the command shown above with sudo"
}

# Show help
show_help() {
    cat << EOF
AI Employee Management Script

Usage: bash scripts/manage.sh [command]

Commands:
  start       Start all AI Employee services
  stop        Stop all services
  restart     Restart all services
  status      Show service status
  logs        Show logs (optionally specify service name)
  health      Run health check
  briefing    Generate daily briefing
  setup       Setup auto-start on boot
  help        Show this help message

Examples:
  bash scripts/manage.sh start
  bash scripts/manage.sh logs whatsapp-watcher
  bash scripts/manage.sh health

Service Names:
  - whatsapp-watcher
  - whatsapp-processor
  - gmail-watcher
EOF
}

# Main command handler
case "$1" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "$@"
        ;;
    health)
        run_health_check
        ;;
    briefing)
        generate_briefing
        ;;
    setup)
        setup_startup
        ;;
    help|--help|-h|"")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
