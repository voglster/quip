# Release Process

## Quick Release

```bash
./scripts/release.sh patch    # v0.6.6 -> v0.6.7
./scripts/release.sh minor    # v0.6.6 -> v0.7.0
./scripts/release.sh major    # v0.6.6 -> v1.0.0
./scripts/release.sh patch -y # skip confirmation
```

The script will:
1. Run preflight checks (clean tree, on main, lint, tests)
2. Compute next version from latest git tag
3. Create and push the tag
4. Poll GitHub Actions until release completes (or timeout after 5 min)

## What Happens on GitHub

Tag push triggers `.github/workflows/release.yml`:
1. Version is injected into `desktop/_version.py`
2. Lint + tests run as a gate
3. Release archives are built (tar.gz + zip)
4. AI generates release notes from commits since last tag
5. GitHub Release is created with archives and notes

## Version Management

Version lives **only in git tags**. No files are edited for releases.

- `desktop/_version.py` defaults to `"0.0.0-dev"` in the repo
- CI overwrites it with the tag version during release builds
- `pyproject.toml` uses `dynamic = ["version"]` + hatchling to read `_version.py`

## Secrets Required

Set on the repo via `gh secret set <name> -R voglster/quip`:
- `LLM_API_KEY` - API key for AI release notes generation
- `LLM_BASE_URL` - LLM endpoint URL
- `LLM_MODEL` - Model name

If LLM secrets aren't configured, release notes fall back to a commit log.

## Rollback

```bash
# Delete release and tag
gh release delete "vX.Y.Z" --yes
git tag -d "vX.Y.Z"
git push origin --delete "vX.Y.Z"
```
