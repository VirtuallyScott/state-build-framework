# State-Based Build Framework

This workspace contains a reusable framework for implementing state-based build pipelines for multi-cloud IaaS image creation.

## Getting Started

**🚀 Quick Start**: Read `.copilot/QUICKSTART.md` for a step-by-step implementation guide!

The complete framework documentation and implementation guides are in the `.copilot/` directory:

```bash
# Quick start guide (recommended)
cat .copilot/QUICKSTART.md

# Complete framework overview
cat .copilot/README.md

# See the setup script for copying to new workspaces
.copilot/setup.sh --help

# Copy framework to a new project
.copilot/setup.sh /path/to/new/image-build-project
```

## Framework Summary

- **State Codes**: 0-100 (incrementing by 5) for build milestones
- **Resumable Builds**: Failed states are retried without losing progress
- **Multi-Cloud Support**: Works across AWS, Azure, GCP, and private clouds
- **Storage Options**: SQLite, DynamoDB, S3, or JSON files
- **Tools Integration**: Packer, Ansible, Concourse CI/CD

## Files

- `.copilot/index.md` - Framework overview and quick start guide
- `.copilot/README.md` - Complete framework documentation
- `.copilot/states.md` - Detailed state code definitions
- `.copilot/storage-implementation.md` - Storage architecture and APIs
- `.copilot/sample-implementation.md` - AWS RHEL 8 concrete example
- `.copilot/failure-handling.md` - Failure handling and retry logic
- `.copilot/setup.sh` - Script to copy framework to new workspaces

---

**Framework Version**: 1.0
**Created**: February 12, 2026
**For**: SAP Platform Engineering Team