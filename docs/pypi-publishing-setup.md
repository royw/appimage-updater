# PyPI Publishing Setup Guide

This guide provides step-by-step instructions for setting up automated PyPI publishing using GitHub Actions with Trusted Publishing.

## Overview

The publishing workflow (`.github/workflows/publish.yml`) automatically publishes to PyPI when a GitHub release is created. It uses PyPI's Trusted Publishing feature, which eliminates the need for API tokens.

## Prerequisites

- Repository owner/admin access on GitHub
- PyPI account with project ownership rights
- Package name available on PyPI (or already registered to you)

## Setup Instructions

### Step 1: Configure PyPI Trusted Publishing

1. **Log in to PyPI**
   - Go to [https://pypi.org/](https://pypi.org/)
   - Sign in with your account

2. **Navigate to Publishing Settings**
   - Go to your account settings: [https://pypi.org/manage/account/publishing/](https://pypi.org/manage/account/publishing/)
   - Or: Click your username → "Your projects" → "Publishing"

3. **Add a New Pending Publisher**

   Click "Add a new pending publisher" and fill in:

   - **PyPI Project Name**: `appimage-updater`
   - **Owner**: `royw` (your GitHub username)
   - **Repository name**: `appimage-updater`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi`

   Click "Add" to save.

4. **Important Notes**
   - This creates a "pending" publisher that will be activated on first successful publish
   - After the first publish, the pending publisher becomes a permanent trusted publisher
   - You can add this before or after creating the first release

### Step 2: Configure GitHub Environment

1. **Navigate to Repository Settings**
   - Go to your repository: [https://github.com/royw/appimage-updater](https://github.com/royw/appimage-updater)
   - Click "Settings" tab
   - Click "Environments" in the left sidebar

2. **Create PyPI Environment**
   - Click "New environment"
   - Name: `pypi`
   - Click "Configure environment"

3. **Configure Environment Protection Rules** (Recommended)

   Add protection rules to prevent accidental publishes:

   - **Required reviewers**: Add yourself or trusted maintainers
     - This requires manual approval before publishing
   - **Wait timer**: Optional delay before deployment (e.g., 5 minutes)
   - **Deployment branches**: Select "Selected branches"
     - Add rule: `main` (only allow publishes from main branch)

   Click "Save protection rules"

4. **Environment Secrets** (Not needed for Trusted Publishing)
   - With Trusted Publishing, you don't need to add any secrets
   - GitHub automatically provides authentication to PyPI

### Step 3: Verify Workflow Configuration

The workflow file `.github/workflows/publish.yml` should contain:

```yaml
environment:
  name: pypi
  url: https://pypi.org/p/appimage-updater
permissions:
  id-token: write  # Required for trusted publishing
```

This is already configured correctly in the repository.

### Step 4: Remove Old Publishing Job from CI

The `publish-to-pypi` job should be removed from `.github/workflows/ci.yml` since we now have a dedicated publishing workflow.

## Publishing Process

### Creating a Release

1. **Ensure Version is Updated**
   ```bash
   # Version should be updated in pyproject.toml
   grep "version =" pyproject.toml
   ```

2. **Commit and Push Changes**
   ```bash
   git add .
   git commit -m "release: prepare v0.5.1"
   git push origin main
   ```

3. **Create Git Tag**
   ```bash
   git tag -a v0.5.1 -m "Release v0.5.1"
   git push origin v0.5.1
   ```

4. **Create GitHub Release**
   - Go to [https://github.com/royw/appimage-updater/releases/new](https://github.com/royw/appimage-updater/releases/new)
   - Choose tag: `v0.5.1`
   - Release title: `v0.5.1`
   - Description: Copy relevant section from CHANGELOG.md
   - Check "Set as the latest release"
   - Click "Publish release"

5. **Monitor Publishing**
   - Go to Actions tab: [https://github.com/royw/appimage-updater/actions](https://github.com/royw/appimage-updater/actions)
   - Watch the "Publish to PyPI" workflow
   - If environment protection is enabled, approve the deployment
   - Verify successful publish to PyPI

### Manual Publishing (Testing)

For testing the workflow without creating a release:

1. **Navigate to Actions**
   - Go to [https://github.com/royw/appimage-updater/actions](https://github.com/royw/appimage-updater/actions)
   - Click "Publish to PyPI" workflow

2. **Run Workflow**
   - Click "Run workflow" button
   - Select branch: `main`
   - Click "Run workflow"

3. **Note**: Manual runs will still publish to PyPI, so use with caution!

## Troubleshooting

### Common Issues

#### 1. "Trusted publishing exchange failure"

**Cause**: PyPI trusted publisher not configured correctly

**Solution**:
- Verify all fields in PyPI publishing settings match exactly:
  - Owner: `royw`
  - Repository: `appimage-updater`
  - Workflow: `publish.yml`
  - Environment: `pypi`
- Check that the workflow is running from the correct repository

#### 2. "Environment protection rules failed"

**Cause**: Deployment waiting for approval or branch restrictions

**Solution**:
- Check the Actions tab for pending approvals
- Verify the workflow is running from an allowed branch
- Review environment protection rules in Settings → Environments

#### 3. "Package name already exists"

**Cause**: First-time publish with existing package name

**Solution**:
- If you own the package: Add trusted publisher to existing project
- If you don't own it: Choose a different package name

#### 4. "Permission denied: id-token"

**Cause**: Missing or incorrect permissions in workflow

**Solution**:
- Verify `permissions: id-token: write` is in the workflow
- Check that the workflow has not been modified incorrectly

### Viewing Logs

1. **GitHub Actions Logs**
   - Go to Actions tab
   - Click on the workflow run
   - Click on job name to see detailed logs

2. **PyPI Activity**
   - Go to [https://pypi.org/project/appimage-updater/](https://pypi.org/project/appimage-updater/)
   - Check "Release history" for published versions

## Security Best Practices

1. **Use Environment Protection**
   - Always require manual approval for production publishes
   - Restrict to main branch only

2. **Review Before Publishing**
   - Check CHANGELOG.md is updated
   - Verify version number is correct
   - Run tests locally: `uv run pytest`
   - Build and inspect package: `uv build && ls -lh dist/`

3. **Monitor Published Packages**
   - Review PyPI project page after each publish
   - Verify package metadata is correct
   - Test installation: `pip install appimage-updater==0.5.1`

4. **Trusted Publishing Benefits**
   - No API tokens to manage or leak
   - Automatic credential rotation
   - Audit trail through GitHub Actions
   - Reduced attack surface

## Additional Resources

- [PyPI Trusted Publishing Guide](https://docs.pypi.org/trusted-publishers/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [PyPI Publishing Action](https://github.com/pypa/gh-action-pypi-publish)
- [Python Packaging Guide](https://packaging.python.org/)

## Quick Reference

### PyPI URLs
- Project page: https://pypi.org/project/appimage-updater/
- Publishing settings: https://pypi.org/manage/account/publishing/

### GitHub URLs
- Repository: https://github.com/royw/appimage-updater
- Actions: https://github.com/royw/appimage-updater/actions
- Environments: https://github.com/royw/appimage-updater/settings/environments
- Releases: https://github.com/royw/appimage-updater/releases

### Commands
```bash
# Build package locally
uv build

# Check package
twine check dist/*

# Test installation
pip install --user appimage-updater==0.5.1

# Create and push tag
git tag -a v0.5.1 -m "Release v0.5.1"
git push origin v0.5.1
```
