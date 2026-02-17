# Documentation Index

Complete documentation for the State-Based Build Framework, API, and CLI.

## 📖 Quick Links

### Getting Started
- **[Main README](../README.md)** - Project overview and quick start
- **[Credentials & URLs](../CREDENTIALS.md)** - All access credentials and endpoints
- **[API Quick Start](../api_service/docs/README.md)** - Start API in 5 minutes
- **[CLI Quick Start](../bldst_cli/CLI_QUICKSTART.md)** - CLI in 5 minutes

### API Documentation
- **[API Reference](../api_service/docs/API-REFERENCE.md)** - Complete endpoint documentation
  - All HTTP endpoints
  - Request/response schemas
  - Error codes
  - Usage examples
  
- **[Authentication & Authorization Guide](../api_service/docs/AUTHENTICATION.md)** - Security
  - API keys vs JWT tokens
  - Authorization scopes
  - Best practices
  - Integration examples

- **[Architecture Overview](../api_service/docs/ARCHITECTURE.md)** - System design
  - Component architecture
  - Scaling approach
  - Database design
  - Security model

### CLI Documentation
- **[CLI Documentation](../bldst_cli/README.md)** - Complete CLI reference
  - Installation
  - Configuration
  - All commands
  - CI/CD integration
  
- **[CLI Quick Start](../bldst_cli/CLI_QUICKSTART.md)** - Get started fast
  - 5-minute guide
  - Common workflows
  - Examples

### CI/CD & Deployment
- **[CI/CD Pipeline](CI-CD-PIPELINE.md)** - Automated builds and versioning
  - GitHub Actions workflows
  - Semantic versioning
  - Container registry publishing
  - Release process
  
- **[Resumable Builds Design](RESUMABLE-BUILDS-DESIGN.md)** - Advanced resumability
  - Architecture overview
  - Artifact and variable tracking
  - Resume operations
  - Build orchestration
  
- **[Resumable Builds Quick Start](RESUMABLE-BUILDS-QUICKSTART.md)** - Usage guide
  - Getting started
  - API examples
  - Integration patterns

### Problem Statement & Architecture
- **[Problem Statement](PROBLEM-STATEMENT.md)** - Why this framework exists
  - The problems we solve
  - How state-based builds help
  - Real-world use cases
  - Migration strategy
  - Technical architecture

- **[Database Architecture](DATABASE-ARCHITECTURE.md)** - Data model details
  - Schema design
  - Relationships
  - Indexing strategy

### Artifact Storage
- **[Artifact Storage Tracking](ARTIFACT-STORAGE.md)** - Distributed build artifacts
  - Overview and use cases
  - Database schema
  - Supported storage types (S3, NFS, EBS, Ceph)
  - API and CLI usage
  - Best practices
  - Migration guide
  - Complete workflow examples

## 📚 Documentation by Role

### For Developers

**Building the API:**
1. [Architecture Overview](../api_service/docs/ARCHITECTURE.md) - Understand the system
2. [API Reference](../api_service/docs/API-REFERENCE.md) - Learn the endpoints
3. [Database Architecture](DATABASE-ARCHITECTURE.md) - Data model and schema

**Building with the API:**
1. [Authentication Guide](../api_service/docs/AUTHENTICATION.md) - Get authenticated
2. [API Reference](../api_service/docs/API-REFERENCE.md) - Use the endpoints
3. [CLI Documentation](../bldst_cli/README.md) - Or use the CLI

### For DevOps / SRE

**Deploying:**
1. [API Deployment Guide](../api_service/docs/README.md) - Production setup
2. [Architecture Overview](../api_service/docs/ARCHITECTURE.md) - Scaling strategy
3. [Main README](../README.md) - Overall system

**Operating:**
1. [Authentication Guide](../api_service/docs/AUTHENTICATION.md) - Manage access
2. [API Reference](../api_service/docs/API-REFERENCE.md) - Health checks, monitoring
3. [CLI Documentation](../bldst_cli/README.md) - Admin tasks

### For Pipeline Engineers

**Integration:**
1. [CLI Quick Start](../bldst_cli/CLI_QUICKSTART.md) - Get CLI working
2. [CLI Documentation](../bldst_cli/README.md#cicd-integration) - CI/CD examples
3. [API Reference](../api_service/docs/API-REFERENCE.md) - Direct API usage

**Implementation:**
1. [Problem Statement](PROBLEM-STATEMENT.md) - Understand the framework
2. [Artifact Storage](ARTIFACT-STORAGE.md) - Distributed artifact tracking
3. [API Reference](../api_service/docs/API-REFERENCE.md) - Build state endpoints

### For Security Teams

**Security Review:**
1. [Authentication Guide](../api_service/docs/AUTHENTICATION.md) - Auth/authz model
2. [Architecture Overview](../api_service/docs/ARCHITECTURE.md) - Security design
3. [API Reference](../api_service/docs/API-REFERENCE.md) - Endpoint permissions

## 📊 Documentation Coverage

### API Service ✅
- ✅ Complete endpoint documentation
- ✅ Authentication and authorization guide
- ✅ Architecture and design docs
- ✅ Deployment and operations guide
- ✅ Error handling reference
- ✅ Integration examples

### CLI Tool ✅
- ✅ Installation guide
- ✅ Complete command reference
- ✅ Configuration instructions
- ✅ Usage examples
- ✅ CI/CD integration patterns
- ✅ Troubleshooting guide

### Framework ✅
- ✅ Conceptual overview
- ✅ State code definitions
- ✅ Storage implementation
- ✅ Sample implementations
- ✅ Failure handling
- ✅ Quick start guide

## 🎯 Common Tasks

### I want to...

**...get access credentials**
→ [CREDENTIALS.md](../CREDENTIALS.md) - All URLs, API keys, and test accounts

**...start using the system**
→ [Main README](../README.md) - Quick Start section

**...integrate with my CI/CD pipeline**
→ [CLI Documentation](../bldst_cli/README.md#cicd-integration)

**...understand the API**
→ [API Reference](../api_service/docs/API-REFERENCE.md)

**...set up authentication**
→ [Authentication Guide](../api_service/docs/AUTHENTICATION.md)

**...deploy to production**
→ [Deployment Guide](../api_service/docs/README.md)

**...understand why we built this**
→ [Problem Statement](PROBLEM-STATEMENT.md)

**...implement state-based builds**
→ [Problem Statement](PROBLEM-STATEMENT.md) and [API Reference](../api_service/docs/API-REFERENCE.md)

**...track artifacts in distributed builds**
→ [Artifact Storage](ARTIFACT-STORAGE.md)

**...understand the database**
→ [Database Architecture](DATABASE-ARCHITECTURE.md)

**...use the CLI**
→ [CLI Quick Start](../bldst_cli/CLI_QUICKSTART.md)

**...make direct API calls**
→ [API Reference](../api_service/docs/API-REFERENCE.md)

**...scale the system**
→ [Architecture Overview](../api_service/docs/ARCHITECTURE.md)

**...troubleshoot issues**
→ [CLI Troubleshooting](../bldst_cli/README.md#troubleshooting) or [API Errors](../api_service/docs/API-REFERENCE.md#error-responses)

## 🔗 External Resources

### Interactive Documentation
- **Swagger UI**: http://localhost:8080/docs (when API is running)
- **ReDoc**: http://localhost:8080/redoc (when API is running)

### API Endpoints
- **Base URL**: http://localhost:8080 (development)
- **Health Check**: http://localhost:8080/health
- **API Status**: http://localhost:8080/status

## 📝 Document Formats

All documentation is in Markdown format for easy viewing:
- **GitHub/GitLab**: Renders automatically
- **Local**: Use any Markdown viewer or editor
- **Terminal**: Use `cat`, `less`, or `bat`
- **VS Code**: Built-in Markdown preview

## 🆕 Recently Updated

The following documents were recently created or updated:

- ✨ **NEW**: [Problem Statement](PROBLEM-STATEMENT.md) - Consolidated problem/solution overview (Feb 2026)
- ✨ **NEW**: [Artifact Storage](ARTIFACT-STORAGE.md) - Distributed artifact tracking (Feb 2026)
- ✨ **NEW**: [API Reference](../api_service/docs/API-REFERENCE.md) - Complete endpoint documentation
- ✨ **NEW**: [Authentication Guide](../api_service/docs/AUTHENTICATION.md) - Security guide
- 🔄 **UPDATED**: [Main README](../README.md) - Complete overview
- 🔄 **UPDATED**: [CLI Documentation](../bldst_cli/README.md) - Current commands
- 🔄 **UPDATED**: File naming standardized (hyphens instead of underscores)

## 📧 Getting Help

If you can't find what you need:
1. Check the [Main README](../README.md) for overview
2. Read the [Problem Statement](PROBLEM-STATEMENT.md) to understand the framework
3. Search relevant documentation sections above
4. Check interactive API docs at http://localhost:8080/docs
5. Open an issue on GitHub/GitLab

---

**Last Updated**: February 16, 2026
**Documentation Version**: 1.1
