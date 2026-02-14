# CI/CD Quick Reference

Quick commands and workflows for managing CI/CD in the Build State project.

## Version Management

```bash
# View current version
./scripts/version.sh current

# View version with git info
./scripts/version.sh full

# Bump version
./scripts/version.sh bump patch    # 2.0.0 → 2.0.1
./scripts/version.sh bump minor    # 2.0.1 → 2.1.0  
./scripts/version.sh bump major    # 2.1.0 → 3.0.0

# Create git tag
./scripts/version.sh tag
git push origin v$(cat VERSION)

# Calculate next version from conventional commits
./scripts/version.sh next
```

## GitHub Actions

```bash
# List recent workflow runs
./scripts/gh-actions-status.sh list

# Watch running workflow
./scripts/gh-actions-status.sh watch

# View specific workflow
./scripts/gh-actions-status.sh workflow build-and-publish.yml

# View logs for a run
./scripts/gh-actions-status.sh logs <run-id>

# Manually trigger workflow
./scripts/gh-actions-status.sh trigger build-and-publish.yml

# Show summary
./scripts/gh-actions-status.sh summary
```

Or use `gh` CLI directly:

```bash
# List runs
gh run list

# Watch run
gh run watch

# View run
gh run view <run-id>

# View logs
gh run view <run-id> --log

# Trigger workflow manually
gh workflow run build-and-publish.yml
```

## Container Registry

### Pull Images

```bash
# Latest stable
docker pull ghcr.io/<owner>/state-builds-api:latest
docker pull ghcr.io/<owner>/state-builds-nginx:latest

# Specific version
docker pull ghcr.io/<owner>/state-builds-api:2.0.0

# Latest develop
docker pull ghcr.io/<owner>/state-builds-api:develop
```

### Login to GHCR

```bash
# Create personal access token with read:packages scope
# Then login
echo $GITHUB_TOKEN | docker login ghcr.io -u <username> --password-stdin
```

### Use Registry Images

```bash
# Using docker-compose.registry.yml
export GHCR_OWNER=<your-github-username>
export IMAGE_VERSION=2.0.0
docker compose -f docker-compose.registry.yml up -d
```

## Git Flow Workflow

### Feature Development

```bash
# Start feature
git flow feature start my-awesome-feature

# Work on feature
git add .
git commit -m "feat: add awesome feature"

# Finish feature (merges to develop)
git flow feature finish my-awesome-feature
git push origin develop

# Trigger build
# Push to develop automatically triggers GitHub Actions
```

### Release Process

```bash
# Option 1: Manual via GitHub Actions
# Go to Actions → Version and Release → Run workflow
# Select bump type (major, minor, patch)
# Creates tag and optionally GitHub release

# Option 2: Manual via scripts
./scripts/version.sh bump minor
git add VERSION buildstate_cli/pyproject.toml
git commit -m "chore: bump version to $(cat VERSION)"
git push origin develop

./scripts/version.sh tag
git push origin v$(cat VERSION)

# Merge to main
git checkout main
git merge develop
git push origin main
```

### Hotfix

```bash
# Start hotfix from main
git flow hotfix start fix-critical-bug

# Fix the issue
git add .
git commit -m "fix: critical security issue"

# Finish hotfix (merges to main and develop)
git flow hotfix finish fix-critical-bug

# Bump patch version via GitHub Actions
# Go to Actions → Version and Release → patch
```

## Conventional Commits

Use conventional commit messages for automatic version bumping:

```bash
# Patch bump (bug fixes)
git commit -m "fix: resolve authentication bug"
git commit -m "fix(api): handle null values in response"

# Minor bump (new features)
git commit -m "feat: add artifact compression"
git commit -m "feat(cli): add progress bars"

# Major bump (breaking changes)
git commit -m "feat!: redesign API endpoints"
# or
git commit -m "feat: redesign API

BREAKING CHANGE: All /api/v1 endpoints moved to /api/v2"

# Other types (don't trigger version bump)
git commit -m "docs: update README"
git commit -m "chore: update dependencies"
git commit -m "refactor: simplify auth logic"
git commit -m "test: add unit tests"
git commit -m "style: fix linting"
git commit -m "perf: optimize queries"
```

## Build Locally

```bash
# Get current version
VERSION=$(./scripts/version.sh current)
GIT_SHA=$(git rev-parse --short HEAD)
FULL_VERSION="${VERSION}+${GIT_SHA}"

# Build API container
docker build \
  --build-arg VERSION=$FULL_VERSION \
  -t state-builds-api:$VERSION \
  -f api_service/docker/Dockerfile \
  api_service/

# Build Nginx container
docker build \
  --build-arg VERSION=$FULL_VERSION \
  -t state-builds-nginx:$VERSION \
  -f api_service/docker/nginx.Dockerfile \
  api_service/

# Tag as latest
docker tag state-builds-api:$VERSION state-builds-api:latest
docker tag state-builds-nginx:$VERSION state-builds-nginx:latest
```

## Publishing

### Automatic Publishing

Push to branches triggers automatic builds:
- `develop` → builds and tags with `develop`
- `main` → builds and tags with `latest`
- `v*` tags → builds and tags with version number

### Manual Publishing

```bash
# Trigger manual build via GitHub Actions UI
# Go to Actions → Build and Publish → Run workflow
# Enter version (optional)

# Or via CLI
gh workflow run build-and-publish.yml -f version=2.1.0
```

## Checking Image Versions

```bash
# Check version label
docker inspect ghcr.io/<owner>/state-builds-api:latest | jq '.[0].Config.Labels'

# Check version in running container
docker run --rm ghcr.io/<owner>/state-builds-api:latest \
  python -c "from app.core.config import settings; print(settings.VERSION)"
```

## Troubleshooting

### Workflow Not Triggering

```bash
# Check workflow status
gh workflow list

# Check if workflow is enabled
gh workflow enable build-and-publish.yml

# Check recent runs
gh run list --workflow=build-and-publish.yml
```

### Build Failing

```bash
# View logs
./scripts/gh-actions-status.sh logs <run-id>

# Or
gh run view <run-id> --log

# Rerun failed jobs
gh run rerun <run-id>
```

### Can't Pull Images

```bash
# Check if logged in
docker info | grep Username

# Login again
echo $GITHUB_TOKEN | docker login ghcr.io -u <username> --password-stdin

# Make package public (if needed)
# Go to: https://github.com/users/<owner>/packages/container/<package>/settings
```

### Version Out of Sync

```bash
# Check versions
cat VERSION
git describe --tags --abbrev=0
cd buildstate_cli && grep "^version" pyproject.toml

# Sync to git tag
git describe --tags --abbrev=0 | sed 's/^v//' > VERSION

# Sync CLI version
./scripts/version.sh current
cd buildstate_cli
sed -i "s/^version = .*/version = \"$(cat ../VERSION)\"/" pyproject.toml
```

## Resources

- Full documentation: [CI_CD_PIPELINE.md](CI_CD_PIPELINE.md)
- Version script: `scripts/version.sh`
- Actions status script: `scripts/gh-actions-status.sh`
- GitHub Actions: `.github/workflows/`
