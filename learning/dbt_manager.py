import os
import tempfile
import shutil
import subprocess
from pathlib import Path
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class DBTManager:
    """Manage DBT workspace and operations"""
    
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
      threads: 4
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
                    '--project-dir', str(self.workspace_path)
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
        """Run DBT seeds"""
        try:
            seed_dir = self.workspace_path / 'seeds' / self.lesson['id']
            if not seed_dir.exists():
                return True, 'No seeds found for this lesson'
            
            cmd = [
                'dbt', 'seed',
                '--profiles-dir', str(self.workspace_path),
                '--project-dir', str(self.workspace_path)
            ]
            
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
            
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "Seed command timed out"
        except Exception as e:
            return False, str(e)