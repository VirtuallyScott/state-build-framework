# State-Based Build Framework

This workspace contains a reusable framework for implementing state-based build pipelines for multi-cloud IaaS image creation.

## What This Is

The **State-Based Build Framework** solves the critical problem of non-resumable build pipelines that lose all progress when interrupted. By implementing numerical state codes (0-100) and resumable workflows, this framework enables reliable, fault-tolerant image building across AWS, Azure, GCP, and private clouds.

**Why State-Based?** Traditional monolithic pipelines fail completely on interruption. State-based pipelines can resume from any failure point, saving hours of rebuild time and ensuring consistent, reliable deployments.

📖 **[Complete Documentation](problem_statement/)** - Framework overview, implementation guides, and examples

## Getting Started

**🚀 Quick Start**: Read `problem_statement/QUICKSTART.md` for a step-by-step implementation guide!

The complete framework documentation and implementation guides are in the `problem_statement/` directory:

```bash
# Quick start guide (recommended)
cat problem_statement/QUICKSTART.md

# Complete framework overview
cat problem_statement/README.md

# See the setup script for copying to new workspaces
problem_statement/setup.sh --help

# Copy framework to a new project
problem_statement/setup.sh /path/to/new/image-build-project
```

## Framework Summary

- **State Codes**: 0-100 (incrementing by 5) for build milestones
- **Resumable Builds**: Failed states are retried without losing progress
- **Multi-Cloud Support**: Works across AWS, Azure, GCP, and private clouds
- **Storage Options**: SQLite, DynamoDB, S3, or JSON files
- **Tools Integration**: Packer, Ansible, Concourse CI/CD

## Files

- `problem_statement/index.md` - Framework overview and quick start guide
- `problem_statement/README.md` - Complete framework documentation
- `problem_statement/states.md` - Detailed state code definitions
- `problem_statement/storage-implementation.md` - Storage architecture and APIs
- `problem_statement/sample-implementation.md` - AWS RHEL 8 concrete example
- `problem_statement/failure-handling.md` - Failure handling and retry logic
- `problem_statement/setup.sh` - Script to copy framework to new workspaces

---

**Framework Version**: 1.0
**Created**: February 12, 2026
**For**: SAP Platform Engineering Team