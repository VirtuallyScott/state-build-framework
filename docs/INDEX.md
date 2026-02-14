# Documentation Index

Complete documentation for the State-Based Build Framework, API, and CLI.

## 📖 Quick Links

### Getting Started
- **[Main README](../README.md)** - Project overview and quick start
- **[Credentials & URLs](../CREDENTIALS.md)** - All access credentials and endpoints
- **[API Quick Start](../api_service/docs/README.md)** - Start API in 5 minutes
- **[CLI Quick Start](../buildstate_cli/CLI_QUICKSTART.md)** - CLI in 5 minutes

### API Documentation
- **[API Reference](../api_service/docs/API_REFERENCE.md)** - Complete endpoint documentation
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
- **[CLI Documentation](../buildstate_cli/README.md)** - Complete CLI reference
  - Installation
  - Configuration
  - All commands
  - CI/CD integration
  
- **[CLI Quick Start](../buildstate_cli/CLI_QUICKSTART.md)** - Get started fast
  - 5-minute guide
  - Common workflows
  - Examples

### Framework Documentation
- **[Framework Overview](../problem_statement/README.md)** - Complete design
  - State-based architecture
  - Why state-based builds
  - Design decisions
  
- **[Framework Quick Start](../problem_statement/QUICKSTART.md)** - Implementation guide
  - Step-by-step setup
  - Worked examples
  
- **[State Definitions](../problem_statement/states.md)** - State codes 0-100
  - All state codes
  - Categories
  - When to use each
  
- **[Storage Implementation](../problem_statement/storage-implementation.md)** - Data layer
  - Database schema
  - API patterns
  - Storage options
  
- **[Sample Implementation](../problem_statement/sample-implementation.md)** - Concrete example
  - AWS RHEL 8 build
  - Complete workflow
  - Code samples
  
- **[Failure Handling](../problem_statement/failure-handling.md)** - Recovery
  - Retry strategies
  - Error handling
  - Resumable builds

## 📚 Documentation by Role

### For Developers

**Building the API:**
1. [Architecture Overview](../api_service/docs/ARCHITECTURE.md) - Understand the system
2. [API Reference](../api_service/docs/API_REFERENCE.md) - Learn the endpoints
3. Database schema in [Storage Implementation](../problem_statement/storage-implementation.md)

**Building with the API:**
1. [Authentication Guide](../api_service/docs/AUTHENTICATION.md) - Get authenticated
2. [API Reference](../api_service/docs/API_REFERENCE.md) - Use the endpoints
3. [CLI Documentation](../buildstate_cli/README.md) - Or use the CLI

### For DevOps / SRE

**Deploying:**
1. [API Deployment Guide](../api_service/docs/README.md) - Production setup
2. [Architecture Overview](../api_service/docs/ARCHITECTURE.md) - Scaling strategy
3. [Main README](../README.md) - Overall system

**Operating:**
1. [Authentication Guide](../api_service/docs/AUTHENTICATION.md) - Manage access
2. [API Reference](../api_service/docs/API_REFERENCE.md) - Health checks, monitoring
3. [CLI Documentation](../buildstate_cli/README.md) - Admin tasks

### For Pipeline Engineers

**Integration:**
1. [CLI Quick Start](../buildstate_cli/CLI_QUICKSTART.md) - Get CLI working
2. [CLI Documentation](../buildstate_cli/README.md#cicd-integration) - CI/CD examples
3. [API Reference](../api_service/docs/API_REFERENCE.md) - Direct API usage

**Implementation:**
1. [Framework Quick Start](../problem_statement/QUICKSTART.md) - Build state pattern
2. [State Definitions](../problem_statement/states.md) - Which states to use
3. [Sample Implementation](../problem_statement/sample-implementation.md) - Working example

### For Security Teams

**Security Review:**
1. [Authentication Guide](../api_service/docs/AUTHENTICATION.md) - Auth/authz model
2. [Architecture Overview](../api_service/docs/ARCHITECTURE.md) - Security design
3. [API Reference](../api_service/docs/API_REFERENCE.md) - Endpoint permissions

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
→ [CLI Documentation](../buildstate_cli/README.md#cicd-integration)

**...understand the API**
→ [API Reference](../api_service/docs/API_REFERENCE.md)

**...set up authentication**
→ [Authentication Guide](../api_service/docs/AUTHENTICATION.md)

**...deploy to production**
→ [Deployment Guide](../api_service/docs/README.md)

**...implement state-based builds**
→ [Framework Quick Start](../problem_statement/QUICKSTART.md)

**...understand state codes**
→ [State Definitions](../problem_statement/states.md)

**...handle build failures**
→ [Failure Handling](../problem_statement/failure-handling.md)

**...use the CLI**
→ [CLI Quick Start](../buildstate_cli/CLI_QUICKSTART.md)

**...make direct API calls**
→ [API Reference](../api_service/docs/API_REFERENCE.md)

**...scale the system**
→ [Architecture Overview](../api_service/docs/ARCHITECTURE.md)

**...troubleshoot issues**
→ [CLI Troubleshooting](../buildstate_cli/README.md#troubleshooting) or [API Errors](../api_service/docs/API_REFERENCE.md#error-responses)

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

- ✨ **NEW**: [API Reference](../api_service/docs/API_REFERENCE.md) - Complete endpoint documentation
- ✨ **NEW**: [Authentication Guide](../api_service/docs/AUTHENTICATION.md) - Security guide
- 🔄 **UPDATED**: [Main README](../README.md) - Complete overview
- 🔄 **UPDATED**: [CLI Documentation](../buildstate_cli/README.md) - Current commands

## 📧 Getting Help

If you can't find what you need:
1. Check the [Main README](../README.md) for overview
2. Search relevant documentation sections above
3. Check interactive API docs at http://localhost:8080/docs
4. Review examples in [Sample Implementation](../problem_statement/sample-implementation.md)
5. Open an issue on GitHub/GitLab

---

**Last Updated**: February 14, 2026
**Documentation Version**: 1.0
