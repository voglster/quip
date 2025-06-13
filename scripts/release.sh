#!/bin/bash
set -e

# Quip release script
# Usage: ./scripts/release.sh 1.0.0

if [ $# -eq 0 ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 1.0.0"
    echo ""
    echo "This script will:"
    echo "1. Create and push a release branch"
    echo "2. GitHub Actions will automatically create the release"
    echo "3. Clean up the release branch"
    exit 1
fi

VERSION="$1"

# Validate version format
if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "❌ Invalid version format: $VERSION"
    echo "Expected format: 1.0.0"
    exit 1
fi

echo "🚀 Creating release for version $VERSION"

# Check if we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "❌ Please run this script from the main branch"
    echo "Current branch: $CURRENT_BRANCH"
    exit 1
fi

# Check if working directory is clean
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ Working directory is not clean. Please commit or stash changes."
    git status --short
    exit 1
fi

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull origin main

# Update version in pyproject.toml
echo "📝 Updating version in pyproject.toml..."
sed -i "s/version = \"[^\"]*\"/version = \"$VERSION\"/" desktop/pyproject.toml

# Verify the change
if grep -q "version = \"$VERSION\"" desktop/pyproject.toml; then
    echo "✅ Version updated to $VERSION"
else
    echo "❌ Failed to update version in pyproject.toml"
    exit 1
fi

# Commit version change
echo "💾 Committing version change..."
git add desktop/pyproject.toml
git commit -m "chore: bump version to $VERSION"

# Create and push release branch
RELEASE_BRANCH="release/$VERSION"
echo "🌿 Creating release branch: $RELEASE_BRANCH"
git checkout -b "$RELEASE_BRANCH"
git push origin "$RELEASE_BRANCH"

echo ""
echo "✅ Release branch created and pushed!"
echo "🔄 GitHub Actions will now create the release automatically"
echo "📋 Monitor progress at: https://github.com/voglster/quip/actions"

# Wait a moment, then clean up the release branch
echo ""
echo "⏳ Waiting 30 seconds for GitHub Actions to start, then cleaning up..."
sleep 30

# Switch back to main and delete release branch
git checkout main
git branch -D "$RELEASE_BRANCH"

# Push version bump to main
git push origin main

# Delete remote release branch
git push origin --delete "$RELEASE_BRANCH"

echo ""
echo "🎉 Release $VERSION initiated!"
echo "📦 Check the release at: https://github.com/voglster/quip/releases"
echo "🔗 Install command: curl -sSL https://raw.githubusercontent.com/voglster/quip/main/install.sh | bash"
