#!/bin/bash
# Bump version and sync everywhere
# Usage: ./scripts/bump_version.sh <major|minor|patch>

set -e

if [ -z "$1" ]; then
    echo "Usage: ./scripts/bump_version.sh <major|minor|patch>"
    exit 1
fi

BUMP_TYPE=$1

# Get current version
CURRENT=$(grep 'version =' pyproject.toml | sed -E 's/version = "(.+)"/\1/')
IFS='.' read -r -a VERSION_PARTS <<< "$CURRENT"

MAJOR=${VERSION_PARTS[0]}
MINOR=${VERSION_PARTS[1]}
PATCH=${VERSION_PARTS[2]}

case $BUMP_TYPE in
    major)
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
    minor)
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    patch)
        PATCH=$((PATCH + 1))
        ;;
    *)
        echo "Invalid bump type. Use: major, minor, or patch"
        exit 1
        ;;
esac

NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"

echo "Bumping version: $CURRENT → $NEW_VERSION"

# Update pyproject.toml
sed -i "s/version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml

# Sync to other files
python3 scripts/sync_version.py

echo "Version bumped to $NEW_VERSION"
echo "Files updated:"
echo "  - pyproject.toml"
echo "  - dashboard/backend/server.py"
echo "  - tars_sdk/_version.py (auto-syncs from package metadata)"
