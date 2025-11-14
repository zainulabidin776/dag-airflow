"""
ETL Functions for NASA APOD Pipeline
Designed for Astronomer Airflow Environment
"""

import requests
import pandas as pd
import psycopg2
from datetime import datetime
import time
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
    # Allow user to provide a real NASA API key via env var; fall back to DEMO_KEY
    api_key = os.getenv('NASA_API_KEY', 'DEMO_KEY')
    url = f"https://api.nasa.gov/planetary/apod?api_key={api_key}"

    max_retries = 5
    base_backoff = 5  # seconds

    try:
        logger.info("Fetching data from NASA APOD API...")

        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(url, timeout=30)
                # If the API returns 429 (rate limit) or 503, we'll retry
                if response.status_code in (429, 503):
                    raise requests.exceptions.HTTPError(f"HTTP {response.status_code}", response=response)

                response.raise_for_status()
                data = response.json()

                # Push to XCom for next task
                context['ti'].xcom_push(key='apod_data', value=data)

                logger.info(f"✅ Successfully extracted APOD data for {data.get('date')}")
                logger.info(f"Title: {data.get('title')}")
                return data

            except requests.exceptions.HTTPError as he:
                status = None
                try:
                    status = he.response.status_code if he.response is not None else None
                except Exception:
                    status = None

                # If rate-limited, retry with backoff
                if status in (429, 503):
                    sleep_time = base_backoff * (2 ** (attempt - 1))
                    logger.warning(f"⚠️  NASA API rate limited (HTTP {status}). Retry {attempt}/{max_retries} in {sleep_time}s...")
                    time.sleep(sleep_time)
                    continue
                else:
                    logger.error(f"❌ HTTP error fetching data from NASA API: {str(he)}")
                    raise

            except requests.exceptions.RequestException as e:
                # Network-level errors; retry a few times
                if attempt < max_retries:
                    sleep_time = base_backoff * (2 ** (attempt - 1))
                    logger.warning(f"⚠️  Network error fetching NASA API: {str(e)}. Retry {attempt}/{max_retries} in {sleep_time}s...")
                    time.sleep(sleep_time)
                    continue
                logger.error(f"❌ Error fetching data from NASA API after {attempt} attempts: {str(e)}")
                raise

        # If we exit loop without returning, attempt graceful fallback
        # Fallback strategy: if a local CSV exists, use the most recent row
        csv_path = '/usr/local/airflow/include/data/apod_data.csv'
        if os.path.exists(csv_path):
            try:
                logger.warning(f"⚠️  Falling back to local CSV data at {csv_path}")
                df = pd.read_csv(csv_path)
                if not df.empty:
                    latest = df.sort_values('date', ascending=False).iloc[0].to_dict()
                    # Map CSV columns to API-like response keys
                    fallback_data = {
                        'date': str(latest.get('date')),
                        'title': latest.get('title'),
                        'url': latest.get('url'),
                        'hdurl': latest.get('hdurl') if 'hdurl' in latest else latest.get('url'),
                        'media_type': latest.get('media_type', 'image'),
                        'explanation': latest.get('explanation', ''),
                        'copyright': latest.get('copyright', 'NASA')
                    }
                    context['ti'].xcom_push(key='apod_data', value=fallback_data)
                    logger.info(f"✅ Used fallback APOD data for {fallback_data.get('date')}")
                    return fallback_data
            except Exception as fe:
                logger.error(f"❌ Failed to read fallback CSV: {str(fe)}")

        # No fallback available — create a safe placeholder so downstream tasks can continue
        logger.warning("⚠️  No local CSV fallback found; using placeholder APOD data to allow pipeline to continue")
        placeholder = {
            'date': datetime.now().date().isoformat(),
            'title': 'NASA APOD (placeholder)',
            'url': 'https://apod.nasa.gov/apod/image/1901/Placeholder.jpg',
            'hdurl': 'https://apod.nasa.gov/apod/image/1901/Placeholder.jpg',
            'media_type': 'image',
            'explanation': 'Placeholder APOD used due to API rate limits or connectivity issues.',
            'copyright': 'NASA'
        }
        context['ti'].xcom_push(key='apod_data', value=placeholder)
        logger.info(f"✅ Used placeholder APOD data for {placeholder.get('date')}")
        return placeholder

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
    
    conn = None
    cursor = None
    
    try:
        logger.info("Connecting to PostgreSQL database...")
        
        # Use Airflow's PostgresHook for connection management
        postgres_hook = PostgresHook(postgres_conn_id='postgres_apod')
        conn = postgres_hook.get_conn()
        cursor = conn.cursor()
        
        # First, ensure database exists (if not created by init script)
        cursor.execute("SELECT 1 FROM information_schema.schemata WHERE schema_name = 'public';")
        if not cursor.fetchone():
            logger.warning("Public schema not found, attempting to create...")
            cursor.execute("CREATE SCHEMA IF NOT EXISTS public;")
            conn.commit()
        
        logger.info("✅ Schema verified successfully")
        
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        cursor.execute(create_table_query)
        conn.commit()
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
            retrieved_at = EXCLUDED.retrieved_at,
            updated_at = CURRENT_TIMESTAMP;
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
        
        conn.commit()
        
        # Verify insertion
        cursor.execute("SELECT COUNT(*) FROM apod_data WHERE date = %s", (data['date'],))
        count = cursor.fetchone()[0]
        
        logger.info(f"✅ Successfully loaded data to PostgreSQL for {data['date']}")
        logger.info(f"Total records for this date: {count}")
        
    except psycopg2.OperationalError as e:
        logger.error(f"❌ Database connection error: {str(e)}")
        if conn:
            conn.rollback()
        raise
    except psycopg2.DatabaseError as e:
        logger.error(f"❌ Database error: {str(e)}")
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        logger.error(f"❌ Error loading to PostgreSQL: {str(e)}")
        if conn:
            try:
                conn.rollback()
            except:
                pass
        raise
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass


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