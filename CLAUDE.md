# Claude Code Guidelines

## Style
- No emojis, no [NEW] markers, no "vs" comparisons
- Concise, technical, factual only
- No fluff, benefits sections, or marketing language

## Docs
- Start with practical info
- Minimal code examples
- No motivational or sales language

## Commits
- Imperative mood: "Add feature" not "Added feature"
- No emojis

## Code Comments
- Explain "why" not "what"
- No decorative elements or TODO comments

## Pi Access

```bash
ssh tars-pi  # tars.local or Tailscale: tars, user: mac, repo: ~/tars-daemon
```

## PyPI Release

Credentials are in `~/.pypirc` on the Pi.

```bash
ssh tars-pi
cd ~/tars-daemon
source venv/bin/activate
# 1. Bump version in pyproject.toml
# 2. Commit the bump
rm -rf dist/
python -m build
python -m twine upload dist/tars_robot-<version>*
```
