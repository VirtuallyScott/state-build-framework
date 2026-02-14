# CI/CD Pipeline and Semantic Versioning

This document describes the CI/CD infrastructure for the Build State project, including semantic versioning, automated builds, and container registry publishing.

## Table of Contents

- [Overview](#overview)
- [Semantic Versioning](#semantic-versioning)
- [GitHub Actions Workflows](#github-actions-workflows)
- [Container Registry](#container-registry)
- [Version Management](#version-management)
- [Release Process](#release-process)
- [Usage Examples](#usage-examples)

## Overview

The Build State project uses a lightweight, file-based semantic versioning approach with GitHub Actions for automated builds and container publishing. This provides:

- **Semantic versioning** via a VERSION file at the project root
- **Automated container builds** for every push to main/develop
- **GitHub Container Registry** (ghcr.io) for hosting Docker images
- **Git flow** branching model (main, develop, feature/*)
- **Lightweight tooling** - no heavy dependencies like gitversion

## Semantic Versioning

### Version Format

We follow [Semantic Versioning 2.0.0](https://semver.org/):

```
MAJOR.MINOR.PATCH[-PRERELEASE][+BUILDMETADATA]
```

- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)
- **PRERELEASE**: Optional pre-release identifier (e.g., `-beta.1`, `-rc.2`)
- **BUILDMETADATA**: Build information (e.g., `+abc1234`, `+abc1234-dirty`)

### Version File

The authoritative version is stored in the `VERSION` file at the project root:

```bash
$ cat VERSION
2.0.0
```

### Version Script

The `scripts/version.sh` script provides version management:

```bash
# View current version
./scripts/version.sh current

# View version with git info
./scripts/version.sh full
# Output: 2.0.0+abc1234

# Bump version
./scripts/version.sh bump patch    # 2.0.0 → 2.0.1
./scripts/version.sh bump minor    # 2.0.1 → 2.1.0
./scripts/version.sh bump major    # 2.1.0 → 3.0.0

# Set specific version
./scripts/version.sh set 2.5.0

# Create git tag
./scripts/version.sh tag

# Calculate next version from conventional commits
./scripts/version.sh next
```

## GitHub Actions Workflows

### 1. Build and Publish (`build-and-publish.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Push tags matching `v*`
- Pull requests to `main` or `develop`
- Manual workflow dispatch

**What it does:**
1. Determines version from VERSION file, git tag, or manual input
2. Builds API service Docker image
3. Builds Nginx load balancer Docker image
4. Builds Python CLI package
5. Pushes images to GitHub Container Registry
6. Tags images with multiple tags:
   - Semantic version (e.g., `2.0.0`)
   - Full version with SHA (e.g., `2.0.0+abc1234`)
   - Branch name (e.g., `develop`, `main`)
   - Git SHA (e.g., `main-abc1234`)
   - `latest` for main branch
   - `develop` for develop branch

**Images published:**
- `ghcr.io/<owner>/state-builds-api:<version>`
- `ghcr.io/<owner>/state-builds-nginx:<version>`

### 2. Version and Release (`version-and-release.yml`)

**Triggers:**
- Manual workflow dispatch only

**Inputs:**
- `bump`: Version bump type (major, minor, patch)
- `create_tag`: Whether to create a git tag (default: true)
- `create_release`: Whether to create GitHub release (default: false)

**What it does:**
1. Bumps version in VERSION file
2. Updates version in `buildstate_cli/pyproject.toml`
3. Commits changes
4. Creates git tag (if requested)
5. Creates GitHub release with changelog (if requested)

### 3. Test Build (`test.yml`)

**Triggers:**
- Pull requests to `main` or `develop`
- Manual workflow dispatch

**What it does:**
1. Lints Python code with ruff
2. Tests CLI installation
3. Performs test Docker builds (without pushing)

## Container Registry

### Authentication

Images are published to GitHub Container Registry (ghcr.io). To pull images:

```bash
# Public images (no auth needed)
docker pull ghcr.io/<owner>/state-builds-api:latest

# Private images (requires GitHub token)
echo $GITHUB_TOKEN | docker login ghcr.io -u <username> --password-stdin
docker pull ghcr.io/<owner>/state-builds-api:latest
```

### Image Tags

Each build produces multiple tags:

| Tag Pattern | Example | Description |
|-------------|---------|-------------|
| `<version>` | `2.0.0` | Semantic version |
| `<version>+<sha>` | `2.0.0+abc1234` | Full version with git SHA |
| `<branch>` | `develop` | Branch name |
| `<branch>-<sha>` | `main-abc1234` | Branch + short SHA |
| `latest` | `latest` | Latest main branch build |
| `develop` | `develop` | Latest develop branch build |

### Using Images

Update your `docker-compose.yml` to use registry images:

```yaml
services:
  api:
    image: ghcr.io/<owner>/state-builds-api:2.0.0
    # ... rest of config
  
  nginx:
    image: ghcr.io/<owner>/state-builds-nginx:2.0.0
    # ... rest of config
```

## Version Management

### Conventional Commits

We recommend using [Conventional Commits](https://www.conventionalcommits.org/) for automatic version bumping:

```bash
# Patch bump (2.0.0 → 2.0.1)
git commit -m "fix: resolve authentication bug"

# Minor bump (2.0.0 → 2.1.0)
git commit -m "feat: add artifact compression support"

# Major bump (2.0.0 → 3.0.0)
git commit -m "feat!: redesign API endpoints

BREAKING CHANGE: All /api/v1 endpoints moved to /api/v2"
```

### Manual Version Bumps

```bash
# Bump version locally
./scripts/version.sh bump patch

# Commit and push
git add VERSION buildstate_cli/pyproject.toml
git commit -m "chore: bump version to $(cat VERSION)"
git push

# Create and push tag
./scripts/version.sh tag
git push origin v$(cat VERSION)
```

### Automated Version Bumps

Use the "Version and Release" workflow:

1. Go to Actions → Version and Release
2. Click "Run workflow"
3. Select bump type (major, minor, patch)
4. Choose whether to create tag and release
5. Run workflow

## Release Process

### Standard Release (Git Flow)

```bash
# 1. Create feature branch
git flow feature start awesome-feature

# 2. Make changes and commit
git add .
git commit -m "feat: implement awesome feature"

# 3. Finish feature (merges to develop)
git flow feature finish awesome-feature

# 4. Push develop
git push origin develop

# 5. When ready for release, use GitHub Actions:
#    - Go to Actions → Version and Release
#    - Select bump type and run workflow
#    - This creates tag and merges to main

# 6. Merge to main (or use release branch)
git checkout main
git merge develop
git push origin main

# 7. GitHub Actions automatically builds and publishes containers
```

### Hotfix Release

```bash
# 1. Create hotfix branch
git flow hotfix start critical-fix

# 2. Fix the issue
git commit -m "fix: critical security issue"

# 3. Finish hotfix (merges to main and develop)
git flow hotfix finish critical-fix

# 4. Use GitHub Actions to bump patch version
```

### Pre-release

```bash
# 1. Manually set pre-release version
./scripts/version.sh set 2.1.0-beta.1

# 2. Commit and tag
git add VERSION
git commit -m "chore: release 2.1.0-beta.1"
./scripts/version.sh tag
git push origin v2.1.0-beta.1

# 3. Build and publish as pre-release
```

## Usage Examples

### Checking Action Status

Use `gh` CLI to check workflow runs:

```bash
# List recent workflow runs
gh run list

# View specific workflow
gh run list --workflow=build-and-publish.yml

# Watch running workflow
gh run watch

# View workflow details
gh run view <run-id>

# View logs
gh run view <run-id> --log
```

### Building Locally with Version

```bash
# Get current version
VERSION=$(./scripts/version.sh current)
GIT_SHA=$(git rev-parse --short HEAD)
FULL_VERSION="${VERSION}+${GIT_SHA}"

# Build with version
docker build \
  --build-arg VERSION=$FULL_VERSION \
  -t state-builds-api:$VERSION \
  -f api_service/docker/Dockerfile \
  api_service/

# Tag with multiple tags
docker tag state-builds-api:$VERSION state-builds-api:latest
docker tag state-builds-api:$VERSION state-builds-api:develop
```

### Pulling Specific Versions

```bash
# Pull specific version
docker pull ghcr.io/<owner>/state-builds-api:2.0.0

# Pull latest develop
docker pull ghcr.io/<owner>/state-builds-api:develop

# Pull latest stable
docker pull ghcr.io/<owner>/state-builds-api:latest

# Pull specific commit
docker pull ghcr.io/<owner>/state-builds-api:main-abc1234
```

### Inspecting Image Version

```bash
# Check version label
docker inspect ghcr.io/<owner>/state-builds-api:latest \
  | jq '.[0].Config.Labels'

# Run container and check version endpoint
docker run --rm ghcr.io/<owner>/state-builds-api:latest \
  python -c "from app.core.config import settings; print(settings.VERSION)"
```

## CI/CD Best Practices

### Branch Protection

Configure branch protection rules:
- **main**: Require PR, require status checks, no direct pushes
- **develop**: Require PR for external contributors

### Secrets Management

Required GitHub secrets:
- `GITHUB_TOKEN`: Automatically provided (for container registry)
- `PYPI_API_TOKEN`: Optional, for publishing CLI to PyPI

### Caching

GitHub Actions uses Docker layer caching:
- `cache-from: type=gha`
- `cache-to: type=gha,mode=max`

This speeds up builds significantly.

### Multi-architecture Builds

To build for multiple architectures:

```yaml
- name: Build and push
  uses: docker/build-push-action@v5
  with:
    platforms: linux/amd64,linux/arm64
    # ... rest of config
```

### Security Scanning

Add security scanning to workflow:

```yaml
- name: Run Trivy vulnerability scanner
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ${{ env.IMAGE_BASE }}/state-builds-api:${{ needs.version.outputs.version }}
    format: 'sarif'
    output: 'trivy-results.sarif'

- name: Upload Trivy results to GitHub Security
  uses: github/codeql-action/upload-sarif@v2
  with:
    sarif_file: 'trivy-results.sarif'
```

## Troubleshooting

### Workflow Fails to Push Images

**Error:** `denied: permission_denied: write_package`

**Solution:**
1. Go to Settings → Actions → General
2. Under "Workflow permissions", select "Read and write permissions"
3. Save changes

### Version File Out of Sync

**Error:** Version mismatch between VERSION file and git tags

**Solution:**
```bash
# Check current versions
cat VERSION
git describe --tags --abbrev=0

# Sync VERSION file to latest tag
git describe --tags --abbrev=0 | sed 's/^v//' > VERSION
git add VERSION
git commit -m "chore: sync VERSION file with git tag"
```

### Docker Build Fails

**Error:** Build fails in GitHub Actions but works locally

**Solution:**
1. Check architecture compatibility
2. Verify all files are committed (`.dockerignore` might be hiding files)
3. Check build args are properly passed
4. Review build logs for specific errors

### Cannot Pull Images

**Error:** `Error response from daemon: unauthorized`

**Solution:**
```bash
# Ensure you're logged in
echo $GITHUB_TOKEN | docker login ghcr.io -u <username> --password-stdin

# Check image exists and is public
gh api /users/<owner>/packages/container/state-builds-api

# Make package public (if needed)
# Go to: https://github.com/users/<owner>/packages/container/state-builds-api/settings
```

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
