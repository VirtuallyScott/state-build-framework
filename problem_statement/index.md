# State-Based Build Framework for Multi-Cloud IaaS Images

This `problem_statement/` directory contains a complete framework for implementing state-based build pipelines for multi-cloud IaaS image creation at SAP.

## Framework Overview

The State-Based Build Framework introduces numerical state codes (0-100, incrementing by 5) to track build progress, enabling:

- **Resumable Pipelines**: Failed builds can resume from the last completed state
- **Cross-Platform Communication**: Unambiguous status reporting across AWS, Azure, GCP, etc.
- **Progress Preservation**: Failed states are retried without losing previous progress
- **Scalable Architecture**: Easy to insert new states without breaking numbering

## Directory Contents

### Core Documentation
- **`README.md`** - Main framework overview, state definitions, and implementation guide
- **`QUICKSTART.md`** - Step-by-step implementation guide (start here!)
- **`states.md`** - Detailed descriptions of each state code (0-100)
- **`failure-handling.md`** - Comprehensive guide to failure handling and retry logic

### Implementation Details
- **`storage-implementation.md`** - Complete storage architecture, database schemas, and API functions
- **`sample-implementation.md`** - Concrete AWS RHEL 8 example with Packer, Ansible, and Concourse

### Database Schema & Data
- **`database-schema.sql`** - Complete DDL for SQLite/PostgreSQL with UUID PKs
- **`sample-data.sql`** - Sample data with all your image types/platforms
- **`database-queries.sql`** - Useful queries for monitoring and reporting
- **`init-database.sh`** - Script to initialize database with schema and data

## Quick Start

1. **Copy to new workspace**:
   ```bash
   # Option 1: Manual copy
   cp -r problem_statement/ /path/to/new/workspace/

   # Option 2: Use setup script
   problem_statement/setup.sh /path/to/new/workspace/
   ```

2. **Review the framework**:
   ```bash
   cat problem_statement/README.md
   ```

3. **Start with sample implementation**:
   ```bash
   cat problem_statement/sample-implementation.md
   ```

## Key Concepts

### State Codes
- **0**: Initial state (nothing started)
- **5-95**: Progressive build milestones (incrementing by 5)
- **100**: Complete and delivered

### Failure Handling
- **Stay at failed state** (don't rollback to 0)
- **Separate state from status** (state = progress, status = success/failure)
- **Retry failed states** rather than starting over

### Storage Options
- **SQLite + S3**: Recommended for multi-cloud with local performance
- **DynamoDB/CosmosDB**: For cloud-native environments
- **JSON files**: For simple deployments

## Implementation Checklist

- [ ] Choose storage backend (SQLite recommended)
- [ ] Set up state database schema
- [ ] Implement state update functions
- [ ] Add state tracking to Packer builds
- [ ] Add state tracking to Ansible playbooks
- [ ] Configure Concourse pipeline with resume logic
- [ ] Test failure scenarios and retry logic

## Migration from Current System

If migrating from non-transactional "start over" builds:

1. **Phase 1**: Add state tracking (no behavior change)
2. **Phase 2**: Implement selective retry for expensive operations
3. **Phase 3**: Full resumability with intelligent retry strategies

## Support

This framework was designed for SAP's platform engineering team building IaaS images across multiple cloud providers using Packer, Ansible, and Cloud Foundry Concourse.

For questions or contributions, refer to the detailed documentation in each file.

---

**Created**: February 12, 2026
**Framework Version**: 1.0
**Target Platforms**: AWS, Azure, GCP, Private Clouds
**Tools**: Packer, Ansible, Concourse