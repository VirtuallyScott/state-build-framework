# BuildState CLI - Quick Start Guide

The BuildState CLI provides a complete interface to manage your build infrastructure with proper authentication and authorization.

## Installation

```bash
cd buildstate_cli
pip install -e .
```

## Configuration

### 1. Set API URL
```bash
buildctl config set-url http://localhost:8080
```

### 2. Configure Authentication

**Option A: API Key (recommended for automation)**
```bash
buildctl config set-key dev-key-12345
```

**Option B: JWT Token (for interactive use)**
```bash
buildctl auth login
# Enter username and password when prompted
```

## Usage Examples

### Platform Management

**List all platforms:**
```bash
buildctl platform list
```

**Create a platform (requires write permission):**
```bash
buildctl platform create \
  --name "my-aws-platform" \
  --cloud-provider "aws" \
  --region "us-east-1"
```

**Get platform details:**
```bash
buildctl platform get <platform-id>
```

**Update a platform (requires write permission):**
```bash
buildctl platform update <platform-id> \
  --region "us-west-2"
```

**Delete a platform (requires admin permission):**
```bash
buildctl platform delete <platform-id>
```

### OS Version Management

**List all OS versions:**
```bash
buildctl os-version list
```

**Create an OS version (requires write permission):**
```bash
buildctl os-version create \
  --name "Red Hat Enterprise Linux" \
  --version "9.3"
```

**Update an OS version (requires write permission):**
```bash
buildctl os-version update <os-version-id> \
  --version "9.4"
```

**Delete an OS version (requires admin permission):**
```bash
buildctl os-version delete <os-version-id>
```

### Image Type Management

**List all image types:**
```bash
buildctl image-type list
```

**Create an image type (requires write permission):**
```bash
buildctl image-type create \
  --name "kubernetes-node" \
  --description "Kubernetes worker node image"
```

**Update an image type (requires write permission):**
```bash
buildctl image-type update <image-type-id> \
  --description "Updated description"
```

**Delete an image type (requires admin permission):**
```bash
buildctl image-type delete <image-type-id>
```

### Project Management

**List all projects:**
```bash
buildctl project list
```

**Create a project (requires write permission):**
```bash
buildctl project create \
  --name "my-project" \
  --description "My build project"
```

### Build Management

**List all builds:**
```bash
buildctl build list
```

**Get build details:**
```bash
buildctl build get <build-id>
```

**Get build states:**
```bash
buildctl build states <build-id>
```

## Authorization Levels

The CLI supports three authorization levels via API tokens:

1. **Read** - View resources
   - List and get operations
   
2. **Write** - Create and update resources
   - Includes read permissions
   - Create and update operations
   
3. **Admin** - Full access including delete
   - Includes read and write permissions
   - Delete operations (soft delete)

## API Keys

Three test API keys are available:

- `dev-key-12345` - read + write permissions
- `admin-key-99999` - read + write + admin permissions
- `readonly-key-888` - read-only permissions

## Output Formats

By default, output is formatted as a table. Use `--output json` for JSON output:

```bash
buildctl platform list --output json
```

## Health Check

Verify API connectivity:

```bash
buildctl health check
```

## Configuration Management

**View current configuration:**
```bash
buildctl config show
```

**Clear stored credentials:**
```bash
buildctl auth logout        # Clear JWT token
buildctl auth clear-key     # Clear API key
```

## Examples

### Complete Workflow

```bash
# 1. Configure CLI
buildctl config set-url http://localhost:8080
buildctl config set-key dev-key-12345

# 2. List existing resources
buildctl platform list
buildctl os-version list
buildctl image-type list

# 3. Create new resources
PLATFORM_ID=$(buildctl platform create \
  --name "production-aws" \
  --cloud-provider "aws" \
  --region "us-east-1" \
  --output json | jq -r '.id')

OS_ID=$(buildctl os-version create \
  --name "Ubuntu" \
  --version "22.04" \
  --output json | jq -r '.id')

IMAGE_ID=$(buildctl image-type create \
  --name "web-server" \
  --description "Nginx web server" \
  --output json | jq -r '.id')

# 4. Update resources
buildctl platform update $PLATFORM_ID --region "us-west-2"

# 5. Soft delete (requires admin key)
buildctl config set-key admin-key-99999
buildctl platform delete $PLATFORM_ID
```

### Automated Script Example

```bash
#!/bin/bash
# Setup API key from environment
export BUILDSTATE_API_KEY="${BUILDSTATE_API_KEY}"

# Configure CLI
buildctl config set-url "${BUILDSTATE_API_URL}"
buildctl config set-key "${BUILDSTATE_API_KEY}"

# List platforms and filter
buildctl platform list --output json | \
  jq -r '.[] | select(.cloud_provider == "aws") | .name'
```

## Troubleshooting

**"Authentication failed" error:**
- Verify API URL is correct: `buildctl config show`
- Check API key is valid: `buildctl config set-key <your-key>`
- Test API connectivity: `buildctl health check`

**"Permission denied" errors:**
- Check your API token has appropriate scopes
- Write operations require `write` scope
- Delete operations require `admin` scope

**"Connection refused" error:**
- Ensure the API is running: `docker compose ps`
- Verify the API URL is accessible: `curl http://localhost:8080/health`

## Advanced Features

### Using JWT Tokens

For interactive use, you can use JWT tokens instead of API keys:

```bash
# Login with username/password
buildctl auth login
# Username: admin
# Password: admin123

# Use the CLI (JWT token is automatically used)
buildctl platform list

# Logout when done
buildctl auth logout
```

### Scripting with the CLI

The CLI is designed for automation:

```bash
# Get all platforms and process with jq
buildctl platform list --output json | \
  jq -r '.[] | "\(.name): \(.cloud_provider) (\(.region))"'

# Check if specific platform exists
if buildctl platform get "my-platform" > /dev/null 2>&1; then
  echo "Platform exists"
else
  echo "Platform not found"
fi
```

## Additional Resources

- API Documentation: http://localhost:8080/docs
- GitHub Repository: [Your repo URL]
- Issue Tracker: [Your issue tracker URL]
