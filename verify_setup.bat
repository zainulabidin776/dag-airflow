@echo off
REM Verification Script for NASA APOD ETL Pipeline (Windows)
REM Checks if all components are properly configured

cls
echo.
echo ==========================================
echo ^🔍 NASA APOD ETL Pipeline Verification
echo ==========================================
echo.

setlocal enabledelayedexpansion

set passed=0
set failed=0

REM 1. Check Python version
echo [1/10] Checking Python version...
python --version >nul 2>&1
if !errorlevel! equ 0 (
    echo [OK] ^✓ Python installed
    set /a passed+=1
) else (
    echo [FAIL] ^✗ Python not found
    set /a failed+=1
)

REM 2. Check Astronomer CLI
echo [2/10] Checking Astronomer CLI...
astro version >nul 2>&1
if !errorlevel! equ 0 (
    echo [OK] ^✓ Astronomer CLI installed
    set /a passed+=1
) else (
    echo [FAIL] ^✗ Astronomer CLI not found (run: pip install astronomer)
    set /a failed+=1
)

REM 3. Check Docker
echo [3/10] Checking Docker...
docker --version >nul 2>&1
if !errorlevel! equ 0 (
    echo [OK] ^✓ Docker installed
    set /a passed+=1
) else (
    echo [FAIL] ^✗ Docker not found
    set /a failed+=1
)

REM 4. Check DAG file
echo [4/10] Checking DAG file...
if exist "dags\nasa_apod_pipeline.py" (
    echo [OK] ^✓ DAG file exists
    set /a passed+=1
) else (
    echo [FAIL] ^✗ DAG file not found
    set /a failed+=1
)

REM 5. Check ETL functions
echo [5/10] Checking ETL functions...
if exist "include\scripts\etl_functions.py" (
    echo [OK] ^✓ ETL functions exist
    set /a passed+=1
) else (
    echo [FAIL] ^✗ ETL functions not found
    set /a failed+=1
)

REM 6. Check Version control script
echo [6/10] Checking version control script...
if exist "include\scripts\version_control.py" (
    echo [OK] ^✓ Version control script exists
    set /a passed+=1
) else (
    echo [FAIL] ^✗ Version control script not found
    set /a failed+=1
)

REM 7. Check requirements.txt
echo [7/10] Checking Python requirements...
if exist "requirements.txt" (
    echo [OK] ^✓ requirements.txt exists
    set /a passed+=1
) else (
    echo [FAIL] ^✗ requirements.txt not found
    set /a failed+=1
)

REM 8. Check Docker Compose
echo [8/10] Checking Docker Compose config...
if exist "docker-compose.override.yml" (
    echo [OK] ^✓ docker-compose.override.yml exists
    set /a passed+=1
) else (
    echo [FAIL] ^✗ docker-compose.override.yml not found
    set /a failed+=1
)

REM 9. Check init DB script
echo [9/10] Checking database initialization...
if exist "init_db.sql" (
    echo [OK] ^✓ init_db.sql exists
    set /a passed+=1
) else (
    echo [FAIL] ^✗ init_db.sql not found
    set /a failed+=1
)

REM 10. Check GitHub token in .env
echo [10/10] Checking GitHub token...
findstr /M "GITHUB_TOKEN=" .env >nul 2>&1
if !errorlevel! equ 0 (
    echo [OK] ^✓ GitHub token configured
    set /a passed+=1
) else (
    echo [FAIL] ^✗ GitHub token not found in .env
    set /a failed+=1
)

echo.
echo ==========================================
echo ^📋 Configuration Summary
echo ==========================================
echo.

echo DAG Name: nasa_apod_etl_pipeline
echo Tasks:
echo   1. extract_data
echo   2. transform_data
echo   3. load_to_postgres
echo   4. load_to_csv
echo   5. initialize_dvc
echo   6. version_with_dvc
echo   7. commit_to_git
echo   8. push_to_github

echo.
echo Database:
echo   - Type: PostgreSQL 12.6
echo   - Database: apod_db
echo   - Table: apod_data
echo   - Connection ID: postgres_apod

echo.
echo Storage:
echo   - CSV: /usr/local/airflow/include/data/apod_data.csv
echo   - Version Control: Git + GitHub
echo   - Data Versioning: DVC (with auto-fallback)

echo.
echo GitHub:
echo   - User: zainulabidin776
echo   - Repo: https://github.com/zainulabidin776/dag-airflow
echo   - Authentication: PAT (Personal Access Token) ^✓

echo.
echo ==========================================
echo ^🚀 Next Steps
echo ==========================================
echo.
echo 1. Start Airflow:
echo    astro dev start
echo.
echo 2. Open web UI:
echo    http://localhost:8080 (admin / admin)
echo.
echo 3. Find and trigger DAG:
echo    - Go to DAGs page
echo    - Find 'nasa_apod_etl_pipeline'
echo    - Click the play button
echo.
echo 4. Monitor execution:
echo    - Watch task graph in real-time
echo    - Check logs for each task
echo.
echo 5. Verify data:
echo    - PostgreSQL: Records in apod_data table
echo    - CSV: New rows in apod_data.csv
echo    - GitHub: New commits visible at repo
echo.

echo ==========================================
echo Results: %passed% passed, %failed% failed
echo ==========================================

if %failed% gtr 0 (
    echo.
    echo WARNING: Some checks failed. Please fix before running.
    pause
    exit /b 1
) else (
    echo.
    echo ^✓ All checks passed! Ready to run.
    echo.
    echo Run: astro dev start
    pause
)
