# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## State of the project

Serverless Python API for cuy (guinea pig) farm yards and movements. Poetry manages dependencies with an in-project `.venv` (`poetry install`, `poetry run python ...`). No tests or linter yet.

## Commands

- Install deps / create `.venv`: `poetry install`
- Deploy: `serverless deploy` (Serverless v4 packages Python deps from Poetry natively via `custom.pythonRequirements`; no plugin needed)
- Run locally as HTTP server: `serverless offline start --param="runtime=python3.13"` (serverless-offline rejects `python3.14`; needs `npm install --save-dev serverless-offline serverless-dynamodb` and podman). `serverless-dynamodb` starts DynamoDB Local in a podman container on :8000 (in-memory) and creates the tables from `resources`; `db.py` points boto3 there when `IS_OFFLINE` is set.
- Invoke locally: `serverless invoke local --function listYards`

## Architecture

All code lives in `src/`:

- `models/` – Pydantic models/schemas (`Yard`, `YardCreate`, `YardUpdate`, `Movement`, `MovementCreate`, enums `MovementType`, `Gender`).
- `services/` – business logic (`yard_service`, `movement_service`). Movements adjust yard totals transactionally; `notDefined` gender is counted as babies.
- `routes/` – one Lambda handler per endpoint, wrapped with `@handler` from `utils/http.py` (maps validation/service errors to HTTP responses).
- `utils/` – reusable code: `db.py` (generic DynamoDB put/get/update/delete/scan/transact across tables), `http.py`, `openapi.py` (OpenAPI 3.1 spec built from the Pydantic models; update its `paths` when adding routes).
- `routes/docs.py` serves the spec at `GET /openapi.json` and a Scalar API reference UI at `GET /docs`.

`serverless.yml` declares the functions (`src.routes.<module>.<fn>`), HTTP API events and three DynamoDB tables: yards, yard-names (name uniqueness lock items) and movements. Table names come from env vars.
`.serverless/` (build output) is gitignored.
