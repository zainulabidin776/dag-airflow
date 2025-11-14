"""
NASA APOD ETL Pipeline with DVC Versioning
Designed for Astronomer Cloud Platform

This DAG implements a complete MLOps pipeline:
1. Extract data from NASA APOD API
2. Transform data using Pandas
3. Load to PostgreSQL and CSV simultaneously
4. Version data with DVC
5. Commit metadata to Git

Author: Your Name
Date: November 2024
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from datetime import datetime, timedelta
import sys
import os

# Add include directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'include')))

# Import custom functions
from scripts.etl_functions import (
    extract_apod_data,
    transform_apod_data,
    load_to_postgres,
    load_to_csv,
    verify_data
)
from scripts.version_control import (
    initialize_dvc,
    version_data_with_dvc,
    commit_to_git,
    push_to_github
)

# Default arguments for all tasks
default_args = {
    'owner': 'astronomer',
    'depends_on_past': False,
    'start_date': datetime(2024, 11, 14),
    'email': ['itsmezayynn@gmail.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=30),
}

# Define the DAG
with DAG(
    dag_id='nasa_apod_etl_pipeline',
    default_args=default_args,
    description='🚀 NASA APOD ETL Pipeline with DVC Versioning on Astronomer',
    
    # SCHEDULE: Runs daily at midnight UTC
    schedule_interval='@daily',
    
    # Start date and configuration
    start_date=datetime(2024, 11, 14),
    catchup=False,  # Don't backfill past runs
    max_active_runs=1,  # Only one DAG run at a time
    
    # Tags for organization in Astronomer UI
    tags=['nasa', 'etl', 'mlops', 'dvc', 'astronomer'],
    
    # Documentation
    doc_md="""
    # NASA APOD ETL Pipeline
    
    ## Purpose
    This pipeline demonstrates a complete MLOps workflow using:
    - **Airflow** for orchestration
    - **Astronomer** for deployment
    - **PostgreSQL** for structured storage
    - **DVC** for data versioning
    - **Git** for code versioning
    
    ## Workflow
    1. **Extract**: Fetch daily APOD data from NASA API
    2. **Transform**: Clean and structure data with Pandas
    3. **Load**: Save to PostgreSQL database and CSV file
    4. **Version**: Track data changes with DVC
    5. **Commit**: Version metadata with Git
    
    ## Schedule
    Runs daily at 00:00 UTC to fetch the latest APOD
    
    ## Data Storage
    - **Database**: `apod_db.apod_data` table
    - **CSV**: `/usr/local/airflow/include/data/apod_data.csv`
    - **DVC Metadata**: `apod_data.csv.dvc`
    
    ## Monitoring
    Check task logs for detailed execution information
    """,
    
) as dag:
    
    # ============================================
    # TASK 0: Pipeline Start Marker
    # ============================================
    start = EmptyOperator(
        task_id='start_pipeline',
        doc_md="""
        ## Pipeline Start
        Marks the beginning of the NASA APOD ETL pipeline execution.
        """
    )
    
    # ============================================
    # TASK 1: EXTRACT - Fetch data from NASA API
    # ============================================
    extract_task = PythonOperator(
        task_id='extract_data',
        python_callable=extract_apod_data,
        provide_context=True,
        doc_md="""
        ## Extract NASA APOD Data
        
        **Purpose**: Fetch today's Astronomy Picture of the Day from NASA API
        
        **API Endpoint**: https://api.nasa.gov/planetary/apod
        
        **Output**: Raw JSON data pushed to XCom
        
        **Fields Retrieved**:
        - date
        - title
        - url (image/video URL)
        - hdurl (high-definition URL)
        - explanation
        - media_type
        - copyright
        """
    )
    
    # ============================================
    # TASK 2: TRANSFORM - Clean and structure data
    # ============================================
    transform_task = PythonOperator(
        task_id='transform_data',
        python_callable=transform_apod_data,
        provide_context=True,
        doc_md="""
        ## Transform APOD Data
        
        **Purpose**: Clean and structure raw API data into usable format
        
        **Operations**:
        - Select relevant fields
        - Limit text field lengths
        - Add metadata (retrieved_at timestamp)
        - Create Pandas DataFrame
        - Validate data quality
        
        **Output**: Structured dictionary pushed to XCom
        """
    )
    
    # ============================================
    # TASK 3A: LOAD - Save to PostgreSQL
    # ============================================
    load_postgres_task = PythonOperator(
        task_id='load_to_postgres',
        python_callable=load_to_postgres,
        provide_context=True,
        doc_md="""
        ## Load to PostgreSQL Database
        
        **Purpose**: Persist structured data to relational database
        
        **Database**: `apod_db`
        
        **Table**: `apod_data`
        
        **Schema**:
        - id (SERIAL PRIMARY KEY)
        - date (DATE UNIQUE)
        - title (TEXT)
        - url (TEXT)
        - hdurl (TEXT)
        - media_type (VARCHAR)
        - explanation (TEXT)
        - copyright (VARCHAR)
        - retrieved_at (TIMESTAMP)
        - created_at (TIMESTAMP)
        
        **Behavior**: UPSERT (insert or update on conflict)
        """
    )
    
    # ============================================
    # TASK 3B: LOAD - Save to CSV file
    # ============================================
    load_csv_task = PythonOperator(
        task_id='load_to_csv',
        python_callable=load_to_csv,
        provide_context=True,
        doc_md="""
        ## Load to CSV File
        
        **Purpose**: Save data to flat file for versioning
        
        **File Path**: `/usr/local/airflow/include/data/apod_data.csv`
        
        **Behavior**: 
        - Append new records
        - Remove duplicates (keep latest)
        - Sort by date (descending)
        
        **Format**: CSV with headers
        """
    )
    
    # ============================================
    # TASK 3C: VERIFY - Check data integrity
    # ============================================
    verify_task = PythonOperator(
        task_id='verify_data_load',
        python_callable=verify_data,
        provide_context=True,
        doc_md="""
        ## Verify Data Load
        
        **Purpose**: Confirm data was loaded successfully to both destinations
        
        **Checks**:
        - PostgreSQL: Record exists for today's date
        - CSV: File exists and contains data
        - Row counts match expectations
        
        **Output**: Verification report in logs
        """
    )
    
    # ============================================
    # TASK 4: Initialize DVC and Git
    # ============================================
    init_dvc_task = PythonOperator(
        task_id='initialize_dvc',
        python_callable=initialize_dvc,
        provide_context=True,
        doc_md="""
        ## Initialize Version Control
        
        **Purpose**: Set up DVC and Git for data versioning
        
        **Operations**:
        - Initialize Git repository (if needed)
        - Configure Git user
        - Initialize DVC (if needed)
        - Commit DVC configuration
        
        **Directory**: `/usr/local/airflow/include/data/`
        
        **Note**: This task is idempotent (safe to run multiple times)
        """
    )
    
    # ============================================
    # TASK 5: Version data with DVC
    # ============================================
    dvc_version_task = PythonOperator(
        task_id='version_with_dvc',
        python_callable=version_data_with_dvc,
        provide_context=True,
        doc_md="""
        ## Version Data with DVC
        
        **Purpose**: Track CSV file changes with Data Version Control
        
        **Operations**:
        - Run `dvc add apod_data.csv`
        - Generate `apod_data.csv.dvc` metadata file
        - Update `.gitignore` to exclude large data files
        - Stage .dvc file for Git commit
        
        **Output**: 
        - `apod_data.csv.dvc` (metadata file)
        - `.gitignore` (updated)
        
        **Note**: Actual data file is NOT committed to Git
        """
    )
    
    # ============================================
    # TASK 6: Commit DVC metadata to Git
    # ============================================
    git_commit_task = PythonOperator(
        task_id='commit_to_git',
        python_callable=commit_to_git,
        provide_context=True,
        doc_md="""
        ## Commit to Git Repository
        
        **Purpose**: Version control for DVC metadata files
        
        **Operations**:
        - Commit `apod_data.csv.dvc` file
        - Commit `.gitignore` updates
        - Generate commit with date-specific message
        
        **Commit Message**: "Update APOD data version for YYYY-MM-DD"
        
        **Note**: This creates a link between code version and data version
        """
    )
    
    # ============================================
    # TASK 7: (Optional) Push to GitHub
    # ============================================
    push_github_task = PythonOperator(
        task_id='push_to_github',
        python_callable=push_to_github,
        provide_context=True,
        trigger_rule='all_done',  # Run even if previous tasks fail
        doc_md="""
        ## Push to GitHub Remote
        
        **Purpose**: Sync local Git commits to remote repository
        
        **Operations**:
        - Check if remote is configured
        - Push commits to `origin/master`
        
        **Note**: 
        - This task is optional
        - Requires GitHub remote to be configured
        - Will skip gracefully if no remote exists
        
        **Setup**:
        ```bash
        git remote add origin https://github.com/zainulabidin776/dag-airflow.git
        ```
        """
    )
    
    # ============================================
    # TASK 8: Pipeline End Marker
    # ============================================
    end = EmptyOperator(
        task_id='pipeline_complete',
        trigger_rule='all_success',
        doc_md="""
        ## Pipeline Complete
        
        Marks successful completion of the entire ETL pipeline.
        
        **Success Criteria**:
        - Data extracted from NASA API
        - Data transformed successfully
        - Data loaded to PostgreSQL
        - Data saved to CSV
        - CSV versioned with DVC
        - Metadata committed to Git
        """
    )
    
    # ============================================
    # DEFINE TASK DEPENDENCIES
    # ============================================
    
    # Linear flow: Extract → Transform
    start >> extract_task >> transform_task
    
    # Parallel loading: Transform → [Postgres, CSV]
    transform_task >> [load_postgres_task, load_csv_task]
    
    # Verify both loads completed
    [load_postgres_task, load_csv_task] >> verify_task
    
    # Sequential versioning: CSV → Init DVC → Add to DVC → Commit to Git → (Push to GitHub)
    verify_task >> init_dvc_task >> dvc_version_task >> git_commit_task >> push_github_task
    
    # End marker
    push_github_task >> end
    
    # Alternative: Skip GitHub push and still complete
    # git_commit_task >> end


# ============================================
# DAG DOCUMENTATION (visible in Astronomer UI)
# ============================================
"""
# 🚀 NASA APOD ETL Pipeline

## Overview
Production-ready MLOps pipeline for NASA's Astronomy Picture of the Day

## Architecture
```
NASA API → Extract → Transform → [PostgreSQL, CSV] → DVC → Git → GitHub
```

## Key Features
- ✅ Daily automated execution
- ✅ Parallel data loading
- ✅ Data versioning with DVC
- ✅ Code versioning with Git
- ✅ Comprehensive error handling
- ✅ Detailed logging and monitoring

## Deployment
Designed for Astronomer Cloud Platform with Docker containerization

## Monitoring
- Check task logs for execution details
- View DAG graph for workflow visualization
- Monitor task duration in Gantt chart

## Maintenance
- Update `requirements.txt` for new dependencies
- Modify `schedule_interval` to change execution frequency
- Configure GitHub remote for automatic pushes
"""