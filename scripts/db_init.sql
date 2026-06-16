-- Auto-generiert fuer natives Deployment der App 'personal'. Enthaelt das DB-Passwort.
-- Idempotent: Rolle + DB werden nur angelegt, falls nicht vorhanden.
\set ON_ERROR_STOP on
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'personal_user') THEN
      CREATE ROLE personal_user WITH LOGIN PASSWORD 'BITTE_STARKES_PASSWORT_EINSETZEN';
   ELSE
      ALTER ROLE personal_user WITH LOGIN PASSWORD 'BITTE_STARKES_PASSWORT_EINSETZEN';
   END IF;
END
$$;
ALTER ROLE personal_user SET client_encoding TO 'utf8';
ALTER ROLE personal_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE personal_user SET timezone TO 'Europe/Berlin';
SELECT format('CREATE DATABASE personal_db OWNER personal_user ENCODING ''UTF8'' TEMPLATE template0')
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'personal_db')
\gexec
GRANT ALL PRIVILEGES ON DATABASE personal_db TO personal_user;
