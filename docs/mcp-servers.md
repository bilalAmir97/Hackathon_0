# MCP Servers Documentation

**Version**: 1.0
**Last Updated**: March 2026

---

## Overview

Model Context Protocol (MCP) servers provide standardized tool interfaces for external services. Each server implements the MCP protocol (JSON-RPC 2.0) and integrates with the approval workflow system.

---

## MCP Protocol

### Request Format

```json
{
  "jsonrpc": "2.0",
  "method": "tool_name",
  "params": {
    "param1": "value1",
    "param2": "value2"
  },
  "id": 1
}
```

### Response Format

```json
{
  "jsonrpc": "2.0",
  "result": {
    "status": "success",
    "data": {}
  },
  "id": 1
}
```

---

## Email MCP Server

**File**: `mcp_servers/email_client.py`

**Purpose**: Gmail integration for email management

### Tools

#### 1. `send_email`

Send an email via Gmail.

**Parameters**:
- `to` (string, required): Recipient email address
- `subject` (string, required): Email subject
- `body` (string, required): Email body (plain text or HTML)
- `cc` (string, optional): CC recipients (comma-separated)
- `bcc` (string, optional): BCC recipients (comma-separated)

**Returns**:
```json
{
  "status": "success",
  "message_id": "18f3a2b1c4d5e6f7"
}
```

**Approval**: Required

#### 2. `search_emails`

Search emails in Gmail.

**Parameters**:
- `query` (string, required): Gmail search query
- `max_results` (int, optional): Maximum results (default: 10)

**Returns**:
```json
{
  "status": "success",
  "emails": [
    {
      "id": "18f3a2b1c4d5e6f7",
      "subject": "Invoice Request",
      "from": "customer@example.com",
      "date": "2026-03-20T00:00:00Z"
    }
  ]
}
```

**Approval**: Not required (read-only)

---

## Odoo MCP Server

**File**: `mcp_servers/odoo_mcp_server.py`

**Purpose**: Odoo ERP integration for financial operations

### Tools

#### 1. `odoo_create_invoice`

Create a draft invoice in Odoo.

**Parameters**:
- `customer_name` (string, required): Customer name
- `customer_email` (string, required): Customer email
- `items` (array, required): Invoice line items
- `due_date` (string, optional): Due date (ISO 8601)

**Returns**:
```json
{
  "status": "approval_created",
  "approval_id": "ODOO_INVOICE_20260320_120000",
  "invoice_id": 42
}
```

**Approval**: Required

#### 2. `odoo_record_payment`

Record a payment for an invoice.

**Parameters**:
- `invoice_id` (int, required): Invoice ID
- `amount` (float, required): Payment amount
- `payment_date` (string, required): Payment date (ISO 8601)
- `payment_method` (string, required): Payment method

**Returns**:
```json
{
  "status": "approval_created",
  "approval_id": "ODOO_PAYMENT_20260320_120000",
  "payment_id": 123
}
```

**Approval**: Required

#### 3. `odoo_list_invoices`

List invoices from Odoo.

**Parameters**:
- `filters` (array, optional): Odoo domain filters
- `limit` (int, optional): Maximum results (default: 10)

**Returns**:
```json
{
  "status": "success",
  "invoices": [
    {
      "id": 42,
      "name": "INV/2026/0042",
      "partner_name": "Customer Name",
      "amount_total": 1000.00,
      "state": "posted"
    }
  ]
}
```

**Approval**: Not required (read-only)

---

## Facebook & Instagram MCP Server

**File**: `mcp_servers/facebook_instagram_mcp_server.py`

**Purpose**: Social media integration for Facebook and Instagram

### Tools

#### 1. `facebook_post_text`

Post text to Facebook page.

**Parameters**:
- `message` (string, required): Post text (max 63,206 characters)
- `link` (string, optional): URL to include
- `scheduled_time` (string, optional): Schedule time (ISO 8601)

**Returns**:
```json
{
  "status": "approval_created",
  "approval_id": "SOCIAL_FACEBOOK_POST_TEXT_20260320_120000"
}
```

**Approval**: Required

#### 2. `facebook_post_image`

Post image to Facebook page.

**Parameters**:
- `image_path` (string, required): Local path to image
- `caption` (string, optional): Image caption
- `scheduled_time` (string, optional): Schedule time (ISO 8601)

**Returns**:
```json
{
  "status": "approval_created",
  "approval_id": "SOCIAL_FACEBOOK_POST_IMAGE_20260320_120000"
}
```

**Approval**: Required

#### 3. `instagram_post_image`

Post image to Instagram.

**Parameters**:
- `image_path` (string, required): Local path to image
- `caption` (string, optional): Image caption (max 2,200 characters)
- `scheduled_time` (string, optional): Schedule time (ISO 8601)

**Returns**:
```json
{
  "status": "approval_created",
  "approval_id": "SOCIAL_INSTAGRAM_POST_IMAGE_20260320_120000"
}
```

**Approval**: Required

#### 4. `instagram_post_carousel`

Post carousel (multiple images) to Instagram.

**Parameters**:
- `image_paths` (array, required): Local paths to images (2-10 images)
- `caption` (string, optional): Carousel caption
- `scheduled_time` (string, optional): Schedule time (ISO 8601)

**Returns**:
```json
{
  "status": "approval_created",
  "approval_id": "SOCIAL_INSTAGRAM_POST_CAROUSEL_20260320_120000"
}
```

**Approval**: Required

---

## Twitter MCP Server

**File**: `mcp_servers/twitter_mcp_server.py`

**Purpose**: Twitter/X integration for tweet posting and monitoring

### Tools

#### 1. `twitter_post_tweet`

Post a tweet to Twitter.

**Parameters**:
- `text` (string, required): Tweet text (max 280 characters)
- `image_paths` (array, optional): Local paths to images (max 4)
- `scheduled_time` (string, optional): Schedule time (ISO 8601)

**Returns**:
```json
{
  "status": "approval_created",
  "approval_id": "SOCIAL_TWITTER_POST_TWEET_20260320_120000"
}
```

**Approval**: Required

#### 2. `twitter_post_thread`

Post a tweet thread to Twitter.

**Parameters**:
- `tweets` (array, required): Array of tweet texts (2-25 tweets, max 260 chars each)
- `image_paths` (array, optional): Local paths to images (max 4 total)
- `scheduled_time` (string, optional): Schedule time (ISO 8601)

**Returns**:
```json
{
  "status": "approval_created",
  "approval_id": "SOCIAL_TWITTER_POST_THREAD_20260320_120000"
}
```

**Approval**: Required

#### 3. `twitter_get_mentions`

Retrieve tweets mentioning the authenticated user.

**Parameters**:
- `since` (string, optional): ISO 8601 timestamp (max 7 days ago)
- `max_results` (int, optional): Maximum results (5-100, default: 10)

**Returns**:
```json
{
  "status": "success",
  "mentions": [
    {
      "mention_id": "1234567890",
      "author_username": "user123",
      "text": "@yourhandle Great work!",
      "created_at": "2026-03-20T00:00:00Z"
    }
  ],
  "count": 1,
  "cached": false
}
```

**Approval**: Not required (read-only)

#### 4. `twitter_get_metrics`

Retrieve engagement metrics for a tweet.

**Parameters**:
- `tweet_id` (string, required): Twitter tweet ID

**Returns**:
```json
{
  "status": "success",
  "metrics": {
    "likes": 42,
    "retweets": 10,
    "replies": 5,
    "impressions": 1000,
    "engagement_rate": 0.057
  },
  "cached": false
}
```

**Approval**: Not required (read-only)

---

## Common Patterns

### 1. Approval Workflow Integration

All write operations create approval requests:

```python
def tool_handler(params):
    # Validate inputs
    validate_params(params)

    # Create approval request
    approval_id = create_approval_id()
    approval_file = create_approval_request(
        approval_id=approval_id,
        action_type='tool_name',
        metadata=params,
        reasoning='Human-readable explanation'
    )

    # Return approval status
    return {
        'status': 'approval_created',
        'approval_id': approval_id,
        'approval_file': approval_file
    }
```

### 2. Rate Limiting

All MCP servers implement rate limiting:

```python
@with_rate_limit(endpoint='tool_name')
def tool_handler(params):
    # Check rate limit before execution
    rate_limiter.check_limit('tool_name')

    # Execute tool
    result = execute_tool(params)

    # Update rate limit from response headers
    rate_limiter.update_from_headers('tool_name', response.headers)

    return result
```

### 3. Error Recovery

All MCP servers implement retry and circuit breaker:

```python
@with_retry(max_attempts=3, base_delay=1.0)
@with_circuit_breaker(failure_threshold=5, cooldown_seconds=60)
def tool_handler(params):
    # Tool implementation
    pass
```

### 4. Audit Logging

All actions are logged:

```python
def tool_handler(params):
    # Execute action
    result = execute_action(params)

    # Log to audit
    audit_logger.log_action(
        action_type='tool_name',
        actor='mcp_server',
        target='resource_id',
        parameters=params,
        result=result
    )

    return result
```

---

## Configuration

### Environment Variables

Each MCP server requires specific credentials:

```bash
# Email MCP
GMAIL_CREDENTIALS_PATH=credentials.json

# Odoo MCP
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USERNAME=admin
ODOO_PASSWORD=admin

# Facebook/Instagram MCP
FACEBOOK_PAGE_ID=123456789
FACEBOOK_PAGE_ACCESS_TOKEN=EAAxxxxx
INSTAGRAM_ACCOUNT_ID=987654321

# Twitter MCP
TWITTER_API_KEY=xxxxx
TWITTER_API_SECRET=xxxxx
TWITTER_ACCESS_TOKEN=xxxxx
TWITTER_ACCESS_TOKEN_SECRET=xxxxx
```

---

## Testing

### Unit Tests

Test each tool handler:

```python
def test_tool_handler():
    server = MCPServer()
    result = server.tool_handler({'param': 'value'})
    assert result['status'] == 'approval_created'
```

### Integration Tests

Test with real APIs (use test accounts):

```python
def test_integration():
    server = MCPServer()
    result = server.tool_handler({'param': 'value'})

    # Approve manually
    approve_request(result['approval_id'])

    # Verify execution
    assert action_executed()
```

---

## Best Practices

1. **Input Validation**: Validate all inputs before processing
2. **Error Messages**: Provide clear, actionable error messages
3. **Rate Limiting**: Always check rate limits before API calls
4. **Audit Logging**: Log all actions with full context
5. **Approval Workflow**: Never bypass approval for write operations
6. **Idempotency**: Make operations idempotent where possible
7. **Caching**: Cache read-only data with appropriate TTL

---

## Troubleshooting

### Tool Returns Error

**Check**:
1. Credentials valid
2. Rate limits not exceeded
3. Input parameters valid
4. Service accessible

**Debug**:
```bash
# Test credentials
python scripts/verify_<service>_setup.py

# Check rate limits
python -c "from mcp_servers.<service>_rate_limiter import RateLimiter; print(RateLimiter().get_all_status())"

# Check logs
tail -f AI_Employee_Vault/Logs/audit_*.jsonl
```

---

## Conclusion

MCP servers provide a standardized, secure interface to external services. Their integration with the approval workflow, rate limiting, and audit logging ensures safe and compliant automation.
