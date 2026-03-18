# Odoo Accounting Integration

**Skill Name:** odoo-accounting
**Category:** Gold Tier - Accounting & Business Management
**MCP Required:** Yes (Odoo MCP Server)

## Purpose

Integrate with self-hosted Odoo Community Edition (v19+) for comprehensive business accounting, invoicing, and financial management using Odoo's JSON-RPC API.

## Prerequisites

- Odoo Community Edition 19+ installed locally or on VM
- Odoo MCP server configured in `.claude/mcp.json`
- Odoo API credentials in `.env`
- Basic understanding of accounting concepts

## Setup

### 1. Install Odoo Community Edition

```bash
# Docker installation (recommended)
docker pull odoo:19
docker run -d -e POSTGRES_USER=odoo -e POSTGRES_PASSWORD=odoo -e POSTGRES_DB=postgres --name db postgres:15
docker run -p 8069:8069 --name odoo --link db:db -t odoo:19
```

### 2. Configure Odoo MCP Server

Add to `.claude/mcp.json`:

```json
{
  "mcpServers": {
    "odoo": {
      "command": "uv",
      "args": ["run", "python", "mcp_servers/odoo_mcp_server.py"],
      "env": {
        "ODOO_URL": "http://localhost:8069",
        "ODOO_DB": "odoo",
        "ODOO_USERNAME": "admin",
        "ODOO_PASSWORD": "admin"
      }
    }
  }
}
```

### 3. Environment Variables

Add to `.env`:

```bash
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USERNAME=admin
ODOO_PASSWORD=admin
ODOO_API_KEY=your_api_key_here
```

## Usage

### Invoke the Skill

```bash
/odoo-accounting [action] [options]
```

### Available Actions

1. **Create Invoice**
   ```
   /odoo-accounting create-invoice --customer "Client A" --amount 1500 --description "January Services"
   ```

2. **Record Payment**
   ```
   /odoo-accounting record-payment --invoice-id 123 --amount 1500 --method "bank_transfer"
   ```

3. **Generate Financial Report**
   ```
   /odoo-accounting financial-report --period "2026-01" --type "profit_loss"
   ```

4. **List Unpaid Invoices**
   ```
   /odoo-accounting list-unpaid --days-overdue 30
   ```

5. **Create Expense**
   ```
   /odoo-accounting create-expense --category "Software" --amount 99 --vendor "Adobe"
   ```

## Workflow Integration

### Automatic Invoice Creation from Email

When a client requests an invoice via email:

1. Email watcher detects request → Creates file in `Needs_Action/`
2. Claude reads request → Extracts client info and amount
3. Skill creates draft invoice in Odoo
4. Creates approval request in `Pending_Approval/`
5. Human approves → Invoice finalized and sent
6. Transaction logged to `Logs/`

### Monthly Financial Summary

Scheduled task (cron) triggers:

```bash
# Run on 1st of each month at 9 AM
0 9 1 * * cd $PROJECT_DIR && claude --print "/odoo-accounting financial-report --period last-month"
```

## Approval Workflow

All financial actions require human approval:

### Draft Invoice Approval

```markdown
---
type: approval_request
action: odoo_create_invoice
customer: Client A
amount: 1500.00
description: January 2026 Services
created: 2026-03-14T10:00:00Z
status: pending
---

## Invoice Details

- **Customer:** Client A (client_a@example.com)
- **Amount:** $1,500.00
- **Description:** January 2026 Services
- **Due Date:** 2026-04-14

## To Approve

Move this file to `/Approved` folder.

## To Reject

Move this file to `/Rejected` folder with reason.
```

## MCP Server Implementation

The Odoo MCP server (`mcp_servers/odoo_mcp_server.py`) provides these tools:

```python
# Available MCP Tools
- odoo_create_invoice(customer, amount, description, due_date)
- odoo_record_payment(invoice_id, amount, payment_method)
- odoo_create_expense(category, amount, vendor, date)
- odoo_get_financial_report(period, report_type)
- odoo_list_invoices(status, customer, date_range)
- odoo_get_balance_sheet(date)
- odoo_get_profit_loss(start_date, end_date)
```

## Integration with Weekly Audit

The weekly business audit skill automatically:

1. Fetches all invoices from Odoo
2. Calculates revenue and expenses
3. Identifies overdue payments
4. Generates CEO briefing with financial summary

## Error Handling

- **Connection Failed:** Retry 3 times with exponential backoff
- **Authentication Error:** Alert user, pause operations
- **Invalid Data:** Create alert in `Needs_Action/` for manual review
- **API Rate Limit:** Queue requests, process when limit resets

## Security

- Never commit Odoo credentials
- Use environment variables for all sensitive data
- Implement IP whitelist for Odoo API access
- Enable 2FA on Odoo admin account
- Regular backup of Odoo database

## Logging

All Odoo operations are logged to `AI_Employee_Vault/Logs/odoo_YYYYMMDD.log`:

```json
{
  "timestamp": "2026-03-14T10:30:00Z",
  "action": "create_invoice",
  "actor": "claude_code",
  "customer": "Client A",
  "amount": 1500.00,
  "invoice_id": 123,
  "approval_status": "approved",
  "result": "success"
}
```

## Troubleshooting

**Q: Odoo MCP server won't connect**
- Verify Odoo is running: `curl http://localhost:8069`
- Check credentials in `.env`
- Review MCP server logs: `tail -f /tmp/odoo-mcp-error.log`

**Q: Invoice creation fails**
- Ensure customer exists in Odoo
- Verify product/service is configured
- Check Odoo user has accounting permissions

**Q: Financial reports are empty**
- Confirm date range is correct
- Verify transactions exist in Odoo
- Check Odoo fiscal year configuration

## References

- [Odoo 19 External API Documentation](https://www.odoo.com/documentation/19.0/developer/reference/external_api.html)
- [Odoo MCP Server GitHub](https://github.com/AlanOgic/mcp-odoo-adv)
- [Odoo Community Edition](https://www.odoo.com/page/download)

## Example: Complete Invoice Flow

```bash
# 1. Client requests invoice via email
# Email watcher creates: Needs_Action/EMAIL_client_a_invoice_request.md

# 2. Process the request
/odoo-accounting create-invoice --customer "Client A" --amount 1500 --description "January Services"

# 3. Claude creates approval request
# File created: Pending_Approval/ODOO_INVOICE_client_a_123.md

# 4. Human reviews and approves
# Move file to: Approved/

# 5. Invoice finalized in Odoo
# Confirmation: Done/ODOO_INVOICE_client_a_123.md

# 6. Update Dashboard
# Dashboard.md updated with: "Invoice #123 created for Client A ($1,500)"
```

## Gold Tier Completion Criteria

- ✅ Odoo Community Edition installed and running
- ✅ MCP server configured and tested
- ✅ Can create invoices via Claude Code
- ✅ Can record payments
- ✅ Can generate financial reports
- ✅ Approval workflow implemented
- ✅ Integration with weekly audit
- ✅ Comprehensive logging enabled
