# Build Scripts

Automated scripts for version management and building.

## Version Management

### Bump Version

Automatically bump version across all files:

```bash
# Bump patch version (0.3.4 → 0.3.5)
./scripts/bump_version.sh patch

# Bump minor version (0.3.4 → 0.4.0)
./scripts/bump_version.sh minor

# Bump major version (0.3.4 → 1.0.0)
./scripts/bump_version.sh major
```

This updates:
- `pyproject.toml` (source of truth)
- `dashboard/backend/server.py`
- `tars_sdk/_version.py` (auto-syncs from package metadata)

### Sync Version Manually

If you manually edit `pyproject.toml`, sync to other files:

```bash
python3 scripts/sync_version.py
```

## Building Package

### Automated Build

```bash
# Syncs versions, cleans, and builds
./scripts/build.sh
```

### Manual Build

```bash
# Clean
rm -rf dist/ build/ *.egg-info

# Build
python -m build
```

## Publishing to PyPI

```bash
# Build first
./scripts/build.sh

# Upload to PyPI
python -m twine upload dist/*

# Or upload specific version
python -m twine upload dist/tars_robot-0.3.4*
```

## Release Workflow

Complete workflow for new release:

```bash
# 1. Bump version
./scripts/bump_version.sh patch

# 2. Commit version bump
git add pyproject.toml dashboard/backend/server.py tars_sdk/_version.py
git commit -m "bump: version 0.3.5"
git push

# 3. Build package
./scripts/build.sh

# 4. Create tag
git tag v0.3.5
git push origin v0.3.5

# 5. Upload to PyPI
python -m twine upload dist/tars_robot-0.3.5*

# 6. Create GitHub release
# Go to https://github.com/latishab/tars/releases/new
# - Tag: v0.3.5
# - Title: v0.3.5 - Description
# - Add changelog
```

## Version Sources

- **Single source of truth**: `pyproject.toml`
- **Auto-synced files**:
  - `dashboard/backend/server.py` (via sync_version.py)
  - `tars_sdk/_version.py` (via importlib.metadata at runtime)
