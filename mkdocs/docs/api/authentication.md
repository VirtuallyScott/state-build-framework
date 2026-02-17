# Authentication & Authorization Guide

Complete guide to authentication and authorization in the Build State API.

> **💡 CLI Users:** The `bldst` CLI handles authentication automatically. Simply configure once:
> ```bash
> bldst config set-url http://localhost:8080
> bldst auth set-key your-api-key    # Or: bldst auth login
> ```
> See the [CLI README](../cli/README.md) for details.

## Overview

The Build State API supports two authentication methods:
1. **API Keys** - Recommended for automation, scripts, and CI/CD pipelines
2. **JWT Tokens** - Recommended for interactive use and web applications

Both methods support **scope-based authorization** (read, write, admin).

---

## Authentication Methods

### API Key Authentication

API keys are static tokens ideal for service-to-service communication and automation.

**CLI Usage (Recommended):**
```bash
# Configure once
bldst auth set-key your-api-key

# Use commands - authentication is automatic
bldst platform list
bldst build create ...
```

**Direct HTTP Usage:**
```bash
curl -H "X-API-Key: your-api-key" http://localhost:8080/platforms/
```

**Advantages:**
- Simple to use
- No expiration (unless manually revoked)
- Perfect for CI/CD pipelines
- No need to manage username/password

**Security Considerations:**
- Store API keys securely (environment variables, secret managers)
- Never commit API keys to version control
- Rotate keys periodically
- Use separate keys for different environments

### JWT Token Authentication

JWT (JSON Web Tokens) provide time-limited authentication ideal for user sessions.

**Obtaining a Token:**
```bash
curl -X POST http://localhost:8080/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Using the Token:**
```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  http://localhost:8080/platforms/
```

**Advantages:**
- Time-limited (expires after 1 hour by default)
- Can be refreshed
- Includes user identity claims
- Better audit trail

**Token Expiration:**
- Default: 3600 seconds (1 hour)
- After expiration, request a new token
- CLI automatically handles re-authentication

---

## Authorization Scopes

The API uses scope-based authorization with three permission levels:

### 1. Read Scope

**Permissions:**
- View all resources (GET operations)
- List platforms, OS versions, image types, projects, builds
- View dashboard and statistics
- Check health and status

**Example Operations:**
```bash
# ✓ Allowed
GET /platforms/
GET /os_versions/
GET /builds/{build_id}
GET /dashboard/summary

# ✗ Denied
POST /platforms/     # Needs write scope
DELETE /builds/123   # Needs admin scope
```

### 2. Write Scope

**Permissions:**
- All read permissions
- Create resources (POST)
- Update resources (PUT/PATCH)
- Record build states and failures

**Example Operations:**
```bash
# ✓ Allowed
GET /platforms/                    # Read permission
POST /platforms/                   # Write permission
PUT /platforms/aws-commercial      # Write permission
POST /builds/{id}/state           # Write permission

# ✗ Denied
DELETE /platforms/aws-commercial   # Needs admin scope
```

### 3. Admin Scope

**Permissions:**
- All write permissions
- All read permissions
- Delete resources (soft delete)
- User management
- API token management

**Example Operations:**
```bash
# ✓ Allowed (everything)
GET /platforms/
POST /platforms/
PUT /platforms/{id}
DELETE /platforms/{id}
POST /users
DELETE /users/{id}
```

---

## Test API Keys

Three test keys are pre-configured for development:

### Read-Only Key
```
readonly-key-888
```
**Scopes:** `read`
**Use for:** Monitoring, dashboards, read-only scripts

### Development Key
```
dev-key-12345
```
**Scopes:** `read`, `write`
**Use for:** Development, build pipelines, automation

### Admin Key
```
admin-key-99999
```
**Scopes:** `read`, `write`, `admin`
**Use for:** Administrative tasks, maintenance, cleanup

---

## Default Users

Development environment includes default users:

### Admin User
- **Username:** `admin`
- **Password:** `admin123`
- **Scopes:** `read`, `write`, `admin`

### Regular User
- **Username:** `user`
- **Password:** `user123`
- **Scopes:** `read`, `write`

### Read-Only User
- **Username:** `readonly`
- **Password:** `readonly123`
- **Scopes:** `read`

**⚠️ Change these credentials in production!**

---

## Managing API Keys

### Creating API Keys

API keys can be created via the API (requires admin scope):

```bash
curl -X POST http://localhost:8080/users/{user_id}/tokens \
  -H "X-API-Key: admin-key-99999" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Pipeline Token",
    "scopes": ["read", "write"],
    "expires_in_days": 365
  }'
```

**Response:**
```json
{
  "token": "new-key-abc123def456",
  "name": "Pipeline Token",
  "scopes": ["read", "write"],
  "expires_at": "2027-02-14T17:30:00Z",
  "created_at": "2026-02-14T17:30:00Z"
}
```

### Listing API Keys

```bash
curl http://localhost:8080/users/{user_id}/tokens \
  -H "X-API-Key: admin-key-99999"
```

### Revoking API Keys

```bash
curl -X DELETE http://localhost:8080/users/{user_id}/tokens/{token_id} \
  -H "X-API-Key: admin-key-99999"
```

---

## Integration Examples

### Concourse CI Pipeline

```yaml
resources:
  - name: buildstate-api
    type: http-api
    source:
      uri: http://api.example.com
      headers:
        X-API-Key: ((buildstate-api-key))

jobs:
  - name: build-image
    plan:
      - task: create-build
        config:
          platform: linux
          run:
            path: /bin/bash
            args:
              - -c
              - |
                # Create build
                BUILD_ID=$(curl -X POST http://api.example.com/builds \
                  -H "X-API-Key: $API_KEY" \
                  -H "Content-Type: application/json" \
                  -d '{"project_id": "rhel-9", "platform_id": "aws"}' \
                  | jq -r '.id')
                
                # Update state
                curl -X POST http://api.example.com/builds/$BUILD_ID/state \
                  -H "X-API-Key: $API_KEY" \
                  -H "Content-Type: application/json" \
                  -d '{"state_code": 5, "status": "in_progress"}'
        params:
          API_KEY: ((buildstate-api-key))
```

### Python Script

```python
import os
import requests

API_URL = os.getenv("BUILDSTATE_API_URL", "http://localhost:8080")
API_KEY = os.getenv("BUILDSTATE_API_KEY")

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# List platforms
response = requests.get(f"{API_URL}/platforms/", headers=headers)
platforms = response.json()

# Create build
build_data = {
    "project_id": "rhel-9",
    "platform_id": "aws-commercial",
    "os_version_id": "rhel-9.3",
    "image_type_id": "base",
    "build_number": "2024.02.001"
}
response = requests.post(f"{API_URL}/builds", headers=headers, json=build_data)
build = response.json()
print(f"Created build: {build['id']}")
```

### Shell Script

```bash
#!/bin/bash
set -euo pipefail

API_URL="${BUILDSTATE_API_URL:-http://localhost:8080}"
API_KEY="${BUILDSTATE_API_KEY}"

# Function to call API
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3
    
    curl -s -X "$method" "$API_URL$endpoint" \
        -H "X-API-Key: $API_KEY" \
        -H "Content-Type: application/json" \
        ${data:+-d "$data"}
}

# Create build
BUILD_ID=$(api_call POST /builds '{
    "project_id": "rhel-9",
    "platform_id": "aws-commercial",
    "os_version_id": "rhel-9.3",
    "image_type_id": "base",
    "build_number": "2024.02.001"
}' | jq -r '.id')

echo "Created build: $BUILD_ID"

# Update state
api_call POST "/builds/$BUILD_ID/state" '{
    "state_code": 5,
    "status": "in_progress",
    "message": "Starting build"
}'
```

---

## Error Handling

### Authentication Errors

**No authentication provided:**
```http
HTTP/1.1 401 Unauthorized
```
```json
{
  "detail": "Authentication required. Use Bearer token or X-API-Key."
}
```

**Invalid API key:**
```http
HTTP/1.1 401 Unauthorized
```
```json
{
  "detail": "Invalid API key"
}
```

**Expired JWT token:**
```http
HTTP/1.1 401 Unauthorized
```
```json
{
  "detail": "Token has expired"
}
```

### Authorization Errors

**Insufficient permissions:**
```http
HTTP/1.1 403 Forbidden
```
```json
{
  "detail": "Write permission required"
}
```

or

```json
{
  "detail": "Admin permission required"
}
```

---

## Best Practices

### For Development

1. **Use separate keys for different environments**
   ```bash
   export BUILDSTATE_API_KEY_DEV="dev-key-12345"
   export BUILDSTATE_API_KEY_PROD="prod-key-secure-token"
   ```

2. **Store keys in environment variables**
   ```bash
   # .env file (never commit this!)
   BUILDSTATE_API_KEY=dev-key-12345
   ```

3. **Use the CLI for interactive work**
   ```bash
   bldst auth set-key dev-key-12345
   bldst platform list
   ```

### For Production

1. **Use secret management systems**
   - AWS Secrets Manager
   - HashiCorp Vault
   - Azure Key Vault
   - Kubernetes Secrets

2. **Rotate keys regularly**
   - Set expiration dates on API keys
   - Automate key rotation
   - Monitor key usage

3. **Use least-privilege principle**
   - Build pipelines: `read` + `write` scopes
   - Monitoring tools: `read` scope only
   - Admin tasks: `admin` scope (temporary)

4. **Audit API key usage**
   - Monitor API logs
   - Track which keys are used where
   - Revoke unused keys

5. **Enable HTTPS**
   - Never send API keys over unencrypted connections
   - Use TLS 1.2 or higher

### For CI/CD Pipelines

1. **Store keys as secrets**
   ```yaml
   # GitHub Actions
   - name: Call API
     env:
       API_KEY: ${{ secrets.BUILDSTATE_API_KEY }}
     run: |
       curl -H "X-API-Key: $API_KEY" $API_URL/builds
   ```

2. **Use dedicated pipeline keys**
   - One key per pipeline or service
   - Makes revocation easier
   - Better audit trail

3. **Implement retry logic**
   ```bash
   for i in {1..3}; do
     if curl -f -H "X-API-Key: $API_KEY" $API_URL/builds; then
       break
     fi
     sleep 5
   done
   ```

---

## Security Considerations

### API Key Security

- ✅ Store in environment variables or secret managers
- ✅ Use HTTPS in production
- ✅ Rotate keys periodically
- ✅ Use separate keys per environment
- ✅ Revoke keys when no longer needed
- ❌ Never commit keys to version control
- ❌ Never log API keys
- ❌ Never include keys in URLs
- ❌ Never expose keys in error messages

### JWT Token Security

- ✅ Short expiration times (1 hour default)
- ✅ Refresh tokens regularly
- ✅ Store tokens securely (httpOnly cookies for web)
- ✅ Validate tokens on every request
- ❌ Never store tokens in localStorage (XSS risk)
- ❌ Never send tokens in URLs
- ❌ Don't include sensitive data in token payload

### General Security

1. **Use HTTPS in production**
   - Prevents man-in-the-middle attacks
   - Protects credentials in transit

2. **Implement rate limiting**
   - Prevent brute force attacks
   - Protect against abuse

3. **Monitor authentication failures**
   - Detect unauthorized access attempts
   - Alert on suspicious activity

4. **Regular security audits**
   - Review active API keys
   - Check user permissions
   - Remove unused accounts

---

## Troubleshooting

### "Authentication required" error

**Cause:** No authentication provided

**Solution:**
```bash
# Add API key header
curl -H "X-API-Key: your-key" http://localhost:8080/platforms/

# Or use Bearer token
curl -H "Authorization: Bearer your-token" http://localhost:8080/platforms/
```

### "Invalid API key" error

**Cause:** API key is incorrect or revoked

**Solution:**
1. Verify the API key is correct
2. Check if key has been revoked
3. Request a new key from admin

### "Token has expired" error

**Cause:** JWT token has expired (default: 1 hour)

**Solution:**
```bash
# Get a new token
curl -X POST http://localhost:8080/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

### "Permission denied" errors

**Cause:** Insufficient scopes for the operation

**Solution:**
1. Check required scope for the endpoint
2. Request appropriate API key from admin
3. Verify user has correct permissions

---

## Migration Guide

### From Password to API Keys

If you're currently using username/password in scripts:

**Before:**
```bash
TOKEN=$(curl -X POST http://localhost:8080/token \
  -d "username=admin&password=admin123" | jq -r '.access_token')
curl -H "Authorization: Bearer $TOKEN" http://localhost:8080/platforms/
```

**After:**
```bash
# Much simpler!
curl -H "X-API-Key: dev-key-12345" http://localhost:8080/platforms/
```

**Benefits:**
- No token expiration handling
- Simpler code
- Better for automation
- No password exposure

---

## FAQ

**Q: Should I use API keys or JWT tokens?**
A: Use API keys for automation and scripts, JWT tokens for interactive use.

**Q: How long do JWT tokens last?**
A: 1 hour by default. Request a new token after expiration.

**Q: Can I use both authentication methods simultaneously?**
A: The API will check API key first, then bearer token. Use one method per request.

**Q: How do I create a new API key?**
A: Use the `/users/{user_id}/tokens` endpoint with admin credentials.

**Q: Can I revoke an API key?**
A: Yes, use `DELETE /users/{user_id}/tokens/{token_id}` with admin credentials.

**Q: What happens when I delete a user?**
A: All their API keys are automatically revoked.

**Q: How do I check what scopes my API key has?**
A: Contact your administrator or check the API key listing.

---

## Additional Resources

- [API Reference](api-reference.md) - Complete endpoint documentation
- [CLI Documentation](../cli/README.md) - CLI usage and configuration
- [Deployment Guide](README.md) - Production deployment setup
