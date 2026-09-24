-- ---------------------------------------------------------------------------
-- One PostgreSQL instance, one database + one login role per service.
--
-- Each role owns its own database and can see nothing else. This is the
-- whole point: a container per project costs 100-150 MB of RAM each, while
-- one shared instance costs ~200 MB total.
--
-- Passwords here come from the init environment for the demo. In a real
-- deployment they are injected as secrets, never committed.
-- ---------------------------------------------------------------------------

\set alpha_password `echo "${ALPHA_DB_PASSWORD:-alpha}"`
\set gamma_password `echo "${GAMMA_DB_PASSWORD:-gamma}"`

-- alpha ----------------------------------------------------------------------
CREATE ROLE alpha WITH LOGIN PASSWORD :'alpha_password';
CREATE DATABASE alpha OWNER alpha;
REVOKE ALL ON DATABASE alpha FROM PUBLIC;
GRANT CONNECT ON DATABASE alpha TO alpha;

-- gamma: a second tenant, to show the pattern is not a special case ----------
CREATE ROLE gamma WITH LOGIN PASSWORD :'gamma_password';
CREATE DATABASE gamma OWNER gamma;
REVOKE ALL ON DATABASE gamma FROM PUBLIC;
GRANT CONNECT ON DATABASE gamma TO gamma;

-- Lock down the public schema in each database so tenants cannot create
-- objects in one another's default namespace.
\connect alpha
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO alpha;

\connect gamma
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO gamma;
