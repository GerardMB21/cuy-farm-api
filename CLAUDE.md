# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## State of the project

This is an unmodified Serverless Framework v4 "AWS Python" template scaffold. It contains a single Lambda function (`hello` in `handler.py`) with no event triggers, no persistence, no dependencies file, no tests, and no linter config. Not a git repository yet. Update this file as real structure emerges.

## Commands

- Deploy: `serverless deploy`
- Invoke deployed function: `serverless invoke --function hello`
- Invoke locally: `serverless invoke local --function hello`
- Bundle third-party Python deps: `serverless plugin install -n serverless-python-requirements`, then list dependencies in `requirements.txt` (this also creates `package.json`).

## Architecture

- `serverless.yml` defines the service (`cuy-farm-api`, org `gerardmatos`, app `cuy-farm-api`), provider AWS with runtime `python3.14` on `arm64`, and maps each function to a handler (`handler.hello` → `hello()` in `handler.py`). New Lambdas need a `functions:` entry here, and HTTP routes need an `events:` entry (none exist yet).
- Handlers follow the Lambda signature `(event, context)` and return an API-Gateway-style dict `{"statusCode": ..., "body": <json string>}`.
- `.serverless/` (build output) is gitignored.
