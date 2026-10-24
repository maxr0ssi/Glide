# Learnings — web-ui-publish-lint-cleanup

## What surprised us
- `publish-web-ui.yml` published to GitHub Packages on every push to main while `package.json`
  `publishConfig` pointed at npmjs, so the two registries could drift.
- `npm run lint` had never worked: ESLint 9 was installed with no flat config, and `--ext` is not
  accepted by flat config.
- The lockfile root still said `@glide/web-ui` and listed react/react-dom as dependencies (they are
  peer dependencies); `npm install` rewrote both.
- The React Compiler rules in eslint-plugin-react-hooks 7 flagged `useGlide` returning
  `configRef.current` during render. It was stable (never reassigned), but the `useRef(mergeConfig(...))`
  initialiser re-merged config on every render.
- The shared `.git/hooks/pre-commit` pointed at a Python from another project's venv.

## Decisions made (and why)
- Publishing is manual only. Trusted publishing (OIDC) is preferred; `NPM_TOKEN` is the fallback. The
  early credential check is skipped when the repo variable `NPM_TRUSTED_PUBLISHING` is `true`, so OIDC
  setups don't need a token. Real publishes are main-only; `dry_run` works from any branch.
- `useGlide` config moved to a lazy `useState`: same mount-time semantics, one merge.
- `react-hooks/globals` and `react-hooks/refs` are off for `tests/**` only, because the harnesses capture
  hook output in module variables on purpose.
- pre-commit is installed with pipx (pipx from Homebrew), not a repo venv, so it serves every worktree.

## Follow-ups
- Owner: configure npm trusted publishing for `publish-web-ui.yml` (and set
  `NPM_TRUSTED_PUBLISHING=true`), or add an `NPM_TOKEN` secret.

### PATCH SUMMARY
- Mode: Doing
- Changed files:
  - .github/workflows/publish-web-ui.yml, .github/workflows/ci.yml, Makefile
  - apps/web-ui/eslint.config.js, apps/web-ui/package.json, apps/web-ui/package-lock.json
  - apps/web-ui/src/hooks/useGlide.ts
  - apps/web-ui/README.md, docs/DEPENDENCIES.md, CHANGELOG.md, docs/learnings/
- Why: stop accidental GitHub Packages publishes, make npm publishing deliberate and reproducible, fix
  the stale package name, and make lint real.
- How: workflow_dispatch + OIDC/NPM_TOKEN; ESLint flat config; lazy config state in `useGlide`.
- Tests: existing 99 vitest tests pass; lint, typecheck and build:lib are clean.
- Risks & Mitigations: the publish workflow can't be exercised until the owner sets up auth; the
  `dry_run` input allows a safe first run.
