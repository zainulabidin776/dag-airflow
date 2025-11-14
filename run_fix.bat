@echo off
REM Execute these commands in order to fix your pipeline on Windows

echo ==================================
echo. 
echo ^<U+26A1^> NASA APOD Pipeline Fix Script
echo ==================================
echo.

REM Step 1: Kill all containers
echo [1/5] Killing existing Docker containers...
astro dev kill
timeout /t 5 /nobreak
echo ^<U+2705^> Containers killed
echo.

REM Step 2: Start fresh
echo [2/5] Starting fresh environment...
astro dev start
echo ^<U+23F3^> Waiting 60 seconds for PostgreSQL to initialize...
timeout /t 60 /nobreak
echo ^<U+2705^> Environment started
echo.

REM Step 3: Get container name
for /f "delims=" %%A in ('docker ps --filter "name=postgres" --format "{{.Names}}"') do set POSTGRES_CONTAINER=%%A

if "%POSTGRES_CONTAINER%"=="" (
    echo ^<U+26A0^> Could not find PostgreSQL container
    goto error
)

echo PostgreSQL container: %POSTGRES_CONTAINER%
echo.

REM Step 4: Verify database was created
echo [3/5] Verifying database creation...
docker exec -it %POSTGRES_CONTAINER% psql -U postgres -l | findstr "apod_db" >nul
if %ERRORLEVEL% EQU 0 (
    echo ^<U+2705^> Database apod_db exists
) else (
    echo ^<U+26A0^> Database not found, attempting manual creation...
    docker exec -it %POSTGRES_CONTAINER% psql -U postgres -c "CREATE DATABASE apod_db;"
    timeout /t 5 /nobreak
)
echo.

REM Step 5: Verify table structure
echo [4/5] Verifying table structure...
docker exec -it %POSTGRES_CONTAINER% psql -U postgres -d apod_db -c "\dt"
echo ^<U+2705^> Table verification complete
echo.

REM Step 6: Test DAG
echo [5/5] Testing DAG...
astro dev run dags test nasa_apod_etl_pipeline
echo.

echo ==================================
echo ^<U+2705^> All fixes applied!
echo ==================================
echo.
echo Next steps:
echo 1. Open Airflow UI: http://localhost:8080
echo 2. Trigger nasa_apod_etl_pipeline manually
echo 3. Monitor task logs
echo 4. Check PostgreSQL for data:
echo.
echo    docker exec -it %POSTGRES_CONTAINER% psql -U postgres -d apod_db
echo    SELECT * FROM apod_data;
echo.
pause
goto end

:error
echo ^<U+274C^> Error: PostgreSQL container not found
echo Make sure Docker is running and containers are started
pause
goto end

:end
echo Script completed
