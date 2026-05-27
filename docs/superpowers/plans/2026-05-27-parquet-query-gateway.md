# Parquet Query Gateway Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a FastAPI service and OpenCLI-facing client that provide permission-controlled queries over server-local Parquet files.

**Architecture:** Clients use `opencli parquet ...` through an OpenCLI plugin. The plugin calls the FastAPI service with a restricted JSON DSL instead of SQL. The service authenticates bearer tokens, applies YAML dataset/column/row policies, compiles safe parameterized DuckDB SQL, executes it, and writes audit events to SQLite.

**Tech Stack:** Python 3.12, FastAPI, DuckDB, PyYAML, Pydantic, SQLite, pytest.

---

### Task 1: Project Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `.gitignore`
- Create: `parquet_gateway/__init__.py`

- [x] Add Python package metadata and runtime dependencies.
- [x] Add local development and test commands.
- [x] Ignore virtual environments, caches, database files, and generated sample data.

### Task 2: Configuration And Auth

**Files:**
- Create: `parquet_gateway/config.py`
- Create: `parquet_gateway/auth.py`
- Create: `config/example.yml`
- Test: `tests/test_config_auth.py`

- [x] Load YAML config into typed models.
- [x] Authenticate bearer tokens against configured users.
- [x] Compute role-based dataset visibility.

### Task 3: Query DSL Compiler

**Files:**
- Create: `parquet_gateway/models.py`
- Create: `parquet_gateway/policy.py`
- Create: `parquet_gateway/query_builder.py`
- Test: `tests/test_query_builder.py`

- [x] Validate dataset, selected columns, filters, groupings, aggregations, ordering, and limit.
- [x] Inject server-side row policies.
- [x] Generate parameterized SQL over `read_parquet(?)`.

### Task 4: DuckDB Execution And Audit

**Files:**
- Create: `parquet_gateway/executor.py`
- Create: `parquet_gateway/audit.py`
- Test: `tests/test_executor_audit.py`

- [x] Execute compiled queries in read-only DuckDB connections.
- [x] Return rows and metadata.
- [x] Store audit events for allowed and denied requests.

### Task 5: FastAPI App

**Files:**
- Create: `parquet_gateway/app.py`
- Create: `parquet_gateway/main.py`
- Test: `tests/test_app.py`

- [x] Implement `GET /health`, `GET /datasets`, `GET /datasets/{dataset}/schema`, and `POST /query`.
- [x] Convert policy and validation failures into clear HTTP responses.
- [x] Wire config path and audit DB path through environment variables.

### Task 6: Verification

**Files:**
- Modify: `README.md`

- [x] Run the test suite.
- [x] Run a small end-to-end query against generated Parquet data.
- [x] Document setup, configuration, and curl usage.

### Task 7: OpenCLI Client Surface

**Files:**
- Create: `parquet_gateway/cli.py`
- Modify: `pyproject.toml`
- Modify: `README.md`
- Test: `tests/test_cli.py`

- [x] Add `parquet-gw datasets`, `parquet-gw schema <dataset>`, and `parquet-gw query <dataset>`.
- [x] Read `PARQUET_GATEWAY_URL` and `PARQUET_GATEWAY_TOKEN`.
- [x] Document `opencli external register parquet --binary parquet-gw`.

### Task 8: OpenCLI Native Plugin

**Files:**
- Create: `opencli-plugin.json`
- Create: `gateway-client.js`
- Create: `datasets.js`
- Create: `schema.js`
- Create: `query.js`
- Create: `audit.js`
- Test: `tests/test_opencli_plugin.py`

- [x] Register `parquet` site commands through `@jackwener/opencli/registry`.
- [x] Keep authorization and Parquet access in the gateway service.
- [x] Document `opencli plugin install file:///...` as the primary user path.
