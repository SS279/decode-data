"""
DBT Lineage Parser
Extracts table lineage and field information from dbt models
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class DBTLineageParser:
    """Parse dbt models to extract lineage and field information"""

    def __init__(self, project_path: str):
        """Initialize parser with dbt project path"""
        self.project_path = Path(project_path)
        self.models = {}
        self.sources = {}

    def parse_project(self, model_dir: str) -> Dict[str, Any]:
        """
        Parse a specific model directory and return lineage information

        Args:
            model_dir: Relative path to model directory (e.g., 'models/fintech')

        Returns:
            Dictionary containing nodes, edges, and metadata
        """
        model_path = self.project_path / model_dir

        if not model_path.exists():
            logger.error(f"Model directory not found: {model_path}")
            return {'nodes': [], 'edges': []}

        # Parse sources
        self._parse_sources(model_path)

        # Parse SQL models
        self._parse_models(model_path)

        # Build lineage graph
        return self._build_lineage_graph()

    def _parse_sources(self, model_path: Path):
        """Parse sources.yml to extract source table definitions"""
        sources_file = model_path / 'sources.yml'

        if not sources_file.exists():
            logger.warning(f"No sources.yml found in {model_path}")
            return

        try:
            with open(sources_file, 'r') as f:
                sources_config = yaml.safe_load(f)

            if not sources_config or 'sources' not in sources_config:
                return

            for source in sources_config['sources']:
                source_name = source.get('name')
                tables = source.get('tables', [])

                for table in tables:
                    table_name = table.get('name')
                    columns = table.get('columns', [])

                    # Create unique identifier for source
                    source_id = f"source.{source_name}.{table_name}"

                    self.sources[source_id] = {
                        'id': source_id,
                        'name': table_name,
                        'type': 'source',
                        'source_name': source_name,
                        'description': table.get('description', ''),
                        'columns': [
                            {
                                'name': col.get('name'),
                                'description': col.get('description', ''),
                                'tests': col.get('tests', [])
                            }
                            for col in columns
                        ],
                        'dependencies': []
                    }
        except Exception as e:
            logger.error(f"Error parsing sources.yml: {e}")

    def _parse_models(self, model_path: Path):
        """Parse SQL model files to extract dependencies and columns"""
        sql_files = model_path.glob('*.sql')

        for sql_file in sql_files:
            try:
                model_name = sql_file.stem

                with open(sql_file, 'r') as f:
                    sql_content = f.read()

                # Extract model type from config
                model_type = self._extract_model_type(sql_content)

                # Extract dependencies (ref() and source() calls)
                dependencies = self._extract_dependencies(sql_content)

                # Extract columns from SELECT statement
                columns = self._extract_columns(sql_content)

                # Extract description from comments
                description = self._extract_description(sql_content)

                self.models[model_name] = {
                    'id': f"model.{model_name}",
                    'name': model_name,
                    'type': self._classify_model_type(model_name),
                    'materialization': model_type,
                    'description': description,
                    'columns': columns,
                    'dependencies': dependencies
                }
            except Exception as e:
                logger.error(f"Error parsing model {sql_file}: {e}")

    def _extract_model_type(self, sql_content: str) -> str:
        """Extract materialization type from config"""
        config_match = re.search(r"config\s*\(\s*materialized\s*=\s*['\"](\w+)['\"]", sql_content)
        return config_match.group(1) if config_match else 'view'

    def _extract_dependencies(self, sql_content: str) -> List[str]:
        """Extract model dependencies from ref() and source() calls"""
        dependencies = []

        # Find all ref() calls
        ref_pattern = r"ref\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"
        ref_matches = re.findall(ref_pattern, sql_content)
        dependencies.extend([f"model.{ref}" for ref in ref_matches])

        # Find all source() calls
        source_pattern = r"source\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)"
        source_matches = re.findall(source_pattern, sql_content)
        dependencies.extend([f"source.{src}.{tbl}" for src, tbl in source_matches])

        return dependencies

    def _extract_columns(self, sql_content: str) -> List[Dict[str, str]]:
        """Extract column names and expressions from SELECT statement"""
        columns = []

        # Remove comments
        sql_no_comments = re.sub(r'/\*.*?\*/', '', sql_content, flags=re.DOTALL)
        sql_no_comments = re.sub(r'--.*$', '', sql_no_comments, flags=re.MULTILINE)

        # Find the main SELECT statement
        select_match = re.search(
            r'SELECT\s+(.*?)\s+FROM',
            sql_no_comments,
            re.IGNORECASE | re.DOTALL
        )

        if select_match:
            select_clause = select_match.group(1)

            # Split by comma (basic parsing - may not handle all cases perfectly)
            # This is a simplified approach
            column_patterns = [
                r'(\w+)\s+AS\s+(\w+)',  # column AS alias
                r'(\w+\.\w+)\s+AS\s+(\w+)',  # table.column AS alias
                r'(\w+)',  # simple column name
            ]

            lines = select_clause.split(',')
            for line in lines:
                line = line.strip()
                if not line or line.upper() in ['DISTINCT', '*']:
                    continue

                # Try to extract column name
                as_match = re.search(r'\s+AS\s+(\w+)', line, re.IGNORECASE)
                if as_match:
                    col_name = as_match.group(1)
                    columns.append({
                        'name': col_name,
                        'expression': line.replace(as_match.group(0), '').strip()
                    })
                elif re.match(r'^\w+$', line):
                    columns.append({
                        'name': line,
                        'expression': line
                    })

        return columns[:20]  # Limit to first 20 columns for display

    def _extract_description(self, sql_content: str) -> str:
        """Extract description from SQL comments"""
        # Look for multi-line comment at the beginning
        comment_match = re.search(r'/\*\s*(.*?)\s*\*/', sql_content, re.DOTALL)
        if comment_match:
            comment_text = comment_match.group(1)
            # Get first line or first meaningful line
            lines = [line.strip() for line in comment_text.split('\n') if line.strip()]
            if lines:
                # Skip lines that look like headers
                for line in lines:
                    if not line.startswith('Learning') and not line.startswith('-'):
                        return line[:200]  # Limit length
        return ''

    def _classify_model_type(self, model_name: str) -> str:
        """Classify model type based on naming convention"""
        if model_name.startswith('stg_'):
            return 'staging'
        elif model_name.startswith('fct_') or model_name.startswith('fact_'):
            return 'fact'
        elif model_name.startswith('dim_'):
            return 'dimension'
        else:
            return 'model'

    def _build_lineage_graph(self) -> Dict[str, Any]:
        """Build lineage graph with nodes and edges"""
        nodes = []
        edges = []

        # Add source nodes
        for source_id, source_data in self.sources.items():
            nodes.append({
                'id': source_id,
                'name': source_data['name'],
                'type': 'source',
                'description': source_data['description'],
                'columns': source_data['columns']
            })

        # Add model nodes and edges
        for model_id, model_data in self.models.items():
            # Add node
            nodes.append({
                'id': model_data['id'],
                'name': model_data['name'],
                'type': model_data['type'],
                'materialization': model_data['materialization'],
                'description': model_data['description'],
                'columns': model_data['columns']
            })

            # Add edges for dependencies
            for dep in model_data['dependencies']:
                edges.append({
                    'from': dep,
                    'to': model_data['id']
                })

        return {
            'nodes': nodes,
            'edges': edges,
            'summary': {
                'total_models': len(self.models),
                'total_sources': len(self.sources),
                'staging_models': sum(1 for m in self.models.values() if m['type'] == 'staging'),
                'fact_models': sum(1 for m in self.models.values() if m['type'] == 'fact'),
                'dimension_models': sum(1 for m in self.models.values() if m['type'] == 'dimension')
            }
        }


def get_project_lineage(project_id: str) -> Dict[str, Any]:
    """
    Get lineage data for a specific project

    Args:
        project_id: Project identifier (e.g., 'fintech', 'cafe_chain')

    Returns:
        Lineage data with nodes and edges
    """
    # Map project IDs to model directories
    project_mapping = {
        'hello_dbt': 'models/hello_dbt',
        'fintech': 'models/fintech',
        'cafe_chain': 'models/cafe_chain',
        'energy_smart': 'models/energy_smart'
    }

    if project_id not in project_mapping:
        return {'nodes': [], 'edges': [], 'error': 'Project not found'}

    # Get the dbt project path
    from django.conf import settings
    from pathlib import Path

    dbt_project_path = Path(__file__).parent.parent / 'dbt_project'

    parser = DBTLineageParser(str(dbt_project_path))
    lineage = parser.parse_project(project_mapping[project_id])

    return lineage
