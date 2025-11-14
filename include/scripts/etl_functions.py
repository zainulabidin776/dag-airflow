"""
ETL Functions for NASA APOD Pipeline
Designed for Astronomer Airflow Environment
"""

import requests
import pandas as pd
import psycopg2
from datetime import datetime
import logging
import os
from airflow.hooks.postgres_hook import PostgresHook

# Configure logging
logger = logging.getLogger(__name__)


def extract_apod_data(**context):
    """
    Extract data from NASA APOD API
    
    Args:
        context: Airflow context with task instance
    
    Returns:
        dict: Raw APOD data
    """
    url = "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY"
    
    try:
        logger.info("Fetching data from NASA APOD API...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Push to XCom for next task
        context['ti'].xcom_push(key='apod_data', value=data)
        
        logger.info(f"✅ Successfully extracted APOD data for {data.get('date')}")
        logger.info(f"Title: {data.get('title')}")
        
        return data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error fetching data from NASA API: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error during extraction: {str(e)}")
        raise


def transform_apod_data(**context):
    """
    Transform raw APOD data into structured format
    
    Args:
        context: Airflow context with task instance
    
    Returns:
        dict: Transformed data
    """
    ti = context['ti']
    raw_data = ti.xcom_pull(key='apod_data', task_ids='extract_data')
    
    if not raw_data:
        raise ValueError("No data received from extraction task")
    
    try:
        logger.info("Transforming APOD data...")
        
        # Select and transform fields
        transformed_data = {
            'date': raw_data.get('date'),
            'title': raw_data.get('title', 'No Title'),
            'url': raw_data.get('url', ''),
            'hdurl': raw_data.get('hdurl', ''),
            'media_type': raw_data.get('media_type', 'image'),
            'explanation': raw_data.get('explanation', '')[:1000],  # Limit length
            'copyright': raw_data.get('copyright', 'NASA')[:255],  # Limit length
            'retrieved_at': datetime.now().isoformat()
        }
        
        # Validate required fields
        if not transformed_data['date']:
            raise ValueError("Date field is missing from API response")
        
        # Create DataFrame for validation
        df = pd.DataFrame([transformed_data])
        logger.info(f"DataFrame shape: {df.shape}")
        logger.info(f"Columns: {df.columns.tolist()}")
        
        # Push to XCom
        ti.xcom_push(key='transformed_data', value=transformed_data)
        
        logger.info(f"✅ Successfully transformed data for {transformed_data['date']}")
        
        return transformed_data
        
    except Exception as e:
        logger.error(f"❌ Error during transformation: {str(e)}")
        raise


def load_to_postgres(**context):
    """
    Load data to PostgreSQL database using Airflow PostgresHook
    
    Args:
        context: Airflow context with task instance
    """
    ti = context['ti']
    data = ti.xcom_pull(key='transformed_data', task_ids='transform_data')
    
    if not data:
        raise ValueError("No transformed data available")
    
    try:
        logger.info("Connecting to PostgreSQL database...")
        
        # Use Airflow's PostgresHook for connection management
        postgres_hook = PostgresHook(postgres_conn_id='postgres_apod')
        conn = postgres_hook.get_conn()
        cursor = conn.cursor()
        
        # Create table if not exists
        create_table_query = """
        CREATE TABLE IF NOT EXISTS apod_data (
            id SERIAL PRIMARY KEY,
            date DATE UNIQUE NOT NULL,
            title TEXT NOT NULL,
            url TEXT,
            hdurl TEXT,
            media_type VARCHAR(50),
            explanation TEXT,
            copyright VARCHAR(255),
            retrieved_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        cursor.execute(create_table_query)
        logger.info("✅ Table created/verified successfully")
        
        # Insert data (on conflict update)
        insert_query = """
        INSERT INTO apod_data 
            (date, title, url, hdurl, media_type, explanation, copyright, retrieved_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (date) DO UPDATE SET
            title = EXCLUDED.title,
            url = EXCLUDED.url,
            hdurl = EXCLUDED.hdurl,
            media_type = EXCLUDED.media_type,
            explanation = EXCLUDED.explanation,
            copyright = EXCLUDED.copyright,
            retrieved_at = EXCLUDED.retrieved_at;
        """
        
        cursor.execute(insert_query, (
            data['date'],
            data['title'],
            data['url'],
            data['hdurl'],
            data['media_type'],
            data['explanation'],
            data['copyright'],
            data['retrieved_at']
        ))
        
        # Verify insertion
        cursor.execute("SELECT COUNT(*) FROM apod_data WHERE date = %s", (data['date'],))
        count = cursor.fetchone()[0]
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Successfully loaded data to PostgreSQL for {data['date']}")
        logger.info(f"Total records for this date: {count}")
        
    except Exception as e:
        logger.error(f"❌ Error loading to PostgreSQL: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


def load_to_csv(**context):
    """
    Load data to CSV file in Astronomer environment
    
    Args:
        context: Airflow context with task instance
    
    Returns:
        str: Path to CSV file
    """
    ti = context['ti']
    data = ti.xcom_pull(key='transformed_data', task_ids='transform_data')
    
    if not data:
        raise ValueError("No transformed data available")
    
    # Use Astronomer-compatible path
    csv_path = '/usr/local/airflow/include/data/apod_data.csv'
    
    try:
        logger.info(f"Saving data to CSV: {csv_path}")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        
        # Create DataFrame
        df = pd.DataFrame([data])
        
        # Append to CSV if exists, otherwise create new
        if os.path.exists(csv_path):
            logger.info("Appending to existing CSV file...")
            existing_df = pd.read_csv(csv_path)
            
            # Remove duplicate dates (keep new data)
            existing_df = existing_df[existing_df['date'] != data['date']]
            
            # Combine and sort by date
            df = pd.concat([existing_df, df], ignore_index=True)
            df = df.sort_values('date', ascending=False)
        else:
            logger.info("Creating new CSV file...")
        
        # Save to CSV
        df.to_csv(csv_path, index=False)
        
        # Verify file
        if os.path.exists(csv_path):
            file_size = os.path.getsize(csv_path)
            row_count = len(df)
            logger.info(f"✅ CSV saved successfully")
            logger.info(f"   File size: {file_size} bytes")
            logger.info(f"   Total rows: {row_count}")
        else:
            raise FileNotFoundError(f"CSV file was not created at {csv_path}")
        
        return csv_path
        
    except Exception as e:
        logger.error(f"❌ Error saving to CSV: {str(e)}")
        raise


def verify_data(**context):
    """
    Verify data was loaded successfully to both Postgres and CSV
    
    Args:
        context: Airflow context with task instance
    """
    ti = context['ti']
    data = ti.xcom_pull(key='transformed_data', task_ids='transform_data')
    csv_path = '/usr/local/airflow/include/data/apod_data.csv'
    
    try:
        # Verify Postgres
        postgres_hook = PostgresHook(postgres_conn_id='postgres_apod')
        result = postgres_hook.get_first(
            "SELECT COUNT(*) FROM apod_data WHERE date = %s",
            parameters=(data['date'],)
        )
        postgres_count = result[0] if result else 0
        
        # Verify CSV
        csv_exists = os.path.exists(csv_path)
        csv_rows = 0
        if csv_exists:
            df = pd.read_csv(csv_path)
            csv_rows = len(df)
        
        logger.info("=" * 50)
        logger.info("📊 DATA VERIFICATION REPORT")
        logger.info("=" * 50)
        logger.info(f"Date: {data['date']}")
        logger.info(f"PostgreSQL Records: {postgres_count}")
        logger.info(f"CSV File Exists: {csv_exists}")
        logger.info(f"CSV Total Rows: {csv_rows}")
        logger.info("=" * 50)
        
        if postgres_count > 0 and csv_exists:
            logger.info("✅ All verifications passed!")
            return True
        else:
            logger.error("❌ Verification failed!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error during verification: {str(e)}")
        raise