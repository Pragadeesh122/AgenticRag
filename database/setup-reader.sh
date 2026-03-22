#!/bin/bash
# Creates the read-only LLM user with password from environment
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER llm_reader WITH PASSWORD '${DB_PASSWORD}';
    GRANT CONNECT ON DATABASE ${POSTGRES_DB} TO llm_reader;
    GRANT USAGE ON SCHEMA public TO llm_reader;
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO llm_reader;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO llm_reader;
EOSQL
