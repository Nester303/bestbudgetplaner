-- ============================================================
--  Inicjalizacja bazy — uruchamiana raz przy pierwszym starcie
--  kontenera PostgreSQL (docker-entrypoint-initdb.d)
-- ============================================================

-- Rozszerzenia
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";    -- szybkie wyszukiwanie tekstowe

-- ============================================================
--  Domyślne kategorie systemowe (user_id = NULL)
-- ============================================================

-- Poczekaj aż tabela istnieje (migrations tworzą schemat)
-- Ten plik uruchamiany jest PRZED Flask-Migrate, więc tylko dane seed
-- Tabele tworzone są przez: docker compose exec backend flask db upgrade

-- Seed uruchamiamy przez osobny skrypt po migracji (patrz Makefile)
-- Ten plik zostawiamy na rozszerzenia PostgreSQL.
