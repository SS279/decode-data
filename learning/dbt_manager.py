import os
import tempfile
import shutil
import subprocess
from pathlib import Path
from django.conf import settings
import logging
import threading
import queue
import uuid
import time

logger = logging.getLogger(__name__)


class DBTManager:
    """Manage DBT workspace and operations"""

    # Class-level storage for active jobs and their logs
    active_jobs = {}
    # Maximum number of concurrent jobs to prevent resource exhaustion
    MAX_CONCURRENT_JOBS = 3

    def __init__(self, user, lesson):
        self.user = user
        self.lesson = lesson
        self.workspace_path = self._get_workspace_path()
    
    def _get_workspace_path(self):
        """Get or create workspace path for user"""
        # Use local temp directory for development
        # Can be changed to persistent storage for production
        base_dir = Path(tempfile.gettempdir()) / 'dbt_workspaces'
        workspace = base_dir / f"user_{self.user.id}" / self.lesson['id']
        return workspace
    
    def is_initialized(self):
        """Check if workspace is initialized"""
        return (
            self.workspace_path.exists() and 
            (self.workspace_path / 'dbt_project.yml').exists()
        )
    
    def initialize_workspace(self):
        """Initialize DBT workspace"""
        try:
            # Create workspace directory
            self.workspace_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created workspace at: {self.workspace_path}")
            
            # Copy dbt project
            source_dir = Path(__file__).parent.parent / 'dbt_project'
            if not source_dir.exists():
                return False, f'dbt_project directory not found at: {source_dir}'
            
            logger.info(f"Copying dbt project from: {source_dir}")
            shutil.copytree(source_dir, self.workspace_path, dirs_exist_ok=True)
            
            # Create schema in MotherDuck
            from learning.storage import MotherDuckStorage
            storage = MotherDuckStorage()
            
            try:
                conn = storage._get_connection()
                conn.execute(f"USE {storage.share}")
                conn.execute(f"CREATE SCHEMA IF NOT EXISTS {self.user.schema_name}")
                logger.info(f"Created schema in MotherDuck: {self.user.schema_name}")
                conn.close()
            except Exception as e:
                logger.warning(f"Could not create schema in MotherDuck: {e}")
                # Don't fail initialization if schema creation fails
            
            # Create profiles.yml
            profiles_content = f"""
decode_dbt:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: "md:{settings.MOTHERDUCK_SHARE}"
      schema: {self.user.schema_name}
      threads: 1
      motherduck_token: {settings.MOTHERDUCK_TOKEN}
"""
            profiles_path = self.workspace_path / 'profiles.yml'
            profiles_path.write_text(profiles_content)
            logger.info(f"Created profiles.yml at: {profiles_path}")
            
            return True, 'Workspace initialized successfully'
        except Exception as e:
            logger.error(f"Error initializing workspace: {str(e)}")
            return False, f'Error initializing workspace: {str(e)}'
    
    def get_model_files(self):
        """Get list of model files"""
        if not self.is_initialized():
            return []
        
        model_dir = self.workspace_path / self.lesson['model_dir']
        if not model_dir.exists():
            return []
        
        return sorted([f.stem for f in model_dir.glob('*.sql')])
    
    def load_model(self, model_name):
        """Load model SQL content"""
        model_path = self.workspace_path / self.lesson['model_dir'] / f'{model_name}.sql'
        if model_path.exists():
            return model_path.read_text()
        return ""
    
    def load_original_model(self, model_name):
        """Load original model from source"""
        source_path = Path(__file__).parent.parent / 'dbt_project' / self.lesson['model_dir'] / f'{model_name}.sql'
        if source_path.exists():
            return source_path.read_text()
        return ""
    
    def save_model(self, model_name, sql_content):
        """Save model SQL"""
        try:
            model_path = self.workspace_path / self.lesson['model_dir'] / f'{model_name}.sql'
            model_path.parent.mkdir(parents=True, exist_ok=True)
            model_path.write_text(sql_content)
            return True, 'Model saved successfully'
        except Exception as e:
            return False, f'Error saving model: {str(e)}'
    
    def execute_models(self, model_names, include_children=False, full_refresh=False):
        """Execute DBT models"""
        if not self.is_initialized():
            return False, 'Workspace not initialized'
        
        try:
            results = []
            for model_name in model_names:
                # Build the selector
                selector = model_name
                if include_children:
                    selector += "+"
                
                # Build command
                cmd = [
                    'dbt', 'run',
                    '--select', selector,
                    '--profiles-dir', str(self.workspace_path),
                    '--project-dir', str(self.workspace_path),
                    '--fail-fast'
                ]
                if full_refresh:
                    cmd.append('--full-refresh')
                
                logger.info(f"Executing dbt command: {' '.join(cmd)}")
                logger.info(f"Working directory: {self.workspace_path}")
                logger.info(f"User schema: {self.user.schema_name}")
                
                result = subprocess.run(
                    cmd,
                    cwd=self.workspace_path,
                    capture_output=True,
                    text=True,
                    env={
                        **os.environ,
                        'MOTHERDUCK_TOKEN': settings.MOTHERDUCK_TOKEN,
                        'DBT_PROFILES_DIR': str(self.workspace_path)
                    },
                    timeout=300  # 5 minute timeout
                )
                
                logger.info(f"dbt return code: {result.returncode}")
                logger.info(f"dbt stdout:\n{result.stdout}")
                if result.stderr:
                    logger.error(f"dbt stderr:\n{result.stderr}")
                
                results.append({
                    'model': model_name,
                    'success': result.returncode == 0,
                    'output': result.stdout + '\n' + result.stderr,
                    'returncode': result.returncode
                })
            
            return True, results
        except subprocess.TimeoutExpired:
            logger.error("dbt command timed out")
            return False, "dbt execution timed out after 5 minutes"
        except Exception as e:
            logger.error(f"Error executing models: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False, str(e)
    
    def run_seeds(self):
        """Run DBT seeds for specific lesson only"""
        try:
            seed_dir = self.workspace_path / 'seeds' / self.lesson['id']
            if not seed_dir.exists():
                return True, 'No seeds found for this lesson'
            
            # Get all seed files for this lesson
            seed_files = list(seed_dir.glob('*.csv'))
            if not seed_files:
                return True, 'No seed files found for this lesson'
            
            logger.info(f"Found {len(seed_files)} seed files for lesson {self.lesson['id']}")
            
            # Run seeds only for this lesson's files
            # Use --select to target specific seeds by path pattern
            cmd = [
                'dbt', 'seed',
                '--select', f"path:seeds/{self.lesson['id']}/*",
                '--profiles-dir', str(self.workspace_path),
                '--project-dir', str(self.workspace_path),
                '--fail-fast'
            ]
            
            logger.info(f"Running seed command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                env={
                    **os.environ,
                    'MOTHERDUCK_TOKEN': settings.MOTHERDUCK_TOKEN
                },
                timeout=300
            )
            
            logger.info(f"Seed command completed with return code: {result.returncode}")
            if result.stdout:
                logger.info(f"Seed stdout: {result.stdout}")
            if result.stderr:
                logger.error(f"Seed stderr: {result.stderr}")
            
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "Seed command timed out"
        except Exception as e:
            logger.error(f"Error running seeds: {str(e)}")
            return False, str(e)

    def _stream_output(self, process, log_queue, job_id, timeout=300):
        """Stream output from subprocess to queue with timeout"""
        start_time = time.time()
        try:
            while True:
                # Check timeout
                if time.time() - start_time > timeout:
                    logger.error(f"Job {job_id} timed out after {timeout} seconds")
                    process.kill()
                    log_queue.put(f"__ERROR__:Execution timed out after {timeout} seconds")
                    break

                # Try to read line with small timeout
                line = process.stdout.readline()
                if line:
                    log_queue.put(line)
                    logger.debug(f"Job {job_id}: {line.rstrip()}")

                # Check if process has finished
                if process.poll() is not None:
                    # Process has finished, read any remaining output
                    for line in process.stdout:
                        if line:
                            log_queue.put(line)
                    break

                # Small sleep to prevent busy waiting
                time.sleep(0.1)

            # Send completion message
            if process.returncode == 0:
                log_queue.put("__COMPLETE__")
            else:
                log_queue.put(f"__ERROR__:{process.returncode}")

        except Exception as e:
            logger.error(f"Error streaming output for job {job_id}: {str(e)}")
            log_queue.put(f"__ERROR__:{str(e)}")
            try:
                process.kill()
            except:
                pass
        finally:
            # Mark job as finished
            if job_id in self.active_jobs:
                self.active_jobs[job_id]['finished'] = True

    def execute_models_streaming(self, model_names, include_children=False, full_refresh=False):
        """Execute DBT models with streaming logs"""
        if not self.is_initialized():
            return None, 'Workspace not initialized'

        # Check concurrent job limit
        if len(self.active_jobs) >= self.MAX_CONCURRENT_JOBS:
            return None, f'Maximum concurrent jobs ({self.MAX_CONCURRENT_JOBS}) reached. Please wait for existing jobs to complete.'

        try:
            # Generate job ID
            job_id = str(uuid.uuid4())

            # Create log queue
            log_queue = queue.Queue()

            # Build the selector
            selectors = []
            for model_name in model_names:
                selector = model_name
                if include_children:
                    selector += "+"
                selectors.append(selector)

            # Build command
            cmd = [
                'dbt', 'run',
                '--select', ' '.join(selectors),
                '--profiles-dir', str(self.workspace_path),
                '--project-dir', str(self.workspace_path),
                '--fail-fast'
            ]
            if full_refresh:
                cmd.append('--full-refresh')

            logger.info(f"Starting streaming execution with job ID: {job_id}")
            logger.info(f"Executing dbt command: {' '.join(cmd)}")

            # Start subprocess
            process = subprocess.Popen(
                cmd,
                cwd=self.workspace_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env={
                    **os.environ,
                    'MOTHERDUCK_TOKEN': settings.MOTHERDUCK_TOKEN,
                    'DBT_PROFILES_DIR': str(self.workspace_path)
                }
            )

            # Store job info
            self.active_jobs[job_id] = {
                'process': process,
                'log_queue': log_queue,
                'model_names': model_names,
                'finished': False
            }

            # Start thread to stream output
            thread = threading.Thread(
                target=self._stream_output,
                args=(process, log_queue, job_id),
                daemon=True
            )
            thread.start()

            return job_id, None

        except Exception as e:
            logger.error(f"Error starting streaming execution: {str(e)}")
            return None, str(e)

    def run_seeds_streaming(self):
        """Run DBT seeds with streaming logs"""
        # Check concurrent job limit
        if len(self.active_jobs) >= self.MAX_CONCURRENT_JOBS:
            return None, f'Maximum concurrent jobs ({self.MAX_CONCURRENT_JOBS}) reached. Please wait for existing jobs to complete.'

        try:
            seed_dir = self.workspace_path / 'seeds' / self.lesson['id']
            if not seed_dir.exists():
                return None, 'No seeds found for this lesson'

            # Get all seed files for this lesson
            seed_files = list(seed_dir.glob('*.csv'))
            if not seed_files:
                return None, 'No seed files found for this lesson'

            logger.info(f"Found {len(seed_files)} seed files for lesson {self.lesson['id']}")

            # Generate job ID
            job_id = str(uuid.uuid4())

            # Create log queue
            log_queue = queue.Queue()

            # Build command
            cmd = [
                'dbt', 'seed',
                '--select', f"path:seeds/{self.lesson['id']}/*",
                '--profiles-dir', str(self.workspace_path),
                '--project-dir', str(self.workspace_path),
                '--fail-fast'
            ]

            logger.info(f"Starting streaming seed execution with job ID: {job_id}")
            logger.info(f"Running seed command: {' '.join(cmd)}")

            # Start subprocess
            process = subprocess.Popen(
                cmd,
                cwd=self.workspace_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env={
                    **os.environ,
                    'MOTHERDUCK_TOKEN': settings.MOTHERDUCK_TOKEN
                }
            )

            # Store job info
            self.active_jobs[job_id] = {
                'process': process,
                'log_queue': log_queue,
                'finished': False
            }

            # Start thread to stream output
            thread = threading.Thread(
                target=self._stream_output,
                args=(process, log_queue, job_id),
                daemon=True
            )
            thread.start()

            return job_id, None

        except Exception as e:
            logger.error(f"Error starting streaming seed execution: {str(e)}")
            return None, str(e)

    @classmethod
    def get_job_logs(cls, job_id):
        """Get logs for a specific job (generator for streaming)"""
        if job_id not in cls.active_jobs:
            yield "data: __NOTFOUND__\n\n"
            return

        job_info = cls.active_jobs[job_id]
        log_queue = job_info['log_queue']

        while True:
            try:
                # Get log line with timeout
                line = log_queue.get(timeout=0.1)

                # Check for completion markers
                if line.startswith("__COMPLETE__"):
                    yield f"data: __COMPLETE__\n\n"
                    break
                elif line.startswith("__ERROR__"):
                    yield f"data: {line}\n\n"
                    break
                else:
                    # Send log line to client
                    yield f"data: {line}\n\n"

            except queue.Empty:
                # Check if job is finished
                if job_info['finished']:
                    # No more logs, job is done
                    yield "data: __COMPLETE__\n\n"
                    break
                # Otherwise, continue waiting for logs
                continue
            except Exception as e:
                logger.error(f"Error getting logs for job {job_id}: {str(e)}")
                yield f"data: __ERROR__:{str(e)}\n\n"
                break

        # Clean up job after streaming is complete
        try:
            del cls.active_jobs[job_id]
        except KeyError:
            pass