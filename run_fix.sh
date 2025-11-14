#!/bin/bash
# Execute these commands in order to fix your pipeline

echo "=================================="
echo "🔧 NASA APOD Pipeline Fix Script"
echo "=================================="
echo ""

# Step 1: Kill all containers
echo "[1/5] Killing existing Docker containers..."
astro dev kill
sleep 5
echo "✅ Containers killed"
echo ""

# Step 2: Start fresh
echo "[2/5] Starting fresh environment..."
astro dev start
echo "⏳ Waiting 60 seconds for PostgreSQL to initialize..."
sleep 60
echo "✅ Environment started"
echo ""

# Step 3: Verify database was created
echo "[3/5] Verifying database creation..."
docker exec -it $(docker ps --filter "name=postgres" --format "{{.Names}}" | head -1) psql -U postgres -l | grep apod_db
if [ $? -eq 0 ]; then
    echo "✅ Database apod_db exists"
else
    echo "⚠️  Database not found, attempting manual creation..."
    docker exec -it $(docker ps --filter "name=postgres" --format "{{.Names}}" | head -1) psql -U postgres -c "CREATE DATABASE apod_db;"
    sleep 5
fi
echo ""

# Step 4: Verify table structure
echo "[4/5] Verifying table structure..."
docker exec -it $(docker ps --filter "name=postgres" --format "{{.Names}}" | head -1) psql -U postgres -d apod_db -c "\dt"
echo "✅ Table verification complete"
echo ""

# Step 5: Test DAG
echo "[5/5] Testing DAG..."
astro dev run dags test nasa_apod_etl_pipeline
echo ""
echo "=================================="
echo "✅ All fixes applied!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Open Airflow UI: http://localhost:8080"
echo "2. Trigger nasa_apod_etl_pipeline manually"
echo "3. Monitor task logs"
echo "4. Check PostgreSQL for data:"
echo ""
echo "   docker exec -it <postgres-container> psql -U postgres -d apod_db"
echo "   SELECT * FROM apod_data;"
echo ""
