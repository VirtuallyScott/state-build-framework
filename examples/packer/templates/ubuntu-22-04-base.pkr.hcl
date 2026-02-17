##############################################################################
# Ubuntu 22.04 LTS Base Image Template
##############################################################################
#
# This Packer template builds a hardened Ubuntu 22.04 LTS base image for
# AWS, Azure, and GCP with full Build State API integration.
#
# Features:
# - Multi-cloud support (AWS, Azure, GCP)
# - Security hardening (CIS benchmarks)
# - Cloud-init configuration
# - System updates and essential tools
# - Build state tracking at every phase
#
# Usage:
#   packer init ubuntu-22-04-base.pkr.hcl
#   packer build -var-file=vars/production.pkrvars.hcl ubuntu-22-04-base.pkr.hcl
#
# Environment Variables Required:
#   BLDST_API_URL      - Build State API endpoint
#   BLDST_API_KEY      - API authentication key
#   PROJECT_ID         - Build State project ID
#   BUILD_ID           - Build State build ID (or auto-generated)

##############################################################################
# Packer Configuration
##############################################################################

packer {
  required_version = ">= 1.9.0"
  
  required_plugins {
    amazon = {
      version = ">= 1.2.0"
      source  = "github.com/hashicorp/amazon"
    }
    azure = {
      version = ">= 1.4.0"
      source  = "github.com/hashicorp/azure"
    }
    googlecompute = {
      version = ">= 1.1.0"
      source  = "github.com/hashicorp/googlecompute"
    }
  }
}

##############################################################################
# Variable Definitions
##############################################################################

# Build State API Configuration
variable "bldst_api_url" {
  type        = string
  description = "Build State API endpoint URL"
  default     = env("BLDST_API_URL")
}

variable "bldst_api_key" {
  type        = string
  description = "Build State API key for authentication"
  sensitive   = true
  default     = env("BLDST_API_KEY")
}

variable "project_id" {
  type        = string
  description = "Build State project ID"
  default     = env("PROJECT_ID")
}

variable "build_id" {
  type        = string
  description = "Build State build ID (leave empty to auto-generate)"
  default     = env("BUILD_ID")
}

# Image Configuration
variable "image_version" {
  type        = string
  description = "Version tag for the image"
  default     = "1.0.0"
}

variable "os_version" {
  type        = string
  description = "Ubuntu version"
  default     = "22.04"
}

variable "target_clouds" {
  type        = list(string)
  description = "List of cloud providers to build for"
  default     = ["aws"]
  # Valid values: aws, azure, gcp
}

# AWS Configuration
variable "aws_region" {
  type        = string
  description = "AWS region for image build"
  default     = "us-east-1"
}

variable "aws_instance_type" {
  type        = string
  description = "EC2 instance type for build"
  default     = "t3.medium"
}

variable "aws_vpc_id" {
  type        = string
  description = "VPC ID to launch instance in"
  default     = ""
}

variable "aws_subnet_id" {
  type        = string
  description = "Subnet ID to launch instance in"
  default     = ""
}

# Azure Configuration
variable "azure_location" {
  type        = string
  description = "Azure region for image build"
  default     = "East US"
}

variable "azure_resource_group" {
  type        = string
  description = "Azure resource group for managed images"
  default     = "packer-images-rg"
}

variable "azure_subscription_id" {
  type        = string
  description = "Azure subscription ID"
  default     = env("ARM_SUBSCRIPTION_ID")
}

# GCP Configuration
variable "gcp_project_id" {
  type        = string
  description = "GCP project ID"
  default     = env("GCP_PROJECT_ID")
}

variable "gcp_zone" {
  type        = string
  description = "GCP zone for image build"
  default     = "us-central1-a"
}

variable "gcp_machine_type" {
  type        = string
  description = "GCP machine type for build"
  default     = "n1-standard-2"
}

# Build Configuration
variable "ssh_username" {
  type        = string
  description = "SSH username for provisioning"
  default     = "ubuntu"
}

##############################################################################
# Local Variables
##############################################################################

locals {
  # Timestamp for unique naming
  timestamp = formatdate("YYYYMMDD-hhmm", timestamp())
  
  # Image naming
  image_name = "ubuntu-${var.os_version}-base-${var.image_version}-${local.timestamp}"
  
  # Tags common to all clouds
  common_tags = {
    Name          = local.image_name
    OS            = "Ubuntu"
    OSVersion     = var.os_version
    ImageVersion  = var.image_version
    BuildDate     = local.timestamp
    ManagedBy     = "Packer"
    BuildStateAPI = "enabled"
  }
}

##############################################################################
# Data Sources
##############################################################################

# Find latest Ubuntu 22.04 LTS AMI (AWS)
data "amazon-ami" "ubuntu" {
  filters = {
    virtualization-type = "hvm"
    name                = "ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"
    root-device-type    = "ebs"
  }
  owners      = ["099720109477"] # Canonical
  most_recent = true
  region      = var.aws_region
}

##############################################################################
# AWS Builder
##############################################################################

source "amazon-ebs" "ubuntu" {
  # Only build if 'aws' is in target_clouds list
  # In Packer, we use -only=amazon-ebs.ubuntu to control this
  
  # Instance Configuration
  ami_name      = local.image_name
  instance_type = var.aws_instance_type
  region        = var.aws_region
  source_ami    = data.amazon-ami.ubuntu.id
  
  # Network Configuration  
  vpc_id                      = var.aws_vpc_id
  subnet_id                   = var.aws_subnet_id
  associate_public_ip_address = true
  
  # SSH Configuration
  ssh_username = var.ssh_username
  ssh_timeout  = "10m"
  
  # AMI Configuration
  ami_description = "Ubuntu ${var.os_version} LTS base image - version ${var.image_version}"
  ami_regions     = [var.aws_region]
  
  # Snapshot Configuration
  snapshot_tags = merge(
    local.common_tags,
    {
      SnapshotType = "root-volume"
    }
  )
  
  # Tags
  tags = merge(
    local.common_tags,
    {
      CloudProvider = "AWS"
      BaseAMI       = data.amazon-ami.ubuntu.id
    }
  )
  
  # Launch configuration
  run_tags = {
    Name        = "Packer Builder - ${local.image_name}"
    PackerBuild = "true"
  }
}

##############################################################################
# Azure Builder
##############################################################################

source "azure-arm" "ubuntu" {
  # Authentication (using environment variables)
  subscription_id = var.azure_subscription_id
  
  # Image Source
  os_type         = "Linux"
  image_publisher = "Canonical"
  image_offer     = "0001-com-ubuntu-server-jammy"
  image_sku       = "22_04-lts-gen2"
  
  # Build Configuration
  location = var.azure_location
  vm_size  = "Standard_D2s_v3"
  
  # Managed Image Output
  managed_image_name                = local.image_name
  managed_image_resource_group_name = var.azure_resource_group
  
  # Temporary Resource Configuration
  build_resource_group_name = "${var.azure_resource_group}-build"
  
  # Azure Tags
  azure_tags = merge(
    local.common_tags,
    {
      CloudProvider = "Azure"
    }
  )
}

##############################################################################
# GCP Builder
##############################################################################

source "googlecompute" "ubuntu" {
  # Authentication (using environment variables or application default credentials)
  project_id = var.gcp_project_id
  
  # Image Source
  source_image_family = "ubuntu-2204-lts"
  
  # Build Configuration
  zone         = var.gcp_zone
  machine_type = var.gcp_machine_type
  
  # Image Output
  image_name        = local.image_name
  image_description = "Ubuntu ${var.os_version} LTS base image - version ${var.image_version}"
  image_family      = "ubuntu-2204-base"
  
  # Disk Configuration
  disk_size = 20
  disk_type = "pd-ssd"
  
  # SSH Configuration
  ssh_username = var.ssh_username
  
  # Labels
  image_labels = {
    os            = "ubuntu"
    os_version    = replace(var.os_version, ".", "-")
    image_version = replace(var.image_version, ".", "-")
    build_date    = local.timestamp
    managed_by    = "packer"
  }
}

##############################################################################
# Build Definition
##############################################################################

build {
  # Define which sources to use
  sources = [
    "source.amazon-ebs.ubuntu",
    "source.azure-arm.ubuntu",
    "source.googlecompute.ubuntu"
  ]
  
  ##############################################################################
  # Phase 1: Initialize Build State
  ##############################################################################
  
  provisioner "shell" {
    inline = [
      "echo '==> Phase 1: Initializing Build State API tracking'",
      "export DEBIAN_FRONTEND=noninteractive",
      "",
      "# Install bldst CLI",
      "sudo apt-get update -qq",
      "sudo apt-get install -y -qq python3-pip",
      "sudo pip3 install --quiet buildstate-cli",
      "",
      "# Configure bldst",
      "export BLDST_API_URL='${var.bldst_api_url}'",
      "export BLDST_API_KEY='${var.bldst_api_key}'",
      "",
      "# Initialize or continue existing build",
      "if [ -n '${var.build_id}' ]; then",
      "  echo 'Using existing build ID: ${var.build_id}'",
      "  BUILD_ID='${var.build_id}'",
      "else",
      "  echo 'Creating new build...'",
      "  BUILD_ID=$(bldst builds create \\",
      "    --project-id '${var.project_id}' \\",
      "    --image-type base \\",
      "    --os-distribution ubuntu \\",
      "    --os-version '${var.os_version}' \\",
      "    --format json | jq -r '.build_id')",
      "  echo \"Created build ID: $BUILD_ID\"",
      "fi",
      "",
      "# Store build ID for subsequent provisioners",
      "echo \"$BUILD_ID\" | sudo tee /tmp/build_id",
      "",
      "# Update build state to PROVISIONING",
      "bldst builds update-state \\",
      "  --build-id \"$BUILD_ID\" \\",
      "  --state-code PROVISIONING \\",
      "  --message 'Starting Ubuntu 22.04 base image provisioning'",
      "",
      "echo '✓ Build state tracking initialized'"
    ]
  }
  
  ##############################################################################
  # Phase 2: System Updates and Base Packages
  ##############################################################################
  
  provisioner "shell" {
    inline = [
      "echo '==> Phase 2: Updating system packages'",
      "export DEBIAN_FRONTEND=noninteractive",
      "",
      "# Update build state",
      "BUILD_ID=$(cat /tmp/build_id)",
      "export BLDST_API_URL='${var.bldst_api_url}'",
      "export BLDST_API_KEY='${var.bldst_api_key}'",
      "",
      "bldst builds update-state \\",
      "  --build-id \"$BUILD_ID\" \\",
      "  --state-code PROVISIONING \\",
      "  --message 'Installing system updates and base packages'",
      "",
      "# Update package lists",
      "sudo apt-get update",
      "",
      "# Upgrade all packages",
      "sudo apt-get upgrade -y",
      "",
      "# Install essential packages",
      "sudo apt-get install -y \\",
      "  curl \\",
      "  wget \\",
      "  vim \\",
      "  git \\",
      "  jq \\",
      "  unzip \\",
      "  htop \\",
      "  netcat \\",
      "  dnsutils \\",
      "  ca-certificates \\",
      "  software-properties-common \\",
      "  apt-transport-https \\",
      "  gnupg \\",
      "  lsb-release",
      "",
      "# Install security tools",
      "sudo apt-get install -y \\",
      "  ufw \\",
      "  fail2ban \\",
      "  aide \\",
      "  auditd \\",
      "  libpam-pwquality",
      "",
      "# Install cloud provider tools",
      "sudo apt-get install -y cloud-init",
      "",
      "echo '✓ System packages updated'"
    ]
  }
  
  ##############################################################################
  # Phase 3: Security Hardening
  ##############################################################################
  
  provisioner "file" {
    source      = "${path.root}/../scripts/common/system-hardening.sh"
    destination = "/tmp/system-hardening.sh"
  }
  
  provisioner "shell" {
    inline = [
      "echo '==> Phase 3: Applying security hardening'",
      "",
      "# Update build state",
      "BUILD_ID=$(cat /tmp/build_id)",
      "export BLDST_API_URL='${var.bldst_api_url}'",
      "export BLDST_API_KEY='${var.bldst_api_key}'",
      "",
      "bldst builds update-state \\",
      "  --build-id \"$BUILD_ID\" \\",
      "  --state-code PROVISIONING \\",
      "  --message 'Applying security hardening (CIS benchmarks)'",
      "",
      "# Run hardening script",
      "chmod +x /tmp/system-hardening.sh",
      "sudo /tmp/system-hardening.sh",
      "",
      "# Configure UFW firewall",
      "sudo ufw --force enable",
      "sudo ufw default deny incoming",
      "sudo ufw default allow outgoing",
      "sudo ufw allow ssh",
      "",
      "# Enable fail2ban",
      "sudo systemctl enable fail2ban",
      "sudo systemctl start fail2ban",
      "",
      "echo '✓ Security hardening complete'"
    ]
  }
  
  ##############################################################################
  # Phase 4: Cloud-Init Configuration
  ##############################################################################
  
  provisioner "shell" {
    inline = [
      "echo '==> Phase 4: Configuring cloud-init'",
      "",
      "# Update build state",
      "BUILD_ID=$(cat /tmp/build_id)",
      "export BLDST_API_URL='${var.bldst_api_url}'",
      "export BLDST_API_KEY='${var.bldst_api_key}'",
      "",
      "bldst builds update-state \\",
      "  --build-id \"$BUILD_ID\" \\",
      "  --state-code PROVISIONING \\",
      "  --message 'Configuring cloud-init for multi-cloud support'",
      "",
      "# Configure cloud-init",
      "sudo tee /etc/cloud/cloud.cfg.d/99-custom.cfg > /dev/null <<'CLOUDCFG'",
      "# Custom cloud-init configuration",
      "datasource_list: [ Ec2, Azure, GCE, None ]",
      "",
      "# Preserve hostname",
      "preserve_hostname: false",
      "",
      "# Package management",
      "package_update: true",
      "package_upgrade: false",
      "",
      "# SSH key management",
      "ssh_deletekeys: true",
      "ssh_genkeytypes: ['rsa', 'ecdsa', 'ed25519']",
      "",
      "# System info",
      "system_info:",
      "  default_user:",
      "    name: ubuntu",
      "    groups: [adm, audio, cdrom, dialout, dip, floppy, lxd, netdev, plugdev, sudo, video]",
      "    sudo: ['ALL=(ALL) NOPASSWD:ALL']",
      "    shell: /bin/bash",
      "CLOUDCFG",
      "",
      "# Clean cloud-init state (will regenerate on first boot)",
      "sudo cloud-init clean --logs --seed",
      "",
      "echo '✓ Cloud-init configured'"
    ]
  }
  
  ##############################################################################
  # Phase 5: Cleanup and Finalization
  ##############################################################################
  
  provisioner "shell" {
    inline = [
      "echo '==> Phase 5: Cleaning up and finalizing image'",
      "",
      "# Update build state",
      "BUILD_ID=$(cat /tmp/build_id)",
      "export BLDST_API_URL='${var.bldst_api_url}'",
      "export BLDST_API_KEY='${var.bldst_api_key}'",
      "",
      "bldst builds update-state \\",
      "  --build-id \"$BUILD_ID\" \\",
      "  --state-code PROVISIONING \\",
      "  --message 'Performing final cleanup and validation'",
      "",
      "# Clean package cache",
      "sudo apt-get clean",
      "sudo apt-get autoremove -y",
      "",
      "# Clear logs",
      "sudo find /var/log -type f -exec truncate -s 0 {} \\;",
      "",
      "# Remove temporary files",
      "sudo rm -rf /tmp/*",
      "sudo rm -rf /var/tmp/*",
      "",
      "# Clear bash history",
      "history -c",
      "cat /dev/null > ~/.bash_history",
      "",
      "# Remove SSH host keys (regenerated by cloud-init)",
      "sudo rm -f /etc/ssh/ssh_host_*",
      "",
      "# Clear machine ID (regenerated on boot)",
      "sudo truncate -s 0 /etc/machine-id",
      "",
      "# Update build state to TESTING",
      "bldst builds update-state \\",
      "  --build-id \"$BUILD_ID\" \\",
      "  --state-code TESTING \\",
      "  --message 'Image provisioning complete, pending validation'",
      "",
      "echo '✓ Cleanup complete'"
    ]
  }
  
  ##############################################################################
  # Post-Processors
  ##############################################################################
  
  # Generate manifest with image IDs
  post-processor "manifest" {
    output     = "manifest-ubuntu-${var.image_version}.json"
    strip_path = true
    custom_data = {
      build_id      = var.build_id
      os            = "Ubuntu"
      os_version    = var.os_version
      image_version = var.image_version
      build_date    = local.timestamp
    }
  }
  
  # Record artifacts in Build State API
  # Note: This step would typically be handled by CI/CD after validation
  post-processor "shell-local" {
    inline = [
      "echo '==> Recording image artifacts in Build State API'",
      "",
      "# Read manifest to get image IDs",
      "MANIFEST='manifest-ubuntu-${var.image_version}.json'",
      "",
      "if [ -f \"$MANIFEST\" ]; then",
      "  # Extract artifact information",
      "  # This is a placeholder - adjust based on your CI/CD integration",
      "  echo \"Manifest generated: $MANIFEST\"",
      "  echo \"Review and record artifacts using: bldst artifacts record\"",
      "else",
      "  echo \"Warning: Manifest not found\"",
      "fi"
    ]
  }
}

##############################################################################
# Usage Examples
##############################################################################
#
# Build for single cloud:
#   packer build -only=amazon-ebs.ubuntu ubuntu-22-04-base.pkr.hcl
#   packer build -only=azure-arm.ubuntu ubuntu-22-04-base.pkr.hcl
#   packer build -only=googlecompute.ubuntu ubuntu-22-04-base.pkr.hcl
#
# Build for multiple clouds:
#   packer build ubuntu-22-04-base.pkr.hcl
#
# With custom variables:
#   packer build \
#     -var 'image_version=2.0.0' \
#     -var 'aws_region=us-west-2' \
#     ubuntu-22-04-base.pkr.hcl
#
# Using variable file:
#   packer build -var-file=vars/production.pkrvars.hcl ubuntu-22-04-base.pkr.hcl
#
