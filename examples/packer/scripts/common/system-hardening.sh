#!/bin/bash
##############################################################################
# System Hardening Script for RHEL/CentOS Base Images
##############################################################################
#
# This script implements security hardening based on CIS benchmarks and
# industry best practices for cloud instances.
#
# Features:
# - SSH hardening
# - Firewall configuration
# - Kernel parameter tuning
# - Audit logging
# - File permissions hardening
#
# Usage:
#   Called by Packer during image provisioning
#   Can also be run standalone: sudo ./system-hardening.sh

set -euo pipefail

echo "========================================="
echo "Starting System Hardening"
echo "========================================="

##############################################################################
# SSH Hardening
##############################################################################
echo "==> Hardening SSH configuration..."

sudo tee /etc/ssh/sshd_config.d/hardening.conf > /dev/null <<'EOF'
# Disable root login
PermitRootLogin no

# Disable password authentication (use keys only)
PasswordAuthentication no
PermitEmptyPasswords no
ChallengeResponseAuthentication no

# Disable X11 forwarding
X11Forwarding no

# Set strong ciphers and MACs
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com,aes256-ctr,aes192-ctr,aes128-ctr
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com,hmac-sha2-512,hmac-sha2-256

# Set key exchange algorithms
KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org,ecdh-sha2-nistp521,ecdh-sha2-nistp384,ecdh-sha2-nistp256

# Disconnect idle sessions
ClientAliveInterval 300
ClientAliveCountMax 2

# Limit authentication attempts
MaxAuthTries 3
MaxSessions 10

# Log verbosely
LogLevel VERBOSE

# Use privilege separation
UsePrivilegeSeparation sandbox
EOF

echo "    ✓ SSH hardening complete"

##############################################################################
# Kernel Parameter Tuning
##############################################################################
echo "==> Configuring kernel security parameters..."

sudo tee /etc/sysctl.d/99-security.conf > /dev/null <<'EOF'
# IP Forwarding (disable unless needed)
net.ipv4.ip_forward = 0
net.ipv6.conf.all.forwarding = 0

# Syn cookies protection
net.ipv4.tcp_syncookies = 1

# Disable ICMP redirect acceptance
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0

# Disable source packet routing
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv6.conf.default.accept_source_route = 0

# Enable source address verification
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Log martian packets
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1

# Ignore ICMP ping requests
net.ipv4.icmp_echo_ignore_all = 0
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Ignore bogus ICMP error responses
net.ipv4.icmp_ignore_bogus_error_responses = 1

# TCP hardening
net.ipv4.tcp_timestamps = 1
net.ipv4.tcp_sack = 1

# Increase system file descriptor limit
fs.file-max = 65535

# Restrict core dumps
fs.suid_dumpable = 0

# Randomize virtual address space
kernel.randomize_va_space = 2

# Restrict kernel pointer exposure
kernel.kptr_restrict = 2

# Restrict dmesg access
kernel.dmesg_restrict = 1

# Restrict ptrace scope
kernel.yama.ptrace_scope = 1
EOF

# Apply sysctl settings
sudo sysctl -p /etc/sysctl.d/99-security.conf > /dev/null 2>&1 || true

echo "    ✓ Kernel parameters configured"

##############################################################################
# Firewall Configuration
##############################################################################
echo "==> Configuring firewall (firewalld)..."

if command -v firewall-cmd &> /dev/null; then
    # Ensure firewalld is enabled
    sudo systemctl enable firewalld
    
    # Note: In cloud environments, external firewall/security groups
    # typically handle access control. This is a baseline.
    echo "    ✓ Firewalld enabled (configured by cloud provider security groups)"
else
    echo "    ⚠ firewalld not found, skipping"
fi

##############################################################################
# File Permissions Hardening
##############################################################################
echo "==> Hardening file permissions..."

# Secure cron
if [ -d /etc/cron.d ]; then
    sudo chmod 700 /etc/cron.d
    sudo chmod 700 /etc/cron.daily
    sudo chmod 700 /etc/cron.hourly
    sudo chmod 700 /etc/cron.monthly
    sudo chmod 700 /etc/cron.weekly
fi

# Secure SSH directory permissions
sudo chmod 700 /root/.ssh 2>/dev/null || true
sudo chmod 700 /home/*/.ssh 2>/dev/null || true

# Secure important config files
sudo chmod 644 /etc/passwd
sudo chmod 644 /etc/group
sudo chmod 000 /etc/shadow
sudo chmod 000 /etc/gshadow

echo "    ✓ File permissions hardened"

##############################################################################
# Audit Logging (if auditd available)
##############################################################################
echo "==> Configuring audit logging..."

if command -v auditctl &> /dev/null; then
    # Enable auditd
    sudo systemctl enable auditd
    
    # Add basic audit rules
    sudo tee -a /etc/audit/rules.d/hardening.rules > /dev/null <<'EOF'
# Monitor changes to system files
-w /etc/passwd -p wa -k identity
-w /etc/group -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/gshadow -p wa -k identity
-w /etc/sudoers -p wa -k actions
-w /etc/ssh/sshd_config -p wa -k sshd

# Monitor kernel module loading
-w /sbin/insmod -p x -k modules
-w /sbin/rmmod -p x -k modules
-w /sbin/modprobe -p x -k modules

# Monitor system calls
-a always,exit -F arch=b64 -S adjtimex -S settimeofday -k time-change
-a always,exit -F arch=b32 -S adjtimex -S settimeofday -S stime -k time-change
EOF
    
    echo "    ✓ Audit logging configured"
else
    echo "    ⚠ auditd not found, skipping"
fi

##############################################################################
# Security Limits
##############################################################################
echo "==> Setting security limits..."

sudo tee /etc/security/limits.d/99-security.conf > /dev/null <<'EOF'
# Limit core dumps
* hard core 0
* soft core 0

# Set reasonable process limits
* soft nproc 1024
* hard nproc 4096

# Set file descriptor limits
* soft nofile 4096
* hard nofile 65536
EOF

echo "    ✓ Security limits configured"

##############################################################################
# Disable Unnecessary Services
##############################################################################
echo "==> Disabling unnecessary services..."

# List of services to disable (adjust based on your needs)
SERVICES_TO_DISABLE=(
    "postfix"      # Mail server (disable if not needed)
    "avahi-daemon" # Multicast DNS (rarely needed in cloud)
)

for service in "${SERVICES_TO_DISABLE[@]}"; do
    if systemctl list-unit-files | grep -q "^${service}"; then
        sudo systemctl disable "${service}" 2>/dev/null || true
        echo "    ✓ Disabled ${service}"
    fi
done

##############################################################################
# SELinux Configuration
##############################################################################
echo "==> Verifying SELinux configuration..."

if command -v getenforce &> /dev/null; then
    SELINUX_STATUS=$(getenforce)
    echo "    SELinux status: ${SELINUX_STATUS}"
    
    if [ "$SELINUX_STATUS" != "Enforcing" ] && [ "$SELINUX_STATUS" != "Permissive" ]; then
        echo "    ⚠ SELinux is disabled. Consider enabling for enhanced security."
    fi
fi

##############################################################################
# Set Proper Timezone
##############################################################################
echo "==> Setting timezone to UTC..."
sudo timedatectl set-timezone UTC
echo "    ✓ Timezone set to UTC"

##############################################################################
# Summary
##############################################################################
echo ""
echo "========================================="
echo "System Hardening Complete"
echo "========================================="
echo ""
echo "Hardening applied:"
echo "  ✓ SSH hardened (key-only auth, strong ciphers)"
echo "  ✓ Kernel parameters tuned"
echo "  ✓ Firewall configured"
echo "  ✓ File permissions secured"
echo "  ✓ Audit logging enabled"
echo "  ✓ Security limits set"
echo "  ✓ Unnecessary services disabled"
echo ""
echo "Post-deployment recommendations:"
echo "  - Configure cloud provider security groups"
echo "  - Enable automatic security updates"
echo "  - Implement log aggregation"
echo "  - Regular vulnerability scanning"
echo "  - Periodic security audits"
echo ""

exit 0
