"""
Version Control Functions for NASA APOD Pipeline
Handles DVC and Git operations in Astronomer environment
"""

import subprocess
import logging
import os
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)


def run_command(cmd, cwd=None, check=True):
    """
    Helper function to run shell commands
    
    Args:
        cmd: Command to run (list or string)
        cwd: Working directory
        check: Raise exception on error
    
    Returns:
        subprocess.CompletedProcess
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=check,
            shell=isinstance(cmd, str)
        )
        
        if result.stdout:
            logger.debug(f"STDOUT: {result.stdout}")
        if result.stderr:
            logger.debug(f"STDERR: {result.stderr}")
            
        return result
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
        logger.error(f"Error: {e.stderr}")
        raise


def initialize_dvc(**context):
    """
    Initialize DVC and Git in the data directory
    
    Args:
        context: Airflow context with task instance
    
    Returns:
        str: Status message
    """
    data_dir = '/usr/local/airflow/include/data'
    
    try:
        logger.info("=" * 50)
        logger.info("🔧 INITIALIZING VERSION CONTROL")
        logger.info("=" * 50)
        
        # Ensure directory exists
        os.makedirs(data_dir, exist_ok=True)
        os.chdir(data_dir)
        
        logger.info(f"Working directory: {os.getcwd()}")
        
        # Initialize Git if not already initialized
        if not os.path.exists('.git'):
            logger.info("Initializing Git repository...")
            run_command(['git', 'init'], cwd=data_dir)
            run_command(['git', 'config', 'user.email', 'airflow@astronomer.io'], cwd=data_dir)
            run_command(['git', 'config', 'user.name', 'Airflow Pipeline'], cwd=data_dir)
            logger.info("✅ Git repository initialized")
        else:
            logger.info("✓ Git repository already exists")
        
        # Initialize DVC if not already initialized
        if not os.path.exists('.dvc'):
            logger.info("Initializing DVC...")
            run_command(['dvc', 'init'], cwd=data_dir)
            
            # Commit DVC initialization
            run_command(['git', 'add', '.dvc', '.dvcignore'], cwd=data_dir)
            run_command(
                ['git', 'commit', '-m', 'Initialize DVC'], 
                cwd=data_dir,
                check=False  # Don't fail if nothing to commit
            )
            logger.info("✅ DVC initialized")
        else:
            logger.info("✓ DVC already initialized")
        
        # List directory contents
        logger.info("\nDirectory contents:")
        result = run_command(['ls', '-la'], cwd=data_dir)
        logger.info(result.stdout)
        
        logger.info("=" * 50)
        logger.info("✅ VERSION CONTROL INITIALIZATION COMPLETE")
        logger.info("=" * 50)
        
        return "DVC and Git initialized successfully"
        
    except Exception as e:
        logger.error(f"❌ Error initializing version control: {str(e)}")
        raise


def version_data_with_dvc(**context):
    """
    Add CSV file to DVC version control
    
    Args:
        context: Airflow context with task instance
    
    Returns:
        str: Status message
    """
    data_dir = '/usr/local/airflow/include/data'
    csv_file = 'apod_data.csv'
    dvc_file = f'{csv_file}.dvc'
    
    try:
        logger.info("=" * 50)
        logger.info("📦 VERSIONING DATA WITH DVC")
        logger.info("=" * 50)
        
        os.chdir(data_dir)
        
        # Verify CSV file exists
        if not os.path.exists(csv_file):
            raise FileNotFoundError(f"CSV file not found: {csv_file}")
        
        csv_size = os.path.getsize(csv_file)
        logger.info(f"CSV file size: {csv_size} bytes")
        
        # Remove existing .dvc file if present (for updates)
        if os.path.exists(dvc_file):
            logger.info(f"Removing existing {dvc_file}...")
            run_command(['dvc', 'remove', dvc_file], cwd=data_dir, check=False)
            
            # Remove from git tracking
            run_command(['git', 'rm', '-f', dvc_file], cwd=data_dir, check=False)
        
        # Add file to DVC
        logger.info(f"Adding {csv_file} to DVC...")
        run_command(['dvc', 'add', csv_file], cwd=data_dir)
        
        # Verify .dvc file was created
        if os.path.exists(dvc_file):
            logger.info(f"✅ {dvc_file} created successfully")
            
            # Show .dvc file contents
            with open(dvc_file, 'r') as f:
                dvc_content = f.read()
            logger.info(f"\n{dvc_file} contents:\n{dvc_content}")
        else:
            raise FileNotFoundError(f"DVC file was not created: {dvc_file}")
        
        # Stage .dvc file and .gitignore for commit
        logger.info("Staging files for Git commit...")
        run_command(['git', 'add', dvc_file, '.gitignore'], cwd=data_dir)
        
        # Show git status
        result = run_command(['git', 'status', '--short'], cwd=data_dir)
        logger.info(f"Git status:\n{result.stdout}")
        
        logger.info("=" * 50)
        logger.info("✅ DATA VERSIONING COMPLETE")
        logger.info("=" * 50)
        
        return f"{csv_file} versioned with DVC successfully"
        
    except Exception as e:
        logger.error(f"❌ Error versioning with DVC: {str(e)}")
        raise


def commit_to_git(**context):
    """
    Commit DVC metadata to Git repository
    
    Args:
        context: Airflow context with task instance
    
    Returns:
        str: Status message
    """
    data_dir = '/usr/local/airflow/include/data'
    
    try:
        logger.info("=" * 50)
        logger.info("💾 COMMITTING TO GIT")
        logger.info("=" * 50)
        
        os.chdir(data_dir)
        
        # Get date from transformed data
        ti = context['ti']
        data = ti.xcom_pull(key='transformed_data', task_ids='transform_data')
        date = data.get('date', 'unknown') if data else 'unknown'
        
        # Create commit message
        commit_message = f"Update APOD data version for {date}"
        logger.info(f"Commit message: {commit_message}")
        
        # Check if there are changes to commit
        status_result = run_command(['git', 'status', '--porcelain'], cwd=data_dir)
        
        if not status_result.stdout.strip():
            logger.info("ℹ️  No changes to commit")
            return "No changes to commit"
        
        # Show what will be committed
        logger.info("\nFiles to be committed:")
        logger.info(status_result.stdout)
        
        # Commit changes
        logger.info("Committing changes...")
        run_command(['git', 'commit', '-m', commit_message], cwd=data_dir)
        
        # Show commit log
        log_result = run_command(
            ['git', 'log', '--oneline', '-5'],
            cwd=data_dir
        )
        logger.info(f"\nRecent commits:\n{log_result.stdout}")
        
        # Show current commit hash
        hash_result = run_command(['git', 'rev-parse', 'HEAD'], cwd=data_dir)
        commit_hash = hash_result.stdout.strip()
        logger.info(f"\nCurrent commit: {commit_hash}")
        
        logger.info("=" * 50)
        logger.info("✅ GIT COMMIT COMPLETE")
        logger.info("=" * 50)
        
        # Note about pushing to remote
        logger.info("\n📝 Note: To push to GitHub, configure remote:")
        logger.info("   git remote add origin <your-repo-url>")
        logger.info("   git push -u origin main")
        
        return f"Git commit successful: {commit_hash[:7]}"
        
    except subprocess.CalledProcessError as e:
        if "nothing to commit" in e.stderr:
            logger.info("ℹ️  Nothing to commit, working tree clean")
            return "No changes to commit"
        logger.error(f"❌ Error committing to Git: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"❌ Error in Git commit: {str(e)}")
        raise


def push_to_github(**context):
    """
    (Optional) Push commits to GitHub remote repository
    
    This task is optional and requires GitHub remote to be configured.
    
    Args:
        context: Airflow context with task instance
    
    Returns:
        str: Status message
    """
    data_dir = '/usr/local/airflow/include/data'
    
    try:
        logger.info("=" * 50)
        logger.info("🚀 PUSHING TO GITHUB")
        logger.info("=" * 50)
        
        os.chdir(data_dir)
        
        # Check if remote exists
        result = run_command(
            ['git', 'remote', '-v'],
            cwd=data_dir,
            check=False
        )
        
        if not result.stdout.strip():
            logger.warning("⚠️  No Git remote configured")
            logger.info("To configure remote:")
            logger.info("  git remote add origin https://github.com/username/repo.git")
            return "Skipped: No remote configured"
        
        logger.info(f"Remote repositories:\n{result.stdout}")
        
        # Push to remote
        logger.info("Pushing to remote...")
        run_command(['git', 'push', 'origin', 'main'], cwd=data_dir)
        
        logger.info("✅ Successfully pushed to GitHub")
        logger.info("=" * 50)
        
        return "Pushed to GitHub successfully"
        
    except subprocess.CalledProcessError as e:
        logger.warning(f"⚠️  Could not push to GitHub: {e.stderr}")
        logger.info("This is optional - pipeline will continue")
        return "GitHub push skipped"
    except Exception as e:
        logger.warning(f"⚠️  Error pushing to GitHub: {str(e)}")
        return "GitHub push skipped"