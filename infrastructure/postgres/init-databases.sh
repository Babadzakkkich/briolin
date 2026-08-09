#!/usr/bin/env bash
set -euo pipefail

# One PostgreSQL instance, isolated databases/users per business service.
# This script is executed only on the first initialization of postgres-db.

create_role() {
  local role="$1"
  local password="$2"

  if ! psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -tAc \
      "SELECT 1 FROM pg_roles WHERE rolname='${role}'" | grep -q 1; then
    psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -v ON_ERROR_STOP=1 \
      -c "CREATE ROLE \"${role}\" LOGIN PASSWORD '${password}';"
  fi
}

create_database() {
  local database="$1"
  local owner="$2"

  if ! psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -tAc \
      "SELECT 1 FROM pg_database WHERE datname='${database}'" | grep -q 1; then
    createdb --username "$POSTGRES_USER" --owner "$owner" "$database"
  fi
}

create_service_database() {
  local database="$1"
  local role="$2"
  local password="$3"

  create_role "$role" "$password"
  create_database "$database" "$role"
}

create_service_database "auth_db"     "auth_user"     "auth_password"
create_service_database "user_db"     "user_user"     "user_password"
create_service_database "profile_db"  "profile_user"  "profile_password"
create_service_database "testing_db"  "testing_user"  "testing_password"
create_service_database "chat_db"     "chat_user"     "chat_password"
create_service_database "matching_db" "matching_user" "matching_password"
create_service_database "media_db"    "media_user"    "media_password"

# profile-service uses pgvector directly. matching_db keeps the extension too,
# matching the previous pgvector-based database container setup.
psql --username "$POSTGRES_USER" --dbname "profile_db" -v ON_ERROR_STOP=1 \
  -c "CREATE EXTENSION IF NOT EXISTS vector;"
psql --username "$POSTGRES_USER" --dbname "matching_db" -v ON_ERROR_STOP=1 \
  -c "CREATE EXTENSION IF NOT EXISTS vector;"

echo "Business databases initialized successfully."
