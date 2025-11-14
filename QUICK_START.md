# 🚀 Quick Start Guide - NASA APOD ETL Pipeline

**Student:** Zain Ul Abidin  
**Roll No:** 22I-2738  
**Date:** November 14, 2025

---

## One-Liner to Get Started

```bash
cd "c:\Users\zainy\OneDrive\Desktop\Semester-7\MLOPS\Assignment-3\a3"
astro dev start
```

Then open: http://localhost:8080 (admin / admin)

---

## Running the Pipeline

### Option 1: Via UI (Easiest)
1. Open http://localhost:8080
2. Click DAGs → `nasa_apod_etl_pipeline`
3. Click the play button (Trigger DAG)
4. Watch tasks execute in real-time

### Option 2: Via CLI
```bash
# Full DAG run
astro dev run dags test nasa_apod_etl_pipeline

# Or individual tasks
astro dev run tasks test nasa_apod_etl_pipeline extract_data
astro dev run tasks test nasa_apod_etl_pipeline transform_data
astro dev run tasks test nasa_apod_etl_pipeline load_to_postgres
astro dev run tasks test nasa_apod_etl_pipeline load_to_csv
astro dev run tasks test nasa_apod_etl_pipeline initialize_dvc
astro dev run tasks test nasa_apod_etl_pipeline version_with_dvc
astro dev run tasks test nasa_apod_etl_pipeline commit_to_git
astro dev run tasks test nasa_apod_etl_pipeline push_to_github
```

---

## What the Pipeline Does (5 Steps)

### 1️⃣ **Extract** 
Fetches NASA APOD (Astronomy Picture of the Day) data from the API
- Retries with exponential backoff on rate limits
- Fallback to local CSV if API fails
- Uses placeholder if no CSV available

### 2️⃣ **Transform**
Normalizes data to standard format
- Removes/truncates long fields
- Adds metadata timestamps
- Validates required fields

### 3️⃣ **Load**
Stores data in two places:
- **PostgreSQL** (`apod_db` table)
- **CSV file** (`/usr/local/airflow/include/data/apod_data.csv`)

### 4️⃣ **Version**
Creates DVC metadata for data versioning
- Automatic `.dvc` file generation
- MD5 checksum tracking
- Handles DVC incompatibilities gracefully

### 5️⃣ **Commit & Push**
Commits to Git and pushes to GitHub
- Commits to local repository
- **Now pushing to GitHub with your PAT token!** ✅
- View commits at: https://github.com/zainulabidin776/dag-airflow

---

## Authentication ✅

Your GitHub PAT is already configured in `.env`:
```
GITHUB_TOKEN=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
```

This enables:
- ✅ Non-interactive GitHub push
- ✅ Automatic credential authentication
- ✅ Commits appear in your GitHub repo

---

## Verify Everything Works

### Check PostgreSQL
```bash
astro dev exec postgres psql -U airflow -d apod_db -c "SELECT COUNT(*) FROM apod_data;"
```

### Check CSV
```bash
astro dev exec webserver test -f /usr/local/airflow/include/data/apod_data.csv && echo "✅ CSV exists"
```

### Check Git Commits
```bash
astro dev exec webserver git -C /usr/local/airflow/include/data log --oneline -5
```

### View Logs
```bash
# Full DAG logs
astro dev logs

# Specific task
astro dev logs | grep "push_to_github"
```

---

## Common Commands

```bash
# Start Airflow environment
astro dev start

# Stop Airflow
astro dev stop

# Restart (after code changes)
astro dev restart

# View running containers
docker ps

# View logs
astro dev logs -f

# Run DAG test
astro dev run dags test nasa_apod_etl_pipeline

# Clean up everything
astro dev kill
```

---

## Troubleshooting

### 🔧 PostgreSQL Connection Error
```bash
astro dev restart
# Wait 30 seconds for containers to be healthy
```

### 🔧 DVC Not Working
✅ Already handled! Pipeline uses simulated DVC metadata automatically.

### 🔧 GitHub Push Failed
Check:
1. PAT token is valid (expiration date)
2. Network connectivity
3. GitHub repo exists: https://github.com/zainulabidin776/dag-airflow
4. View logs: `astro dev logs | grep "push_to_github"`

### 🔧 NASA API Rate Limited (429)
✅ Already handled! Pipeline retries and falls back automatically.
- If using DEMO_KEY, may hit limits
- (Optional) Set NASA_API_KEY in `.env` for higher limits

---

## File Locations

| What | Where |
|------|-------|
| DAG Definition | `dags/nasa_apod_pipeline.py` |
| ETL Functions | `include/scripts/etl_functions.py` |
| Git/DVC Logic | `include/scripts/version_control.py` |
| Data (CSV) | `include/data/apod_data.csv` |
| DB Init | `init_db.sql` |
| Config | `.env`, `airflow_settings.yaml`, `docker-compose.override.yml` |
| Full Docs | `SUBMISSION_DOCUMENTATION.md` |

---

## Success Indicators 🎉

You'll see these in the DAG logs:

```
✅ Successfully extracted APOD data for 2025-11-14
✅ Successfully transformed data for 2025-11-14
✅ Successfully loaded data to PostgreSQL for 2025-11-14
✅ CSV saved successfully
✅ Simulated apod_data.csv.dvc created
✅ Git user configured (zainulabidin776)
✅ Successfully pushed to GitHub!
```

---

## GitHub Repository

**Your Repo:** https://github.com/zainulabidin776/dag-airflow

After running the pipeline, you'll see:
- ✅ New commits in the `main` or `master` branch
- ✅ CSV file version tracked
- ✅ `.dvc` metadata files

---

## Need Help?

1. Check logs: `astro dev logs`
2. Read detailed docs: `SUBMISSION_DOCUMENTATION.md`
3. Verify setup: Run individual tasks one by one

---

**Ready to run?** 🚀

```bash
astro dev start
# Then go to http://localhost:8080
# Find nasa_apod_etl_pipeline DAG
# Click the play button!
```

---

*Last Updated: November 14, 2025*
