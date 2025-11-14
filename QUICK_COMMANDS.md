# Quick Commands to Fix and Verify Your Setup

## 🔧 Clean Restart (IMPORTANT - Do this first!)

```bash
# Kill all containers
astro dev kill

# Start fresh
astro dev start

# Wait 30-60 seconds for PostgreSQL to initialize
```

## ✅ Verify PostgreSQL Setup

```bash
# Connect to PostgreSQL
docker exec -it $(docker ps --filter "name=postgres" --format "{{.Names}}" | head -1) psql -U postgres

# Inside psql, run:
\l                    # List databases - should see 'apod_db'
\c apod_db            # Connect to apod_db
\dt                   # List tables - should see 'apod_data'
\d apod_data          # Describe table structure
\di                   # List indexes
SELECT * FROM pg_tables WHERE schemaname = 'public';
```

## 🧪 Test the Pipeline

```bash
# Parse DAG for errors
astro dev run dags list

# Test single DAG
astro dev run dags test nasa_apod_etl_pipeline

# Run tasks individually
astro dev run tasks test nasa_apod_etl_pipeline extract_data
astro dev run tasks test nasa_apod_etl_pipeline transform_data
astro dev run tasks test nasa_apod_etl_pipeline load_to_postgres
```

## 🔍 Check Connections in Airflow

```bash
# Access Airflow UI at http://localhost:8080
# Admin > Connections > postgres_apod
# Verify:
# - Conn ID: postgres_apod
# - Conn Type: postgres
# - Host: postgres
# - Database: apod_db
# - Login: postgres
# - Password: postgres
# - Port: 5432
```

## 📋 Manual Database Initialization (if init_db.sql didn't work)

```bash
# Get container name
docker ps --filter "name=postgres" --format "{{.Names}}"

# Connect and create database
docker exec -it <container-name> psql -U postgres -c "CREATE DATABASE apod_db;"

# Verify
docker exec -it <container-name> psql -U postgres -l | grep apod_db
```

## 🐛 Debugging

```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Check Airflow webserver logs
docker-compose logs webserver

# Check Airflow scheduler logs
docker-compose logs scheduler

# Check Airflow triggerer logs
docker-compose logs triggerer

# Interactive bash in postgres container
docker exec -it <postgres-container-name> /bin/bash
```

## 🔄 Restart Services Without Full Kill

```bash
# Restart only PostgreSQL
docker-compose restart postgres

# Restart all services
docker-compose restart
```

## 📊 Expected Output After Fix

When you run `\dt` in PostgreSQL, you should see:
```
                List of relations
 Schema |     Name      | Type  | Owner
--------+---------------+-------+-------
 public | apod_data     | table | postgres
```

## ⚡ Quick Health Check Script

```bash
#!/bin/bash
echo "=== Checking PostgreSQL ==="
docker exec -it $(docker ps --filter "name=postgres" --format "{{.Names}}" | head -1) pg_isready -U postgres
echo ""
echo "=== Checking Airflow Connection ==="
astro dev run connections list | grep postgres_apod
echo ""
echo "=== Checking DAG ==="
astro dev run dags list | grep nasa_apod_etl_pipeline
```

Save this as `health_check.sh` and run with `bash health_check.sh`
