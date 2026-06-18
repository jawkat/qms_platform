#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
for i in $(seq 1 30); do
    if python -c "
import psycopg2
psycopg2.connect(
    host='db', port=5432, dbname='qms_platform',
    user='qms_user', password='qms_password'
)
" 2>/dev/null; then
        echo "PostgreSQL ready."
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 2
done

echo "Running bootstrap..."
python bootstrap_database.py

echo "Starting application..."
exec "$@"
