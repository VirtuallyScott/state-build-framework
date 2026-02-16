#########################################
# RHEL 8 Base Image - Build State Tracked
#########################################
#
# This Packer template builds a hardened RHEL 8 base image for AWS EC2
# with full Build State API integration for tracking build progress.
#
# Features:
# - Security hardening (CIS benchmarks)
# - Minimal package installation
# - Cloud-init configured
# - Build state tracking at each phase
# - AMI artifact registration
#
# Usage with Build State API:
#   1. Create build record: BUILD_UUID=$(bldst build create ...)
#   2. Run packer: packer build -var "build_uuid=$BUILD_UUID" rhel-8-base.pkr.hcl
#   3. Complete build: bldst build add-state "$BUILD_UUID" --state 100
#
# Or let CI/CD pipeline manage the lifecycle.

####################
# Required Plugins #
####################

packer {
  required_version = ">= 1.8.0"
  
  required_plugins {
    amazon = {
      version = ">= 1.0.0"
      source  = "github.com/hashicorp/amazon"
    }
  }
}

####################
# Input Variables  #
####################

# Build State API Configuration
variable "build_uuid" {
  type        = string
  description = "Build UUID from Build State API for tracking this build's progress"
  default     = ""
}

variable "bldst_api_url" {
  type        = string
  description = "Build State API endpoint URL (e.g., https://api.example.com)"
  default     = env("BLDST_API_URL")
}

variable "bld

st_api_key" {
  type        = string
  description = "Build State API authentication key"
  default     = env("BLDST_API_KEY")
  sensitive   = true
}

# AWS Configuration
variable "aws_region" {
  type        = string
  description = "AWS region to build the AMI in"
  default     = "us-east-1"
}

variable "aws_instance_type" {
  type        = string
  description = "EC2 instance type for building"
  default     = "t3.medium"
}

variable "aws_source_ami_owner" {
  type        = string
  description = "AWS account ID that owns the source AMI"
  default     = "309956199498"  # Red Hat official account
}

# Image Configuration
variable "rhel_version" {
  type        = string
  description = "RHEL version to build (e.g., 8.10)"
  default     = "8.10"
}

variable "image_name_prefix" {
  type        = string
  description = "Prefix for the AMI name"
  default     = "rhel-8-base"
}

variable "build_timestamp" {
  type        = string
  description = "Timestamp for build identification"
  default     = "${formatdate("YYYYMMDD-hhmm", timestamp())}"
}

# Build Configuration
variable "ssh_username" {
  type        = string
  description = "SSH username for connecting to instance"
  default     = "ec2-user"
}

variable "enable_state_tracking" {
  type        = bool
  description = "Enable Build State API tracking (requires build_uuid)"
  default     = true
}

####################
# Local Variables  #
####################

locals {
  # AMI name with timestamp
  ami_name = "${var.image_name_prefix}-${var.rhel_version}-${var.build_timestamp}"
  
  # Tags for the AMI
  ami_tags = {
    Name          = local.ami_name
    OS            = "RHEL"
    OSVersion     = var.rhel_version
    BaseImage     = "true"
    BuildDate     = "${formatdate("YYYY-MM-DD", timestamp())}"
    BuildUUID     = var.build_uuid
    ManagedBy     = "Packer"
    BuildStateAPI = var.enable_state_tracking ? "enabled" : "disabled"
  }
  
  # Build state tracking enabled
  state_tracking_enabled = var.enable_state_tracking && var.build_uuid != ""
}

####################
# Data Sources     #
####################

# Find the latest RHEL 8 AMI from Red Hat
data "amazon-ami" "rhel8" {
  filters = {
    name                = "RHEL-${var.rhel_version}*"
    root-device-type    = "ebs"
    virtualization-type = "hvm"
    architecture        = "x86_64"
  }
  
  most_recent = true
  owners      = [var.aws_source_ami_owner]
  region      = var.aws_region
}

####################
# Source Builder   #
####################

source "amazon-ebs" "rhel8_base" {
  # AWS Configuration
  region        = var.aws_region
  instance_type = var.aws_instance_type
  
  # Source AMI
  source_ami    = data.amazon-ami.rhel8.id
  
  # SSH Configuration
  ssh_username  = var.ssh_username
  ssh_timeout   = "10m"
  
  # AMI Configuration
  ami_name        = local.ami_name
  ami_description = "RHEL ${var.rhel_version} base image - Build UUID: ${var.build_uuid}"
  
  # Tags applied to the AMI and snapshots
  tags            = local.ami_tags
  snapshot_tags   = local.ami_tags
  
  # Tags applied to the build instance (deleted after build)
  run_tags = {
    Name      = "Packer-Builder-${local.ami_name}"
    BuildUUID = var.build_uuid
    Temporary = "true"
  }
  
  # EBS volume configuration
  launch_block_device_mappings {
    device_name = "/dev/sda1"
    volume_size = 20
    volume_type = "gp3"
    iops        = 3000
    throughput  = 125
    encrypted   = true
    delete_on_termination = true
  }
  
  # Force deregister previous AMI with same name (useful for testing)
  force_deregister      = false
  force_delete_snapshot = false
  
  # Shutdown behavior
  shutdown_behavior = "terminate"
}

####################
# Build Definition #
####################

build {
  name    = "rhel8-base-aws"
  sources = ["source.amazon-ebs.rhel8_base"]
  
  #############################################
  # PHASE 1: Initial Setup & State Tracking ##
  #############################################
  
  # Update build state: Starting preparation
  provisioner "shell" {
    inline = [
      "echo '=== Phase 1: Initial Setup ==='",
      "echo 'Build UUID: ${var.build_uuid}'",
      "echo 'Source AMI: ${data.amazon-ami.rhel8.id}'",
    ]
  }
  
  # Install bldst CLI if state tracking is enabled
  provisioner "shell" {
    only   = ["amazon-ebs.rhel8_base"]
    inline = [
      "if [ '${local.state_tracking_enabled}' = 'true' ]; then",
      "  echo 'Installing bldst CLI for state tracking...'",
      "  sudo yum install -y python3-pip",
      "  sudo pip3 install --quiet buildstate-cli",
      "  bldst --version",
      "  # Configure CLI",
      "  bldst config set-url '${var.bldst_api_url}'",
      "  bldst auth set-key '${var.bldst_api_key}'",
      "  # Verify connection",
      "  bldst health check || echo 'Warning: Could not verify API connection'",
      "  # Update state: Preparation phase",
      "  bldst build add-state '${var.build_uuid}' --state 15 --status 'Packer preparing build environment' || true",
      "else",
      "  echo 'Build state tracking disabled'",
      "fi"
    ]
  }
  
  #############################################
  # PHASE 2: System Updates                 ##
  #############################################
  
  provisioner "shell" {
    inline = [
      "echo '=== Phase 2: System Updates ==='",
      "if [ '${local.state_tracking_enabled}' = 'true' ]; then",
      "  bldst build add-state '${var.build_uuid}' --state 20 --status 'Updating system packages' || true",
      "fi",
      "",
      "# Update all packages to latest versions",
      "sudo yum update -y",
      "",
      "# Install common utilities",
      "sudo yum install -y \\",
      "  cloud-init \\",
      "  cloud-utils-growpart \\",
      "  gdisk \\",
      "  vim \\",
      "  wget \\",
      "  curl \\",
      "  git \\",
      "  jq \\",
      "  nc \\",
      "  tcpdump \\",
      "  bind-utils",
      "",
      "echo 'System updates completed'"
    ]
    # Retry on transient failures
    max_retries = 3
    pause_before = "5s"
  }
  
  #############################################
  # PHASE 3: Security Hardening             ##
  #############################################
  
  provisioner "shell" {
    script = "${path.root}/../scripts/common/system-hardening.sh"
  }
  
  provisioner "shell" {
    inline = [
      "if [ '${local.state_tracking_enabled}' = 'true' ]; then",
      "  bldst build add-state '${var.build_uuid}' --state 30 --status 'Security hardening completed' || true",
      "fi"
    ]
  }
  
  #############################################
  # PHASE 4: Cloud-Init Configuration       ##
  #############################################
  
  provisioner "shell" {
    inline = [
      "echo '=== Phase 4: Cloud-Init Configuration ==='",
      "if [ '${local.state_tracking_enabled}' = 'true' ]; then",
      "  bldst build add-state '${var.build_uuid}' --state 40 --status 'Configuring cloud-init' || true",
      "fi",
      "",
      "# Enable and configure cloud-init",
      "sudo systemctl enable cloud-init",
      "sudo systemctl enable cloud-init-local",
      "sudo systemctl enable cloud-config",
      "sudo systemctl enable cloud-final",
      "",
      "# Configure cloud-init for AWS",
      "sudo tee /etc/cloud/cloud.cfg.d/99_aws.cfg > /dev/null <<'EOF'",
      "datasource_list: [ Ec2, None ]",
      "datasource:",
      "  Ec2:",
      "    strict_id: false",
      "    timeout: 10",
      "    max_wait: 30",
      "EOF",
      "",
      "echo 'Cloud-init configuration completed'"
    ]
  }
  
  #############################################
  # PHASE 5: Cleanup & Preparation          ##
  #############################################
  
  provisioner "shell" {
    inline = [
      "echo '=== Phase 5: Cleanup & Preparation ==='",
      "if [ '${local.state_tracking_enabled}' = 'true' ]; then",
      "  bldst build add-state '${var.build_uuid}' --state 45 --status 'Cleaning up for AMI creation' || true",
      "fi",
      "",
      "# Clean yum cache",
      "sudo yum clean all",
      "sudo rm -rf /var/cache/yum",
      "",
      "# Remove SSH host keys (will be regenerated on first boot)",
      "sudo rm -f /etc/ssh/ssh_host_*",
      "",
      "# Clear machine-id (will be regenerated)",
      "sudo truncate -s 0 /etc/machine-id",
      "",
      "# Clear log files",
      "sudo find /var/log -type f -exec truncate -s 0 {} \\;",
      "",
      "# Clear shell history",
      "history -c",
      "cat /dev/null > ~/.bash_history",
      "",
      "# Remove cloud-init artifacts from build",
      "sudo cloud-init clean --logs --seed",
      "",
      "echo 'Cleanup completed - image ready for AMI creation'"
    ]
  }
  
  # Final state update before AMI creation
  provisioner "shell" {
    inline = [
      "if [ '${local.state_tracking_enabled}' = 'true' ]; then",
      "  bldst build add-state '${var.build_uuid}' --state 48 --status 'Packer creating AMI' || true",
      "fi"
    ]
  }
  
  #############################################
  # Post-Processors                         ##
  #############################################
  
  # Generate manifest file with AMI details
  post-processor "manifest" {
    output     = "manifest.json"
    strip_path = true
    custom_data = {
      build_uuid     = var.build_uuid
      build_time     = "${formatdate("YYYY-MM-DD hh:mm:ss ZZZ", timestamp())}"
      source_ami     = data.amazon-ami.rhel8.id
      rhel_version   = var.rhel_version
    }
  }
  
  # Extract AMI ID to file for CI/CD consumption
  post-processor "shell-local" {
    inline = [
      "echo 'Extracting AMI ID from manifest...'",
      "AMI_ID=$(jq -r '.builds[0].artifact_id' manifest.json | cut -d: -f2)",
      "echo \"$AMI_ID\" > ami-id.txt",
      "echo \"AMI ID: $AMI_ID\"",
      "",
      "# If state tracking enabled, CI/CD should update final state",
      "if [ '${local.state_tracking_enabled}' = 'true' ]; then",
      "  echo 'AMI created successfully. CI/CD should now:'",
      "  echo '  1. Record artifact: bldst build add-artifact'",
      "  echo '  2. Complete build: bldst build add-state ${var.build_uuid} --state 100'",
      "fi"
    ]
  }
}

####################
# End of Template  #
####################
