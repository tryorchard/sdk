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

Bump the version in `python/pyproject.toml`, `python/orchard_sdk/_version.py` and `typescript/package.json`, then publish each package.
