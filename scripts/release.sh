#!/bin/bash
# Usage: ./scripts/release.sh [major|minor|patch] [-y]  (default: patch)
set -e

BUMP="patch"
SKIP_CONFIRM=""

for arg in "$@"; do
  case "$arg" in
    -y|--yes) SKIP_CONFIRM=1 ;;
    major|minor|patch) BUMP="$arg" ;;
    *) echo "Usage: $0 [major|minor|patch] [-y]"; exit 1 ;;
  esac
done

# --- Preflight checks ---

# Must be on main
BRANCH=$(git branch --show-current)
if [ "$BRANCH" != "main" ]; then
  echo "Error: must be on main branch (currently on $BRANCH)"
  exit 1
fi

# No uncommitted changes
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Error: uncommitted changes detected. Commit or stash first."
  git status --short
  exit 1
fi

# No untracked files
if [ -n "$(git ls-files --others --exclude-standard)" ]; then
  echo "Error: untracked files detected. Commit or remove first."
  git ls-files --others --exclude-standard
  exit 1
fi

# Lint + test
echo "Running lint and tests..."
cd desktop
if ! uv run ruff check . > /dev/null 2>&1; then
  echo "Error: ruff check failed. Fix errors before releasing."
  uv run ruff check .
  exit 1
fi
if ! uv run ruff format --check . > /dev/null 2>&1; then
  echo "Error: ruff format check failed. Run 'uv run ruff format .' first."
  exit 1
fi
if ! uv run pytest tests/ --cov=. --cov-fail-under=80 -q > /dev/null 2>&1; then
  echo "Error: tests failed. Fix before releasing."
  uv run pytest tests/ -v --cov=. --cov-fail-under=80
  exit 1
fi
cd ..
echo "Preflight passed."

# --- Version bump ---

# Get latest stable tag (vX.Y.Z), default to v0.0.0 if none
LATEST=$(git tag -l 'v*' --sort=-v:refname | head -1)
LATEST="${LATEST:-v0.0.0}"

# Parse and bump
IFS='.' read -r MAJOR MINOR PATCH <<< "${LATEST#v}"
case "$BUMP" in
  major) MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0 ;;
  minor) MINOR=$((MINOR + 1)); PATCH=0 ;;
  patch) PATCH=$((PATCH + 1)) ;;
esac
NEW_VERSION="v${MAJOR}.${MINOR}.${PATCH}"

echo "Releasing $LATEST -> $NEW_VERSION"

if [[ -z "$SKIP_CONFIRM" ]]; then
  read -r -p "Continue? [y/N] " answer
  if [[ ! "$answer" =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
  fi
fi

git tag "$NEW_VERSION"
git push origin "$NEW_VERSION"
echo "Tag $NEW_VERSION pushed."

# --- Monitor workflows ---

echo ""
echo "Waiting for GitHub Actions..."

TAG_SHA=$(git rev-parse "$NEW_VERSION")
MAX_WAIT=300  # 5 minutes
POLL_INTERVAL=15
WAITED=0

while [ $WAITED -lt $MAX_WAIT ]; do
  sleep $POLL_INTERVAL
  WAITED=$((WAITED + POLL_INTERVAL))

  # Get all runs triggered by this tag push
  RUNS=$(gh run list --commit "$TAG_SHA" --limit 10 --json name,status,conclusion,url 2>/dev/null || echo "[]")

  TOTAL=$(echo "$RUNS" | jq length)
  COMPLETED=$(echo "$RUNS" | jq '[.[] | select(.status == "completed")] | length')
  FAILED=$(echo "$RUNS" | jq '[.[] | select(.conclusion == "failure")] | length')

  if [ "$TOTAL" -eq 0 ]; then
    continue  # Workflows haven't started yet
  fi

  if [ "$FAILED" -gt 0 ]; then
    echo ""
    echo "Workflow failure:"
    echo "$RUNS" | jq -r '.[] | select(.conclusion == "failure") | "  \(.name): \(.url)"'
    exit 1
  fi

  if [ "$COMPLETED" -eq "$TOTAL" ]; then
    echo ""
    echo "All workflows passed:"
    echo "$RUNS" | jq -r '.[] | "  \(.name): \(.conclusion)"'
    echo ""
    echo "$NEW_VERSION released successfully!"
    exit 0
  fi

  printf "."
done

echo ""
echo "Timed out waiting for workflows (${MAX_WAIT}s). Check manually:"
echo "  https://github.com/$(gh repo view --json nameWithOwner -q .nameWithOwner)/actions"
exit 1
