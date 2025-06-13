# Quip Release Process

This document outlines the repeatable steps for releasing new versions of Quip.

## Prerequisites

- Push access to the main repository
- GitHub CLI (`gh`) installed and authenticated
- `uv` package manager installed
- Pre-commit hooks configured

## Version Management

Quip uses semantic versioning (MAJOR.MINOR.PATCH) with versions managed in:
- `desktop/pyproject.toml` - Python package version
- Git tags for release tracking

## Release Steps

### 1. Pre-Release Preparation

```bash
# Ensure you're on main branch and up to date
git checkout main
git pull origin main

# Verify working directory is clean
git status

# Run full test suite and quality checks
cd desktop
uv run ruff check . --fix
uv run ruff format .
uv run pytest tests/ --cov=. --cov-fail-under=80
uv run pre-commit run --all-files
```

### 2. Version Update

```bash
# Update version in pyproject.toml
# Example: 0.6.1 -> 0.6.2 (patch) or 0.6.1 -> 0.7.0 (minor)
cd desktop
# Edit pyproject.toml version field manually or use uv tool
uv version patch  # or minor/major as appropriate
```

### 3. Update Documentation

```bash
# Update DEVELOPMENT.md with new version in "Current State" section
# Update any version references in README.md if needed
# Consider updating install script references
```

### 4. Commit Version Changes

```bash
# Stage version-related changes
git add desktop/pyproject.toml DEVELOPMENT.md README.md

# Commit with conventional commit format
git commit -m "chore: bump version to vX.Y.Z"
```

### 5. Create and Push Release

```bash
# Create and push the version tag
VERSION=$(cd desktop && uv run python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")
git tag -a "v$VERSION" -m "Release v$VERSION"
git push origin main
git push origin "v$VERSION"
```

### 6. Create GitHub Release

```bash
# Create GitHub release with gh CLI
gh release create "v$VERSION" \
    --title "Quip v$VERSION" \
    --notes "$(cat <<EOF
## What's New in v$VERSION

[Describe key features and changes]

## Installation

Quick install:
\`\`\`bash
curl -sSL https://raw.githubusercontent.com/voglster/quip/main/install.sh | bash
\`\`\`

Manual install:
\`\`\`bash
git clone https://github.com/voglster/quip.git
cd quip/desktop
uv sync
uv run quip
\`\`\`

## Full Changelog

[Link to commits or detailed changelog]
EOF
)"
```

### 7. Post-Release Tasks

```bash
# Verify the release appears on GitHub
gh release list

# Test the installation script works with the new version
curl -sSL https://raw.githubusercontent.com/voglster/quip/main/install.sh | bash

# Update any external documentation or announcements as needed
```

## Release Checklist

- [ ] Working directory is clean
- [ ] All tests pass
- [ ] Code quality checks pass (ruff, pre-commit)
- [ ] Version updated in `desktop/pyproject.toml`
- [ ] Documentation updated with new version
- [ ] Version commit created and pushed
- [ ] Git tag created and pushed
- [ ] GitHub release created with release notes
- [ ] Installation script tested with new version

## Hotfix Releases

For urgent fixes:

1. Create hotfix branch from the release tag: `git checkout -b hotfix/vX.Y.Z+1 vX.Y.Z`
2. Apply minimal fixes
3. Follow same release process but increment patch version
4. Consider cherry-picking the fix to main if needed

## Rollback Process

If a release needs to be rolled back:

```bash
# Delete the problematic release
gh release delete "vX.Y.Z" --yes

# Delete the tag
git tag -d "vX.Y.Z"
git push origin --delete "vX.Y.Z"

# Revert version commit if needed
git revert <commit-hash>
git push origin main
```

## Notes

- Always use fast-forward merges (no merge commits) as per project conventions
- Keep releases small and focused
- Test the installation process after each release
- Use conventional commit messages for version bumps
- Consider creating a CHANGELOG.md for detailed release notes