---
approval_id: approval_20260318_172940_payment
operation: payment
status: pending
created: 2026-03-18T17:29:40.411624
expires: 2026-03-19T17:29:40.411624
invoice_id: 100
---

# Approval Request: Record Payment

**Approval ID**: `approval_20260318_172940_payment`

## Payment Details

```yaml
{
  "invoice_id": 100,
  "amount": "***",
  "payment_date": "2026-03-17",
  "payment_method": "bank",
  "invoice_name": "INV/2026/0001",
  "outstanding_balance": 200.0
}
```

## Action Required

Please review the payment details above and approve or reject this request.

- To **approve**: Move this file to `Approved/` directory
- To **reject**: Move this file to `Rejected/` directory or delete it

**Note**: Financial amounts are masked for security. Full details will be visible in Odoo after approval.
