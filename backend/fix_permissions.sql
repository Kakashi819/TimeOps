# PostgreSQL Permission Fix Commands

# Connect to PostgreSQL as superuser (postgres)
# Run these commands in your PostgreSQL client (pgAdmin, psql, etc.)

# 1. Connect to the timeops database
\c timeops;

# 2. Grant all privileges on the database to ayushadmin
GRANT ALL PRIVILEGES ON DATABASE timeops TO ayushadmin;

# 3. Grant usage on the public schema
GRANT USAGE ON SCHEMA public TO ayushadmin;

# 4. Grant create privileges on the public schema
GRANT CREATE ON SCHEMA public TO ayushadmin;

# 5. Grant all privileges on all tables in public schema
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ayushadmin;

# 6. Grant all privileges on all sequences in public schema
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ayushadmin;

# 7. Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ayushadmin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ayushadmin;

# 8. Make ayushadmin the owner of the database (optional but recommended)
ALTER DATABASE timeops OWNER TO ayushadmin;
