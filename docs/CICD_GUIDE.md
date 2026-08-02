# Backend — CI/CD Guide

Two workflows in `.github/workflows/`:

## `ci.yml` — every PR and every push to `dev`/`uat`

```
lint  → ruff check, black --check, isort --check-only, mypy
test  → spins up a postgres:16-alpine service container, runs `alembic upgrade head`, then pytest
build → docker build (not pushed — validates the Dockerfile builds cleanly)
```
`test` and `lint` run in parallel; `build` waits for both. All three must pass before a
PR can merge (branch protection — configure once in GitHub repo settings).

## `release.yml` — every push to `main`

```
release-please        → scans Conventional Commits since the last release, opens/updates
                         a Release PR with the computed version + changelog
[on Release PR merge]  → tags vX.Y.Z, publishes a GitHub Release with generated notes
build-and-push          → builds the Docker image, pushes ghcr.io/.../paisa-backend:{vX.Y.Z,latest}
deploy                  → curls the Render Deploy Hook — Render re-pulls :latest and restarts
```
See the workspace `docs/RELEASE_PROCESS.md` for the versioning rules and
`docs/DEPLOYMENT_GUIDE.md` for one-time Render/GHCR setup and required secrets
(`RENDER_DEPLOY_HOOK_URL`).

**Required GitHub Actions secrets for this repo:** `RENDER_DEPLOY_HOOK_URL` (the
`GITHUB_TOKEN` used for GHCR push is automatic — no setup needed).
