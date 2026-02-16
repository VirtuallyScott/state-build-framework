# BuildState CLI - Quick Start Guide

The BuildState CLI provides a complete interface to manage your build infrastructure with proper authentication and authorization.

## Installation

```bash
cd bldst_cli
pip install -e .
```

## Configuration

### 1. Set API URL
```bash
bldst config set-url http://localhost:8080
```

### 2. Configure Authentication

**Option A: API Key (recommended for automation)**
```bash
bldst config set-key dev-key-12345
```

**Option B: JWT Token (for interactive use)**
```bash
bldst auth login
# Enter username and password when prompted
```

## Usage Examples

### Platform Management

**List all platforms:**
```bash
bldst platform list
```

**Create a platform (requires write permission):**
```bash
bldst platform create \
  --name "my-aws-platform" \
  --cloud-provider "aws" \
  --region "us-east-1"
```

**Get platform details:**
```bash
bldst platform get <platform-id>
```

**Update a platform (requires write permission):**
```bash
bldst platform update <platform-id> \
  --region "us-west-2"
```

**Delete a platform (requires admin permission):**
```bash
bldst platform delete <platform-id>
```

### OS Version Management

**List all OS versions:**
```bash
bldst os-version list
```

**Create an OS version (requires write permission):**
```bash
bldst os-version create \
  --name "Red Hat Enterprise Linux" \
  --version "9.3"
```

**Update an OS version (requires write permission):**
```bash
bldst os-version update <os-version-id> \
  --version "9.4"
```

**Delete an OS version (requires admin permission):**
```bash
bldst os-version delete <os-version-id>
```

### Image Type Management

**List all image types:**
```bash
bldst image-type list
```

**Create an image type (requires write permission):**
```bash
bldst image-type create \
  --name "kubernetes-node" \
  --description "Kubernetes worker node image"
```

**Update an image type (requires write permission):**
```bash
bldst image-type update <image-type-id> \
  --description "Updated description"
```

**Delete an image type (requires admin permission):**
```bash
bldst image-type delete <image-type-id>
```

### Project Management

**List all projects:**
```bash
bldst project list
```

**Create a project (requires write permission):**
```bash
bldst project create \
  --name "my-project" \
  --description "My build project"
```

### Build Management

**List all builds:**
```bash
bldst build list
```

**Get build details:**
```bash
bldst build get <build-id>
```

**Get build states:**
```bash
bldst build states <build-id>
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
bldst platform list --output json
```

## Health Check

Verify API connectivity:

```bash
bldst health check
```

## Configuration Management

**View current configuration:**
```bash
bldst config show
```

**Clear stored credentials:**
```bash
bldst auth logout        # Clear JWT token
bldst auth clear-key     # Clear API key
```

## Examples

### Complete Workflow

```bash
# 1. Configure CLI
bldst config set-url http://localhost:8080
bldst config set-key dev-key-12345

# 2. List existing resources
bldst platform list
bldst os-version list
bldst image-type list

# 3. Create new resources
PLATFORM_ID=$(bldst platform create \
  --name "production-aws" \
  --cloud-provider "aws" \
  --region "us-east-1" \
  --output json | jq -r '.id')

OS_ID=$(bldst os-version create \
  --name "Ubuntu" \
  --version "22.04" \
  --output json | jq -r '.id')

IMAGE_ID=$(bldst image-type create \
  --name "web-server" \
  --description "Nginx web server" \
  --output json | jq -r '.id')

# 4. Update resources
bldst platform update $PLATFORM_ID --region "us-west-2"

# 5. Soft delete (requires admin key)
bldst config set-key admin-key-99999
bldst platform delete $PLATFORM_ID
```

### Automated Script Example

```bash
#!/bin/bash
# Setup API key from environment
export BUILDSTATE_API_KEY="${BUILDSTATE_API_KEY}"

# Configure CLI
bldst config set-url "${BUILDSTATE_API_URL}"
bldst config set-key "${BUILDSTATE_API_KEY}"

# List platforms and filter
bldst platform list --output json | \
  jq -r '.[] | select(.cloud_provider == "aws") | .name'
```

## Troubleshooting

**"Authentication failed" error:**
- Verify API URL is correct: `bldst config show`
- Check API key is valid: `bldst config set-key <your-key>`
- Test API connectivity: `bldst health check`

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
bldst auth login
# Username: admin
# Password: admin123

# Use the CLI (JWT token is automatically used)
bldst platform list

# Logout when done
bldst auth logout
```

### Scripting with the CLI

The CLI is designed for automation:

```bash
# Get all platforms and process with jq
bldst platform list --output json | \
  jq -r '.[] | "\(.name): \(.cloud_provider) (\(.region))"'

# Check if specific platform exists
if bldst platform get "my-platform" > /dev/null 2>&1; then
  echo "Platform exists"
else
  echo "Platform not found"
fi
```

## Additional Resources

- API Documentation: http://localhost:8080/docs
- GitHub Repository: [Your repo URL]
- Issue Tracker: [Your issue tracker URL]
