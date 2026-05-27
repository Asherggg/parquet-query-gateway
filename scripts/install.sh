#!/usr/bin/env bash
set -euo pipefail

DATA_ROOT="/home/ai_ds/sd_data_center"
CONFIG_PATH="config/production.yml"
PORT="8080"
INSTALL_OPENCLI="auto"
OVERWRITE_CONFIG="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --data-root)
      DATA_ROOT="$2"
      shift 2
      ;;
    --config)
      CONFIG_PATH="$2"
      shift 2
      ;;
    --port)
      PORT="$2"
      shift 2
      ;;
    --overwrite-config)
      OVERWRITE_CONFIG="true"
      shift
      ;;
    --skip-opencli)
      INSTALL_OPENCLI="false"
      shift
      ;;
    -h|--help)
      cat <<EOF
Usage: ./scripts/install.sh [options]

Options:
  --data-root PATH       Parquet data root. Default: /home/ai_ds/sd_data_center
  --config PATH          Config path to create. Default: config/production.yml
  --port PORT            Gateway port for smoke-test hints. Default: 8080
  --overwrite-config     Replace an existing config file.
  --skip-opencli         Do not install/register the OpenCLI plugin.
EOF
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 2
      ;;
  esac
done

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required" >&2
  exit 1
fi

python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

INIT_ARGS=(init-config --data-root "$DATA_ROOT" --output "$CONFIG_PATH")
if [[ "$OVERWRITE_CONFIG" == "true" ]]; then
  INIT_ARGS+=(--overwrite)
fi

INIT_OUTPUT="$(python -m parquet_gateway.cli "${INIT_ARGS[@]}")"
echo "$INIT_OUTPUT"
ADMIN_TOKEN="$(python -c 'import json,sys; print(json.load(sys.stdin)["admin_token"])' <<<"$INIT_OUTPUT")"

if [[ "$INSTALL_OPENCLI" != "false" ]]; then
  if ! command -v opencli >/dev/null 2>&1; then
    if command -v npm >/dev/null 2>&1; then
      npm install -g @jackwener/opencli
    else
      echo "npm is not installed; skipping OpenCLI installation" >&2
      INSTALL_OPENCLI="false"
    fi
  fi
  if [[ "$INSTALL_OPENCLI" != "false" ]]; then
    opencli plugin install "file://$PWD"
  fi
fi

cat <<EOF

Installation complete.

Start the gateway:
  source .venv/bin/activate
  export PARQUET_GATEWAY_CONFIG="$CONFIG_PATH"
  export PARQUET_GATEWAY_AUDIT_DB="audit.sqlite3"
  parquet-gateway

In another shell, verify with:
  export PARQUET_GATEWAY_URL="http://127.0.0.1:$PORT"
  export PARQUET_GATEWAY_TOKEN="$ADMIN_TOKEN"
  parquet-gw smoke-test
EOF
