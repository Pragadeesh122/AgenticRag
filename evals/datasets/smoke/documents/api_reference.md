# XR-7 REST API Reference — v2.1

## Authentication

All API requests require a Bearer token in the Authorization header. Tokens are obtained via the `/auth/token` endpoint using client credentials.

```
POST /auth/token
Content-Type: application/x-www-form-urlencoded

client_id=<your_id>&client_secret=<your_secret>&grant_type=client_credentials
```

Tokens expire after 3600 seconds (1 hour). The response includes an `expires_in` field.

## Endpoints

### GET /api/v2/status
Returns the current controller status including uptime, CPU load, and I/O states.

Response:
```json
{
  "uptime_seconds": 86400,
  "cpu_load_percent": 23.5,
  "memory_used_mb": 1024,
  "digital_inputs": [1,0,1,1,0,0,1,0,1,1,0,0,1,0,1,0],
  "digital_outputs": [1,0,1,0,0,1,0,1],
  "firmware_version": "2.1.4"
}
```

### POST /api/v2/config
Update controller configuration. Requires admin-level token.

Request body:
```json
{
  "network": {
    "ip_address": "192.168.1.100",
    "subnet_mask": "255.255.255.0",
    "gateway": "192.168.1.1"
  },
  "sampling_rate_hz": 1000,
  "watchdog_timeout_ms": 5000
}
```

### GET /api/v2/logs
Retrieve system logs with optional filtering.

Query parameters:
- `level`: Filter by log level (debug, info, warn, error)
- `since`: ISO 8601 timestamp for start of range
- `limit`: Maximum number of entries (default: 100, max: 1000)

### POST /api/v2/firmware/update
Initiate a firmware update. The controller will reboot after a successful update. Maximum firmware image size is 256 MB.

## Rate Limits
- Standard tokens: 60 requests per minute
- Admin tokens: 120 requests per minute
- Firmware updates: 1 per hour
