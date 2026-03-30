# Forge Compute Control Desk

## Project Status

**Bootstrap completed:** 2026-03-30

## Quick Start

1. Copy `.env.template` to `.env` and fill in values
2. Enable required APIs in Google Cloud Console
3. Create service account with appropriate scopes
4. Create Sheets spreadsheet and note its ID
5. Create Drive folder for evidence and note its ID
6. Run `python -m src.core.bootstrap` to validate

## Project Structure

```
forge-cloud-control-desk/
├── config/          # Configuration files (schemas, models)
├── data/            # Local state, logs,缓存
├── docs/            # Documentation (architecture, runbooks)
├── src/             # Source code
│   ├── core/        # Core business logic
│   ├── integrations/ # Google API integrations
│   └── ui/          # Dashboard UI code
├── tests/           # Test suite
├── .env             # Environment variables (gitignored)
└── .env.template    # Environment template
```

## Phase Plan

- **Phase 1**: Design & foundation (done)
- **Phase 2**: Thin end-to-end flow (next)
- **Phase 3**: Broaden action set
- **Phase 4**: Operational hardening

## Solo Governance Rules

1. No destructive action without confirmation
2. No create action without register entry
3. No "success" state until operation resource confirms
4. No important action without Drive evidence
5. No silent failures

## Next Steps

Run `make validate` to verify environment setup.
Run `make start` to launch the development server.

---

*Project bootstrap complete.*
