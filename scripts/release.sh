#!/bin/bash
#
# Release script for ux3270
#
# Usage: ./scripts/release.sh VERSION [-n]
#
# Example:
#   ./scripts/release.sh 1.0.1      # Full release
#   ./scripts/release.sh 1.0.1 -n   # Dry run (prints push command)

set -e

usage() {
    echo "Usage: $0 VERSION [-n]"
    echo ""
    echo "Arguments:"
    echo "  VERSION   Version number (e.g., 1.0.1)"
    echo "  -n        Dry run: print push command instead of executing it"
    exit 1
}

if [[ $# -lt 1 ]]; then
    usage
fi

VERSION="$1"
DRY_RUN=false

if [[ "$2" == "-n" ]]; then
    DRY_RUN=true
fi

# Validate version format (simple check for x.y.z)
if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Version must be in format x.y.z (e.g., 1.0.1)"
    exit 1
fi

# Check for uncommitted changes
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "Error: Working directory has uncommitted changes"
    exit 1
fi

# Run tests (including doc snippet validation)
echo "Running tests..."
if ! uv run pytest; then
    echo "Error: Tests failed"
    exit 1
fi

# Check if tag already exists
if git rev-parse "v$VERSION" >/dev/null 2>&1; then
    echo "Error: Tag v$VERSION already exists"
    exit 1
fi

echo "Releasing version $VERSION..."

# Update version in pyproject.toml
sed -i '' "s/^version = \".*\"/version = \"$VERSION\"/" pyproject.toml

# Commit the version bump
git add pyproject.toml
git commit -m "Bump version to $VERSION"

# Create the tag
git tag "v$VERSION"

echo ""
echo "Version bumped and tagged locally."
echo ""

# Push or print push command
if $DRY_RUN; then
    echo "Dry run mode. To complete the release, run:"
    echo ""
    echo "  git push origin main --tags"
    echo ""
    echo "To undo the local changes:"
    echo ""
    echo "  git tag -d v$VERSION && git reset --hard HEAD~1"
else
    git push origin main --tags
    echo "Release v$VERSION pushed successfully!"
fi
