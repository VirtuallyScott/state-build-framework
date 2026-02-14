# Access Credentials and URLs

Quick reference for development access credentials and URLs.

## ⚠️ WARNING

**These are development/test credentials only. DO NOT use in production!**

---

## 🌐 API URLs

### Base URL
```
http://localhost:8080
```

### Interactive Documentation
```
Swagger UI:  http://localhost:8080/docs
ReDoc:       http://localhost:8080/redoc
OpenAPI:     http://localhost:8080/openapi.json
```

### Health Endpoints
```
Health:      http://localhost:8080/health
Readiness:   http://localhost:8080/ready
Status:      http://localhost:8080/status
```

### Authentication
```
Token:       POST http://localhost:8080/token
IDM Auth:    POST http://localhost:8080/auth/idm
```

### Main Resources
```
Platforms:   http://localhost:8080/platforms/
OS Versions: http://localhost:8080/os_versions/
Image Types: http://localhost:8080/image_types/
Projects:    http://localhost:8080/projects/
Builds:      http://localhost:8080/builds
Users:       http://localhost:8080/users
Dashboard:   http://localhost:8080/dashboard/summary
```

---

## 🔑 API Keys

### Read-Only Key
```
readonly-key-888
```
**Scopes:** `read`  
**Use for:** Monitoring, dashboards, viewing resources

### Development Key
```
dev-key-12345
```
**Scopes:** `read`, `write`  
**Use for:** Development, build pipelines, creating/updating resources

### Admin Key
```
admin-key-99999
```
**Scopes:** `read`, `write`, `admin`  
**Use for:** Administrative tasks, deleting resources, user management

---

## 👤 User Credentials

### Admin User
```
Username: admin
Password: admin123
Scopes:   read, write, admin
```

### Regular User
```
Username: user
Password: user123
Scopes:   read, write
```

### Read-Only User
```
Username: readonly
Password: readonly123
Scopes:   read
```

---

## 📋 Quick Test Commands

### Using API Keys

```bash
# Set API key
export API_KEY="dev-key-12345"
export API_URL="http://localhost:8080"

# List platforms
curl -H "X-API-Key: $API_KEY" $API_URL/platforms/

# Create platform
curl -X POST "$API_URL/platforms/" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-platform",
    "cloud_provider": "aws",
    "region": "us-east-1"
  }'

# Get platform
curl -H "X-API-Key: $API_KEY" "$API_URL/platforms/test-platform"

# Delete platform (requires admin key)
export API_KEY="admin-key-99999"
curl -X DELETE "$API_URL/platforms/test-platform" \
  -H "X-API-Key: $API_KEY"
```

### Using JWT Tokens

```bash
# Get token
TOKEN=$(curl -X POST http://localhost:8080/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" \
  | jq -r '.access_token')

# Use token
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8080/platforms/
```

### Using CLI

```bash
# Configure CLI
bldst config set-url http://localhost:8080
bldst auth set-key dev-key-12345

# Test
bldst platform list
bldst os-version list
bldst image-type list
```

---

## 🔧 CLI Configuration

### Quick Setup
```bash
# Set URL
bldst config set-url http://localhost:8080

# Set API key (choose one based on permission needed)
bldst auth set-key readonly-key-888     # Read-only
bldst auth set-key dev-key-12345        # Read + Write
bldst auth set-key admin-key-99999      # Full admin

# Or login with username/password
bldst auth login
# Username: admin
# Password: admin123
```

### Environment Variables
```bash
export BUILDSTATE_API_URL="http://localhost:8080"
export BUILDSTATE_API_KEY="dev-key-12345"
```

---

## 🧪 Testing Authorization

### Test Read-Only Access
```bash
# Set read-only key
bldst auth set-key readonly-key-888

# These should work
bldst platform list          # ✓ Works
bldst os-version list        # ✓ Works
bldst build list             # ✓ Works

# These should fail
bldst platform create --name test  # ✗ Permission denied (needs write)
bldst platform delete test         # ✗ Permission denied (needs admin)
```

### Test Write Access
```bash
# Set write key
bldst auth set-key dev-key-12345

# These should work
bldst platform list                           # ✓ Works (read)
bldst platform create --name test --cloud-provider aws --region us-east-1  # ✓ Works (write)
bldst platform update test --region us-west-2 # ✓ Works (write)

# This should fail
bldst platform delete test   # ✗ Permission denied (needs admin)
```

### Test Admin Access
```bash
# Set admin key
bldst auth set-key admin-key-99999

# Everything should work
bldst platform list          # ✓ Works (read)
bldst platform create ...    # ✓ Works (write)
bldst platform delete test   # ✓ Works (admin)
```

---

## 🐳 Docker Services

### Service URLs (when using docker compose)

```
Nginx Load Balancer:  http://localhost:8080
API Instance 1:       http://localhost:8001
API Instance 2:       http://localhost:8002
API Instance 3:       http://localhost:8003
PostgreSQL:           localhost:5432
Redis:                localhost:6379
```

### Database Credentials
```
Database: buildstate
Username: buildstate
Password: buildstate123
Host:     localhost
Port:     5432
```

### Redis
```
Host: localhost
Port: 6379
No password (development)
```

---

## 📊 Example Workflow

### Complete Build Creation Flow

```bash
# 1. Configure and authenticate
export API_KEY="dev-key-12345"
export API_URL="http://localhost:8080"

# 2. Create a project
PROJECT_ID=$(curl -s -X POST "$API_URL/projects/" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "test-project", "description": "Test project"}' \
  | jq -r '.id')

echo "Created project: $PROJECT_ID"

# 3. Create a build
BUILD_ID=$(curl -s -X POST "$API_URL/builds" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"project_id\": \"$PROJECT_ID\",
    \"platform_id\": \"aws-commercial\",
    \"os_version_id\": \"rhel-9.3\",
    \"image_type_id\": \"base\",
    \"build_number\": \"test-001\"
  }" | jq -r '.id')

echo "Created build: $BUILD_ID"

# 4. Update build state
curl -X POST "$API_URL/builds/$BUILD_ID/state" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "state_code": 25,
    "status": "in_progress",
    "message": "Installing packages"
  }'

# 5. Get build status
curl -s "$API_URL/builds/$BUILD_ID/state" \
  -H "X-API-Key: $API_KEY" | jq

# 6. View dashboard
curl -s "$API_URL/dashboard/summary" \
  -H "X-API-Key: $API_KEY" | jq
```

---

## 🔒 Security Reminders

### DO NOT in Production
- ❌ Do not use these credentials in production
- ❌ Do not commit credentials to version control
- ❌ Do not expose API without HTTPS
- ❌ Do not use default passwords
- ❌ Do not share API keys in logs or error messages

### DO in Production
- ✅ Change all passwords and API keys
- ✅ Use HTTPS/TLS for all connections
- ✅ Store credentials in secret managers (Vault, AWS Secrets Manager, etc.)
- ✅ Rotate keys regularly
- ✅ Use least-privilege access (read-only where possible)
- ✅ Monitor authentication failures
- ✅ Enable audit logging

---

## 📚 Additional Resources

- [API Reference](api_service/docs/API_REFERENCE.md) - Complete endpoint documentation
- [Authentication Guide](api_service/docs/AUTHENTICATION.md) - Detailed security guide
- [CLI Documentation](buildstate_cli/README.md) - CLI usage
- [Main README](README.md) - Project overview

---

**Last Updated**: February 14, 2026  
**Environment**: Development/Testing Only
