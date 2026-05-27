# Parquet Query Gateway Design

## Goal

Build a small HTTP service plus OpenCLI-facing client that lets authenticated users query Parquet files on a server without granting direct filesystem, SSH, or database access. The service enforces dataset, column, and row permissions before DuckDB reads the files; the intended user entry point is `opencli parquet ...`.

## Architecture

The API is the only supported entry point. Clients send a restricted query DSL, not SQL and not file paths. The service authenticates the caller, looks up allowed datasets and columns from YAML configuration, adds mandatory row policies, generates parameterized SQL, executes it through DuckDB, and records an audit event.

```text
Client
  -> FastAPI authentication
  -> policy checks
  -> DSL-to-SQL compiler
  -> DuckDB read_parquet()
  -> Parquet files
```

## First-Version Scope

- Token authentication with users and roles defined in YAML.
- Dataset registry with logical dataset ids mapped to server-side Parquet paths.
- Dataset-level role checks.
- Column allow lists by role.
- Row policy injection from user attributes.
- Restricted operators: `=`, `!=`, `>`, `>=`, `<`, `<=`, `in`, `contains`, `startswith`.
- Aggregations: `count`, `sum`, `avg`, `min`, `max`.
- Mandatory result limit and query timeout settings.
- SQLite audit log for allowed and denied queries.
- JSON API responses.

## Out Of Scope

- Arbitrary SQL submitted by users.
- User-supplied filesystem paths.
- Mutation, export, file upload, or background jobs.
- OIDC/SSO integration. The token model is intentionally simple so it can later be replaced.

## API

- `GET /health` returns service status.
- `GET /datasets` returns datasets visible to the current user.
- `GET /datasets/{dataset}/schema` returns visible columns for one dataset.
- `POST /query` accepts the restricted DSL and returns rows plus metadata.

## OpenCLI Surface

The project is an OpenCLI plugin. Install it with:

```bash
opencli plugin install file:///absolute/path/to/this/project
```

After registration, users run:

```bash
opencli parquet datasets
opencli parquet schema orders
opencli parquet query orders --select order_id,amount --where "amount>=10"
```

The `parquet-gw` binary remains available as a debugging fallback, but the primary interface is the OpenCLI plugin.

## Feishu Auth

Feishu authorization should be implemented in the FastAPI gateway. The OpenCLI plugin should only pass a gateway token. The gateway can exchange Feishu OAuth/OIDC identity for internal roles and short-lived gateway tokens, keeping authorization decisions server-side.

## Security Rules

The server denies by default. A user must have at least one role listed by a dataset. Requested columns must be explicitly allowed for that user's roles. Row policies are appended by the server and cannot be disabled by the client. All generated SQL uses DuckDB parameters for filter values.

## Deployment Model

Run the service on the Parquet server. Put it behind Caddy, Nginx, or an existing internal gateway for HTTPS. Keep Parquet files readable only by the service account, not by all users.
