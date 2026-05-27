FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PARQUET_GATEWAY_CONFIG=/app/config/production.yml
ENV PARQUET_GATEWAY_AUDIT_DB=/app/state/audit.sqlite3

WORKDIR /app

COPY pyproject.toml README.md ./
COPY parquet_gateway ./parquet_gateway
RUN pip install --no-cache-dir .

RUN mkdir -p /app/config /app/state /home/ai_ds/sd_data_center

EXPOSE 8080

CMD ["uvicorn", "parquet_gateway.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8080"]
