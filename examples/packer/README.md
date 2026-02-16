# Packer Templates for Build State Tracking

This directory contains Packer HCL2 templates that integrate with the Build State API using the `bldst` CLI.

## Directory Structure

```
packer/
├── README.md                           # This file
├── templates/                          # Packer HCL2 templates
│   ├── rhel-8-base.pkr.hcl            # Simple RHEL 8 base image
│   ├── ubuntu-22-04-base.pkr.hcl      # Ubuntu 22.04 base image
│   ├── multi-cloud-rhel8.pkr.hcl      # Multi-cloud template (AWS, Azure, GCP)
│   └── resumable-build.pkr.hcl        # Template with checkpoint/resume support
└── scripts/                            # Provisioning and helper scripts
    ├── common/                         # Scripts used across templates
    │   ├── install-bldst-cli.sh       # Install bldst CLI in image
    │   ├── update-build-state.sh      # Helper to update state during build
    │   └── system-hardening.sh        # Security hardening
    ├── rhel/                           # RHEL-specific scripts
    │   ├── subscription-manager.sh    # Register with Red Hat
    │   └── yum-repos.sh               # Configure repositories
    └── ubuntu/                         # Ubuntu-specific scripts
        └── apt-setup.sh               # Configure APT repositories
```

## Prerequisites

### 1. Packer Installation
Install Packer 1.8.0 or later:

```bash
# macOS
brew install packer

# Linux
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
sudo apt-get update && sudo apt-get install packer

# Verify
packer version
```

### 2. Cloud Provider Credentials

#### AWS
```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

#### Azure
```bash
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
export AZURE_TENANT_ID="your-tenant-id"
```

#### GCP
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
export GCP_PROJECT_ID="your-project-id"
```

### 3. Build State API Access
```bash
export BLDST_API_URL="https://buildstate-api.example.com"
export BLDST_API_KEY="your-api-key"
```

## Quick Start

### 1. Initialize Packer
```bash
cd templates
packer init rhel-8-base.pkr.hcl
```

### 2. Validate Template
```bash
packer validate \
  -var "bldst_api_url=$BLDST_API_URL" \
  -var "bldst_api_key=$BLDST_API_KEY" \
  -var "build_uuid=test-uuid" \
  rhel-8-base.pkr.hcl
```

### 3. Build Image
```bash
# Create build record first (get UUID)
BUILD_UUID=$(bldst build create \
  --build-number "rhel8-$(date +%s)" \
  --project-id "$PROJECT_ID" \
  --platform-id "$PLATFORM_ID" \
  --os-version-id "$OS_VERSION_ID" \
  --image-type-id "$IMAGE_TYPE_ID" \
  --output json | jq -r '.id')

# Run Packer with build UUID
packer build \
  -var "bldst_api_url=$BLDST_API_URL" \
  -var "bldst_api_key=$BLDST_API_KEY" \
  -var "build_uuid=$BUILD_UUID" \
  rhel-8-base.pkr.hcl
```

## Templates

### RHEL 8 Base Image
[`templates/rhel-8-base.pkr.hcl`](templates/rhel-8-base.pkr.hcl)

Builds a hardened RHEL 8 base image for AWS with:
- Build state tracking
- Security hardening
- Minimal package set
- Cloud-init configured

### Ubuntu 22.04 Base Image
[`templates/ubuntu-22-04-base.pkr.hcl`](templates/ubuntu-22-04-base.pkr.hcl)

Builds an Ubuntu 22.04 LTS image with:
- Build state tracking
- Automatic security updates
- Docker pre-installed
- SSH hardening

### Multi-Cloud RHEL 8
[`templates/multi-cloud-rhel8.pkr.hcl`](templates/multi-cloud-rhel8.pkr.hcl)

Single template that builds for AWS, Azure, and GCP:
- Parallel builds across clouds
- Cloud-specific optimizations
- Unified base configuration
- Independent state tracking per platform

### Resumable Build
[`templates/resumable-build.pkr.hcl`](templates/resumable-build.pkr.hcl)

Advanced template with checkpoint/resume support:
- Artifact registration at key stages
- Variable storage for resume context
- Failure recovery
- Incremental builds

## Integration Patterns

### Pattern 1: CI/CD Managed (Recommended)

Let your CI/CD pipeline manage the build state:

```yaml
# Concourse/Jenkins creates build record
BUILD_UUID=$(bldst build create ...)

# Pass to Packer as variable
packer build -var "build_uuid=$BUILD_UUID" template.pkr.hcl

# CI/CD completes the build
bldst build add-state "$BUILD_UUID" --state 100 --status "Complete"
```

**Advantages:**
- Clear separation of concerns
- Pipeline controls state progression
- Easy to add pre/post build steps

### Pattern 2: Packer Self-Managed

Packer provisioners handle all state updates:

```hcl
provisioner "shell" {
  inline = [
    "bldst build add-state ${var.build_uuid} --state 25 --status 'Starting OS configuration'"
  ]
}
```

**Advantages:**
- Self-contained templates
- Detailed build phase tracking
- Works standalone outside CI/CD

### Pattern 3: Hybrid Approach

CI/CD handles initialization, Packer updates during build:

```yaml
# CI/CD: Initialize
BUILD_UUID=$(bldst build create ...)

# Packer: Update states during provisioning
packer build -var "build_uuid=$BUILD_UUID" ...

# CI/CD: Finalize
bldst build add-state "$BUILD_UUID" --state 100
```

**Advantages:**
- Best of both worlds
- Flexible state granularity
- Clearer failure attribution

## Best Practices

### 1. Use Build Variables File
Create `builds.auto.pkrvars.hcl`:

```hcl
bldst_api_url = "https://buildstate-api.example.com"
build_prefix  = "prod"
aws_region    = "us-east-1"
```

### 2. Template Variables for Flexibility
```hcl
variable "build_uuid" {
  type        = string
  description = "Build State API build UUID for tracking"
}

variable "bldst_api_url" {
  type        = string
  description = "Build State API endpoint URL"
}
```

### 3. Error Handling in Provisioners
```hcl
provisioner "shell" {
  inline = [
    "set -e",  # Exit on error
    "bldst build add-state ${var.build_uuid} --state 30 || echo 'State update failed'"
  ]
}
```

### 4. Use Post-Processors for Artifacts
```hcl
post-processor "manifest" {
  output     = "manifest.json"
  strip_path = true
}

post-processor "shell-local" {
  inline = [
    "AMI_ID=$(jq -r '.builds[0].artifact_id' manifest.json | cut -d: -f2)",
    "echo $AMI_ID > ami-id.txt"
  ]
}
```

### 5. Sensitive Variables
Never commit secrets:

```hcl
variable "bldst_api_key" {
  type      = string
  sensitive = true
}
```

Pass via environment or CLI:
```bash
export PKR_VAR_bldst_api_key="$BLDST_API_KEY"
```

## Troubleshooting

### CLI Not Found in Build
Install in provisioner:
```hcl
provisioner "shell" {
  inline = [
    "pip3 install buildstate-cli",
    "bldst --version"
  ]
}
```

### API Connection Timeout
Increase timeout or check network:
```hcl
provisioner "shell" {
  environment_vars = [
    "BLDST_TIMEOUT=60"
  ]
}
```

### Build UUID Not Passed
Verify variable is set:
```hcl
provisioner "shell" {
  inline = [
    "echo 'Build UUID: ${var.build_uuid}'"
  ]
}
```

## Resources

- **Packer Documentation**: https://www.packer.io/docs
- **HCL2 Syntax**: https://www.packer.io/guides/hcl
- **Build State API**: [API Reference](../../api_service/docs/API_REFERENCE.md)
- **CLI Guide**: [bldst CLI](../../buildstate_cli/README.md)

## Contributing

To add new templates:
1. Use HCL2 format (`.pkr.hcl`)
2. Include comprehensive comments
3. Add variables for all configurable values
4. Integrate with bldst CLI for state tracking
5. Test across target platforms
6. Update this README
7. Submit pull request
