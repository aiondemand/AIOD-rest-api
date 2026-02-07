# Rate Limiting

The API implements rate limiting to prevent abuse and ensure fair resource usage.

## Overview

Rate limiting restricts the number of asset uploads a user can perform within a specified time window. This helps maintain system stability and prevents malicious or accidental overuse.

## Scope

- Applies to **asset creation (upload) endpoints**
- Enforced **per authenticated user** (Keycloak subject identifier)
- Does **not** apply to:
  - Asset reads or updates
  - Connector-based bulk uploads

## Configuration

Rate limiting is configured in `src/config.default.toml`:

```toml
[rate_limit]
enabled = true
uploads_per_window = 100
window_seconds = 3600
```

- **enabled**: Toggle rate limiting on/off
- **uploads_per_window**: Maximum uploads allowed per time window
- **window_seconds**: Time window duration in seconds (e.g., 3600 = 1 hour)

## Behavior

### User Uploads

Regular users are subject to rate limits. When the limit is exceeded:

- HTTP status `429 Too Many Requests` is returned
- Response includes a `Retry-After` header indicating when to retry
- Error message specifies the limit and remaining time

### Connector Exemption

Bulk data migration connectors are automatically exempted from rate limiting, as they are designed for large-scale operations.

### Rolling Time Window

The implementation uses a rolling time window rather than fixed buckets. This provides more precise rate limiting by counting uploads within the last N seconds from the current time.

## Implementation

Rate limiting is:

- **Global across asset types**: Limits apply to all uploads regardless of asset type
- **Database-backed**: Uses MySQL to track uploads, avoiding additional infrastructure dependencies
- **Indexed for performance**: Composite index on `(user_identifier, created_at)` optimizes queries
- **Non-atomic**: Minor bursts above the limit may occur under high concurrency (acceptable tradeoff)

## HTTP Response

When rate limited, the API returns:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 1800
Content-Type: application/json

{
  "detail": "Upload rate limit exceeded: max 100 uploads per 3600 seconds. Retry after 1800 seconds."
}
```

## Maintenance

The `asset_upload_log` table tracks all user uploads. Consider implementing periodic cleanup of old records to manage database growth.
