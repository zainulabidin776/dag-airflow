#!/bin/bash
# Verification Script for NASA APOD ETL Pipeline
# Checks if all components are properly configured

echo "=========================================="
echo "🔍 NASA APOD ETL Pipeline Verification"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
        return 0
    else
        echo -e "${RED}❌ $1${NC}"
        return 1
    fi
}

# 1. Check Python version
echo -e "${BLUE}[1/10]${NC} Checking Python version..."
python --version 2>&1 | grep -q "3\."
check_status "Python 3.x installed"

# 2. Check Astronomer CLI
echo -e "${BLUE}[2/10]${NC} Checking Astronomer CLI..."
astro version > /dev/null 2>&1
check_status "Astronomer CLI installed"

# 3. Check Docker
echo -e "${BLUE}[3/10]${NC} Checking Docker..."
docker --version > /dev/null 2>&1
check_status "Docker installed"

# 4. Check DAG file
echo -e "${BLUE}[4/10]${NC} Checking DAG file..."
[ -f "dags/nasa_apod_pipeline.py" ]
check_status "DAG file exists (dags/nasa_apod_pipeline.py)"

# 5. Check ETL functions
echo -e "${BLUE}[5/10]${NC} Checking ETL functions..."
[ -f "include/scripts/etl_functions.py" ]
check_status "ETL functions exist (include/scripts/etl_functions.py)"

# 6. Check Version control script
echo -e "${BLUE}[6/10]${NC} Checking version control script..."
[ -f "include/scripts/version_control.py" ]
check_status "Version control script exists (include/scripts/version_control.py)"

# 7. Check requirements.txt
echo -e "${BLUE}[7/10]${NC} Checking Python requirements..."
[ -f "requirements.txt" ]
check_status "requirements.txt exists"

# 8. Check Docker Compose
echo -e "${BLUE}[8/10]${NC} Checking Docker Compose config..."
[ -f "docker-compose.override.yml" ]
check_status "docker-compose.override.yml exists"

# 9. Check init DB script
echo -e "${BLUE}[9/10]${NC} Checking database initialization..."
[ -f "init_db.sql" ]
check_status "init_db.sql exists"

# 10. Check GitHub token in .env
echo -e "${BLUE}[10/10]${NC} Checking GitHub token..."
grep -q "GITHUB_TOKEN=" .env
check_status "GitHub token configured in .env"

echo ""
echo "=========================================="
echo "📋 Configuration Summary"
echo "=========================================="
echo ""

# Show key configuration
echo -e "${BLUE}DAG Name:${NC} nasa_apod_etl_pipeline"
echo -e "${BLUE}Tasks:${NC}"
echo "  1. extract_data"
echo "  2. transform_data"
echo "  3. load_to_postgres"
echo "  4. load_to_csv"
echo "  5. initialize_dvc"
echo "  6. version_with_dvc"
echo "  7. commit_to_git"
echo "  8. push_to_github"

echo ""
echo -e "${BLUE}Database:${NC}"
echo "  - Type: PostgreSQL 12.6"
echo "  - Database: apod_db"
echo "  - Table: apod_data"
echo "  - Connection ID: postgres_apod"

echo ""
echo -e "${BLUE}Storage:${NC}"
echo "  - CSV: /usr/local/airflow/include/data/apod_data.csv"
echo "  - Version Control: Git (local) + GitHub (remote)"
echo "  - Data Versioning: DVC (simulated fallback)"

echo ""
echo -e "${BLUE}GitHub:${NC}"
echo "  - User: zainulabidin776"
echo "  - Repo: https://github.com/zainulabidin776/dag-airflow"
echo "  - Authentication: PAT (Personal Access Token) ✅"

echo ""
echo "=========================================="
echo "🚀 Next Steps"
echo "=========================================="
echo ""
echo "1. Start Airflow:"
echo "   ${YELLOW}astro dev start${NC}"
echo ""
echo "2. Open web UI:"
echo "   ${YELLOW}http://localhost:8080${NC} (admin / admin)"
echo ""
echo "3. Find and trigger DAG:"
echo "   - Go to DAGs page"
echo "   - Find 'nasa_apod_etl_pipeline'"
echo "   - Click the play button"
echo ""
echo "4. Monitor execution:"
echo "   - Watch task graph in real-time"
echo "   - Check logs for each task"
echo ""
echo "5. Verify data:"
echo "   - PostgreSQL: Records in apod_data table"
echo "   - CSV: New rows in apod_data.csv"
echo "   - GitHub: New commits in dag-airflow repo"
echo ""

echo "=========================================="
echo "✅ Verification Complete!"
echo "=========================================="
