# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## State of the project

Serverless Python API for cuy (guinea pig) farm yards and movements. Poetry manages dependencies with an in-project `.venv` (`poetry install`, `poetry run python ...`). No tests or linter yet.

## Commands

- Install deps / create `.venv`: `poetry install`
- Deploy: `serverless deploy` (needs the `serverless-python-requirements` plugin installed via `serverless plugin install -n serverless-python-requirements`; it uses Poetry)
- Invoke locally: `serverless invoke local --function listYards`

## Architecture

All code lives in `src/`:

- `models/` – Pydantic models/schemas (`Yard`, `YardCreate`, `YardUpdate`, `Movement`, `MovementCreate`, enums `MovementType`, `Gender`).
- `services/` – business logic (`yard_service`, `movement_service`). Movements adjust yard totals transactionally; `notDefined` gender is counted as babies.
- `routes/` – one Lambda handler per endpoint, wrapped with `@handler` from `utils/http.py` (maps validation/service errors to HTTP responses).
- `utils/` – reusable code: `db.py` (generic DynamoDB put/get/update/delete/scan/transact across tables), `http.py`.

`serverless.yml` declares the functions (`src.routes.<module>.<fn>`), HTTP API events and three DynamoDB tables: yards, yard-names (name uniqueness lock items) and movements. Table names come from env vars.
`.serverless/` (build output) is gitignored.
