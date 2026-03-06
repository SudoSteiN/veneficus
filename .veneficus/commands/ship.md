# Ship — Release Preparation

Prepare the current state for release: changelog, version bump, final checks.

## Input
Version or release type: $ARGUMENTS (e.g., "patch", "minor", "major", "v1.2.3")

## Protocol

### 1. Pre-flight Checks
- Run full test suite — all must pass
- Check for uncommitted changes — commit or stash
- Review `.veneficus/docs/features.json` — all `in_progress` features should be `done` or deferred
- Run lint/format checks

### 2. Changelog
- Read recent commits since last tag: `git log $(git describe --tags --abbrev=0 2>/dev/null || echo "HEAD~20")..HEAD --oneline`
- Categorize changes:
  - **Added**: New features
  - **Changed**: Modifications to existing features
  - **Fixed**: Bug fixes
  - **Removed**: Removed features
- Write/update CHANGELOG.md in Keep a Changelog format

### 3. Version Bump
- Determine new version based on input (semver)
- Update version in relevant files (package.json, pyproject.toml, etc.)
- Update any version references in docs

### 4. Final Commit
- Stage changelog and version files
- Commit: `chore: release vX.Y.Z`
- Create git tag: `git tag vX.Y.Z`

### 5. Summary
```
## Release: vX.Y.Z

### Changes
- [changelog summary]

### Checklist
- [x] Tests passing
- [x] Changelog updated
- [x] Version bumped
- [x] Tagged

### Next Steps
- Push: `git push && git push --tags`
- Deploy: [project-specific deployment steps]
```

## Rules
- **Never push automatically**. Prepare the release — the human pushes.
- **All tests must pass**. Don't ship broken code.
- **Changelog is for humans**. Write clear, useful descriptions.
