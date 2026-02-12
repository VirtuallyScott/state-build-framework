# Sample Implementation: AWS RHEL 8 Web Server Image

This directory contains a sample implementation of the State-Based Build Framework for creating an AWS RHEL 8 web server image.

## Directory Structure

```
aws-rhel8-webserver/
├── packer/
│   ├── rhel8.json              # Packer build configuration
│   └── kickstart.cfg           # Kickstart configuration
├── ansible/
│   ├── inventory/              # Ansible inventory files
│   ├── playbooks/              # Ansible playbooks by state
│   │   ├── 15-base-config.yml
│   │   ├── 20-aws-setup.yml
│   │   ├── 25-security.yml
│   │   └── ...
│   └── roles/                  # Ansible roles
├── scripts/
│   ├── init-build.sh           # Initialize build state
│   ├── update-state.sh         # Update build state
│   ├── resume-build.sh         # Resume failed build
│   └── validate-state.sh       # Validate state transitions
├── concourse/
│   └── pipeline.yml            # Concourse pipeline definition
└── state/
    └── build.db                # SQLite state database (created at runtime)
```

## Packer Configuration

### rhel8.json
```json
{
  "builders": [
    {
      "type": "amazon-ebs",
      "region": "us-east-1",
      "source_ami": "ami-0abcdef1234567890",
      "instance_type": "t3.medium",
      "ssh_username": "ec2-user",
      "ami_name": "rhel8-webserver-{{timestamp}}",
      "tags": {
        "Name": "rhel8-webserver",
        "BuildState": "10"
      }
    }
  ],
  "provisioners": [
    {
      "type": "file",
      "source": "kickstart.cfg",
      "destination": "/tmp/kickstart.cfg"
    },
    {
      "type": "shell",
      "inline": [
        "sudo mv /tmp/kickstart.cfg /root/kickstart.cfg",
        "curl -o /tmp/update-state.sh https://raw.githubusercontent.com/sap/state-builds/main/scripts/update-state.sh",
        "chmod +x /tmp/update-state.sh",
        "BUILD_ID=${BUILD_ID} /tmp/update-state.sh 10 completed"
      ]
    }
  ],
  "post-processors": [
    {
      "type": "manifest",
      "output": "packer-manifest.json"
    }
  ]
}
```

### kickstart.cfg
```bash
# Kickstart configuration for RHEL 8
# State 5-10: Create green image

install
cdrom
lang en_US.UTF-8
keyboard us
timezone America/New_York
authconfig --enableshadow --passalgo=sha512
selinux --enforcing
firewall --enabled
network --bootproto=dhcp
bootloader --location=mbr

# Root password (change in production)
rootpw --iscrypted $6$encrypted_password_hash

# Create default user for Ansible access
user --name=ansible --groups=wheel --password=$6$encrypted_password_hash

# Partitioning
clearpart --all --initlabel
part /boot --fstype ext4 --size=1024
part pv.01 --size=1 --grow
volgroup vg00 pv.01
logvol / --fstype ext4 --name=lv00 --vgname=vg00 --size=1 --grow

# Packages
%packages --ignoremissing
@core
openssh-server
curl
wget
vim
sudo
%end

# Post-install scripts
%post --nochroot
echo "State 5: Kickstart initiated" >> /root/build.log
%end

%post
echo "State 10: Green image created" >> /root/build.log

# Configure SSH for key-based auth
mkdir -p /home/ansible/.ssh
echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ..." > /home/ansible/.ssh/authorized_keys
chmod 600 /home/ansible/.ssh/authorized_keys
chown -R ansible:ansible /home/ansible/.ssh

# Allow ansible user sudo without password
echo "ansible ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers.d/ansible

# Enable SSH service
systemctl enable sshd

# Update state
curl -o /tmp/update-state.sh https://raw.githubusercontent.com/sap/state-builds/main/scripts/update-state.sh
chmod +x /tmp/update-state.sh
BUILD_ID=${BUILD_ID} /tmp/update-state.sh 10 completed
%end
```

## Ansible Playbooks

### 15-base-config.yml
```yaml
---
# State 15: Base Configuration Applied
- name: Apply base system configuration
  hosts: all
  become: yes
  vars:
    build_id: "{{ lookup('env', 'BUILD_ID') }}"
    
  pre_tasks:
    - name: Update state to 15 in progress
      command: /usr/local/bin/update-state.sh {{ build_id }} 15 in_progress
      
  tasks:
    - name: Update package cache
      yum:
        name: '*'
        state: latest
        update_cache: yes
        
    - name: Install base packages
      yum:
        name:
          - curl
          - wget
          - vim
          - git
          - unzip
          - chrony
        state: present
        
    - name: Configure timezone
      timezone:
        name: UTC
        
    - name: Configure locale
      lineinfile:
        path: /etc/locale.conf
        line: LANG=en_US.UTF-8
        create: yes
        
    - name: Enable chronyd
      service:
        name: chronyd
        enabled: yes
        state: started
        
  post_tasks:
    - name: Update state to 15 completed
      command: /usr/local/bin/update-state.sh {{ build_id }} 15 completed
      when: not ansible_failed_tasks
```

### 20-aws-setup.yml
```yaml
---
# State 20: Cloud Provider Specific Setup (AWS)
- name: Configure AWS-specific settings
  hosts: all
  become: yes
  vars:
    build_id: "{{ lookup('env', 'BUILD_ID') }}"
    
  pre_tasks:
    - name: Update state to 20 in progress
      command: /usr/local/bin/update-state.sh {{ build_id }} 20 in_progress
      
  tasks:
    - name: Install AWS CLI
      yum:
        name: awscli
        state: present
        
    - name: Install AWS Systems Manager Agent
      yum:
        name: amazon-ssm-agent
        state: present
        
    - name: Enable SSM agent
      service:
        name: amazon-ssm-agent
        enabled: yes
        state: started
        
    - name: Install CloudWatch agent
      yum:
        name: amazon-cloudwatch-agent
        state: present
        
    - name: Configure CloudWatch agent
      template:
        src: templates/cloudwatch-config.json.j2
        dest: /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
        
    - name: Enable CloudWatch agent
      service:
        name: amazon-cloudwatch-agent
        enabled: yes
        state: started
        
  post_tasks:
    - name: Update state to 20 completed
      command: /usr/local/bin/update-state.sh {{ build_id }} 20 completed
      when: not ansible_failed_tasks
```

## State Management Scripts

### update-state.sh
```bash
#!/bin/bash
# Update build state in SQLite database and sync to S3

BUILD_ID=$1
STATE=$2
STATUS=${3:-completed}  # completed, failed, in_progress
ERROR_MSG=${4:-}

DB_PATH="/var/lib/state-builds/${BUILD_ID}.db"
S3_BUCKET="state-builds"
CLOUD_PROVIDER="aws"

# For successful completion, advance to next state
if [ "$STATUS" = "completed" ]; then
    NEXT_STATE=$((STATE + 5))
    sqlite3 $DB_PATH << EOF
    UPDATE builds SET current_state = $NEXT_STATE, last_update = datetime('now'), status = 'running' WHERE build_id = '$BUILD_ID';
    INSERT INTO state_history (build_id, state, timestamp, status, error_message)
    VALUES ('$BUILD_ID', $STATE, datetime('now'), 'completed', '');
EOF
    echo "Advanced build $BUILD_ID from state $STATE to $NEXT_STATE"
    
# For failures, stay at current state but mark as failed
elif [ "$STATUS" = "failed" ]; then
    sqlite3 $DB_PATH << EOF
    UPDATE builds SET last_update = datetime('now'), status = 'failed' WHERE build_id = '$BUILD_ID';
    INSERT INTO state_history (build_id, state, timestamp, status, error_message)
    VALUES ('$BUILD_ID', $STATE, datetime('now'), 'failed', '$ERROR_MSG');
EOF
    echo "Marked build $BUILD_ID state $STATE as failed: $ERROR_MSG"
    
# For in-progress updates
elif [ "$STATUS" = "in_progress" ]; then
    sqlite3 $DB_PATH << EOF
    UPDATE builds SET last_update = datetime('now') WHERE build_id = '$BUILD_ID';
    INSERT INTO state_history (build_id, state, timestamp, status, error_message)
    VALUES ('$BUILD_ID', $STATE, datetime('now'), 'started', '');
EOF
    echo "Marked build $BUILD_ID state $STATE as in progress"
fi

# Sync to S3
aws s3 cp $DB_PATH s3://$S3_BUCKET/$CLOUD_PROVIDER/$BUILD_ID/state.db
```

### resume-build.sh
```bash
#!/bin/bash
# Resume build from last completed state or retry failed state

BUILD_ID=$1
S3_BUCKET="state-builds"
CLOUD_PROVIDER="aws"

# Check if local DB exists
if [ ! -f "/var/lib/state-builds/${BUILD_ID}.db" ]; then
    echo "Downloading state from S3..."
    aws s3 cp s3://$S3_BUCKET/$CLOUD_PROVIDER/$BUILD_ID/state.db /var/lib/state-builds/${BUILD_ID}.db
fi

# Get current state and status
CURRENT_STATE=$(sqlite3 /var/lib/state-builds/${BUILD_ID}.db "SELECT current_state FROM builds WHERE build_id = '$BUILD_ID';")
STATUS=$(sqlite3 /var/lib/state-builds/${BUILD_ID}.db "SELECT status FROM builds WHERE build_id = '$BUILD_ID';")

echo "Build $BUILD_ID at state $CURRENT_STATE with status $STATUS"

# Check if build is already complete
if [ "$STATUS" = "completed" ] && [ "$CURRENT_STATE" -eq 100 ]; then
    echo "Build already completed successfully"
    exit 0
fi

# Handle failed states - retry the failed state
if [ "$STATUS" = "failed" ]; then
    echo "Build failed at state $CURRENT_STATE, attempting retry..."
    
    # Check retry count
    RETRY_COUNT=$(sqlite3 /var/lib/state-builds/${BUILD_ID}.db "
        SELECT COUNT(*) FROM state_history 
        WHERE build_id = '$BUILD_ID' AND state = $CURRENT_STATE AND status = 'failed'
    ")
    
    if [ "$RETRY_COUNT" -ge 3 ]; then
        echo "Max retries exceeded for state $CURRENT_STATE. Manual intervention required."
        exit 1
    fi
    
    echo "Retry attempt $((RETRY_COUNT + 1)) for state $CURRENT_STATE"
    run_state_task $BUILD_ID $CURRENT_STATE
    
elif [ "$STATUS" = "running" ]; then
    # Continue from current state
    echo "Continuing build from state $CURRENT_STATE"
    NEXT_STATE=$((CURRENT_STATE + 5))
    run_state_task $BUILD_ID $NEXT_STATE
fi
```

### run-state-task function
```bash
run_state_task() {
    local build_id=$1
    local state=$2
    
    echo "Executing state $state for build $build_id"
    
    # Mark state as in progress
    ./scripts/update-state.sh $build_id $state in_progress
    
    case $state in
        5)
            echo "Running kickstart..."
            if packer build -var build_id=$build_id packer/rhel8.json; then
                ./scripts/update-state.sh $build_id $state completed
            else
                ./scripts/update-state.sh $build_id $state failed "Packer build failed"
                return 1
            fi
            ;;
        10)
            echo "Running base configuration..."
            if ansible-playbook -i ansible/inventory/aws ansible/playbooks/15-base-config.yml; then
                ./scripts/update-state.sh $build_id $state completed
            else
                ./scripts/update-state.sh $build_id $state failed "Base config playbook failed"
                return 1
            fi
            ;;
        # Add cases for all states...
        *)
            echo "Unknown state: $state"
            return 1
            ;;
    esac
}
```

## Concourse Pipeline

### pipeline.yml
```yaml
---
resource_types:
- name: s3
  type: docker-image
  source:
    repository: governmentpaas/awscli

resources:
- name: source-code
  type: git
  source:
    uri: https://github.com/sap/state-builds.git
    branch: main
    
- name: state-store
  type: s3
  source:
    bucket: state-builds
    access_key_id: ((aws_access_key))
    secret_access_key: ((aws_secret_key))
    region_name: us-east-1

jobs:
- name: build-rhel8-webserver
  plan:
  - get: source-code
    trigger: true
  - get: state-store
    trigger: false
    
  - task: init-build
    config:
      platform: linux
      image_resource:
        type: docker-image
        source: { repository: busybox }
      inputs:
      - name: source-code
      outputs:
      - name: build-metadata
      run:
        path: source-code/scripts/init-build.sh
    params:
      BUILD_ID: rhel8-webserver-((timestamp))
      CLOUD_PROVIDER: aws
      IMAGE_TYPE: rhel8-webserver
      
  - task: packer-build
    config:
      platform: linux
      image_resource:
        type: docker-image
        source: { repository: hashicorp/packer }
      inputs:
      - name: source-code
      - name: build-metadata
      run:
        path: source-code/scripts/run-packer.sh
      params:
        BUILD_ID: ((.:build-metadata.build-id))
    on_success:
      put: state-store
      params:
        file: build-metadata/state.json
    on_failure:
      put: state-store
      params:
        file: build-metadata/state.json
        
  - task: ansible-base-config
    config:
      platform: linux
      image_resource:
        type: docker-image
        source: { repository: cytopia/ansible }
      inputs:
      - name: source-code
      - name: build-metadata
      run:
        path: source-code/scripts/run-ansible.sh
        args: [15-base-config]
      params:
        BUILD_ID: ((.:build-metadata.build-id))
    on_success: &update-state
      put: state-store
      params:
        file: build-metadata/state.json
    on_failure: *update-state
    
  # Continue with additional Ansible tasks for each state...
  
  - task: finalize-image
    config:
      platform: linux
      image_resource:
        type: docker-image
        source: { repository: amazonlinux }
      inputs:
      - name: source-code
      - name: build-metadata
      run:
        path: source-code/scripts/finalize-image.sh
      params:
        BUILD_ID: ((.:build-metadata.build-id))
```

## Running the Build

### Prerequisites
1. AWS credentials configured
2. Packer installed
3. Ansible installed
4. SQLite3 installed
5. S3 bucket `state-builds` created

### Execute Build
```bash
export BUILD_ID="rhel8-webserver-$(date +%s)"
export AWS_REGION="us-east-1"

# Initialize build state
./scripts/init-build.sh $BUILD_ID aws rhel8-webserver

# Run Packer to create green image
packer build -var build_id=$BUILD_ID packer/rhel8.json

# Run Ansible playbooks
ansible-playbook -i ansible/inventory/aws ansible/playbooks/15-base-config.yml
ansible-playbook -i ansible/inventory/aws ansible/playbooks/20-aws-setup.yml
# ... continue for each state

# On failure, resume from last state
./scripts/resume-build.sh $BUILD_ID
```

## Monitoring

### Check Build Status
```bash
# Get current state
sqlite3 /var/lib/state-builds/${BUILD_ID}.db "SELECT current_state, status FROM builds WHERE build_id = '${BUILD_ID}';"

# View state history
sqlite3 /var/lib/state-builds/${BUILD_ID}.db "SELECT state, timestamp, status FROM state_history WHERE build_id = '${BUILD_ID}' ORDER BY timestamp;"
```

### Logs
- Packer logs: `packer build.log`
- Ansible logs: `ansible/playbooks/logs/`
- Build state logs: `/var/log/state-builds/${BUILD_ID}.log`

This sample implementation demonstrates how to structure a state-based build pipeline for AWS RHEL 8 web server images. The same pattern can be adapted for other cloud providers and image types.