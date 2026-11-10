# Contributing

The SDKs talk only to the public Orchard HTTP/WebSocket API. Keep the two packages in step: a new endpoint lands in both, with the same name (snake_case / camelCase), a test, and an entry in each `docs/reference.md`.

## Python (`python/`)

```bash
cd python
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest
mypy orchard_sdk
```

Tests run against `httpx.MockTransport`; no control plane needed. Set `ORCHARD_SMOKE=1` plus `ORCHARD_API_URL`/`ORCHARD_API_KEY` to run the live smoke test.

## TypeScript (`typescript/`)

```bash
cd typescript
npm install
npm run typecheck   # src + examples
npm test
npm run build       # ESM + CJS + .d.ts into dist/
```

Examples import `@orchard/sdk` by name, so build first, then run one with `node --experimental-strip-types examples/quickstart.mts`.

## Releasing

Each package releases independently from a tag; GitHub Actions tests, builds and publishes it.

```bash
# Python: bump python/pyproject.toml and python/orchard_sdk/_version.py, commit, then
git tag python-v0.0.2 && git push origin python-v0.0.2

# TypeScript: bump typescript/package.json (npm version 0.0.2 --no-git-tag-version), commit, then
git tag typescript-v0.0.2 && git push origin typescript-v0.0.2
```

The workflow fails if the tag doesn't match the package version.
