# Quickstart: Odoo MCP Server

**Feature**: 006-odoo-mcp-server
**Date**: 2026-03-17
**Status**: Planning Complete

## Overview

The Odoo MCP Server provides Claude Code with tools to interact with Odoo accounting system for invoice creation, payment recording, and financial reporting. All financial operations require human approval before execution.

---

## Prerequisites

### 1. Odoo 17 Running

Odoo must be installed and accessible:

```bash
# Check Odoo is running
curl http://localhost:8069

# Expected: HTTP 303 redirect to login page
```

If Odoo is not running, start it:

```bash
# Start Odoo via Docker Compose
docker-compose up -d

# Verify containers are healthy
docker ps | grep odoo
```

### 2. Python Environment

Python 3.10+ with required dependencies:

```bash
# Check Python version
python --version  # Should be 3.10 or higher

# Install dependencies (after implementation)
pip install mcp requests
```

### 3. Environment Variables

Configure Odoo credentials in `.env`:

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add Odoo credentials
nano .env
```

Add these variables:

```bash
# Odoo Configuration
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USERNAME=admin
ODOO_PASSWORD=admin  # Change in production!
```

**Security Note**: Never commit `.env` to git. It's already in `.gitignore`.

---

## Installation

### 1. Install Odoo MCP Server

```bash
# Navigate to project root
cd /path/to/Hackathon_0

# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python -c "import xmlrpc.client; print('xmlrpc.client available')"
```

### 2. Verify Odoo Connection

Test Odoo API connectivity:

```bash
# Test authentication
python -c "
import xmlrpc.client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv('ODOO_URL')
db = os.getenv('ODOO_DB')
username = os.getenv('ODOO_USERNAME')
password = os.getenv('ODOO_PASSWORD')

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

if uid:
    print(f'✅ Authentication successful! User ID: {uid}')
else:
    print('❌ Authentication failed')
"
```

Expected output:
```
✅ Authentication successful! User ID: 2
```

### 3. Start MCP Server

```bash
# Start Odoo MCP Server
python mcp_servers/odoo_mcp_server.py
```

Expected output:
```
🚀 Odoo MCP Server starting...
✅ Connected to Odoo at http://localhost:8069
✅ Authenticated as admin
📡 MCP Server ready on stdio
```

---

## Usage Examples

### Example 1: Create Invoice (Requires Approval)

From Claude Code:

```python
# Call create_invoice MCP tool
result = mcp.call_tool("create_invoice", {
    "customer_id": 45,
    "invoice_date": "2026-03-17",
    "due_date": "2026-04-16",
    "line_items": [
        {
            "product_id": 10,
            "description": "Consulting Services - Project Alpha",
            "quantity": 10,
            "unit_price": 100.00
        },
        {
            "product_id": 15,
            "description": "Software License - Annual",
            "quantity": 1,
            "unit_price": 500.00
        }
    ],
    "reference": "Project Alpha - Phase 1"
})

print(result)
```

Expected response:

```json
{
  "status": "approval_required",
  "approval_file": "APPROVAL_20260317_120000_invoice_123.md",
  "draft_invoice_id": 123,
  "total_amount": "***",
  "message": "Invoice draft created. Approval required before posting."
}
```

**Approval Workflow**:

1. Review approval request in `AI_Employee_Vault/Pending_Approval/`
2. Open the approval file and review invoice details
3. Move file to `Approved/` to finalize invoice
4. Or move to `Rejected/` to cancel

```bash
# Approve invoice
mv AI_Employee_Vault/Pending_Approval/APPROVAL_20260317_120000_invoice_123.md \
   AI_Employee_Vault/Approved/

# Approval executor will finalize invoice in Odoo
# File will be moved to Done/ after execution
```

### Example 2: Record Payment (Requires Approval)

```python
# Call record_payment MCP tool
result = mcp.call_tool("record_payment", {
    "invoice_id": 123,
    "amount": 500.00,
    "payment_date": "2026-03-20",
    "payment_method": "bank_transfer",
    "reference": "Wire transfer #12345"
})

print(result)
```

Expected response:

```json
{
  "status": "approval_required",
  "approval_file": "APPROVAL_20260320_140000_payment_456.md",
  "invoice_id": 123,
  "amount": "***",
  "outstanding_balance_before": "***",
  "outstanding_balance_after": "***",
  "message": "Payment prepared. Approval required before recording."
}
```

**Approval Workflow**: Same as invoice creation (move to Approved/ or Rejected/)

### Example 3: List Invoices (No Approval Required)

```python
# Query invoices for March 2026
result = mcp.call_tool("list_invoices", {
    "date_from": "2026-03-01",
    "date_to": "2026-03-31",
    "status": "posted",
    "limit": 50
})

print(result)
```

Expected response:

```json
{
  "status": "success",
  "count": 25,
  "total_count": 42,
  "invoices": [
    {
      "invoice_id": 123,
      "invoice_number": "INV/2026/0001",
      "customer_id": 45,
      "customer_name": "Acme Corp",
      "date": "2026-03-17",
      "due_date": "2026-04-16",
      "total_amount": "***",
      "status": "posted",
      "outstanding_balance": "***"
    }
  ],
  "message": "Found 25 invoices matching filters"
}
```

### Example 4: Get Financial Report (No Approval Required)

```python
# Get revenue summary for Q1 2026
result = mcp.call_tool("get_financial_report", {
    "report_type": "revenue_summary",
    "date_from": "2026-01-01",
    "date_to": "2026-03-31"
})

print(result)
```

Expected response:

```json
{
  "status": "success",
  "report_type": "revenue_summary",
  "period": "2026-01-01 to 2026-03-31",
  "data": {
    "total_revenue": "***",
    "paid_amount": "***",
    "outstanding_balance": "***",
    "invoice_count": 42,
    "payment_count": 35
  },
  "message": "Revenue summary generated successfully"
}
```

---

## Testing

### Unit Tests

Test Odoo client library:

```bash
# Run Odoo client tests
pytest tests/test_odoo_client.py -v

# Expected output:
# test_authenticate ... PASSED
# test_create_draft_invoice ... PASSED
# test_finalize_invoice ... PASSED
# test_record_payment ... PASSED
# test_search_invoices ... PASSED
```

### Integration Tests

Test MCP server tools:

```bash
# Run MCP server integration tests
pytest tests/test_odoo_mcp_server.py -v

# Expected output:
# test_create_invoice_tool ... PASSED
# test_record_payment_tool ... PASSED
# test_list_invoices_tool ... PASSED
# test_get_financial_report_tool ... PASSED
```

### End-to-End Tests

Test complete workflow:

```bash
# Run end-to-end workflow tests
pytest tests/test_integration_odoo.py -v

# Expected output:
# test_invoice_creation_workflow ... PASSED
# test_payment_recording_workflow ... PASSED
# test_approval_workflow_integration ... PASSED
```

---

## Troubleshooting

### Issue 1: Authentication Failed

**Symptom**: `❌ Authentication failed` or `Invalid credentials`

**Solutions**:

1. Verify Odoo is running:
   ```bash
   curl http://localhost:8069
   ```

2. Check credentials in `.env`:
   ```bash
   cat .env | grep ODOO
   ```

3. Test credentials in Odoo web interface:
   - Open http://localhost:8069
   - Login with username/password from `.env`

4. Check Odoo logs:
   ```bash
   docker logs odoo
   ```

### Issue 2: Customer Not Found

**Symptom**: `Customer ID 999 does not exist in Odoo`

**Solutions**:

1. List available customers:
   ```python
   # In Odoo shell
   docker exec -it odoo odoo shell -d odoo
   >>> partners = env['res.partner'].search([('customer_rank', '>', 0)])
   >>> for p in partners:
   ...     print(f"ID: {p.id}, Name: {p.name}")
   ```

2. Create customer in Odoo web interface:
   - Navigate to Contacts
   - Create new contact
   - Check "Is a Customer"

### Issue 3: Product Not Found

**Symptom**: `Product ID 10 does not exist in Odoo`

**Solutions**:

1. List available products:
   ```python
   # In Odoo shell
   docker exec -it odoo odoo shell -d odoo
   >>> products = env['product.product'].search([('sale_ok', '=', True)])
   >>> for p in products:
   ...     print(f"ID: {p.id}, Name: {p.name}")
   ```

2. Create product in Odoo web interface:
   - Navigate to Sales > Products
   - Create new product
   - Set price and configure

### Issue 4: Payment Exceeds Outstanding Balance

**Symptom**: `Payment amount exceeds outstanding balance`

**Solutions**:

1. Check invoice outstanding balance:
   ```python
   result = mcp.call_tool("list_invoices", {
       "invoice_id": 123
   })
   print(result['invoices'][0]['outstanding_balance'])
   ```

2. Adjust payment amount to be ≤ outstanding balance

### Issue 5: Circuit Breaker Open

**Symptom**: `Circuit breaker open for odoo_api - failing fast`

**Solutions**:

1. Check Odoo service health:
   ```bash
   docker ps | grep odoo
   curl http://localhost:8069
   ```

2. Wait for circuit breaker cooldown (60 seconds)

3. Check service health dashboard:
   ```python
   from scripts.error_recovery.service_health import ServiceHealth
   health = ServiceHealth.get_instance()
   print(health.get_service_status('odoo_api'))
   ```

4. Restart Odoo if needed:
   ```bash
   docker restart odoo
   ```

---

## Configuration

### Error Recovery Settings

Configure retry and circuit breaker behavior in `.env`:

```bash
# Retry Configuration
ERROR_RECOVERY_MAX_ATTEMPTS=3
ERROR_RECOVERY_BASE_DELAY=2.0

# Circuit Breaker Configuration
ERROR_RECOVERY_CIRCUIT_FAILURE_THRESHOLD=5
ERROR_RECOVERY_CIRCUIT_COOLDOWN_SECONDS=60
```

### Audit Logging

All operations are logged to `AI_Employee_Vault/Logs/YYYY-MM-DD.json`:

```bash
# View today's audit log
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | jq .

# Search for invoice operations
cat AI_Employee_Vault/Logs/*.json | jq 'select(.action_type == "invoice_create")'
```

**Note**: Financial amounts are masked as `"***"` in audit logs per SR-009.

---

## Architecture Overview

```
Claude Code
    ↓ MCP Protocol
Odoo MCP Server (odoo_mcp_server.py)
    ↓ JSON-RPC
Odoo Client (odoo_client.py)
    ↓ XML-RPC
Odoo 17 (Docker)
    ↓ PostgreSQL

Approval Workflow:
    Pending_Approval/ → Approved/ → Done/
    (Monitored by approval_executor.py)

Audit Logging:
    All operations → audit_logger.py → Logs/YYYY-MM-DD.json
```

---

## Next Steps

1. **Implement the server**: Follow tasks in `tasks.md` (generated by `/sp.tasks`)
2. **Run tests**: Ensure all tests pass before deployment
3. **Configure production**: Update `.env` with production Odoo credentials
4. **Monitor operations**: Check audit logs and approval workflow
5. **Scale as needed**: Tune error recovery settings based on usage

---

## Additional Resources

- **Specification**: [spec.md](spec.md)
- **Implementation Plan**: [plan.md](plan.md)
- **Data Model**: [data-model.md](data-model.md)
- **API Contracts**: [contracts/](contracts/)
- **Odoo Documentation**: https://www.odoo.com/documentation/17.0/
- **MCP Protocol**: https://modelcontextprotocol.io/

---

**Last Updated**: 2026-03-17
**Status**: Ready for implementation
