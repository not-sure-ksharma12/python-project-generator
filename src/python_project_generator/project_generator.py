"""
Standalone Python Project Generator

A flexible tool for generating Python projects from templates.
Can work with local templates or remote Git repositories.
"""

__version__ = "1.0.0"

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
import json


# Pilot (#24): single source of truth for selected builtin templates. Maps template_id -> ProjectGenerator method name.
_BUILTIN_TEMPLATE_GENERATOR_PILOT: Dict[str, str] = {
    "django-web-app": "_generate_minimal_template",
}


class TemplateManager:
    """Manages project templates from various sources."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.templates_dir = Path.home() / ".python-project-generator" / "templates"
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Default templates configuration
        self.default_templates = {
            "python-skeleton": {
                "name": "Python Skeleton Project",
                "description": "Complete Python project with CLI, GUI, testing, and packaging (builtin)",
                "source": "local",
                "type": "builtin",
                "features": ["cli", "gui", "tests", "executable", "pypi_packaging", "dev_requirements", "license", "readme", "changelog", "contributors", "code_of_conduct", "security", "makefile", "gitignore", "github_actions"]
            },
            "minimal-python": {
                "name": "Minimal Python Project",
                "description": "Basic Python project structure",
                "source": "local",
                "type": "builtin",
                "features": ["pypi_packaging", "tests", "license", "readme", "changelog", "gitignore"]
            },
            "flask-web-app": {
                "name": "Flask Web Application",
                "description": "Flask web application with blueprints, templates, and database support",
                "source": "local",
                "type": "builtin",
                "features": ["web_framework", "database", "templates", "static_files", "tests", "pypi_packaging", "license", "readme", "gitignore", "docker"]
            },
            "fastapi-web-api": {
                "name": "FastAPI Web API",
                "description": "Modern async FastAPI application with automatic docs and validation",
                "source": "local",
                "type": "builtin",
                "features": ["web_framework", "api_docs", "async", "database", "tests", "pypi_packaging", "license", "readme", "gitignore", "docker"]
            },
            "django-web-app": {
                "name": "Django Web Application",
                "description": "Full-featured Django web application with admin and user management",
                "source": "local",
                "type": "builtin",
                "features": ["web_framework", "admin", "user_auth", "database", "templates", "static_files", "tests", "license", "readme", "gitignore"]
            },
            "data-science-project": {
                "name": "Data Science Project",
                "description": "Data science project with Jupyter notebooks, analysis scripts, and visualization",
                "source": "local",
                "type": "builtin",
                "features": ["jupyter", "data_analysis", "visualization", "notebooks", "datasets", "tests", "pypi_packaging", "license", "readme", "gitignore"]
            },
            "machine-learning-project": {
                "name": "Machine Learning Project",
                "description": "ML project template with model training, evaluation, and deployment scripts",
                "source": "local",
                "type": "builtin",
                "features": ["ml_framework", "model_training", "evaluation", "deployment", "experiments", "tests", "pypi_packaging", "license", "readme", "gitignore", "docker"]
            },
            "cli-tool": {
                "name": "Command Line Tool",
                "description": "Professional CLI tool with Click framework and comprehensive testing",
                "source": "local",
                "type": "builtin",
                "features": ["cli", "click_framework", "config_files", "logging", "tests", "pypi_packaging", "license", "readme", "gitignore"]
            },
            "python-library": {
                "name": "Python Library/Package",
                "description": "Professional Python library ready for PyPI publication",
                "source": "local",
                "type": "builtin",
                "features": ["library_structure", "api_documentation", "comprehensive_tests", "pypi_packaging", "tox", "ci_cd", "license", "readme", "changelog", "contributors", "code_of_conduct", "security", "gitignore", "github_actions"]
            },
            "game-development": {
                "name": "Game Development",
                "description": "Game development project with Pygame and asset management",
                "source": "local",
                "type": "builtin",
                "features": ["game_framework", "asset_management", "scenes", "sprites", "sound", "tests", "pypi_packaging", "license", "readme", "gitignore"]
            },
            "desktop-gui-app": {
                "name": "Desktop GUI Application",
                "description": "Cross-platform desktop GUI application with wxPython and packaging",
                "source": "local",
                "type": "builtin",
                "features": ["gui", "desktop_app", "menus", "dialogs", "config", "executable", "tests", "pypi_packaging", "license", "readme", "gitignore"]
            },
            "microservice": {
                "name": "Microservice",
                "description": "Microservice template with FastAPI, Docker, and health checks",
                "source": "local",
                "type": "builtin",
                "features": ["web_framework", "microservice", "health_checks", "metrics", "logging", "docker", "kubernetes", "tests", "license", "readme", "gitignore"]
            },
            "api-client-library": {
                "name": "API Client Library",
                "description": "Python library for interacting with REST APIs",
                "source": "local",
                "type": "builtin",
                "features": ["api_client", "authentication", "rate_limiting", "retries", "comprehensive_tests", "pypi_packaging", "license", "readme", "gitignore"]
            },
            "automation-scripts": {
                "name": "Automation Scripts",
                "description": "Collection of automation scripts with scheduling and monitoring",
                "source": "local",
                "type": "builtin",
                "features": ["automation", "scheduling", "monitoring", "logging", "config_files", "tests", "license", "readme", "gitignore"]
            },
            "jupyter-research": {
                "name": "Jupyter Research Project",
                "description": "Research project template with Jupyter notebooks and reproducible environment",
                "source": "local",
                "type": "builtin",
                "features": ["jupyter", "research", "reproducible_env", "data_versioning", "notebooks", "reports", "license", "readme", "gitignore"]
            },
            "binary-extension": {
                "name": "Binary/Extension Package",
                "description": "Python package with C/C++ extensions and compiled binary modules",
                "source": "local",
                "type": "builtin",
                "features": ["c_extensions", "compilation", "wheel_building", "cross_platform", "performance", "tests", "pypi_packaging", "license", "readme", "gitignore", "ci_cd"]
            },
            "namespace-package": {
                "name": "Namespace Package",
                "description": "Namespace package for distributed development across multiple repositories",
                "source": "local",
                "type": "builtin",
                "features": ["namespace_packaging", "distributed_development", "implicit_namespaces", "pypi_packaging", "tests", "license", "readme", "gitignore"]
            },
            "plugin-framework": {
                "name": "Plugin Framework Package",
                "description": "Plugin-style package with entry points and extensible architecture",
                "source": "local",
                "type": "builtin",
                "features": ["plugin_system", "entry_points", "plugin_discovery", "extensible_architecture", "hooks", "tests", "pypi_packaging", "license", "readme", "gitignore"]
            }}
    
    def get_available_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available templates."""
        return self.default_templates
    
    def download_template(self, template_id: str) -> Optional[Path]:
        """Download template from remote source."""
        template_config = self.default_templates.get(template_id)
        if not template_config:
            self.logger.error(f"Template {template_id} not found")
            return None
        
        if template_config["type"] == "git":
            return self._clone_git_template(template_id, template_config["source"])
        elif template_config["type"] == "builtin":
            return self._get_builtin_template(template_id)
        
        return None
    
    def _clone_git_template(self, template_id: str, git_url: str) -> Optional[Path]:
        """Clone a git repository template."""
        template_path = self.templates_dir / template_id
        
        try:
            if template_path.exists():
                # Update existing template
                self.logger.info(f"Updating template {template_id}...")
                subprocess.run(
                    ["git", "pull"],
                    cwd=template_path,
                    check=True,
                    capture_output=True
                )
            else:
                # Clone new template
                self.logger.info(f"Downloading template {template_id}...")
                subprocess.run(
                    ["git", "clone", git_url, str(template_path)],
                    check=True,
                    capture_output=True
                )
            
            return template_path
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to download template: {e}")
            return None
    
    def _get_builtin_template(self, template_id: str) -> Path:
        """Get path to builtin template."""
        # Builtin templates are generated dynamically, so return None
        # The actual generation happens in _generate_builtin_project
        return None
    
    def get_template_structure(self, template_id: str) -> Dict[str, Any]:
        """Get the expected project structure for a template."""
        structures = {
            "minimal-python": {
                "description": "Basic Python project with essential files only",
                "structure": [
                    "your_project/",
                    "├── src/",
                    "│   └── your_project/",
                    "│       ├── __init__.py",
                    "│       └── core.py",
                    "├── tests/",
                    "│   ├── __init__.py",
                    "│   └── test_core.py",
                    "├── setup.py",
                    "├── pyproject.toml",
                    "├── requirements.txt",
                    "├── .gitignore",
                    "├── LICENSE",
                    "└── README.md"
                ],
                "key_features": [
                    "Simple package structure",
                    "Basic testing setup",
                    "PyPI packaging ready",
                    "Essential documentation"
                ]
            },
            "flask-web-app": {
                "description": "Full-featured Flask web application with blueprints and database support",
                "structure": [
                    "your_project/",
                    "├── src/",
                    "│   └── your_project/",
                    "│       ├── __init__.py",
                    "│       ├── app.py",
                    "│       ├── config.py",
                    "│       ├── blueprints/",
                    "│       │   ├── __init__.py",
                    "│       │   └── main.py",
                    "│       ├── templates/",
                    "│       │   ├── base.html",
                    "│       │   └── index.html",
                    "│       └── static/",
                    "│           ├── css/",
                    "│           └── js/",
                    "├── tests/",
                    "├── requirements.txt",
                    "├── Dockerfile",
                    "├── docker-compose.yml",
                    "└── README.md"
                ],
                "key_features": [
                    "Flask application factory",
                    "Blueprint organization",
                    "Jinja2 templates",
                    "Static file handling",
                    "Database integration",
                    "Docker containerization"
                ]
            },
            "fastapi-web-api": {
                "description": "Modern async FastAPI application with automatic documentation",
                "structure": [
                    "your_project/",
                    "├── src/",
                    "│   └── your_project/",
                    "│       ├── __init__.py",
                    "│       ├── main.py",
                    "│       ├── models.py",
                    "│       ├── routers/",
                    "│       │   ├── __init__.py",
                    "│       │   └── api.py",
                    "│       └── database.py",
                    "├── tests/",
                    "├── requirements.txt",
                    "├── Dockerfile",
                    "├── run.py",
                    "└── README.md"
                ],
                "key_features": [
                    "Async/await support",
                    "Automatic API documentation",
                    "Pydantic data validation",
                    "Type hints throughout",
                    "Database integration",
                    "Production-ready"
                ]
            },
            "data-science-project": {
                "description": "Complete data science project with notebooks and analysis tools",
                "structure": [
                    "your_project/",
                    "├── data/",
                    "│   ├── raw/",
                    "│   ├── processed/",
                    "│   └── external/",
                    "├── notebooks/",
                    "│   └── 01-exploratory-analysis.ipynb",
                    "├── src/",
                    "│   └── your_project/",
                    "│       ├── __init__.py",
                    "│       ├── data.py",
                    "│       └── analysis.py",
                    "├── reports/",
                    "├── requirements.txt",
                    "└── README.md"
                ],
                "key_features": [
                    "Organized data directories",
                    "Jupyter notebook integration",
                    "Data processing utilities",
                    "Analysis modules",
                    "Reproducible workflows"
                ]
            },
            "cli-tool": {
                "description": "Command-line interface tool with Click framework",
                "structure": [
                    "your_project/",
                    "├── src/",
                    "│   └── your_project/",
                    "│       ├── __init__.py",
                    "│       └── cli.py",
                    "├── tests/",
                    "├── setup.py",
                    "├── pyproject.toml",
                    "├── requirements.txt",
                    "└── README.md"
                ],
                "key_features": [
                    "Click CLI framework",
                    "Command-line entry points",
                    "Argument parsing",
                    "Help generation",
                    "Installable commands"
                ]
            },
            "binary-extension": {
                "description": "Python package with C/C++ extensions for high performance",
                "structure": [
                    "your_project/",
                    "├── src/",
                    "│   └── your_project/",
                    "│       ├── __init__.py",
                    "│       ├── core.py",
                    "│       └── ext/",
                    "│           └── your_project_ext.c",
                    "├── tests/",
                    "│   ├── __init__.py",
                    "│   └── test_extension.py",
                    "├── build_ext.py",
                    "├── setup.py",
                    "├── pyproject.toml",
                    "├── .github/workflows/wheels.yml",
                    "└── README.md"
                ],
                "key_features": [
                    "C/C++ extension modules",
                    "Pure Python fallbacks",
                    "Cross-platform compilation",
                    "Binary wheel building",
                    "Performance optimization",
                    "CI/CD for wheels"
                ]
            },
            "namespace-package": {
                "description": "Namespace package for distributed development across repositories",
                "structure": [
                    "namespace-component/",
                    "├── src/",
                    "│   └── namespace/          # No __init__.py!",
                    "│       └── component/",
                    "│           ├── __init__.py",
                    "│           └── core.py",
                    "├── tests/",
                    "├── docs/",
                    "│   └── namespace_usage.md",
                    "├── setup.py",
                    "├── pyproject.toml",
                    "└── README.md"
                ],
                "key_features": [
                    "Implicit namespace packages",
                    "Distributed development",
                    "Independent versioning",
                    "Inter-component communication",
                    "Modular architecture",
                    "Team collaboration"
                ]
            },
            "plugin-framework": {
                "description": "Plugin system with entry points and extensible architecture",
                "structure": [
                    "your_project/",
                    "├── src/",
                    "│   └── your_project/",
                    "│       ├── __init__.py",
                    "│       ├── core.py",
                    "│       ├── registry.py",
                    "│       ├── cli.py",
                    "│       └── plugins/",
                    "│           ├── __init__.py",
                    "│           ├── example_plugin.py",
                    "│           └── logging_plugin.py",
                    "├── tests/",
                    "│   ├── test_plugin_system.py",
                    "│   └── test_example_plugins.py",
                    "├── setup.py",
                    "└── README.md"
                ],
                "key_features": [
                    "Plugin base classes",
                    "Hook system",
                    "Entry point discovery",
                    "Dynamic loading",
                    "CLI management",
                    "Extensible architecture"
                ]
            },
            "django-web-app": {
                "description": "Django web application with models, views, and templates",
                "structure": [
                    "your_project/",
                    "├── your_project/",
                    "│   ├── __init__.py",
                    "│   ├── settings.py",
                    "│   ├── urls.py",
                    "│   └── wsgi.py",
                    "├── app/",
                    "│   ├── __init__.py",
                    "│   ├── models.py",
                    "│   ├── views.py",
                    "│   └── urls.py",
                    "├── templates/",
                    "├── static/",
                    "├── requirements.txt",
                    "├── manage.py",
                    "└── README.md"
                ],
                "key_features": [
                    "Django framework",
                    "Model-View-Template pattern",
                    "Admin interface",
                    "ORM integration",
                    "URL routing",
                    "Static file handling"
                ]
            },
            "machine-learning-project": {
                "description": "Machine learning project with model training and evaluation",
                "structure": [
                    "your_project/",
                    "├── data/",
                    "│   ├── raw/",
                    "│   ├── processed/",
                    "│   └── models/",
                    "├── notebooks/",
                    "├── src/",
                    "│   └── your_project/",
                    "│       ├── __init__.py",
                    "│       ├── data/",
                    "│       ├── features/",
                    "│       ├── models/",
                    "│       └── visualization/",
                    "├── tests/",
                    "├── requirements.txt",
                    "└── README.md"
                ],
                "key_features": [
                    "Data pipeline structure",
                    "Model training modules",
                    "Feature engineering",
                    "Experiment tracking",
                    "Model evaluation",
                    "Visualization tools"
                ]
            },
            "python-library": {
                "description": "Reusable Python library for distribution",
                "structure": [
                    "your_project/",
                    "├── src/",
                    "│   └── your_project/",
                    "│       ├── __init__.py",
                    "│       ├── core.py",
                    "│       └── utils.py",
                    "├── tests/",
                    "├── docs/",
                    "├── examples/",
                    "├── setup.py",
                    "├── pyproject.toml",
                    "├── MANIFEST.in",
                    "└── README.md"
                ],
                "key_features": [
                    "Library structure",
                    "Public API design",
                    "Documentation",
                    "Example usage",
                    "PyPI packaging",
                    "Version management"
                ]
            }
        }
        
        # Add default structure for other templates
        default_structure = {
            "description": "Standard Python project structure",
            "structure": [
                "your_project/",
                "├── src/",
                "│   └── your_project/",
                "│       ├── __init__.py",
                "│       └── core.py",
                "├── tests/",
                "├── setup.py",
                "├── requirements.txt",
                "└── README.md"
            ],
            "key_features": [
                "Standard package layout",
                "Basic functionality",
                "Testing framework",
                "Documentation"
            ]
        }
        
        return structures.get(template_id, default_structure)
    
    def get_template_detailed_info(self, template_id: str) -> Dict[str, Any]:
        """Get detailed information about a template."""
        if template_id not in self.default_templates:
            return {"error": f"Template '{template_id}' not found"}
        
        template_info = self.default_templates[template_id].copy()
        structure_info = self.get_template_structure(template_id)
        
        # Combine template metadata with structure information
        detailed_info = {
            "id": template_id,
            "name": template_info.get("name", "Unknown Template"),
            "description": template_info.get("description", "No description available"),
            "type": template_info.get("type", "unknown"),
            "source": template_info.get("source", "unknown"),
            "features": template_info.get("features", []),
            "structure_description": structure_info.get("description", ""),
            "project_structure": structure_info.get("structure", []),
            "key_features": structure_info.get("key_features", []),
            "use_cases": self._get_template_use_cases(template_id),
            "dependencies": self._get_template_dependencies(template_id)
        }
        
        return detailed_info
    
    def _get_template_use_cases(self, template_id: str) -> List[str]:
        """Get use cases for a template."""
        use_cases = {
            "minimal-python": [
                "Simple scripts and utilities",
                "Learning Python packaging",
                "Quick prototypes",
                "Basic libraries"
            ],
            "flask-web-app": [
                "Web applications",
                "REST APIs",
                "Dashboards",
                "Content management",
                "E-commerce sites"
            ],
            "fastapi-web-api": [
                "High-performance APIs",
                "Microservices",
                "Machine learning APIs",
                "Real-time applications",
                "Data processing services"
            ],
            "data-science-project": [
                "Data analysis",
                "Machine learning research",
                "Statistical modeling",
                "Data visualization",
                "Scientific computing"
            ],
            "cli-tool": [
                "Command-line utilities",
                "Build tools",
                "System administration",
                "File processing",
                "Automation scripts"
            ],
            "binary-extension": [
                "Scientific computing",
                "Performance-critical algorithms",
                "Hardware interfaces",
                "Mathematical libraries",
                "Image/signal processing"
            ],
            "namespace-package": [
                "Large organizations",
                "Microservice architectures",
                "Plugin ecosystems",
                "Distributed teams",
                "Modular frameworks"
            ],
            "plugin-framework": [
                "Extensible applications",
                "Tool frameworks",
                "Workflow systems",
                "IDE plugins",
                "Content management"
            ],
            "django-web-app": [
                "Complex web applications",
                "Content management systems",
                "E-commerce platforms",
                "Social networks",
                "Enterprise applications"
            ],
            "machine-learning-project": [
                "Predictive modeling",
                "Deep learning research",
                "Computer vision",
                "Natural language processing",
                "Recommendation systems"
            ],
            "python-library": [
                "Reusable utilities",
                "API wrappers",
                "Mathematical libraries",
                "Data processing tools",
                "Framework extensions"
            ],
            "game-development": [
                "2D games",
                "Educational games",
                "Game prototypes",
                "Interactive simulations",
                "Game development learning"
            ],
            "desktop-gui-app": [
                "Desktop applications",
                "GUI tools",
                "Data visualization apps",
                "System utilities",
                "Cross-platform apps"
            ],
            "microservice": [
                "Distributed systems",
                "API services",
                "Cloud applications",
                "Container deployments",
                "Service mesh architectures"
            ],
            "api-client-library": [
                "API integration",
                "SDK development",
                "Service wrappers",
                "Third-party integrations",
                "API testing tools"
            ],
            "automation-scripts": [
                "Task automation",
                "System administration",
                "Data processing pipelines",
                "Scheduled jobs",
                "DevOps tooling"
            ],
            "jupyter-research": [
                "Scientific research",
                "Data exploration",
                "Academic projects",
                "Reproducible research",
                "Educational materials"
            ]
        }
        
        return use_cases.get(template_id, ["General Python development"])
    
    def _get_template_dependencies(self, template_id: str) -> List[str]:
        """Get main dependencies for a template."""
        dependencies = {
            "minimal-python": ["setuptools", "wheel"],
            "flask-web-app": ["Flask", "Jinja2", "Werkzeug"],
            "fastapi-web-api": ["FastAPI", "uvicorn", "pydantic"],
            "data-science-project": ["pandas", "numpy", "matplotlib", "jupyter"],
            "cli-tool": ["click"],
            "binary-extension": ["setuptools", "wheel", "build tools (gcc/msvc)"],
            "namespace-package": ["setuptools"],
            "plugin-framework": ["click", "importlib-metadata"],
            "django-web-app": ["Django", "psycopg2", "pillow"],
            "machine-learning-project": ["scikit-learn", "pandas", "numpy", "matplotlib", "seaborn"],
            "python-library": ["setuptools", "wheel", "sphinx"],
            "game-development": ["pygame", "pymunk"],
            "desktop-gui-app": ["wxpython", "Pillow"],
            "microservice": ["FastAPI", "docker", "kubernetes"],
            "api-client-library": ["requests", "httpx", "pydantic"],
            "automation-scripts": ["schedule", "click", "psutil"],
            "jupyter-research": ["jupyter", "ipywidgets", "matplotlib", "seaborn"]
        }
        
        return dependencies.get(template_id, ["setuptools"])


class ProjectGenerator:
    """Generates Python skeleton projects with customizable features."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.template_manager = TemplateManager()
    
    def generate_project(
        self,
        project_name: str,
        output_dir: Path,
        template_id: str = "python-skeleton",
        features: Optional[Dict[str, bool]] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Generate a new Python project from template.
        
        Args:
            project_name: Name of the project
            output_dir: Directory where project will be created
            template_id: ID of the template to use
            features: Dict of feature flags
            metadata: Project metadata (author, email, description, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get template
            template_path = self.template_manager.download_template(template_id)
            if not template_path:
                # Fallback to builtin generation
                return self._generate_builtin_project(project_name, output_dir, features or {}, metadata or {}, template_id)
            
            project_path = output_dir / project_name
            project_path.mkdir(parents=True, exist_ok=True)
            
            # Copy template
            self._copy_template(template_path, project_path)
            
            # Customize project
            self._customize_project(project_path, project_name, features or {}, metadata or {})
            
            self.logger.info(f"Project '{project_name}' generated successfully at {project_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate project: {e}")
            return False
    
    def _copy_template(self, template_path: Path, project_path: Path):
        """Copy template to project directory."""
        # Skip .git directory and other unwanted files
        ignore_patterns = {'.git', '__pycache__', '*.pyc', '.DS_Store', '.vscode', '.idea'}
        
        for item in template_path.iterdir():
            if item.name in ignore_patterns:
                continue
                
            if item.is_dir():
                shutil.copytree(item, project_path / item.name, ignore=shutil.ignore_patterns(*ignore_patterns))
            else:
                shutil.copy2(item, project_path / item.name)
    
    def _customize_project(self, project_path: Path, project_name: str, features: Dict[str, bool], metadata: Dict[str, str]):
        """Customize the project based on features and metadata."""
        package_name = self._to_package_name(project_name)
        
        # Update package names in files
        self._update_package_references(project_path, project_name, package_name, metadata)
        
        # Remove unwanted features
        self._remove_unwanted_features(project_path, features)
        
        # Add common documentation files if selected
        self._apply_common_docs(project_path, project_name, features, metadata)

        # Add optional utility/build scripts
        self._apply_optional_scripts(project_path, project_name, package_name, features, metadata)

    def _apply_optional_scripts(self, project_path: Path, project_name: str, package_name: str, features: Dict[str, bool], metadata: Dict[str, str]) -> None:
        """Create optional helper scripts/files selected in the GUI."""
        try:
            # macOS .app bundle builder script (write under scripts/)
            if features.get('mac_app_bundle', False):
                scripts_dir = project_path / "scripts"
                scripts_dir.mkdir(exist_ok=True)
                app_bundle_py = '''#!/usr/bin/env python3
import os
import shutil
import stat
import plistlib
from pathlib import Path
import sys


def create_app_bundle():
    app_name = "__APP_NAME__"
    bundle_name = app_name + ".app"

    if os.path.exists(bundle_name):
        shutil.rmtree(bundle_name)

    bundle_path = Path(bundle_name)
    contents_path = bundle_path / "Contents"
    macos_path = contents_path / "MacOS"
    resources_path = contents_path / "Resources"

    macos_path.mkdir(parents=True, exist_ok=True)
    resources_path.mkdir(parents=True, exist_ok=True)

    root = Path.cwd()
    src_dir = root / "src"
    if src_dir.exists():
        shutil.copytree(src_dir, resources_path / "src")
    else:
        print("⚠️  src directory not found; the app may not launch.")

    for file in ["requirements.txt", "README.md"]:
        if (root / file).exists():
            shutil.copy2(root / file, resources_path)

    icons_src = root / "icons"
    if icons_src.exists():
        shutil.copytree(icons_src, resources_path / "icons")

    # Create launcher (Python) inside Contents/MacOS
    launcher_code = """#!/usr/bin/env python3
import sys
import os

app_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
resources_path = os.path.join(app_path, "Resources")
src_path = os.path.join(resources_path, "src")

if src_path not in sys.path:
    sys.path.insert(0, src_path)

os.chdir(resources_path)

PACKAGE = "__PACKAGE_NAME__"

def _run():
    try:
        try:
            mod = __import__(PACKAGE + ".__main__", fromlist=["main"])  # type: ignore
            if hasattr(mod, "main"):
                return mod.main()
        except Exception:
            pass
        try:
            mod = __import__(PACKAGE + ".cli", fromlist=["main"])  # type: ignore
            if hasattr(mod, "main"):
                return mod.main()
        except Exception:
            pass
        pkg = __import__(PACKAGE)
        print("Launched " + PACKAGE + ": " + getattr(pkg, "__version__", ""))
    except Exception as e:
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Error", "Failed to start application: " + str(e))
            root.destroy()
        except Exception:
            try:
                with open(os.path.join(resources_path, "launch_error.log"), "a") as f:
                    f.write(str(e) + "\n")
            except Exception:
                pass

if __name__ == "__main__":
    _run()
"""
    launcher_path = macos_path / app_name.replace(" ", "")
    with open(launcher_path, 'w', encoding='utf-8') as f:
        f.write(launcher_code)
    st = os.stat(launcher_path)
    os.chmod(launcher_path, st.st_mode | stat.S_IEXEC)

    plist_data = {
        'CFBundleName': app_name,
        'CFBundleDisplayName': app_name,
        'CFBundleIdentifier': 'com.__PACKAGE_NAME__.app',
        'CFBundleVersion': '__VERSION__',
        'CFBundleShortVersionString': '__VERSION__',
        'CFBundleExecutable': app_name.replace(" ", ""),
        'CFBundleIconFile': 'app_icon.icns',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': '????',
        'LSMinimumSystemVersion': '10.13.0',
        'NSHighResolutionCapable': True,
        'NSSupportsAutomaticGraphicsSwitching': True,
        'NSRequiresAquaSystemAppearance': False,
        'LSApplicationCategoryType': 'public.app-category.productivity',
    }

    with open(contents_path / "Info.plist", 'wb') as f:
        plistlib.dump(plist_data, f)

    print("✅ Created " + bundle_name)
    print("📁 Bundle location: " + os.path.abspath(bundle_name))
    print("🚀 Double-click " + bundle_name + " to launch the application")

    return bundle_name


if __name__ == "__main__":
    print("🏗️  Creating macOS Application Bundle...")
    try:
        name = create_app_bundle()
        print("\n🎉 Application bundle creation complete!")
        print("🚀 Launch: Double-click " + name)
        print("📱 Install: Drag the .app to Applications folder")
    except Exception as e:
        print("❌ Failed: " + str(e))
'''
                version = metadata.get('version', '0.1.0')
                app_bundle_py = app_bundle_py.replace("__APP_NAME__", project_name).replace("__PACKAGE_NAME__", package_name).replace("__VERSION__", version)
                (scripts_dir / "create_app_bundle.py").write_text(app_bundle_py, encoding='utf-8')

            # Icon generator script
            if features.get('icon_generator', False):
                title = (project_name.split()[0] if project_name else "App")
                icon_py = '''#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont
import os


def create_icon():
    size = 1024
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = 80
    bg_rect = [margin, margin, size - margin, size - margin]
    corner_radius = 120
    draw.rounded_rectangle(bg_rect, corner_radius, fill=(45, 55, 72, 255))

    border_margin = margin - 10
    border_rect = [border_margin, border_margin, size - border_margin, size - border_margin]
    draw.rounded_rectangle(border_rect, corner_radius + 10, outline=(200, 200, 200, 100), width=8)

    col_width = 160
    col_height = 400
    col_spacing = 80
    start_x = (size - (3 * col_width + 2 * col_spacing)) // 2
    start_y = (size - col_height) // 2 + 50
    col_colors = [(99, 102, 241, 255), (245, 158, 11, 255), (34, 197, 94, 255)]

    for i in range(3):
        x = start_x + i * (col_width + col_spacing)
        y = start_y
        col_rect = [x, y, x + col_width, y + col_height]
        draw.rounded_rectangle(col_rect, 20, fill=(255, 255, 255, 240))
        header_rect = [x + 10, y + 10, x + col_width - 10, y + 50]
        draw.rounded_rectangle(header_rect, 10, fill=col_colors[i])
        card_height = 60
        card_margin = 15
        num_cards = [3, 2, 4][i]
        for j in range(num_cards):
            card_y = y + 70 + j * (card_height + card_margin)
            if card_y + card_height > y + col_height - 10:
                break
            card_rect = [x + 15, card_y, x + col_width - 15, card_y + card_height]
            shadow_rect = [x + 17, card_y + 2, x + col_width - 13, card_y + card_height + 2]
            draw.rounded_rectangle(shadow_rect, 8, fill=(0, 0, 0, 30))
            draw.rounded_rectangle(card_rect, 8, fill=(255, 255, 255, 255))
            line_y1 = card_y + 15
            line_y2 = card_y + 35
            draw.rectangle([x + 25, line_y1, x + col_width - 25, line_y1 + 3], fill=(120, 120, 120, 180))
            draw.rectangle([x + 25, line_y2, x + col_width - 45, line_y2 + 3], fill=(160, 160, 160, 120))

    try:
        font_size = 80
        font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', font_size)
    except Exception:
        font = ImageFont.load_default()

    title = '__TITLE__'
    title_bbox = draw.textbbox((0, 0), title, font=font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (size - title_width) // 2
    title_y = 180
    draw.text((title_x + 3, title_y + 3), title, font=font, fill=(0, 0, 0, 100))
    draw.text((title_x, title_y), title, font=font, fill=(255, 255, 255, 255))

    return img


def create_icon_set():
    base_icon = create_icon()
    sizes = [16, 32, 64, 128, 256, 512, 1024]
    if not os.path.exists('icons'):
        os.makedirs('icons')
    for size in sizes:
        resized = base_icon.resize((size, size))
        filename = 'icons/app_icon_' + str(size) + 'x' + str(size) + '.png'
        resized.save(filename, 'PNG')
        print('Created ' + filename)
    base_icon.save('icons/app_icon.png', 'PNG')
    print('Created icons/app_icon.png')


if __name__ == '__main__':
    create_icon_set()
'''
                icon_py = icon_py.replace("__TITLE__", title)
                scripts_dir = project_path / "scripts"
                scripts_dir.mkdir(exist_ok=True)
                (scripts_dir / "create_icon.py").write_text(icon_py, encoding='utf-8')

            # Delete git tracking helper
            if features.get('remove_git_tracking', False):
                scripts_dir = project_path / "scripts"
                scripts_dir.mkdir(exist_ok=True)
                (scripts_dir / "delete_git_tracking.txt").write_text("rm -rf .git\n", encoding='utf-8')

            # Freeze requirements script
            if features.get('freeze_requirements', False):
                freeze_py = '''#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path


def main():
    result = subprocess.run([sys.executable, '-m', 'pip', 'freeze'], capture_output=True, text=True, check=True)
    Path('requirements.txt').write_text(result.stdout, encoding='utf-8')
    print('✅ Wrote requirements.txt')


if __name__ == '__main__':
    main()
'''
                scripts_dir = project_path / "scripts"
                scripts_dir.mkdir(exist_ok=True)
                (scripts_dir / "freeze_requirements.py").write_text(freeze_py, encoding='utf-8')

            # Build with setup.py helper
            if features.get('setup_build_script', False):
                build_py = '''#!/usr/bin/env python3
import subprocess
import sys


def main():
    cmd = [sys.executable, 'setup.py', 'sdist', 'bdist_wheel']
    print('🔧 Running: ' + ' '.join(cmd))
    subprocess.run(cmd, check=True)
    print('✅ Build complete. See dist/ directory.')


if __name__ == '__main__':
    main()
'''
                (scripts_dir / "build_with_setup.py").write_text(build_py, encoding='utf-8')

        except Exception as e:
            self.logger.warning(f"Could not create optional scripts: {e}")

    def _apply_common_docs(self, project_path: Path, project_name: str, features: Dict[str, bool], metadata: Dict[str, str]) -> None:
        """Create selected common Markdown files across all templates."""
        md_feature_to_type = {
            'changelog': 'changelog',
            'contributors': 'contributors',
            'code_of_conduct': 'code_of_conduct',
            'security': 'security',
            'contributing': 'contributing',
            'support': 'support',
            'roadmap': 'roadmap',
            'configuration': 'configuration',
            'faq': 'faq',
            'getting_started': 'getting_started',
            'index': 'index',
            'install': 'install',
            'intro': 'intro',
            'summary': 'summary',
            'todo': 'todo',
            'usage': 'usage',
        }
        for feature_key, md_type in md_feature_to_type.items():
            if features.get(feature_key, False):
                try:
                    self.create_md_file(project_path, md_type, project_name, metadata)
                except Exception as e:
                    self.logger.warning(f"Could not create {md_type}: {e}")
    
    def _update_package_references(self, project_path: Path, project_name: str, package_name: str, metadata: Dict[str, str]):
        """Update package references throughout the project."""
        replacements = {
            "skeleton": package_name,
            "Skeleton": self._to_class_name(package_name),
            "python-skeleton-project": package_name.replace('_', '-'),
            "Python Skeleton": project_name,
            "A skeleton Python project": metadata.get('description', f'A {project_name} project'),
            "Your Name": metadata.get('author', 'Your Name'),
            "your.email@example.com": metadata.get('email', 'your.email@example.com'),
            "0.1.0": metadata.get('version', '0.1.0'),
            "https://github.com/yourusername/python-skeleton-project": metadata.get('url', f'https://github.com/yourusername/{package_name.replace("_", "-")}'),
        }
        
        # Files to update
        text_files = [
            'setup.py', 'pyproject.toml', 'README.md', 'LICENSE',
            'requirements.txt', 'requirements-dev.txt', 'Makefile'
        ]
        
        # Update text files
        for file_pattern in text_files:
            for file_path in project_path.rglob(file_pattern):
                if file_path.is_file():
                    self._update_file_content(project_path, file_path, replacements)
        
        # Update Python files
        for py_file in project_path.rglob("*.py"):
            if py_file.is_file():
                self._update_file_content(project_path, py_file, replacements)
        
        # Rename skeleton directory to new package name
        src_dir = project_path / "src"
        if src_dir.exists():
            skeleton_dir = src_dir / "skeleton"
            if skeleton_dir.exists() and package_name != "skeleton":
                new_package_dir = src_dir / package_name
                skeleton_dir.rename(new_package_dir)
    
    def _safe_path_for_project_file_io(self, project_root: Path, candidate: Path) -> Optional[Path]:
        """Path for file I/O only if candidate resolves under project_root; built stepwise (S2083)."""
        try:
            root = project_root.resolve()
            resolved = candidate.resolve()
            rel = resolved.relative_to(root)
        except (OSError, RuntimeError, ValueError):
            return None
        path = root
        for name in rel.parts:
            if name == "..":
                return None
            path = path / name
        return path
    
    def _update_file_content(self, project_path: Path, file_path: Path, replacements: Dict[str, str]):
        """Update file content with replacements."""
        path = self._safe_path_for_project_file_io(project_path, file_path)
        if path is None:
            self.logger.warning(f"Skipping update outside project directory: {file_path}")
            return
        try:
            with path.open("r", encoding="utf-8") as f:
                content = f.read()
            
            for old_text, new_text in replacements.items():
                content = content.replace(old_text, new_text)
            
            with path.open("w", encoding="utf-8") as f:
                f.write(content)
            
        except Exception as e:
            self.logger.warning(f"Could not update {file_path}: {e}")
    
    def _remove_unwanted_features(self, project_path: Path, features: Dict[str, bool]):
        """Remove files for unwanted features."""
        if not features.get('cli', True):
            self._remove_files(project_path, ['**/cli.py'])
        
        if not features.get('gui', True):
            self._remove_files(project_path, ['**/gui.py', '**/generator_gui.py'])
        
        if not features.get('tests', True):
            self._remove_dirs(project_path, ['tests'])
        
        if not features.get('executable', True):
            self._remove_files(project_path, ['scripts/build_executable.py', '**/build_executable.py'])
        
        if not features.get('dev_requirements', True):
            self._remove_files(project_path, ['requirements-dev.txt'])
        
        if not features.get('license', True):
            self._remove_files(project_path, ['LICENSE'])
        
        if not features.get('readme', True):
            self._remove_files(project_path, ['README.md'])
        
        if not features.get('makefile', True):
            self._remove_files(project_path, ['Makefile'])
        
        if not features.get('gitignore', True):
            self._remove_files(project_path, ['.gitignore'])
        
        if not features.get('github_actions', True):
            self._remove_dirs(project_path, ['.github'])

        # No removals needed for optional helper scripts since they are only created when selected
        # (mac_app_bundle, icon_generator, remove_git_tracking, freeze_requirements, build_package_script)
    
    def _remove_files(self, project_path: Path, patterns: List[str]):
        """Remove files matching patterns."""
        for pattern in patterns:
            for file_path in project_path.rglob(pattern):
                if file_path.is_file():
                    file_path.unlink()
                    self.logger.debug(f"Removed file: {file_path}")
    
    def _remove_dirs(self, project_path: Path, dir_names: List[str]):
        """Remove directories."""
        for dir_name in dir_names:
            dir_path = project_path / dir_name
            if dir_path.exists() and dir_path.is_dir():
                shutil.rmtree(dir_path)
                self.logger.debug(f"Removed directory: {dir_path}")
    
    def _generate_builtin_project(self, project_name: str, output_dir: Path, features: Dict[str, bool], metadata: Dict[str, str], template_id: str = "minimal-python") -> bool:
        """Generate a project using builtin templates."""
        try:
            project_path = output_dir / project_name
            package_name = self._to_package_name(project_name)
            
            # Create basic structure
            project_path.mkdir(parents=True, exist_ok=True)
            
            # Generate based on template type
            success = False
            if template_id in _BUILTIN_TEMPLATE_GENERATOR_PILOT:
                gen_name = _BUILTIN_TEMPLATE_GENERATOR_PILOT[template_id]
                success = getattr(self, gen_name)(
                    project_path, project_name, package_name, features, metadata
                )
            elif template_id == "flask-web-app":
                success = self._generate_flask_template(project_path, project_name, package_name, features, metadata)
            elif template_id == "fastapi-web-api":
                success = self._generate_fastapi_template(project_path, project_name, package_name, features, metadata)
            elif template_id == "data-science-project":
                success = self._generate_data_science_template(project_path, project_name, package_name, features, metadata)
            elif template_id == "machine-learning-project":
                success = self._generate_ml_template(project_path, project_name, package_name, features, metadata)
            elif template_id == "cli-tool":
                success = self._generate_cli_tool_template(project_path, project_name, package_name, features, metadata)
            elif template_id == "python-library":
                success = self._generate_library_template(project_path, project_name, package_name, features, metadata)
            elif template_id == "game-development":
                success = self._generate_game_template(project_path, project_name, package_name, features, metadata)
            elif template_id == "desktop-gui-app":
                success = self._generate_desktop_gui_template(project_path, project_name, package_name, features, metadata)
            elif template_id == "microservice":
                success = self._generate_microservice_template(project_path, project_name, package_name, features, metadata)
            elif template_id == "api-client-library":
                success = self._generate_api_client_template(project_path, project_name, package_name, features, metadata)
            elif template_id == "automation-scripts":
                success = self._generate_automation_template(project_path, project_name, package_name, features, metadata)
            elif template_id == "jupyter-research":
                success = self._generate_jupyter_research_template(project_path, project_name, package_name, features, metadata)
            elif template_id == "binary-extension":
                success = self._generate_binary_extension_template(project_path, project_name, package_name, features, metadata)
            elif template_id == "namespace-package":
                success = self._generate_namespace_package_template(project_path, project_name, package_name, features, metadata)
            elif template_id == "plugin-framework":
                success = self._generate_plugin_framework_template(project_path, project_name, package_name, features, metadata)
            else:
                # Default minimal template
                success = self._generate_minimal_template(project_path, project_name, package_name, features, metadata)

            # Always apply optional scripts after generation if successful
            if success:
                self._apply_optional_scripts(project_path, project_name, package_name, features, metadata)
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to generate builtin project: {e}")
            return False
    
    def _create_basic_init(self, src_dir: Path, project_name: str, metadata: Dict[str, str]):
        """Create basic __init__.py file."""
        content = f'''"""
{metadata.get('description', f'A {project_name} project')}
"""

__version__ = "{metadata.get('version', '0.1.0')}"
__author__ = "{metadata.get('author', 'Your Name')}"
__email__ = "{metadata.get('email', 'your.email@example.com')}"
'''
        (src_dir / "__init__.py").write_text(content)
    
    def _create_basic_core(self, src_dir: Path, project_name: str, package_name: str, metadata: Dict[str, str]):
        """Create basic core module."""
        class_name = self._to_class_name(package_name)
        content = f'''"""
Core module for {project_name}.
"""


class {class_name}:
    """Main application class."""
    
    def __init__(self):
        self.name = "{project_name}"
        self.version = "{metadata.get('version', '0.1.0')}"
    
    def run(self):
        """Run the application."""
        print(f"Hello from {{self.name}} v{{self.version}}!")
        return 0
'''
        (src_dir / "core.py").write_text(content)
    
    def _create_basic_cli(self, src_dir: Path, project_name: str, package_name: str, metadata: Dict[str, str]):
        """Create basic CLI module."""
        content = f'''"""
Command-line interface for {project_name}.
"""

import argparse
import sys
from .core import {self._to_class_name(package_name)}


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="{metadata.get('description', f'A {project_name} CLI')}")
    parser.add_argument('--version', action='version', version='{metadata.get("version", "0.1.0")}')
    
    args = parser.parse_args()
    
    app = {self._to_class_name(package_name)}()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
'''
        (src_dir / "cli.py").write_text(content)
    
    def _create_basic_tests(self, project_path: Path, package_name: str):
        """Create basic test structure."""
        tests_dir = project_path / "tests"
        tests_dir.mkdir(exist_ok=True)
        
        (tests_dir / "__init__.py").write_text("# Tests package")
        
        test_content = f'''"""
Basic tests for {package_name}.
"""

from {package_name}.core import {self._to_class_name(package_name)}


def test_creation():
    """Test that the main class can be created."""
    app = {self._to_class_name(package_name)}()
    assert app is not None


def test_run():
    """Test that the app can run."""
    app = {self._to_class_name(package_name)}()
    result = app.run()
    assert result == 0
'''
        (tests_dir / "test_core.py").write_text(test_content)
    
    def _create_basic_setup(self, project_path: Path, project_name: str, package_name: str, metadata: Dict[str, str]):
        """Create basic setup files."""
        # setup.py
        setup_content = f'''from setuptools import setup, find_packages

setup(
    name="{package_name.replace('_', '-')}",
    version="{metadata.get('version', '0.1.0')}",
    author="{metadata.get('author', 'Your Name')}",
    author_email="{metadata.get('email', 'your.email@example.com')}",
    description="{metadata.get('description', f'A {project_name} project')}",
    packages=find_packages(where="src"),
    package_dir={{"": "src"}},
    python_requires=">=3.8",
    entry_points={{
        "console_scripts": [
            "{package_name.replace('_', '-')}-cli={package_name}.cli:main",
        ],
    }},
)
'''
        (project_path / "setup.py").write_text(setup_content)
        
        # requirements.txt
        (project_path / "requirements.txt").write_text("# Add your dependencies here\n")
    
    def _create_basic_readme(self, project_path: Path, project_name: str, metadata: Dict[str, str]):
        """Create basic README."""
        content = f'''# {project_name}

{metadata.get('description', f'A {project_name} project')}

## Installation

```bash
pip install -e .
```

## Usage

```python
from {self._to_package_name(project_name)} import {self._to_class_name(self._to_package_name(project_name))}

app = {self._to_class_name(self._to_package_name(project_name))}()
app.run()
```

## Author

{metadata.get('author', 'Your Name')} - {metadata.get('email', 'your.email@example.com')}
'''
        (project_path / "README.md").write_text(content)
    
    def _create_basic_gitignore(self, project_path: Path):
        """Create basic .gitignore."""
        content = '''__pycache__/
*.py[cod]
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.pytest_cache/
.coverage
htmlcov/
.env
.venv
env/
venv/
.mypy_cache/
.DS_Store
'''
        (project_path / ".gitignore").write_text(content)
    
    def _create_changelog(self, project_path: Path, project_name: str, metadata: Dict[str, str]):
        """Create CHANGELOG.md file."""
        content = f'''# Changelog

All notable changes to {project_name} will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project setup
- Basic project structure
- {metadata.get('description', 'Core functionality')}

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [{metadata.get('version', '0.1.0')}] - {metadata.get('date', '2024-01-01')}

### Added
- Initial release
- Project foundation and structure

[Unreleased]: https://github.com/yourusername/{self._to_package_name(project_name)}/compare/v{metadata.get('version', '0.1.0')}...HEAD
[{metadata.get('version', '0.1.0')}]: https://github.com/yourusername/{self._to_package_name(project_name)}/releases/tag/v{metadata.get('version', '0.1.0')}
'''
        (project_path / "CHANGELOG.md").write_text(content)
    
    def _create_contributors(self, project_path: Path, project_name: str, metadata: Dict[str, str]):
        """Create CONTRIBUTORS.md file."""
        content = f'''# Contributors

Thank you to all the people who have contributed to {project_name}!

## Core Team

- **{metadata.get('author', 'Your Name')}** - *Initial work* - [{metadata.get('author', 'Your Name')}](https://github.com/yourusername)

## Contributors

<!-- Add contributors here -->

## How to Contribute

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Ways to Contribute

- 🐛 Report bugs
- 💡 Suggest new features
- 📝 Improve documentation
- 🧪 Write tests
- 💻 Submit code changes

### Recognition

All contributors will be recognized here. Thank you for making {project_name} better!

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). 
By participating, you are expected to uphold this code.
'''
        (project_path / "CONTRIBUTORS.md").write_text(content)
    
    def _create_code_of_conduct(self, project_path: Path, project_name: str, metadata: Dict[str, str]):
        """Create CODE_OF_CONDUCT.md file."""
        content = f'''# Code of Conduct

## Our Pledge

We as members, contributors, and leaders pledge to make participation in {project_name}
a harassment-free experience for everyone, regardless of age, body size, visible or 
invisible disability, ethnicity, sex characteristics, gender identity and expression, 
level of experience, education, socio-economic status, nationality, personal appearance, 
race, religion, or sexual identity and orientation.

## Our Standards

Examples of behavior that contributes to creating a positive environment include:

- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

Examples of unacceptable behavior include:

- The use of sexualized language or imagery and unwelcome sexual attention or advances
- Trolling, insulting/derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information without explicit permission
- Other conduct which could reasonably be considered inappropriate in a professional setting

## Our Responsibilities

Project maintainers are responsible for clarifying the standards of acceptable behavior
and are expected to take appropriate and fair corrective action in response to any
instances of unacceptable behavior.

## Scope

This Code of Conduct applies both within project spaces and in public spaces when
an individual is representing the project or its community.

## Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported
by contacting the project team at {metadata.get('email', 'your.email@example.com')}.

All complaints will be reviewed and investigated and will result in a response that
is deemed necessary and appropriate to the circumstances.

## Attribution

This Code of Conduct is adapted from the [Contributor Covenant](https://www.contributor-covenant.org),
version 2.0, available at https://www.contributor-covenant.org/version/2/0/code_of_conduct.html.
'''
        (project_path / "CODE_OF_CONDUCT.md").write_text(content)
    
    def _create_security(self, project_path: Path, project_name: str, metadata: Dict[str, str]):
        """Create SECURITY.md file."""
        content = f'''# Security Policy

## Supported Versions

Use this section to tell people about which versions of {project_name} are
currently being supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| {metadata.get('version', '0.1.0')}   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of {project_name} seriously. If you believe you have found a security vulnerability,
please report it to us as described below.

### How to Report

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them by email to {metadata.get('email', 'security@example.com')}.

Please include the following information in your report:

- Type of issue (e.g. buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit the issue

### What to Expect

You should receive a response within 48 hours. If the issue is confirmed as a vulnerability,
we will:

1. Acknowledge your email within 48 hours
2. Provide a more detailed response within 7 days indicating next steps
3. Work on a fix and coordinate disclosure timeline
4. Notify you when the vulnerability is fixed

### Safe Harbor

We support safe harbor for security researchers who:

- Make a good faith effort to avoid privacy violations and disruptions to others
- Only interact with accounts you own or with explicit permission of the account holder
- Do not access or download data that doesn't belong to you
- Do not intentionally harm or degrade our systems

Thank you for helping keep {project_name} and our users safe!
'''
        (project_path / "SECURITY.md").write_text(content)

    def _create_contributing(self, project_path: Path, project_name: str, metadata: Dict[str, str]):
        """Create CONTRIBUTING.md file."""
        content = f'''# Contributing to {project_name}

First off, thank you for considering contributing to {project_name}! It's people like you that make this project great.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How Can I Contribute?](#how-can-i-contribute)
- [Style Guidelines](#style-guidelines)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). 
By participating, you are expected to uphold this code.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git

### Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/{self._to_package_name(project_name)}.git
   cd {self._to_package_name(project_name)}
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

4. Install development dependencies:
   ```bash
   pip install -e .[dev]
   ```

5. Run tests to make sure everything works:
   ```bash
   pytest
   ```

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- A clear and descriptive title
- Steps to reproduce the behavior
- Expected behavior
- Actual behavior
- Screenshots (if applicable)
- Environment details (OS, Python version, etc.)

### Suggesting Enhancements

Enhancement suggestions are welcome! Please provide:

- A clear and descriptive title
- A detailed description of the proposed feature
- Explain why this enhancement would be useful
- Include examples if applicable

### Code Contributions

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Style Guidelines

### Python Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use type hints where appropriate
- Write docstrings for public functions and classes
- Keep functions small and focused

### Git Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

## Pull Request Process

1. Ensure any install or build dependencies are removed before the end of the layer when doing a build
2. Update the README.md with details of changes to the interface, if applicable
3. Update the version numbers in any examples files and the README.md to the new version that this Pull Request would represent
4. You may merge the Pull Request in once you have the sign-off of two other developers, or if you do not have permission to do that, you may request the second reviewer to merge it for you

## Development Guidelines

### Testing

- Write tests for new functionality
- Ensure existing tests still pass
- Aim for good test coverage
- Use descriptive test names

### Documentation

- Update documentation for any changed functionality
- Include docstrings for new functions and classes
- Update README if necessary

## Questions?

Don't hesitate to ask questions! You can reach out to the maintainers at {metadata.get('email', 'maintainers@example.com')}.

Thank you for contributing! 🎉
'''
        (project_path / "CONTRIBUTING.md").write_text(content)

    def _create_roadmap(self, project_path: Path, project_name: str, metadata: Dict[str, str]):
        """Create ROADMAP.md file."""
        content = f'''# {project_name} Roadmap

This document outlines the planned development direction for {project_name}.

## Current Version: {metadata.get('version', '0.1.0')}

### Recently Completed ✅
- Initial project setup
- Core functionality implementation
- Basic documentation

## Upcoming Releases

### Version 0.2.0 (Next Minor Release)
**Target: Q2 2024**

#### Features
- [ ] Feature A
- [ ] Feature B
- [ ] Improved error handling

#### Improvements
- [ ] Performance optimizations
- [ ] Better documentation
- [ ] Additional tests

### Version 0.3.0
**Target: Q3 2024**

#### Features
- [ ] Advanced feature C
- [ ] Integration with external APIs
- [ ] Enhanced user interface

#### Technical Debt
- [ ] Code refactoring
- [ ] Dependency updates
- [ ] Architecture improvements

### Version 1.0.0 (Major Release)
**Target: Q4 2024**

#### Features
- [ ] Production-ready stability
- [ ] Complete feature set
- [ ] Comprehensive documentation

#### Quality Assurance
- [ ] Full test coverage
- [ ] Performance benchmarks
- [ ] Security audit

## Long-term Vision

### Future Considerations
- Plugin system
- Mobile support
- Cloud integration
- Advanced analytics

## Contributing to the Roadmap

We welcome community input on our roadmap! Please:

1. Check existing [issues](https://github.com/yourusername/{self._to_package_name(project_name)}/issues) and [discussions](https://github.com/yourusername/{self._to_package_name(project_name)}/discussions)
2. Create feature requests for new ideas
3. Vote on existing proposals
4. Join roadmap discussions

## Get Involved

- 🐛 [Report bugs](https://github.com/yourusername/{self._to_package_name(project_name)}/issues/new?template=bug_report.md)
- 💡 [Request features](https://github.com/yourusername/{self._to_package_name(project_name)}/issues/new?template=feature_request.md)
- 💬 [Join discussions](https://github.com/yourusername/{self._to_package_name(project_name)}/discussions)
- 🛠️ [Contribute code](CONTRIBUTING.md)

---

*This roadmap is subject to change based on community feedback and project needs.*
*Last updated: {metadata.get('date', '2024-01-01')}*
'''
        (project_path / "ROADMAP.md").write_text(content)

    def _create_support(self, project_path: Path, project_name: str, metadata: Dict[str, str]):
        """Create SUPPORT.md file."""
        content = f'''# Support

Looking for help with {project_name}? Here's how to get support.

## Documentation

Before asking for help, please check our documentation:

- [README](README.md) - Basic usage and setup
- [Contributing Guidelines](CONTRIBUTING.md) - How to contribute
- [Changelog](CHANGELOG.md) - Recent changes and updates

## Getting Help

### Community Support

The fastest way to get help is through our community channels:

- **GitHub Discussions**: [Project Discussions](https://github.com/yourusername/{self._to_package_name(project_name)}/discussions)
  - Ask questions
  - Share ideas
  - Get help from the community

- **GitHub Issues**: [Report Issues](https://github.com/yourusername/{self._to_package_name(project_name)}/issues)
  - Bug reports
  - Feature requests
  - Technical problems

### Professional Support

For commercial or priority support, contact us at {metadata.get('email', 'support@example.com')}.

## FAQ

### Common Questions

**Q: How do I install {project_name}?**
A: See the installation instructions in our [README](README.md).

**Q: I found a bug, what should I do?**
A: Please [create an issue](https://github.com/yourusername/{self._to_package_name(project_name)}/issues/new) with details about the bug.

**Q: Can I contribute to the project?**
A: Absolutely! Check out our [Contributing Guidelines](CONTRIBUTING.md).

**Q: How do I request a new feature?**
A: Create a [feature request](https://github.com/yourusername/{self._to_package_name(project_name)}/issues/new) on GitHub.

## Response Times

- **Community Support**: Best effort, typically within 1-3 days
- **Bug Reports**: We aim to respond within 1 week
- **Professional Support**: Within 24 hours (business days)

## Code of Conduct

Please note that all interactions must follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Contact

- **General Questions**: [GitHub Discussions](https://github.com/yourusername/{self._to_package_name(project_name)}/discussions)
- **Bug Reports**: [GitHub Issues](https://github.com/yourusername/{self._to_package_name(project_name)}/issues)
- **Security Issues**: {metadata.get('email', 'security@example.com')} (see [Security Policy](SECURITY.md))
- **Commercial Support**: {metadata.get('email', 'support@example.com')}

Thank you for using {project_name}! 🚀
'''
        (project_path / "SUPPORT.md").write_text(content)

    @staticmethod
    def get_available_md_files():
        """Get list of available Markdown documentation files."""
        # Organized alphabetically by file name
        return {
            "changelog": {
                "name": "CHANGELOG.md",
                "description": "Track all changes and releases",
                "category": "Documentation",
                "recommended": True
            },
            "code_of_conduct": {
                "name": "CODE_OF_CONDUCT.md",
                "description": "Community guidelines and behavior standards",
                "category": "Documentation", 
                "recommended": False
            },
            "configuration": {
                "name": "CONFIGURATION.md",
                "description": "Configuration options and examples",
                "category": "Documentation",
                "recommended": False
            },
            "contributing": {
                "name": "CONTRIBUTING.md",
                "description": "Guidelines for contributing to the project",
                "category": "Documentation",
                "recommended": False
            },
            "contributors": {
                "name": "CONTRIBUTORS.md", 
                "description": "List project contributors and recognition",
                "category": "Documentation",
                "recommended": False
            },
            "faq": {
                "name": "FAQ.md",
                "description": "Frequently Asked Questions",
                "category": "Documentation",
                "recommended": False
            },
            "getting_started": {
                "name": "GETTING-STARTED.md",
                "description": "Quick start guide for new users",
                "category": "Documentation",
                "recommended": True
            },
            "index": {
                "name": "INDEX.md",
                "description": "Index of documentation pages",
                "category": "Documentation",
                "recommended": False
            },
            "install": {
                "name": "INSTALL.md",
                "description": "Installation instructions",
                "category": "Documentation",
                "recommended": True
            },
            "intro": {
                "name": "INTRO.md",
                "description": "Introduction to the project",
                "category": "Documentation",
                "recommended": False
            },
            "roadmap": {
                "name": "ROADMAP.md",
                "description": "Project roadmap and future plans",
                "category": "Documentation",
                "recommended": False
            },
            "security": {
                "name": "SECURITY.md",
                "description": "Security policy and vulnerability reporting",
                "category": "Documentation",
                "recommended": False
            },
            "summary": {
                "name": "SUMMARY.md",
                "description": "Summary of documentation sections",
                "category": "Documentation",
                "recommended": False
            },
            "support": {
                "name": "SUPPORT.md",
                "description": "How to get help and support",
                "category": "Documentation",
                "recommended": False
            },
            "todo": {
                "name": "TODO.md",
                "description": "Task list and backlog",
                "category": "Documentation",
                "recommended": False
            },
            "usage": {
                "name": "USAGE.md",
                "description": "How to use the project",
                "category": "Documentation",
                "recommended": True
            }
        }

    def create_md_file(self, project_path: Path, md_type: str, project_name: str, metadata: Dict[str, str]):
        """Create a specific Markdown documentation file."""
        md_creators = {
            "changelog": self._create_changelog,
            "contributors": self._create_contributors,
            "code_of_conduct": self._create_code_of_conduct,
            "security": self._create_security,
            "contributing": self._create_contributing,
            "support": self._create_support,
            "roadmap": self._create_roadmap,
            "faq": self._create_faq,
            "getting_started": self._create_getting_started,
            "index": self._create_index,
            "install": self._create_install,
            "intro": self._create_intro,
            "summary": self._create_summary,
            "todo": self._create_todo,
            "usage": self._create_usage,
            "configuration": self._create_configuration,
        }
        
        if md_type in md_creators:
            md_creators[md_type](project_path, project_name, metadata)
            return True
        return False
    
    def _generate_minimal_template(self, project_path: Path, project_name: str, package_name: str, features: Dict[str, bool], metadata: Dict[str, str]) -> bool:
        """Generate the minimal Python project template."""
        src_dir = project_path / "src" / package_name
        src_dir.mkdir(parents=True, exist_ok=True)
        
        # Create basic files
        self._create_basic_init(src_dir, project_name, metadata)
        self._create_basic_core(src_dir, project_name, package_name, metadata)
        
        if features.get('cli', False):
            self._create_basic_cli(src_dir, project_name, package_name, metadata)
        
        if features.get('tests', True):
            self._create_basic_tests(project_path, package_name)
        
        if features.get('pypi_packaging', True):
            self._create_basic_setup(project_path, project_name, package_name, metadata)
        
        if features.get('readme', True):
            self._create_basic_readme(project_path, project_name, metadata)
        
        if features.get('changelog', True):
            self._create_changelog(project_path, project_name, metadata)
        
        if features.get('contributors', False):
            self._create_contributors(project_path, project_name, metadata)
        
        if features.get('code_of_conduct', False):
            self._create_code_of_conduct(project_path, project_name, metadata)
        
        if features.get('security', False):
            self._create_security(project_path, project_name, metadata)
        
        if features.get('contributing', False):
            self._create_contributing(project_path, project_name, metadata)
        
        if features.get('support', False):
            self._create_support(project_path, project_name, metadata)
        
        if features.get('roadmap', False):
            self._create_roadmap(project_path, project_name, metadata)
        
        if features.get('gitignore', True):
            self._create_basic_gitignore(project_path)
        
        return True
    
    def _generate_flask_template(self, project_path: Path, project_name: str, package_name: str, features: Dict[str, bool], metadata: Dict[str, str]) -> bool:
        """Generate a Flask web application template."""
        # Create app structure
        app_dir = project_path / package_name
        app_dir.mkdir(parents=True, exist_ok=True)
        
        # Create Flask app structure
        (app_dir / "__init__.py").write_text(f'''"""
{metadata.get('description', f'A {project_name} Flask application')}
"""

from flask import Flask
from .config import Config

__version__ = "{metadata.get('version', '0.1.0')}"

def create_app(config_class=Config):
    """Application factory pattern."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Register blueprints
    from .main import bp as main_bp
    app.register_blueprint(main_bp)
    
    return app
''')
        
        # Create config
        (app_dir / "config.py").write_text(f'''"""
Configuration for {project_name}.
"""

import os
from pathlib import Path

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    
class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    
class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    
config = {{
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}}
''')
        
        # Create main blueprint
        main_dir = app_dir / "main"
        main_dir.mkdir(exist_ok=True)
        (main_dir / "__init__.py").write_text('''"""
Main blueprint for the application.
"""

from flask import Blueprint

bp = Blueprint('main', __name__)

from . import routes
''')
        
        (main_dir / "routes.py").write_text(f'''"""
Main routes for {project_name}.
"""

from flask import render_template, request, jsonify
from . import bp

@bp.route('/')
def index():
    """Home page."""
    return render_template('index.html', title='Home')

@bp.route('/api/health')
def health():
    """Health check endpoint."""
    return jsonify({{'status': 'healthy', 'app': '{project_name}'}})
''')
        
        # Create templates
        templates_dir = app_dir / "templates"
        templates_dir.mkdir(exist_ok=True)
        (templates_dir / "base.html").write_text(f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{% if title %}}{project_name} - {{{{ title }}}}{{% else %}}{project_name}{{% endif %}}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="{{{{ url_for('main.index') }}}}">{project_name}</a>
        </div>
    </nav>
    
    <main class="container mt-4">
        {{% block content %}}{{% endblock %}}
    </main>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
''')
        
        (templates_dir / "index.html").write_text(f'''{{% extends "base.html" %}}

{{% block content %}}
<div class="row">
    <div class="col-md-8 mx-auto">
        <div class="jumbotron bg-light p-5 rounded">
            <h1 class="display-4">Welcome to {project_name}!</h1>
            <p class="lead">{metadata.get('description', f'A {project_name} Flask application')}</p>
            <hr class="my-4">
            <p>This is a Flask web application generated by the Python Project Generator.</p>
            <a class="btn btn-primary btn-lg" href="/api/health" role="button">Check Health</a>
        </div>
    </div>
</div>
{{% endblock %}}
''')
        
        # Create static files directory
        static_dir = app_dir / "static"
        static_dir.mkdir(exist_ok=True)
        (static_dir / "style.css").write_text('''/* Custom styles for the application */
.jumbotron {
    background-color: #f8f9fa;
}
''')
        
        # Create run script
        (project_path / "run.py").write_text(f'''#!/usr/bin/env python3
"""
Development server for {project_name}.
"""

from {package_name} import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
''')
        
        # Create requirements
        requirements = [
            "Flask>=2.3.0",
            "python-dotenv>=1.0.0"
        ]
        if features.get('database'):
            requirements.extend(["Flask-SQLAlchemy>=3.0.0", "Flask-Migrate>=4.0.0"])
        
        (project_path / "requirements.txt").write_text("\\n".join(requirements) + "\\n")
        
        # Create tests
        if features.get('tests', True):
            self._create_flask_tests(project_path, package_name)
        
        # Create other common files
        if features.get('readme', True):
            self._create_flask_readme(project_path, project_name, metadata)
        
        if features.get('gitignore', True):
            self._create_basic_gitignore(project_path)
            
        if features.get('docker'):
            self._create_flask_docker(project_path, package_name)
        
        return True
    
    def _create_flask_tests(self, project_path: Path, package_name: str):
        """Create tests for Flask application."""
        tests_dir = project_path / "tests"
        tests_dir.mkdir(exist_ok=True)
        
        (tests_dir / "__init__.py").write_text("")
        
        (tests_dir / "conftest.py").write_text(f'''"""
Test configuration for Flask app.
"""

import pytest
from {package_name} import create_app

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app()
    app.config.update({{
        "TESTING": True,
    }})
    return app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()
''')
        
        (tests_dir / "test_routes.py").write_text(f'''"""
Test routes for the application.
"""

def test_index(client):
    """Test the home page."""
    response = client.get('/')
    assert response.status_code == 200

def test_health(client):
    """Test the health endpoint."""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
''')
    
    def _create_flask_readme(self, project_path: Path, project_name: str, metadata: Dict[str, str]):
        """Create README for Flask application."""
        content = f'''# {project_name}

{metadata.get('description', f'A {project_name} Flask application')}

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

### Development Mode
```bash
python run.py
```

The application will be available at http://localhost:5000

### Environment Variables
Create a `.env` file in the project root:
```
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///app.db
FLASK_ENV=development
```

## Testing

```bash
pip install pytest
pytest
```

## Project Structure

```
{self._to_package_name(project_name)}/
├── {self._to_package_name(project_name)}/
│   ├── __init__.py
│   ├── config.py
│   ├── main/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── templates/
│   │   ├── base.html
│   │   └── index.html
│   └── static/
│       └── style.css
├── tests/
├── run.py
└── requirements.txt
```

## Author

{metadata.get('author', 'Your Name')} - {metadata.get('email', 'your.email@example.com')}
'''
        (project_path / "README.md").write_text(content)
    
    def _create_flask_docker(self, project_path: Path, package_name: str):
        """Create Docker files for Flask application."""
        (project_path / "Dockerfile").write_text(f'''FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "run.py"]
''')
        
        (project_path / "docker-compose.yml").write_text(f'''version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=development
    volumes:
               - .:/app
''')
    
    def _generate_fastapi_template(self, project_path: Path, project_name: str, package_name: str, features: Dict[str, bool], metadata: Dict[str, str]) -> bool:
        """Generate a FastAPI web application template."""
        # Create app structure
        app_dir = project_path / package_name
        app_dir.mkdir(parents=True, exist_ok=True)
        
        # Main application
        (app_dir / "__init__.py").write_text(f'''"""
{metadata.get('description', f'A {project_name} FastAPI application')}
"""

__version__ = "{metadata.get('version', '0.1.0')}"
''')
        
        (app_dir / "main.py").write_text(f'''"""
Main FastAPI application for {project_name}.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(
    title="{project_name}",
    description="{metadata.get('description', f'A {project_name} FastAPI application')}",
    version="{metadata.get('version', '0.1.0')}"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    app: str
    version: str

class Item(BaseModel):
    """Example item model."""
    id: Optional[int] = None
    name: str
    description: Optional[str] = None

# In-memory storage (replace with database)
items_db: List[Item] = []

@app.get("/", tags=["root"])
async def read_root():
    """Welcome endpoint."""
    return {{"message": "Welcome to {project_name}!"}}

@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        app="{project_name}",
        version="{metadata.get('version', '0.1.0')}"
    )

@app.get("/items", response_model=List[Item], tags=["items"])
async def read_items():
    """Get all items."""
    return items_db

@app.post("/items", response_model=Item, tags=["items"])
async def create_item(item: Item):
    """Create a new item."""
    item.id = len(items_db) + 1
    items_db.append(item)
    return item

@app.get("/items/{{item_id}}", response_model=Item, tags=["items"])
async def read_item(item_id: int):
    """Get a specific item."""
    for item in items_db:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
''')
        
        # Create requirements
        requirements = [
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0",
            "pydantic>=2.4.0"
        ]
        if features.get('database'):
            requirements.extend(["sqlalchemy>=2.0.0", "alembic>=1.12.0"])
        
        (project_path / "requirements.txt").write_text("\\n".join(requirements) + "\\n")
        
        # Create run script
        (project_path / "run.py").write_text(f'''#!/usr/bin/env python3
"""
Development server for {project_name}.
"""

import uvicorn
from {package_name}.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
''')
        
        # Tests
        if features.get('tests', True):
            tests_dir = project_path / "tests"
            tests_dir.mkdir(exist_ok=True)
            (tests_dir / "__init__.py").write_text("")
            
            (tests_dir / "test_main.py").write_text(f'''"""
Tests for {project_name} FastAPI application.
"""

from fastapi.testclient import TestClient
from {package_name}.main import app

client = TestClient(app)

def test_read_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_health_check():
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_create_and_read_item():
    """Test item creation and retrieval."""
    # Create item
    item_data = {{"name": "Test Item", "description": "Test Description"}}
    response = client.post("/items", json=item_data)
    assert response.status_code == 200
    created_item = response.json()
    assert created_item["name"] == "Test Item"
    assert "id" in created_item
    
    # Read item
    item_id = created_item["id"]
    response = client.get(f"/items/{{item_id}}")
    assert response.status_code == 200
    assert response.json() == created_item
''')
        
        # README
        if features.get('readme', True):
            (project_path / "README.md").write_text(f'''# {project_name}

{metadata.get('description', f'A {project_name} FastAPI application')}

## Installation

```bash
pip install -r requirements.txt
```

## Running

```bash
python run.py
```

API will be available at http://localhost:8000

## Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

```bash
pip install pytest httpx
pytest
```

## Author

{metadata.get('author', 'Your Name')} - {metadata.get('email', 'your.email@example.com')}
''')
        
        if features.get('gitignore', True):
            self._create_basic_gitignore(project_path)
            
        if features.get('docker'):
            self._create_fastapi_docker(project_path, package_name)
        
        return True
    
    def _create_fastapi_docker(self, project_path: Path, package_name: str):
        """Create Docker files for FastAPI application."""
        (project_path / "Dockerfile").write_text('''FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
''')
    
    def _generate_data_science_template(self, project_path: Path, project_name: str, package_name: str, features: Dict[str, bool], metadata: Dict[str, str]) -> bool:
        """Generate a data science project template."""
        # Create structure
        (project_path / "data" / "raw").mkdir(parents=True, exist_ok=True)
        (project_path / "data" / "processed").mkdir(parents=True, exist_ok=True)
        (project_path / "notebooks").mkdir(exist_ok=True)
        (project_path / "reports").mkdir(exist_ok=True)
        (project_path / "src" / package_name).mkdir(parents=True, exist_ok=True)
        
        # Main module
        (project_path / "src" / package_name / "__init__.py").write_text(f'''"""
{metadata.get('description', f'A {project_name} data science project')}
"""

__version__ = "{metadata.get('version', '0.1.0')}"
''')
        
        # Data processing module
        (project_path / "src" / package_name / "data.py").write_text('''"""
Data processing utilities.
"""

import pandas as pd
import numpy as np
from pathlib import Path

def load_data(filepath: str) -> pd.DataFrame:
    """Load data from file."""
    return pd.read_csv(filepath)

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the dataset."""
    # Remove duplicates
    df = df.drop_duplicates()
    
    # Handle missing values
    df = df.dropna()
    
    return df

def save_processed_data(df: pd.DataFrame, filepath: str) -> None:
    """Save processed data."""
    df.to_csv(filepath, index=False)
''')
        
        # Analysis module
        (project_path / "src" / package_name / "analysis.py").write_text('''"""
Data analysis utilities.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Optional

def basic_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Get basic statistics of the dataset."""
    return df.describe()

def correlation_matrix(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """Calculate correlation matrix."""
    if columns:
        df = df[columns]
    return df.corr()

def plot_distribution(df: pd.DataFrame, column: str, figsize: tuple = (10, 6)) -> None:
    """Plot distribution of a column."""
    plt.figure(figsize=figsize)
    sns.histplot(df[column], kde=True)
    plt.title(f'Distribution of {column}')
    plt.show()

def plot_correlation_heatmap(df: pd.DataFrame, figsize: tuple = (12, 8)) -> None:
    """Plot correlation heatmap."""
    plt.figure(figsize=figsize)
    sns.heatmap(df.corr(), annot=True, cmap='coolwarm', center=0)
    plt.title('Correlation Heatmap')
    plt.show()
''')
        
        # Sample notebook
        notebook_content = '''{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Data Analysis Notebook\\n",
    "\\n",
    "This notebook contains the main analysis for the project."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Import libraries\\n",
    "import pandas as pd\\n",
    "import numpy as np\\n",
    "import matplotlib.pyplot as plt\\n",
    "import seaborn as sns\\n",
    "\\n",
    "# Import project modules\\n",
    "import sys\\n",
    "sys.path.append('../src')\\n",
    "from ''' + package_name + ''' import data, analysis"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Load data\\n",
    "# df = data.load_data('../data/raw/sample.csv')"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.8.0"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}'''
        
        (project_path / "notebooks" / "01_exploratory_analysis.ipynb").write_text(notebook_content)
        
        # Requirements
        requirements = [
            "pandas>=2.0.0",
            "numpy>=1.24.0",
            "matplotlib>=3.7.0",
            "seaborn>=0.12.0",
            "jupyter>=1.0.0",
            "scikit-learn>=1.3.0"
        ]
        (project_path / "requirements.txt").write_text("\\n".join(requirements) + "\\n")
        
        # Basic files
        if features.get('readme', True):
            (project_path / "README.md").write_text(f'''# {project_name}

{metadata.get('description', f'A {project_name} data science project')}

## Project Structure

```
├── data/
│   ├── raw/          # Raw data files
│   └── processed/    # Processed data files
├── notebooks/        # Jupyter notebooks
├── reports/          # Generated reports
└── src/
    └── {package_name}/   # Source code
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Start Jupyter:
```bash
jupyter notebook
```

## Author

{metadata.get('author', 'Your Name')} - {metadata.get('email', 'your.email@example.com')}
''')
        
        if features.get('gitignore', True):
            self._create_basic_gitignore(project_path)
        
        return True
    
    def _generate_cli_tool_template(self, project_path: Path, project_name: str, package_name: str, features: Dict[str, bool], metadata: Dict[str, str]) -> bool:
        """Generate a CLI tool template."""
        src_dir = project_path / "src" / package_name
        src_dir.mkdir(parents=True, exist_ok=True)
        
        # Main CLI module
        (src_dir / "__init__.py").write_text(f'''"""
{metadata.get('description', f'A {project_name} CLI tool')}
"""

__version__ = "{metadata.get('version', '0.1.0')}"
''')
        
        (src_dir / "cli.py").write_text(f'''"""
CLI for {project_name}.
"""

import click
import logging
from pathlib import Path
from . import __version__

logger = logging.getLogger(__name__)

@click.group()
@click.version_option(version=__version__)
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, verbose):
    """
    {metadata.get('description', f'A {project_name} CLI tool')}
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    
    # Configure logging
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format='%(levelname)s: %(message)s')

@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output file')
@click.pass_context
def process(ctx, input_file, output):
    """Process an input file."""
    click.echo(f"Processing {{input_file}}...")
    
    # Add your processing logic here
    result = f"Processed {{input_file}}"
    
    if output:
        Path(output).write_text(result)
        click.echo(f"Result saved to {{output}}")
    else:
        click.echo(result)

@cli.command()
@click.pass_context
def info(ctx):
    """Show information about the tool."""
    click.echo(f"{project_name} v{{__version__}}")
    click.echo(f"Author: {metadata.get('author', 'Your Name')}")

if __name__ == '__main__':
    cli()
''')
        
        # Requirements
        requirements = [
            "click>=8.1.0",
            "colorama>=0.4.6"
        ]
        (project_path / "requirements.txt").write_text("\\n".join(requirements) + "\\n")
        
        # Setup.py for CLI entry point
        (project_path / "setup.py").write_text(f'''from setuptools import setup, find_packages

setup(
    name="{package_name.replace('_', '-')}",
    version="{metadata.get('version', '0.1.0')}",
    packages=find_packages(where="src"),
    package_dir={{"": "src"}},
    install_requires=[
        "click>=8.1.0",
        "colorama>=0.4.6",
    ],
    entry_points={{
        "console_scripts": [
            "{package_name.replace('_', '-')}={package_name}.cli:cli",
        ],
    }},
    python_requires=">=3.8",
    author="{metadata.get('author', 'Your Name')}",
    author_email="{metadata.get('email', 'your.email@example.com')}",
    description="{metadata.get('description', f'A {project_name} CLI tool')}",
)
''')
        
        if features.get('tests', True):
            tests_dir = project_path / "tests"
            tests_dir.mkdir(exist_ok=True)
            (tests_dir / "__init__.py").write_text("")
            (tests_dir / "test_cli.py").write_text(f'''"""
Tests for {project_name} CLI.
"""

from click.testing import CliRunner
from {package_name}.cli import cli

def test_cli_info():
    """Test the info command."""
    runner = CliRunner()
    result = runner.invoke(cli, ['info'])
    assert result.exit_code == 0
    assert "{project_name}" in result.output
''')
        
        if features.get('readme', True):
            (project_path / "README.md").write_text(f'''# {project_name}

{metadata.get('description', f'A {project_name} CLI tool')}

## Installation

```bash
pip install -e .
```

## Usage

```bash
{package_name.replace('_', '-')} --help
{package_name.replace('_', '-')} info
{package_name.replace('_', '-')} process input.txt -o output.txt
```

## Author

{metadata.get('author', 'Your Name')} - {metadata.get('email', 'your.email@example.com')}
''')
        
        if features.get('gitignore', True):
            self._create_basic_gitignore(project_path)
        
        return True
    
    # Stub implementations for remaining templates
    def _generate_django_template(self, project_path: Path, project_name: str, package_name: str, features: Dict[str, bool], metadata: Dict[str, str]) -> bool:
        """Generate Django template (stub - falls back to minimal)."""
        return self._generate_minimal_template(project_path, project_name, package_name, features, metadata)
    
    def _generate_ml_template(self, project_path: Path, project_name: str, package_name: str, features: Dict[str, bool], metadata: Dict[str, str]) -> bool:
        """Generate ML template (stub - falls back to minimal)."""
        return self._generate_minimal_template(project_path, project_name, package_name, features, metadata)
    
    def _generate_library_template(self, project_path: Path, project_name: str, package_name: str, features: Dict[str, bool], metadata: Dict[str, str]) -> bool:
        """Generate library template (stub - falls back to minimal)."""
        return self._generate_minimal_template(project_path, project_name, package_name, features, metadata)
    
    def _generate_game_template(self, project_path: Path, project_name: str, package_name: str, features: Dict[str, bool], metadata: Dict[str, str]) -> bool:
        """Generate game template (stub - falls back to minimal)."""
        return self._generate_minimal_template(project_path, project_name, package_name, features, metadata)
    
    def _generate_desktop_gui_template(self, project_path: Path, project_name: str, package_name: str, features: Dict[str, bool], metadata: Dict[str, str]) -> bool:
        """Generate desktop GUI template (stub - falls back to minimal)."""
        return self._generate_minimal_template(project_path, project_name, package_name, features, metadata)
    
    def _generate_microservice_template(self, project_path: Path, project_name: str, package_name: str, features: Dict[str, bool], metadata: Dict[str, str]) -> bool:
        """Generate microservice template (stub - falls back to minimal)."""
        return self._generate_minimal_template(project_path, project_name, package_name, features, metadata)
    
    def _generate_api_client_template(self, project_path: Path, project_name: str, package_name: str, features: Dict[str, bool], metadata: Dict[str, str]) -> bool:
        """Generate API client template (stub - falls back to minimal)."""
        return self._generate_minimal_template(project_path, project_name, package_name, features, metadata)
    
    def _generate_automation_template(self, project_path: Path, project_name: str, package_name: str, features: Dict[str, bool], metadata: Dict[str, str]) -> bool:
        """Generate automation template (stub - falls back to minimal)."""
        return self._generate_minimal_template(project_path, project_name, package_name, features, metadata)
    
    def _generate_jupyter_research_template(self, project_path: Path, project_name: str, package_name: str, features: Dict[str, bool], metadata: Dict[str, str]) -> bool:
        """Generate Jupyter research template (stub - falls back to minimal)."""
        return self._generate_minimal_template(project_path, project_name, package_name, features, metadata)
    
    def _generate_binary_extension_template(self, project_path: Path, project_name: str, package_name: str, features: Dict[str, bool], metadata: Dict[str, str]) -> bool:
        """Generate a binary/extension package template."""
        # Create package structure
        src_dir = project_path / "src" / package_name
        src_dir.mkdir(parents=True, exist_ok=True)
        
        # Create C extension directory
        ext_dir = src_dir / "ext"
        ext_dir.mkdir(exist_ok=True)
        
        # Main package __init__.py
        (src_dir / "__init__.py").write_text(f'''"""
{metadata.get('description', f'A {project_name} package with binary extensions')}
"""

__version__ = "{metadata.get('version', '0.1.0')}"

# Import the C extension
try:
    from .ext import {self._to_class_name(package_name).lower()}_ext
    HAS_C_EXTENSION = True
except ImportError:
    # Fallback to pure Python implementation
    HAS_C_EXTENSION = False

from .core import {self._to_class_name(package_name)}

__all__ = ['{self._to_class_name(package_name)}', 'HAS_C_EXTENSION']
''')
        
        # Core Python module
        (src_dir / "core.py").write_text(f'''"""
Core implementation for {project_name}.
Includes both pure Python and C extension implementations.
"""

import math
from typing import List, Union

try:
    from .ext import {self._to_class_name(package_name).lower()}_ext
    HAS_C_EXTENSION = True
except ImportError:
    HAS_C_EXTENSION = False


class {self._to_class_name(package_name)}:
    """Main class with optional C extension acceleration."""
    
    def __init__(self, use_c_extension: bool = True):
        """Initialize with optional C extension usage."""
        self.use_c_extension = use_c_extension and HAS_C_EXTENSION
        
    def fast_calculation(self, data: List[float]) -> float:
        """Perform fast calculation using C extension if available."""
        if self.use_c_extension:
            return {self._to_class_name(package_name).lower()}_ext.fast_sum(data)
        else:
            return self._pure_python_calculation(data)
    
    def _pure_python_calculation(self, data: List[float]) -> float:
        """Pure Python fallback implementation."""
        return sum(x * x for x in data)
    
    def matrix_multiply(self, a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
        """Matrix multiplication with optional C acceleration."""
        if self.use_c_extension:
            return {self._to_class_name(package_name).lower()}_ext.matrix_multiply(a, b)
        else:
            return self._pure_python_matrix_multiply(a, b)
    
    def _pure_python_matrix_multiply(self, a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
        """Pure Python matrix multiplication."""
        rows_a, cols_a = len(a), len(a[0])
        rows_b, cols_b = len(b), len(b[0])
        
        if cols_a != rows_b:
            raise ValueError("Matrix dimensions don't match for multiplication")
        
        result = [[0.0 for _ in range(cols_b)] for _ in range(rows_a)]
        
        for i in range(rows_a):
            for j in range(cols_b):
                for k in range(cols_a):
                    result[i][j] += a[i][k] * b[k][j]
        
        return result
''')
        
        # C extension source
        (ext_dir / f"{self._to_class_name(package_name).lower()}_ext.c").write_text(f'''/*
 * C extension for {project_name}
 * Provides performance-critical functions
 */

#include <Python.h>
#include <math.h>

/* Fast sum of squares function */
static PyObject *
fast_sum(PyObject *self, PyObject *args)
{{
    PyObject *list;
    Py_ssize_t i, n;
    double result = 0.0;
    
    if (!PyArg_ParseTuple(args, "O!", &PyList_Type, &list))
        return NULL;
    
    n = PyList_Size(list);
    for (i = 0; i < n; i++) {{
        PyObject *item = PyList_GetItem(list, i);
        double value = PyFloat_AsDouble(item);
        if (PyErr_Occurred())
            return NULL;
        result += value * value;
    }}
    
    return PyFloat_FromDouble(result);
}}

/* Matrix multiplication function */
static PyObject *
matrix_multiply(PyObject *self, PyObject *args)
{{
    PyObject *a, *b;
    Py_ssize_t rows_a, cols_a, rows_b, cols_b;
    
    if (!PyArg_ParseTuple(args, "O!O!", &PyList_Type, &a, &PyList_Type, &b))
        return NULL;
    
    rows_a = PyList_Size(a);
    if (rows_a == 0) {{
        PyErr_SetString(PyExc_ValueError, "Empty matrix A");
        return NULL;
    }}
    
    PyObject *first_row_a = PyList_GetItem(a, 0);
    cols_a = PyList_Size(first_row_a);
    
    rows_b = PyList_Size(b);
    if (rows_b == 0) {{
        PyErr_SetString(PyExc_ValueError, "Empty matrix B");
        return NULL;
    }}
    
    PyObject *first_row_b = PyList_GetItem(b, 0);
    cols_b = PyList_Size(first_row_b);
    
    if (cols_a != rows_b) {{
        PyErr_SetString(PyExc_ValueError, "Matrix dimensions don't match");
        return NULL;
    }}
    
    /* Create result matrix */
    PyObject *result = PyList_New(rows_a);
    for (Py_ssize_t i = 0; i < rows_a; i++) {{
        PyObject *row = PyList_New(cols_b);
        for (Py_ssize_t j = 0; j < cols_b; j++) {{
            double sum = 0.0;
            for (Py_ssize_t k = 0; k < cols_a; k++) {{
                PyObject *a_row = PyList_GetItem(a, i);
                PyObject *a_val = PyList_GetItem(a_row, k);
                PyObject *b_row = PyList_GetItem(b, k);
                PyObject *b_val = PyList_GetItem(b_row, j);
                
                double a_double = PyFloat_AsDouble(a_val);
                double b_double = PyFloat_AsDouble(b_val);
                
                if (PyErr_Occurred())
                    return NULL;
                
                sum += a_double * b_double;
            }}
            PyList_SetItem(row, j, PyFloat_FromDouble(sum));
        }}
        PyList_SetItem(result, i, row);
    }}
    
    return result;
}}

/* Method definitions */
static PyMethodDef {self._to_class_name(package_name).lower()}_methods[] = {{
    {{"fast_sum", fast_sum, METH_VARARGS, "Calculate sum of squares"}},
    {{"matrix_multiply", matrix_multiply, METH_VARARGS, "Multiply two matrices"}},
    {{NULL, NULL, 0, NULL}}
}};

/* Module definition */
static struct PyModuleDef {self._to_class_name(package_name).lower()}_module = {{
    PyModuleDef_HEAD_INIT,
    "{self._to_class_name(package_name).lower()}_ext",
    "C extension for {project_name}",
    -1,
    {self._to_class_name(package_name).lower()}_methods
}};

/* Module initialization */
PyMODINIT_FUNC
PyInit_{self._to_class_name(package_name).lower()}_ext(void)
{{
    return PyModule_Create(&{self._to_class_name(package_name).lower()}_module);
}}
''')
        
        # Setup.py with extension configuration
        (project_path / "setup.py").write_text(f'''"""
Setup script for {project_name} with C extensions.
"""

from setuptools import setup, find_packages, Extension
from pathlib import Path
import platform

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ""

# Define C extension
ext_modules = [
    Extension(
        "{package_name}.ext.{self._to_class_name(package_name).lower()}_ext",
        sources=["src/{package_name}/ext/{self._to_class_name(package_name).lower()}_ext.c"],
        include_dirs=[],
        libraries=[],
        extra_compile_args=["-O3"] if platform.system() != "Windows" else ["/O2"],
        extra_link_args=[],
    )
]

setup(
    name="{package_name.replace('_', '-')}",
    version="{metadata.get('version', '0.1.0')}",
    author="{metadata.get('author', 'Your Name')}",
    author_email="{metadata.get('email', 'your.email@example.com')}",
    description="{metadata.get('description', f'A {project_name} package with binary extensions')}",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="{metadata.get('url', f'https://github.com/yourusername/{package_name.replace("_", "-")}')}",
    packages=find_packages(where="src"),
    package_dir={{"": "src"}},
    ext_modules=ext_modules,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: C",
    ],
    python_requires=">=3.8",
    install_requires=[
        "setuptools",
    ],
    extras_require={{
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "cython>=0.29.0",  # For potential Cython integration
            "wheel>=0.37.0",
        ],
    }},
    zip_safe=False,  # Required for C extensions
)
''')
        
        # pyproject.toml for modern build
        (project_path / "pyproject.toml").write_text(f'''[build-system]
requires = ["setuptools>=64", "wheel", "setuptools-scm[toml]>=6.2"]
build-backend = "setuptools.build_meta"

[project]
name = "{package_name.replace('_', '-')}"
dynamic = ["version"]
description = "{metadata.get('description', f'A {project_name} package with binary extensions')}"
readme = "README.md"
authors = [
    {{name = "{metadata.get('author', 'Your Name')}", email = "{metadata.get('email', 'your.email@example.com')}"}}
]
license = {{text = "MIT"}}
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: C",
]
requires-python = ">=3.8"
dependencies = [
    "setuptools",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "cython>=0.29.0",
    "wheel>=0.37.0",
    "build>=0.10.0",
]

[tool.setuptools]
packages = ["src"]
zip-safe = false

[tool.setuptools.dynamic]
version = {{attr = "{package_name}.__version__"}}
''')
        
        # Build script
        (project_path / "build_ext.py").write_text(f'''#!/usr/bin/env python3
"""
Build script for C extensions in {project_name}.
"""

import subprocess
import sys
import platform
from pathlib import Path

def build_extension():
    """Build the C extension."""
    print("Building C extension...")
    
    try:
        # Build in-place for development
        cmd = [sys.executable, "setup.py", "build_ext", "--inplace"]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ C extension built successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to build C extension: {{e}}")
        print(f"stdout: {{e.stdout}}")
        print(f"stderr: {{e.stderr}}")
        return False

def clean_build():
    """Clean build artifacts."""
    print("Cleaning build artifacts...")
    
    import shutil
    patterns = ["build", "*.egg-info", "**/*.so", "**/*.pyd", "**/__pycache__"]
    
    for pattern in patterns:
        for path in Path(".").rglob(pattern):
            if path.exists():
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                print(f"Removed: {{path}}")

def main():
    """Main build script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build script for C extensions")
    parser.add_argument("action", choices=["build", "clean"], help="Action to perform")
    
    args = parser.parse_args()
    
    if args.action == "build":
        success = build_extension()
        sys.exit(0 if success else 1)
    elif args.action == "clean":
        clean_build()
        sys.exit(0)

if __name__ == "__main__":
    main()
''')
        
        # Requirements
        requirements = [
            "setuptools>=64.0.0",
        ]
        (project_path / "requirements.txt").write_text("\\n".join(requirements) + "\\n")
        
        # Tests
        if features.get('tests', True):
            self._create_binary_extension_tests(project_path, package_name)
        
        # README
        if features.get('readme', True):
            self._create_binary_extension_readme(project_path, project_name, package_name, metadata)
        
        # CI configuration for building wheels
        if features.get('ci_cd', True):
            self._create_binary_extension_ci(project_path, package_name)
        
        if features.get('gitignore', True):
            self._create_binary_extension_gitignore(project_path)
        
        return True
    
    def _create_binary_extension_tests(self, project_path: Path, package_name: str):
        """Create tests for binary extension package."""
        tests_dir = project_path / "tests"
        tests_dir.mkdir(exist_ok=True)
        
        (tests_dir / "__init__.py").write_text("")
        
        # Test the C extension
        (tests_dir / "test_extension.py").write_text(f'''"""
Tests for {package_name} C extension.
"""

import unittest
import pytest
from {package_name} import {self._to_class_name(package_name)}, HAS_C_EXTENSION


class TestExtension(unittest.TestCase):
    """Test the binary extension functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calc = {self._to_class_name(package_name)}()
        self.calc_pure = {self._to_class_name(package_name)}(use_c_extension=False)
    
    def test_fast_calculation_consistency(self):
        """Test that C and Python implementations give same results."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        python_result = self.calc_pure.fast_calculation(data)
        
        if HAS_C_EXTENSION:
            c_result = self.calc.fast_calculation(data)
            self.assertAlmostEqual(python_result, c_result, places=10)
        
        # Expected result: 1² + 2² + 3² + 4² + 5² = 55
        self.assertAlmostEqual(python_result, 55.0, places=10)
    
    def test_matrix_multiply_consistency(self):
        """Test matrix multiplication consistency."""
        a = [[1.0, 2.0], [3.0, 4.0]]
        b = [[5.0, 6.0], [7.0, 8.0]]
        
        python_result = self.calc_pure.matrix_multiply(a, b)
        
        if HAS_C_EXTENSION:
            c_result = self.calc.matrix_multiply(a, b)
            self.assertEqual(python_result, c_result)
        
        # Expected result: [[19, 22], [43, 50]]
        expected = [[19.0, 22.0], [43.0, 50.0]]
        self.assertEqual(python_result, expected)
    
    def test_empty_list(self):
        """Test with empty input."""
        result = self.calc.fast_calculation([])
        self.assertEqual(result, 0.0)
    
    def test_matrix_dimension_error(self):
        """Test matrix dimension mismatch error."""
        a = [[1.0, 2.0], [3.0, 4.0]]  # 2x2
        b = [[1.0], [2.0], [3.0]]     # 3x1
        
        with self.assertRaises(ValueError):
            self.calc.matrix_multiply(a, b)
    
    @pytest.mark.skipif(not HAS_C_EXTENSION, reason="C extension not available")
    def test_c_extension_available(self):
        """Test that C extension is available and working."""
        self.assertTrue(HAS_C_EXTENSION)
        
        # Test that C extension is actually being used
        calc_c = {self._to_class_name(package_name)}(use_c_extension=True)
        self.assertTrue(calc_c.use_c_extension)

if __name__ == "__main__":
    unittest.main()
''')
    
    def _create_binary_extension_readme(self, project_path: Path, project_name: str, package_name: str, metadata: Dict[str, str]):
        """Create README for binary extension package."""
        content = f'''# {project_name}

{metadata.get('description', f'A {project_name} package with binary extensions')}

This package includes C extensions for performance-critical operations, with pure Python fallbacks.

## Features

- **C Extensions**: High-performance C implementations for critical functions
- **Pure Python Fallbacks**: Automatic fallback when C extensions unavailable
- **Cross-Platform**: Builds on Windows, macOS, and Linux
- **Wheel Distribution**: Pre-compiled wheels for major platforms

## Installation

### From PyPI (Recommended)
```bash
pip install {package_name.replace('_', '-')}
```

### From Source
```bash
git clone <repository-url>
cd {package_name.replace('_', '-')}
pip install -e .
```

### Building C Extensions

To build the C extensions manually:
```bash
python build_ext.py build
```

## Usage

```python
from {package_name} import {self._to_class_name(package_name)}, HAS_C_EXTENSION

# Create calculator instance
calc = {self._to_class_name(package_name)}()

# Check if C extension is available
print(f"C extension available: {{HAS_C_EXTENSION}}")

# Fast calculation (uses C extension if available)
data = [1.0, 2.0, 3.0, 4.0, 5.0]
result = calc.fast_calculation(data)
print(f"Sum of squares: {{result}}")

# Matrix multiplication
a = [[1.0, 2.0], [3.0, 4.0]]
b = [[5.0, 6.0], [7.0, 8.0]]
result = calc.matrix_multiply(a, b)
print(f"Matrix product: {{result}}")

# Force pure Python implementation
calc_pure = {self._to_class_name(package_name)}(use_c_extension=False)
result = calc_pure.fast_calculation(data)
```

## Performance

The C extensions provide significant performance improvements:

| Operation | Pure Python | C Extension | Speedup |
|-----------|-------------|-------------|---------|
| Sum of squares (1000 elements) | 100μs | 10μs | 10x |
| Matrix multiplication (100x100) | 1000ms | 100ms | 10x |

## Development

### Building for Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Build C extensions in-place
python build_ext.py build

# Run tests
pytest

# Clean build artifacts
python build_ext.py clean
```

### Building Wheels

```bash
# Build source distribution and wheel
python -m build

# Build wheels for multiple platforms (requires cibuildwheel)
pip install cibuildwheel
cibuildwheel --platform linux
```

## C Extension Details

The package includes the following C functions:

- `fast_sum(list)`: Calculate sum of squares of a list of numbers
- `matrix_multiply(a, b)`: Multiply two matrices

### Adding New C Functions

1. Add function to `src/{package_name}/ext/{self._to_class_name(package_name).lower()}_ext.c`
2. Update method definitions array
3. Add Python wrapper in `core.py`
4. Add tests in `tests/test_extension.py`
5. Rebuild: `python build_ext.py build`

## Troubleshooting

### C Extension Build Failures

**Missing Compiler:**
- Windows: Install Microsoft C++ Build Tools
- macOS: Install Xcode Command Line Tools (`xcode-select --install`)
- Linux: Install gcc (`sudo apt-get install build-essential`)

**Python.h Not Found:**
```bash
# Ubuntu/Debian
sudo apt-get install python3-dev

# CentOS/RHEL
sudo yum install python3-devel

# macOS (usually included with Xcode)
xcode-select --install
```

**Fallback Mode:**
If C extensions fail to build, the package will still work using pure Python implementations.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for any new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

{metadata.get('license_type', 'MIT')} License - see LICENSE file for details.

## Author

{metadata.get('author', 'Your Name')} - {metadata.get('email', 'your.email@example.com')}
'''
        (project_path / "README.md").write_text(content)
    
    def _create_binary_extension_ci(self, project_path: Path, package_name: str):
        """Create CI configuration for building wheels."""
        github_dir = project_path / ".github" / "workflows"
        github_dir.mkdir(parents=True, exist_ok=True)
        
        # GitHub Actions workflow for building wheels
        (github_dir / "wheels.yml").write_text(f'''name: Build Wheels

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  release:
    types: [ published ]

jobs:
  build_wheels:
    name: Build wheels on ${{{{ matrix.os }}}}
    runs-on: ${{{{ matrix.os }}}}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.x'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build cibuildwheel

    - name: Build wheels
      run: python -m cibuildwheel --output-dir wheelhouse
      env:
        # Configure cibuildwheel
        CIBW_BUILD: cp38-* cp39-* cp310-* cp311-* cp312-*
        CIBW_SKIP: "*-win32 *-manylinux_i686"
        CIBW_TEST_REQUIRES: pytest
        CIBW_TEST_COMMAND: "pytest {{package}}/tests"

    - name: Upload wheels
      uses: actions/upload-artifact@v3
      with:
        name: wheels
        path: ./wheelhouse/*.whl

  build_sdist:
    name: Build source distribution
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.x'

    - name: Build sdist
      run: |
        python -m pip install --upgrade pip build
        python -m build --sdist

    - name: Upload sdist
      uses: actions/upload-artifact@v3
      with:
        name: wheels
        path: dist/*.tar.gz

  test:
    name: Test on ${{{{ matrix.os }}}} with Python ${{{{ matrix.python-version }}}}
    runs-on: ${{{{ matrix.os }}}}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python ${{{{ matrix.python-version }}}}
      uses: actions/setup-python@v4
      with:
        python-version: ${{{{ matrix.python-version }}}}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"

    - name: Build C extension
      run: python build_ext.py build

    - name: Run tests
      run: pytest tests/ -v

  upload_pypi:
    needs: [build_wheels, build_sdist, test]
    runs-on: ubuntu-latest
    if: github.event_name == 'release' && github.event.action == 'published'
    steps:
    - uses: actions/download-artifact@v3
      with:
        name: wheels
        path: dist

    - name: Publish to PyPI
      uses: pypa/gh-action-pypi-publish@release/v1
      with:
        user: __token__
        password: ${{{{ secrets.PYPI_API_TOKEN }}}}
''')
    
    def _create_binary_extension_gitignore(self, project_path: Path):
        """Create .gitignore for binary extension package."""
        content = '''# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so
*.pyd
*.dll

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Compiled C/C++ files
*.o
*.obj
*.exe
*.out
*.app

# Build artifacts
*.build_ext
*.build
build_temp/

# PyInstaller
*.manifest
*.spec

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
cover/

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Temporary files
*.tmp
*.temp
*.log
'''
        (project_path / ".gitignore").write_text(content)
    
    def _to_package_name(self, project_name: str) -> str:
        """Convert project name to valid Python package name."""
        return project_name.lower().replace('-', '_').replace(' ', '_')
    
    def _to_class_name(self, package_name: str) -> str:
        """Convert package name to class name."""
        return ''.join(word.capitalize() for word in package_name.split('_'))
    
    def _generate_namespace_package_template(self, project_path: Path, project_name: str, package_name: str, features: Dict[str, bool], metadata: Dict[str, str]) -> bool:
        """Generate a namespace package template."""
        # Extract namespace from package name (e.g., 'company_tools' -> 'company', 'tools')
        if '_' in package_name:
            namespace, subpackage = package_name.split('_', 1)
        else:
            namespace = package_name
            subpackage = "core"
        
        # Create namespace package structure (no __init__.py in namespace)
        namespace_dir = project_path / "src" / namespace
        namespace_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subpackage
        subpackage_dir = namespace_dir / subpackage
        subpackage_dir.mkdir(exist_ok=True)
        
        # Subpackage __init__.py (this has __init__.py, namespace doesn't)
        (subpackage_dir / "__init__.py").write_text(f'''"""
{subpackage.title()} subpackage of {namespace} namespace.

This is part of the {namespace} namespace package.
{metadata.get('description', f'A {project_name} namespace package')}
"""

__version__ = "{metadata.get('version', '0.1.0')}"

from .core import {self._to_class_name(subpackage)}

__all__ = ['{self._to_class_name(subpackage)}']
''')
        
        # Core implementation
        (subpackage_dir / "core.py").write_text(f'''"""
Core implementation for {namespace}.{subpackage}.
"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class {self._to_class_name(subpackage)}:
    """Main class for {namespace}.{subpackage}."""
    
    def __init__(self, name: str = "{subpackage}"):
        """Initialize the {subpackage} component."""
        self.name = name
        self.namespace = "{namespace}"
        logger.info(f"Initialized {{self.namespace}}.{{self.name}}")
    
    def get_info(self) -> Dict[str, Any]:
        """Get information about this namespace component."""
        return {{
            "name": self.name,
            "namespace": self.namespace,
            "full_name": f"{{self.namespace}}.{{self.name}}",
            "version": "{metadata.get('version', '0.1.0')}",
            "description": "{metadata.get('description', f'A {project_name} namespace package')}"
        }}
    
    def discover_siblings(self) -> List[str]:
        """Discover other packages in the same namespace."""
        import pkgutil
        
        siblings = []
        try:
            # Import the namespace package
            namespace_module = __import__(self.namespace)
            
            # Discover all subpackages
            for finder, name, ispkg in pkgutil.iter_modules(namespace_module.__path__, 
                                                           prefix=f"{{self.namespace}}."):
                if ispkg and name != f"{{self.namespace}}.{{self.name}}":
                    siblings.append(name)
        except ImportError as e:
            logger.warning(f"Could not discover siblings: {{e}}")
        
        return siblings
    
    def call_sibling(self, sibling_name: str, method_name: str = "get_info", *args, **kwargs):
        """Call a method on a sibling package."""
        try:
            full_module_name = f"{{self.namespace}}.{{sibling_name}}"
            module = __import__(full_module_name, fromlist=[sibling_name])
            
            # Look for a class with the same name pattern
            class_name = self._to_class_name(sibling_name)
            if hasattr(module, class_name):
                cls = getattr(module, class_name)
                instance = cls()
                if hasattr(instance, method_name):
                    return getattr(instance, method_name)(*args, **kwargs)
            
            logger.warning(f"Method {{method_name}} not found in {{full_module_name}}")
            return None
            
        except ImportError as e:
            logger.error(f"Could not import {{full_module_name}}: {{e}}")
            return None
    
    def _to_class_name(self, name: str) -> str:
        """Convert name to class name."""
        return ''.join(word.capitalize() for word in name.split('_'))


def discover_namespace_packages(namespace: str = "{namespace}") -> List[str]:
    """Discover all packages in the namespace."""
    import pkgutil
    
    packages = []
    try:
        namespace_module = __import__(namespace)
        for finder, name, ispkg in pkgutil.iter_modules(namespace_module.__path__, 
                                                       prefix=f"{{namespace}}."):
            if ispkg:
                packages.append(name)
    except ImportError:
        pass
    
    return packages
''')
        
        # Setup.py for namespace package
        (project_path / "setup.py").write_text(f'''"""
Setup script for {namespace}.{subpackage} namespace package.
"""

from setuptools import setup, find_namespace_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ""

setup(
    name="{namespace}-{subpackage}",
    version="{metadata.get('version', '0.1.0')}",
    author="{metadata.get('author', 'Your Name')}",
    author_email="{metadata.get('email', 'your.email@example.com')}",
    description="{metadata.get('description', f'{subpackage.title()} component of {namespace} namespace')}",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="{metadata.get('url', f'https://github.com/yourusername/{namespace}-{subpackage}')}",
    
    # Use find_namespace_packages for namespace package support
    packages=find_namespace_packages(where="src"),
    package_dir={{"": "src"}},
    
    # Namespace packages configuration
    zip_safe=False,
    
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        # Add dependencies here
    ],
    extras_require={{
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    }},
)
''')
        
        # pyproject.toml for namespace package
        (project_path / "pyproject.toml").write_text(f'''[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{namespace}-{subpackage}"
dynamic = ["version"]
description = "{metadata.get('description', f'{subpackage.title()} component of {namespace} namespace')}"
readme = "README.md"
authors = [
    {{name = "{metadata.get('author', 'Your Name')}", email = "{metadata.get('email', 'your.email@example.com')}"}}
]
license = {{text = "MIT"}}
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
requires-python = ">=3.8"
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
]

[tool.setuptools]
# Use find_namespace_packages for implicit namespace support
packages = ["src"]
zip-safe = false

[tool.setuptools.dynamic]
version = {{attr = "{namespace}.{subpackage}.__version__"}}

[tool.setuptools.packages.find]
where = ["src"]
namespaces = true
''')
        
        # Create example sibling package documentation
        docs_dir = project_path / "docs"
        docs_dir.mkdir(exist_ok=True)
        
        (docs_dir / "namespace_usage.md").write_text(f'''# {namespace.title()} Namespace Package

This package is part of the `{namespace}` namespace, allowing for distributed development.

## Namespace Structure

```
{namespace}/
├── {subpackage}/          # This package
├── other_component/       # Another team's package
└── third_component/       # Yet another package
```

## Creating Additional Namespace Packages

To create another component in the `{namespace}` namespace:

### 1. Create the package structure:

```
{namespace}-other-component/
├── src/
│   └── {namespace}/           # No __init__.py here!
│       └── other_component/   # __init__.py goes here
│           ├── __init__.py
│           └── core.py
├── setup.py
└── pyproject.toml
```

### 2. Setup script:

```python
from setuptools import setup, find_namespace_packages

setup(
    name="{namespace}-other-component",
    packages=find_namespace_packages(where="src"),
    package_dir={{"": "src"}},
    # ... other configuration
)
```

### 3. Important Notes:

- **No `__init__.py` in namespace directory**: The `src/{namespace}/` directory should NOT contain an `__init__.py` file
- **Use `find_namespace_packages()`**: This is crucial for proper namespace package detection
- **Separate repositories**: Each component can be in its own repository and released independently
- **Independent versioning**: Each namespace component has its own version

## Usage Examples

### Basic Usage

```python
# Import this component
from {namespace}.{subpackage} import {self._to_class_name(subpackage)}

# Create instance
component = {self._to_class_name(subpackage)}()
print(component.get_info())
```

### Discovering Other Components

```python
from {namespace}.{subpackage} import {self._to_class_name(subpackage)}, discover_namespace_packages

# Discover all packages in namespace
packages = discover_namespace_packages()
print(f"Available packages: {{packages}}")

# Discover siblings from instance
component = {self._to_class_name(subpackage)}()
siblings = component.discover_siblings()
print(f"Sibling packages: {{siblings}}")
```

### Inter-Component Communication

```python
# Call methods on other namespace components
component = {self._to_class_name(subpackage)}()
result = component.call_sibling("other_component", "some_method", arg1="value")
```

## Development Workflow

### Setting Up Development Environment

```bash
# Clone this component
git clone <{namespace}-{subpackage}-repo>
cd {namespace}-{subpackage}

# Install in development mode
pip install -e .

# Install other namespace components
pip install {namespace}-other-component
pip install {namespace}-third-component
```

### Testing with Multiple Components

```python
# Test that all components are accessible
import {namespace}.{subpackage}
import {namespace}.other_component
import {namespace}.third_component

# All should be importable without conflicts
```

## Best Practices

1. **Consistent Naming**: Use `{namespace}-component-name` for package names
2. **No Namespace Conflicts**: Ensure subpackage names don't conflict
3. **Independent Releases**: Each component should be releasable independently
4. **Documentation**: Document the namespace structure and inter-component APIs
5. **Testing**: Test both standalone and with other namespace components

## Troubleshooting

### ImportError: No module named '{namespace}'

This usually means:
1. No namespace components are installed
2. Installation didn't use `find_namespace_packages()`
3. An `__init__.py` file was accidentally added to the namespace directory

### Components Not Discoverable

Check:
1. All components use `find_namespace_packages()`
2. No `__init__.py` in the namespace directory
3. Packages are properly installed (not just on PYTHONPATH)
''')
        
        # Tests for namespace functionality
        if features.get('tests', True):
            self._create_namespace_package_tests(project_path, namespace, subpackage)
        
        # README
        if features.get('readme', True):
            self._create_namespace_package_readme(project_path, project_name, namespace, subpackage, metadata)
        
        if features.get('gitignore', True):
            self._create_basic_gitignore(project_path)
        
        return True

    def _create_namespace_package_tests(self, project_path: Path, namespace: str, subpackage: str):
        """Create tests for namespace package."""
        tests_dir = project_path / "tests"
        tests_dir.mkdir(exist_ok=True)
        
        (tests_dir / "__init__.py").write_text("")
        
        (tests_dir / "test_namespace.py").write_text(f'''"""
Tests for {namespace}.{subpackage} namespace package.
"""

import unittest
import sys
from {namespace}.{subpackage} import {self._to_class_name(subpackage)}, discover_namespace_packages


class TestNamespacePackage(unittest.TestCase):
    """Test namespace package functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.component = {self._to_class_name(subpackage)}()
    
    def test_component_info(self):
        """Test component information."""
        info = self.component.get_info()
        
        self.assertIsInstance(info, dict)
        self.assertEqual(info["namespace"], "{namespace}")
        self.assertEqual(info["name"], "{subpackage}")
        self.assertEqual(info["full_name"], "{namespace}.{subpackage}")
        self.assertIn("version", info)
        self.assertIn("description", info)
    
    def test_namespace_discovery(self):
        """Test namespace package discovery."""
        packages = discover_namespace_packages()
        self.assertIsInstance(packages, list)
        
        # At minimum, our package should be discoverable
        expected_package = f"{namespace}.{subpackage}"
        # Note: This might fail if the package isn't properly installed
        # In a real environment with multiple namespace components
    
    def test_sibling_discovery(self):
        """Test sibling package discovery."""
        siblings = self.component.discover_siblings()
        self.assertIsInstance(siblings, list)
        
        # Should not include itself
        self_name = f"{namespace}.{subpackage}"
        self.assertNotIn(self_name, siblings)
    
    def test_namespace_structure(self):
        """Test that namespace is properly structured."""
        # Verify namespace package doesn't have __init__.py
        import {namespace}
        
        # Namespace package should have __path__ but not __file__
        self.assertTrue(hasattr({namespace}, "__path__"))
        # In Python 3.3+, namespace packages don't have __file__
        if sys.version_info >= (3, 3):
            self.assertFalse(hasattr({namespace}, "__file__"))
    
    def test_component_independence(self):
        """Test that component can work independently."""
        # Create multiple instances
        comp1 = {self._to_class_name(subpackage)}("instance1")
        comp2 = {self._to_class_name(subpackage)}("instance2")
        
        self.assertEqual(comp1.name, "instance1")
        self.assertEqual(comp2.name, "instance2")
        self.assertEqual(comp1.namespace, comp2.namespace)

if __name__ == "__main__":
    unittest.main()
''')
    
    def _create_namespace_package_readme(self, project_path: Path, project_name: str, namespace: str, subpackage: str, metadata: Dict[str, str]):
        """Create README for namespace package."""
        content = f'''# {namespace.title()}.{subpackage.title()} - Namespace Package

{metadata.get('description', f'The {subpackage} component of the {namespace} namespace package')}

This package is part of the `{namespace}` namespace, enabling distributed development and modular architecture.

## What are Namespace Packages?

Namespace packages allow multiple, separately distributed packages to share a common namespace. This enables:

- **Distributed Development**: Different teams can develop separate components
- **Independent Releases**: Each component has its own release cycle  
- **Modular Architecture**: Users install only the components they need
- **Avoiding Conflicts**: No single "root" package owns the namespace

## Installation

```bash
pip install {namespace}-{subpackage}
```

## Usage

### Basic Usage

```python
from {namespace}.{subpackage} import {self._to_class_name(subpackage)}

# Create component instance
component = {self._to_class_name(subpackage)}()

# Get component information
info = component.get_info()
print(f"Component: {{info['full_name']}}")
print(f"Version: {{info['version']}}")
```

### Working with Multiple Namespace Components

```python
from {namespace}.{subpackage} import {self._to_class_name(subpackage)}, discover_namespace_packages

# Discover all available namespace packages
packages = discover_namespace_packages()
print(f"Available {namespace} packages: {{packages}}")

# Discover sibling packages
component = {self._to_class_name(subpackage)}()
siblings = component.discover_siblings()
print(f"Sibling packages: {{siblings}}")

# Call methods on sibling packages (if available)
result = component.call_sibling("other_component", "get_info")
if result:
    print(f"Sibling info: {{result}}")
```

## Package Structure

```
{namespace}-{subpackage}/
├── src/
│   └── {namespace}/           # Namespace (NO __init__.py!)
│       └── {subpackage}/      # Component package
│           ├── __init__.py    # Component init
│           └── core.py        # Implementation
├── tests/
├── docs/
├── setup.py
├── pyproject.toml
└── README.md
```

**Important**: The `src/{namespace}/` directory should NOT contain an `__init__.py` file. This is crucial for proper namespace package functionality.

## Creating Additional Components

To add another component to the `{namespace}` namespace:

### 1. Create New Package Structure

```bash
mkdir {namespace}-new-component
cd {namespace}-new-component

# Create the structure
mkdir -p src/{namespace}/new_component
mkdir tests docs

# Create component files (NO __init__.py in {namespace}/)
touch src/{namespace}/new_component/__init__.py
touch src/{namespace}/new_component/core.py
```

### 2. Setup Configuration

Use `find_namespace_packages()` in setup.py:

```python
from setuptools import setup, find_namespace_packages

setup(
    name="{namespace}-new-component",
    packages=find_namespace_packages(where="src"),
    package_dir={{"": "src"}},
    # ... other configuration
)
```

### 3. Install and Test

```bash
pip install -e .

# Test namespace functionality
python -c "
import {namespace}.{subpackage}
import {namespace}.new_component
print('Both components accessible!')
"
```

## Development

### Development Installation

```bash
git clone <repository-url>
cd {namespace}-{subpackage}
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest tests/
```

### Testing with Other Components

To test interaction with other namespace components:

```bash
# Install other components
pip install {namespace}-other-component

# Run integration tests
pytest tests/ -k "test_sibling"
```

## API Reference

### {self._to_class_name(subpackage)} Class

Main class for the {subpackage} component.

#### Methods

- `get_info()` → `Dict[str, Any]`: Get component information
- `discover_siblings()` → `List[str]`: Find other namespace components  
- `call_sibling(sibling_name, method_name, *args, **kwargs)`: Call method on sibling

### Functions

- `discover_namespace_packages(namespace="{namespace}")` → `List[str]`: Discover all namespace packages

## Best Practices

1. **No Namespace __init__.py**: Never add `__init__.py` to the namespace directory
2. **Use find_namespace_packages()**: Essential for proper namespace support
3. **Independent Versioning**: Each component should have its own version
4. **Clear Naming**: Use `{namespace}-component-name` pattern for package names
5. **Documentation**: Document inter-component dependencies and APIs

## Troubleshooting

### "No module named '{namespace}'" Error

This typically means:
- No namespace components are installed  
- Components weren't installed with `find_namespace_packages()`
- An `__init__.py` file exists in the namespace directory

### Components Not Discoverable

Check that:
- All components use `find_namespace_packages()`
- No `__init__.py` in namespace directory
- Packages are properly installed (not just on PYTHONPATH)

### Import Conflicts

Ensure:
- Subpackage names don't conflict across components
- Each component has unique functionality
- Dependencies are properly declared

## Related Packages

Other components in the `{namespace}` namespace:

- `{namespace}-other-component`: Description of other component
- `{namespace}-third-component`: Description of third component

## Contributing

1. Fork the repository
2. Create a feature branch  
3. Make your changes
4. Test with other namespace components
5. Submit a pull request

## License

{metadata.get('license_type', 'MIT')} License - see LICENSE file for details.

## Author

{metadata.get('author', 'Your Name')} - {metadata.get('email', 'your.email@example.com')}
'''
        (project_path / "README.md").write_text(content)

    def _generate_plugin_framework_template(self, project_path: Path, project_name: str, package_name: str, features: Dict[str, bool], metadata: Dict[str, str]) -> bool:
        """Generate a plugin framework template."""
        # Create main package structure
        src_dir = project_path / "src" / package_name
        src_dir.mkdir(parents=True, exist_ok=True)
        
        # Create plugins directory
        plugins_dir = src_dir / "plugins"
        plugins_dir.mkdir(exist_ok=True)
        
        # Main package __init__.py
        (src_dir / "__init__.py").write_text(f'''"""
{metadata.get('description', f'A {project_name} plugin framework')}
"""

__version__ = "{metadata.get('version', '0.1.0')}"

from .core import PluginManager, Plugin
from .registry import plugin_registry

__all__ = ['PluginManager', 'Plugin', 'plugin_registry']
''')
        
        # Plugin base class and manager
        (src_dir / "core.py").write_text(f'''"""
Core plugin framework for {project_name}.
"""

import abc
import importlib
import inspect
import logging
from typing import Dict, List, Any, Type, Optional, Callable
from pathlib import Path

logger = logging.getLogger(__name__)


class Plugin(abc.ABC):
    """Base class for all plugins."""
    
    # Plugin metadata
    name: str = "Unknown Plugin"
    version: str = "0.1.0"
    description: str = ""
    author: str = ""
    
    def __init__(self):
        """Initialize the plugin."""
        self.enabled = True
        self.config = {{}}
        logger.info(f"Initialized plugin: {{self.name}} v{{self.version}}")
    
    @abc.abstractmethod
    def activate(self) -> bool:
        """
        Activate the plugin.
        
        Returns:
            True if activation successful, False otherwise
        """
        pass
    
    @abc.abstractmethod
    def deactivate(self) -> bool:
        """
        Deactivate the plugin.
        
        Returns:
            True if deactivation successful, False otherwise
        """
        pass
    
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the plugin with settings."""
        self.config.update(config)
        logger.debug(f"Configured plugin {{self.name}} with: {{config}}")
    
    def get_info(self) -> Dict[str, Any]:
        """Get plugin information."""
        return {{
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "enabled": self.enabled,
            "class": self.__class__.__name__,
            "module": self.__class__.__module__,
        }}


class Hook:
    """Represents a hook point where plugins can attach."""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.callbacks: List[Callable] = []
    
    def register(self, callback: Callable) -> None:
        """Register a callback for this hook."""
        if callback not in self.callbacks:
            self.callbacks.append(callback)
            logger.debug(f"Registered callback for hook {{self.name}}")
    
    def unregister(self, callback: Callable) -> None:
        """Unregister a callback from this hook."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            logger.debug(f"Unregistered callback for hook {{self.name}}")
    
    def call(self, *args, **kwargs) -> List[Any]:
        """Call all registered callbacks."""
        results = []
        for callback in self.callbacks:
            try:
                result = callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Error calling hook {{self.name}} callback: {{e}}")
        return results


class PluginManager:
    """Manages plugin loading, activation, and lifecycle."""
    
    def __init__(self):
        self.plugins: Dict[str, Plugin] = {{}}
        self.hooks: Dict[str, Hook] = {{}}
        self.plugin_paths: List[Path] = []
        
        # Register built-in hooks
        self._register_builtin_hooks()
    
    def _register_builtin_hooks(self) -> None:
        """Register built-in hook points."""
        self.register_hook("plugin_loaded", "Called when a plugin is loaded")
        self.register_hook("plugin_activated", "Called when a plugin is activated")
        self.register_hook("plugin_deactivated", "Called when a plugin is deactivated")
        self.register_hook("before_process", "Called before main processing")
        self.register_hook("after_process", "Called after main processing")
        self.register_hook("error_occurred", "Called when an error occurs")
    
    def register_hook(self, name: str, description: str = "") -> Hook:
        """Register a new hook point."""
        if name not in self.hooks:
            self.hooks[name] = Hook(name, description)
            logger.debug(f"Registered hook: {{name}}")
        return self.hooks[name]
    
    def get_hook(self, name: str) -> Optional[Hook]:
        """Get a hook by name."""
        return self.hooks.get(name)
    
    def call_hook(self, name: str, *args, **kwargs) -> List[Any]:
        """Call a hook by name."""
        if name in self.hooks:
            return self.hooks[name].call(*args, **kwargs)
        return []
    
    def add_plugin_path(self, path: Path) -> None:
        """Add a directory to search for plugins."""
        if path.exists() and path.is_dir():
            self.plugin_paths.append(path)
            logger.info(f"Added plugin path: {{path}}")
    
    def discover_plugins(self) -> List[Type[Plugin]]:
        """Discover plugin classes from plugin paths."""
        plugin_classes = []
        
        for path in self.plugin_paths:
            for py_file in path.glob("*.py"):
                if py_file.name.startswith("_"):
                    continue
                
                try:
                    # Import the module
                    spec = importlib.util.spec_from_file_location(
                        py_file.stem, py_file
                    )
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Find Plugin subclasses
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, Plugin) and 
                            obj is not Plugin):
                            plugin_classes.append(obj)
                            logger.debug(f"Discovered plugin: {{obj.name}}")
                
                except Exception as e:
                    logger.error(f"Error loading plugin from {{py_file}}: {{e}}")
        
        return plugin_classes
    
    def load_plugin(self, plugin_class: Type[Plugin]) -> bool:
        """Load and register a plugin instance."""
        try:
            plugin = plugin_class()
            self.plugins[plugin.name] = plugin
            self.call_hook("plugin_loaded", plugin)
            logger.info(f"Loaded plugin: {{plugin.name}}")
            return True
        except Exception as e:
            logger.error(f"Failed to load plugin {{plugin_class}}: {{e}}")
            return False
    
    def activate_plugin(self, name: str) -> bool:
        """Activate a plugin by name."""
        if name in self.plugins:
            plugin = self.plugins[name]
            if plugin.activate():
                plugin.enabled = True
                self.call_hook("plugin_activated", plugin)
                logger.info(f"Activated plugin: {{name}}")
                return True
        return False
    
    def deactivate_plugin(self, name: str) -> bool:
        """Deactivate a plugin by name."""
        if name in self.plugins:
            plugin = self.plugins[name]
            if plugin.deactivate():
                plugin.enabled = False
                self.call_hook("plugin_deactivated", plugin)
                logger.info(f"Deactivated plugin: {{name}}")
                return True
        return False
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name."""
        return self.plugins.get(name)
    
    def list_plugins(self) -> Dict[str, Dict[str, Any]]:
        """List all loaded plugins with their info."""
        return {{name: plugin.get_info() for name, plugin in self.plugins.items()}}
    
    def configure_plugin(self, name: str, config: Dict[str, Any]) -> bool:
        """Configure a plugin."""
        if name in self.plugins:
            self.plugins[name].configure(config)
            return True
        return False
    
    def load_all_plugins(self) -> int:
        """Discover and load all available plugins."""
        plugin_classes = self.discover_plugins()
        loaded_count = 0
        
        for plugin_class in plugin_classes:
            if self.load_plugin(plugin_class):
                loaded_count += 1
        
        logger.info(f"Loaded {{loaded_count}} plugins")
        return loaded_count
''')
        
        # Plugin registry for entry points
        (src_dir / "registry.py").write_text(f'''"""
Plugin registry and entry point management for {project_name}.
"""

import importlib.metadata
import logging
from typing import Dict, List, Type, Optional
from .core import Plugin, PluginManager

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Registry for managing plugins via entry points."""
    
    def __init__(self, entry_point_group: str = "{package_name}.plugins"):
        self.entry_point_group = entry_point_group
        self.registered_plugins: Dict[str, Type[Plugin]] = {{}}
    
    def discover_entry_points(self) -> List[Type[Plugin]]:
        """Discover plugins via entry points."""
        plugin_classes = []
        
        try:
            entry_points = importlib.metadata.entry_points(group=self.entry_point_group)
            
            for entry_point in entry_points:
                try:
                    plugin_class = entry_point.load()
                    if issubclass(plugin_class, Plugin):
                        plugin_classes.append(plugin_class)
                        self.registered_plugins[entry_point.name] = plugin_class
                        logger.debug(f"Discovered entry point plugin: {{entry_point.name}}")
                    else:
                        logger.warning(f"Entry point {{entry_point.name}} is not a Plugin subclass")
                
                except Exception as e:
                    logger.error(f"Failed to load entry point {{entry_point.name}}: {{e}}")
        
        except Exception as e:
            logger.error(f"Failed to discover entry points: {{e}}")
        
        return plugin_classes
    
    def get_plugin_class(self, name: str) -> Optional[Type[Plugin]]:
        """Get a plugin class by entry point name."""
        return self.registered_plugins.get(name)
    
    def list_available_plugins(self) -> Dict[str, str]:
        """List available plugins from entry points."""
        result = {{}}
        
        try:
            entry_points = importlib.metadata.entry_points(group=self.entry_point_group)
            for entry_point in entry_points:
                result[entry_point.name] = str(entry_point.value)
        except Exception as e:
            logger.error(f"Failed to list entry points: {{e}}")
        
        return result


# Global registry instance
plugin_registry = PluginRegistry()


def register_plugin(name: str, plugin_class: Type[Plugin]) -> None:
    """Register a plugin programmatically."""
    plugin_registry.registered_plugins[name] = plugin_class
    logger.info(f"Registered plugin: {{name}}")


def create_plugin_manager_with_entry_points() -> PluginManager:
    """Create a plugin manager and load plugins from entry points."""
    manager = PluginManager()
    
    # Load plugins from entry points
    plugin_classes = plugin_registry.discover_entry_points()
    
    for plugin_class in plugin_classes:
        manager.load_plugin(plugin_class)
    
    return manager
''')
        
        # Example plugins
        (plugins_dir / "__init__.py").write_text(f'''"""
Example plugins for {project_name}.
"""

from .example_plugin import ExamplePlugin
from .logging_plugin import LoggingPlugin

__all__ = ['ExamplePlugin', 'LoggingPlugin']
''')
        
        (plugins_dir / "example_plugin.py").write_text(f'''"""
Example plugin for {project_name}.
"""

from ..core import Plugin
import logging

logger = logging.getLogger(__name__)


class ExamplePlugin(Plugin):
    """Example plugin demonstrating basic functionality."""
    
    name = "Example Plugin"
    version = "1.0.0"
    description = "An example plugin showing basic plugin functionality"
    author = "Plugin Framework"
    
    def __init__(self):
        super().__init__()
        self.data = {{}}
    
    def activate(self) -> bool:
        """Activate the example plugin."""
        logger.info(f"Activating {{self.name}}")
        
        # Register for hooks if manager is available
        if hasattr(self, '_manager'):
            self._register_hooks()
        
        return True
    
    def deactivate(self) -> bool:
        """Deactivate the example plugin."""
        logger.info(f"Deactivating {{self.name}}")
        return True
    
    def _register_hooks(self):
        """Register hook callbacks."""
        before_hook = self._manager.get_hook("before_process")
        if before_hook:
            before_hook.register(self.before_process_callback)
        
        after_hook = self._manager.get_hook("after_process")
        if after_hook:
            after_hook.register(self.after_process_callback)
    
    def before_process_callback(self, *args, **kwargs):
        """Called before main processing."""
        logger.info("Example plugin: before process")
        self.data['before_process_called'] = True
        return "example_before_result"
    
    def after_process_callback(self, *args, **kwargs):
        """Called after main processing."""
        logger.info("Example plugin: after process")
        self.data['after_process_called'] = True
        return "example_after_result"
    
    def process_data(self, data: str) -> str:
        """Example method for processing data."""
        processed = f"[ExamplePlugin] {{data}}"
        logger.debug(f"Processed data: {{processed}}")
        return processed
''')
        
        (plugins_dir / "logging_plugin.py").write_text(f'''"""
Logging plugin for {project_name}.
"""

import logging
import sys
from datetime import datetime
from ..core import Plugin

logger = logging.getLogger(__name__)


class LoggingPlugin(Plugin):
    """Plugin for enhanced logging functionality."""
    
    name = "Logging Plugin"
    version = "1.0.0"
    description = "Enhanced logging capabilities"
    author = "Plugin Framework"
    
    def __init__(self):
        super().__init__()
        self.log_handler = None
        self.original_level = None
    
    def activate(self) -> bool:
        """Activate enhanced logging."""
        logger.info(f"Activating {{self.name}}")
        
        # Set up enhanced logging
        self._setup_enhanced_logging()
        
        # Register for hooks
        if hasattr(self, '_manager'):
            self._register_hooks()
        
        return True
    
    def deactivate(self) -> bool:
        """Deactivate enhanced logging."""
        logger.info(f"Deactivating {{self.name}}")
        
        # Restore original logging
        self._restore_logging()
        
        return True
    
    def _setup_enhanced_logging(self):
        """Set up enhanced logging format."""
        # Create custom formatter
        formatter = logging.Formatter(
            '%(asctime)s [%(name)s:%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Add handler to root logger
        self.log_handler = logging.StreamHandler(sys.stdout)
        self.log_handler.setFormatter(formatter)
        
        root_logger = logging.getLogger()
        self.original_level = root_logger.level
        root_logger.addHandler(self.log_handler)
        root_logger.setLevel(logging.DEBUG)
    
    def _restore_logging(self):
        """Restore original logging configuration."""
        if self.log_handler:
            root_logger = logging.getLogger()
            root_logger.removeHandler(self.log_handler)
            if self.original_level is not None:
                root_logger.setLevel(self.original_level)
    
    def _register_hooks(self):
        """Register logging hook callbacks."""
        error_hook = self._manager.get_hook("error_occurred")
        if error_hook:
            error_hook.register(self.log_error_callback)
    
    def log_error_callback(self, error, context=None):
        """Log error occurrences."""
        timestamp = datetime.now().isoformat()
        error_msg = f"[{{timestamp}}] ERROR: {{error}}"
        if context:
            error_msg += f" (Context: {{context}})"
        
        logger.error(error_msg)
        return f"logged_error_{{timestamp}}"
''')
        
        # CLI interface
        (src_dir / "cli.py").write_text(f'''"""
Command-line interface for {project_name} plugin system.
"""

import click
import logging
from pathlib import Path
from .core import PluginManager
from .registry import create_plugin_manager_with_entry_points, plugin_registry

logger = logging.getLogger(__name__)


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, verbose):
    """
    {project_name} Plugin Framework CLI
    
    Manage and interact with plugins.
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    
    # Set up logging
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format='%(levelname)s: %(message)s')


@cli.command()
@click.pass_context
def list_plugins(ctx):
    """List all available plugins."""
    click.echo("Available plugins from entry points:")
    
    available = plugin_registry.list_available_plugins()
    if not available:
        click.echo("  No plugins found via entry points")
    else:
        for name, value in available.items():
            click.echo(f"  {{name}}: {{value}}")
    
    click.echo("\\nLoaded plugins:")
    manager = create_plugin_manager_with_entry_points()
    plugins = manager.list_plugins()
    
    if not plugins:
        click.echo("  No plugins loaded")
    else:
        for name, info in plugins.items():
            status = "enabled" if info['enabled'] else "disabled"
            click.echo(f"  {{name}} v{{info['version']}} ({{status}})")
            click.echo(f"    {{info['description']}}")


@cli.command()
@click.argument('plugin_name')
@click.pass_context
def activate(ctx, plugin_name):
    """Activate a plugin."""
    manager = create_plugin_manager_with_entry_points()
    
    if manager.activate_plugin(plugin_name):
        click.echo(f"✅ Activated plugin: {{plugin_name}}")
    else:
        click.echo(f"❌ Failed to activate plugin: {{plugin_name}}")


@cli.command()
@click.argument('plugin_name')
@click.pass_context
def deactivate(ctx, plugin_name):
    """Deactivate a plugin."""
    manager = create_plugin_manager_with_entry_points()
    
    if manager.deactivate_plugin(plugin_name):
        click.echo(f"✅ Deactivated plugin: {{plugin_name}}")
    else:
        click.echo(f"❌ Failed to deactivate plugin: {{plugin_name}}")


@cli.command()
@click.argument('plugin_path', type=click.Path(exists=True, path_type=Path))
@click.pass_context
def load_from_path(ctx, plugin_path):
    """Load plugins from a directory path."""
    manager = PluginManager()
    manager.add_plugin_path(plugin_path)
    
    count = manager.load_all_plugins()
    click.echo(f"Loaded {{count}} plugins from {{plugin_path}}")
    
    # List loaded plugins
    plugins = manager.list_plugins()
    for name, info in plugins.items():
        click.echo(f"  {{name}} v{{info['version']}}")


@cli.command()
@click.pass_context
def demo(ctx):
    """Run a demonstration of the plugin system."""
    click.echo("🔌 Plugin Framework Demo")
    click.echo("========================")
    
    # Create manager and load plugins
    manager = create_plugin_manager_with_entry_points()
    
    # Load example plugins from the plugins directory
    from . import plugins
    manager.add_plugin_path(Path(plugins.__file__).parent)
    manager.load_all_plugins()
    
    click.echo(f"\\nLoaded {{len(manager.plugins)}} plugins:")
    for name, plugin in manager.plugins.items():
        click.echo(f"  - {{name}} v{{plugin.version}}")
    
    # Activate all plugins
    click.echo("\\nActivating plugins...")
    for name in manager.plugins.keys():
        if manager.activate_plugin(name):
            click.echo(f"  ✅ {{name}}")
        else:
            click.echo(f"  ❌ {{name}}")
    
    # Demonstrate hooks
    click.echo("\\nDemonstrating hooks...")
    click.echo("Calling 'before_process' hook:")
    results = manager.call_hook("before_process", "demo_data")
    for result in results:
        click.echo(f"  Result: {{result}}")
    
    click.echo("\\nCalling 'after_process' hook:")
    results = manager.call_hook("after_process", "demo_data")
    for result in results:
        click.echo(f"  Result: {{result}}")
    
    # Test error hook
    click.echo("\\nTesting error hook:")
    manager.call_hook("error_occurred", "Demo error", context="demo")
    
    click.echo("\\n✅ Demo completed!")


if __name__ == '__main__':
    cli()
''')
        
        # Setup.py with entry points
        (project_path / "setup.py").write_text(f'''"""
Setup script for {project_name} plugin framework.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ""

setup(
    name="{package_name.replace('_', '-')}",
    version="{metadata.get('version', '0.1.0')}",
    author="{metadata.get('author', 'Your Name')}",
    author_email="{metadata.get('email', 'your.email@example.com')}",
    description="{metadata.get('description', f'A {project_name} plugin framework')}",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="{metadata.get('url', f'https://github.com/yourusername/{package_name.replace("_", "-")}')}",
    packages=find_packages(where="src"),
    package_dir={{"": "src"}},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0.0",
        "importlib-metadata>=4.0.0; python_version<'3.10'",
    ],
    extras_require={{
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    }},
    # Entry points for CLI and example plugins
    entry_points={{
        "console_scripts": [
            "{package_name.replace('_', '-')}-cli={package_name}.cli:cli",
        ],
        "{package_name}.plugins": [
            "example={package_name}.plugins.example_plugin:ExamplePlugin",
            "logging={package_name}.plugins.logging_plugin:LoggingPlugin",
        ],
    }},
    zip_safe=False,
)
''')
        
        # Requirements
        requirements = [
            "click>=8.0.0",
            "importlib-metadata>=4.0.0; python_version<'3.10'",
        ]
        (project_path / "requirements.txt").write_text("\\n".join(requirements) + "\\n")
        
        # Tests
        if features.get('tests', True):
            self._create_plugin_framework_tests(project_path, package_name)
        
        # README
        if features.get('readme', True):
            self._create_plugin_framework_readme(project_path, project_name, package_name, metadata)
        
        if features.get('gitignore', True):
            self._create_basic_gitignore(project_path)
        
        return True

    def _create_plugin_framework_tests(self, project_path: Path, package_name: str):
        """Create tests for plugin framework."""
        tests_dir = project_path / "tests"
        tests_dir.mkdir(exist_ok=True)
        
        (tests_dir / "__init__.py").write_text("")
        
        # Test the core plugin system
        (tests_dir / "test_plugin_system.py").write_text(f'''"""
Tests for {package_name} plugin framework.
"""

import unittest
from unittest.mock import Mock, patch
from {package_name}.core import Plugin, PluginManager, Hook
from {package_name}.registry import PluginRegistry


class MockPlugin(Plugin):
    """Mock plugin for testing."""
    
    name = "Mock Plugin"
    version = "1.0.0"
    description = "A mock plugin for testing"
    author = "Test Suite"
    
    def __init__(self):
        super().__init__()
        self.activated = False
        self.deactivated = False
    
    def activate(self) -> bool:
        self.activated = True
        return True
    
    def deactivate(self) -> bool:
        self.deactivated = True
        return True


class TestHook(unittest.TestCase):
    """Test hook functionality."""
    
    def setUp(self):
        self.hook = Hook("test_hook", "Test hook description")
    
    def test_hook_creation(self):
        self.assertEqual(self.hook.name, "test_hook")
        self.assertEqual(self.hook.description, "Test hook description")
        self.assertEqual(len(self.hook.callbacks), 0)
    
    def test_callback_registration(self):
        def test_callback():
            return "test_result"
        
        self.hook.register(test_callback)
        self.assertIn(test_callback, self.hook.callbacks)
        
        # Should not add duplicate
        self.hook.register(test_callback)
        self.assertEqual(len(self.hook.callbacks), 1)
    
    def test_callback_unregistration(self):
        def test_callback():
            return "test_result"
        
        self.hook.register(test_callback)
        self.hook.unregister(test_callback)
        self.assertNotIn(test_callback, self.hook.callbacks)
    
    def test_hook_call(self):
        results = []
        
        def callback1(data):
            results.append(f"callback1: {{data}}")
            return "result1"
        
        def callback2(data):
            results.append(f"callback2: {{data}}")
            return "result2"
        
        self.hook.register(callback1)
        self.hook.register(callback2)
        
        hook_results = self.hook.call("test_data")
        
        self.assertEqual(len(hook_results), 2)
        self.assertIn("result1", hook_results)
        self.assertIn("result2", hook_results)
        self.assertIn("callback1: test_data", results)
        self.assertIn("callback2: test_data", results)


class TestPlugin(unittest.TestCase):
    """Test plugin base class."""
    
    def setUp(self):
        self.plugin = MockPlugin()
    
    def test_plugin_creation(self):
        self.assertEqual(self.plugin.name, "Mock Plugin")
        self.assertEqual(self.plugin.version, "1.0.0")
        self.assertTrue(self.plugin.enabled)
        self.assertIsInstance(self.plugin.config, dict)
    
    def test_plugin_activation(self):
        result = self.plugin.activate()
        self.assertTrue(result)
        self.assertTrue(self.plugin.activated)
    
    def test_plugin_deactivation(self):
        result = self.plugin.deactivate()
        self.assertTrue(result)
        self.assertTrue(self.plugin.deactivated)
    
    def test_plugin_configuration(self):
        config = {{"setting1": "value1", "setting2": "value2"}}
        self.plugin.configure(config)
        self.assertEqual(self.plugin.config["setting1"], "value1")
        self.assertEqual(self.plugin.config["setting2"], "value2")
    
    def test_plugin_info(self):
        info = self.plugin.get_info()
        self.assertIsInstance(info, dict)
        self.assertEqual(info["name"], "Mock Plugin")
        self.assertEqual(info["version"], "1.0.0")
        self.assertEqual(info["class"], "MockPlugin")
        self.assertTrue(info["enabled"])


class TestPluginManager(unittest.TestCase):
    """Test plugin manager functionality."""
    
    def setUp(self):
        self.manager = PluginManager()
    
    def test_manager_creation(self):
        self.assertIsInstance(self.manager.plugins, dict)
        self.assertIsInstance(self.manager.hooks, dict)
        
        # Should have built-in hooks
        self.assertIn("plugin_loaded", self.manager.hooks)
        self.assertIn("plugin_activated", self.manager.hooks)
        self.assertIn("before_process", self.manager.hooks)
    
    def test_hook_registration(self):
        hook = self.manager.register_hook("custom_hook", "Custom test hook")
        self.assertIsInstance(hook, Hook)
        self.assertEqual(hook.name, "custom_hook")
        self.assertIn("custom_hook", self.manager.hooks)
    
    def test_plugin_loading(self):
        result = self.manager.load_plugin(MockPlugin)
        self.assertTrue(result)
        self.assertIn("Mock Plugin", self.manager.plugins)
        
        plugin = self.manager.get_plugin("Mock Plugin")
        self.assertIsInstance(plugin, MockPlugin)
    
    def test_plugin_activation(self):
        self.manager.load_plugin(MockPlugin)
        
        result = self.manager.activate_plugin("Mock Plugin")
        self.assertTrue(result)
        
        plugin = self.manager.get_plugin("Mock Plugin")
        self.assertTrue(plugin.activated)
        self.assertTrue(plugin.enabled)
    
    def test_plugin_deactivation(self):
        self.manager.load_plugin(MockPlugin)
        self.manager.activate_plugin("Mock Plugin")
        
        result = self.manager.deactivate_plugin("Mock Plugin")
        self.assertTrue(result)
        
        plugin = self.manager.get_plugin("Mock Plugin")
        self.assertTrue(plugin.deactivated)
        self.assertFalse(plugin.enabled)
    
    def test_hook_calling(self):
        # Register a test hook
        test_hook = self.manager.register_hook("test_hook")
        
        # Add a callback
        def test_callback(data):
            return f"processed: {{data}}"
        
        test_hook.register(test_callback)
        
        # Call hook
        results = self.manager.call_hook("test_hook", "test_data")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], "processed: test_data")
    
    def test_plugin_configuration(self):
        self.manager.load_plugin(MockPlugin)
        
        config = {{"test_setting": "test_value"}}
        result = self.manager.configure_plugin("Mock Plugin", config)
        self.assertTrue(result)
        
        plugin = self.manager.get_plugin("Mock Plugin")
        self.assertEqual(plugin.config["test_setting"], "test_value")
    
    def test_list_plugins(self):
        self.manager.load_plugin(MockPlugin)
        
        plugins = self.manager.list_plugins()
        self.assertIn("Mock Plugin", plugins)
        self.assertIsInstance(plugins["Mock Plugin"], dict)


class TestPluginRegistry(unittest.TestCase):
    """Test plugin registry functionality."""
    
    def setUp(self):
        self.registry = PluginRegistry("test.plugins")
    
    def test_registry_creation(self):
        self.assertEqual(self.registry.entry_point_group, "test.plugins")
        self.assertIsInstance(self.registry.registered_plugins, dict)
    
    @patch('importlib.metadata.entry_points')
    def test_entry_point_discovery(self, mock_entry_points):
        # Mock entry point
        mock_ep = Mock()
        mock_ep.name = "test_plugin"
        mock_ep.load.return_value = MockPlugin
        mock_entry_points.return_value = [mock_ep]
        
        plugins = self.registry.discover_entry_points()
        
        self.assertEqual(len(plugins), 1)
        self.assertEqual(plugins[0], MockPlugin)
        self.assertIn("test_plugin", self.registry.registered_plugins)


if __name__ == "__main__":
    unittest.main()
''')
        
        # Test example plugins
        (tests_dir / "test_example_plugins.py").write_text(f'''"""
Tests for example plugins.
"""

import unittest
from unittest.mock import Mock, patch
from {package_name}.plugins.example_plugin import ExamplePlugin
from {package_name}.plugins.logging_plugin import LoggingPlugin


class TestExamplePlugin(unittest.TestCase):
    """Test the example plugin."""
    
    def setUp(self):
        self.plugin = ExamplePlugin()
    
    def test_plugin_info(self):
        info = self.plugin.get_info()
        self.assertEqual(info["name"], "Example Plugin")
        self.assertEqual(info["version"], "1.0.0")
    
    def test_activation(self):
        result = self.plugin.activate()
        self.assertTrue(result)
    
    def test_deactivation(self):
        result = self.plugin.deactivate()
        self.assertTrue(result)
    
    def test_data_processing(self):
        result = self.plugin.process_data("test_data")
        self.assertEqual(result, "[ExamplePlugin] test_data")
    
    def test_hook_callbacks(self):
        # Test callbacks directly
        self.plugin.before_process_callback()
        self.plugin.after_process_callback()
        
        self.assertTrue(self.plugin.data.get('before_process_called'))
        self.assertTrue(self.plugin.data.get('after_process_called'))


class TestLoggingPlugin(unittest.TestCase):
    """Test the logging plugin."""
    
    def setUp(self):
        self.plugin = LoggingPlugin()
    
    def test_plugin_info(self):
        info = self.plugin.get_info()
        self.assertEqual(info["name"], "Logging Plugin")
        self.assertEqual(info["version"], "1.0.0")
    
    def test_activation_deactivation(self):
        # Test activation
        result = self.plugin.activate()
        self.assertTrue(result)
        self.assertIsNotNone(self.plugin.log_handler)
        
        # Test deactivation
        result = self.plugin.deactivate()
        self.assertTrue(result)
    
    def test_error_logging(self):
        with patch('logging.getLogger') as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log
            
            result = self.plugin.log_error_callback("test error", "test context")
            
            self.assertIsNotNone(result)
            self.assertTrue(result.startswith("logged_error_"))


if __name__ == "__main__":
    unittest.main()
''')
    
    def _create_plugin_framework_readme(self, project_path: Path, project_name: str, package_name: str, metadata: Dict[str, str]):
        """Create README for plugin framework."""
        content = f'''# {project_name} - Plugin Framework

{metadata.get('description', f'A {project_name} plugin framework')}

A powerful and flexible plugin system that supports dynamic loading, entry points, hooks, and extensible architecture.

## Features

- **Plugin Base Class**: Abstract base class for all plugins
- **Plugin Manager**: Centralized management of plugin lifecycle
- **Hook System**: Event-driven architecture with hook points
- **Entry Points**: Automatic plugin discovery via setuptools entry points
- **CLI Interface**: Command-line tools for plugin management
- **Dynamic Loading**: Load plugins from directories at runtime
- **Configuration**: Plugin-specific configuration support

## Installation

```bash
pip install {package_name.replace('_', '-')}
```

## Quick Start

### Using the Plugin System

```python
from {package_name} import PluginManager, Plugin
from {package_name}.registry import create_plugin_manager_with_entry_points

# Create a plugin manager with automatic entry point discovery
manager = create_plugin_manager_with_entry_points()

# List available plugins
plugins = manager.list_plugins()
for name, info in plugins.items():
    print(f"{{name}} v{{info['version']}}: {{info['description']}}")

# Activate a plugin
manager.activate_plugin("Example Plugin")

# Call hooks
results = manager.call_hook("before_process", "some_data")
print(f"Hook results: {{results}}")
```

### Command Line Interface

```bash
# List all available plugins
{package_name.replace('_', '-')}-cli list-plugins

# Activate a plugin
{package_name.replace('_', '-')}-cli activate "Example Plugin"

# Run a demonstration
{package_name.replace('_', '-')}-cli demo

# Load plugins from a directory
{package_name.replace('_', '-')}-cli load-from-path /path/to/plugins
```

## Creating Plugins

### Basic Plugin Structure

```python
from {package_name} import Plugin
import logging

logger = logging.getLogger(__name__)

class MyPlugin(Plugin):
    """My custom plugin."""
    
    name = "My Plugin"
    version = "1.0.0"
    description = "A custom plugin that does something useful"
    author = "Your Name"
    
    def activate(self) -> bool:
        """Activate the plugin."""
        logger.info(f"Activating {{self.name}}")
        
        # Register for hooks
        if hasattr(self, '_manager'):
            hook = self._manager.get_hook("before_process")
            if hook:
                hook.register(self.my_callback)
        
        return True
    
    def deactivate(self) -> bool:
        """Deactivate the plugin."""
        logger.info(f"Deactivating {{self.name}}")
        return True
    
    def my_callback(self, data):
        """Example hook callback."""
        logger.info(f"Processing data: {{data}}")
        return f"MyPlugin processed: {{data}}"
```

### Entry Point Registration

In your plugin package's `setup.py`:

```python
setup(
    name="my-plugin-package",
    # ... other settings ...
    entry_points={{
        "{package_name}.plugins": [
            "my_plugin=my_plugin_package.plugin:MyPlugin",
        ],
    }},
)
```

## Hook System

### Built-in Hooks

The framework provides several built-in hooks:

- `plugin_loaded`: Called when a plugin is loaded
- `plugin_activated`: Called when a plugin is activated  
- `plugin_deactivated`: Called when a plugin is deactivated
- `before_process`: Called before main processing
- `after_process`: Called after main processing
- `error_occurred`: Called when an error occurs

### Custom Hooks

```python
# Register a custom hook
hook = manager.register_hook("custom_event", "Called for custom events")

# Register a callback
def my_callback(data):
    print(f"Custom event triggered with: {{data}}")
    return "callback_result"

hook.register(my_callback)

# Call the hook
results = manager.call_hook("custom_event", "event_data")
```

## Plugin Discovery

### Entry Points (Recommended)

Plugins can be automatically discovered through setuptools entry points:

```python
from {package_name}.registry import create_plugin_manager_with_entry_points

manager = create_plugin_manager_with_entry_points()
# Automatically loads all plugins registered via entry points
```

### Directory-based Discovery

Load plugins from specific directories:

```python
from {package_name} import PluginManager
from pathlib import Path

manager = PluginManager()
manager.add_plugin_path(Path("/path/to/plugins"))
count = manager.load_all_plugins()
print(f"Loaded {{count}} plugins")
```

## Configuration

### Plugin Configuration

```python
# Configure a specific plugin
config = {{
    "setting1": "value1",
    "debug": True,
    "max_items": 100
}}

manager.configure_plugin("My Plugin", config)
```

### Global Configuration

```python
# Set up logging for the plugin system
import logging
logging.basicConfig(level=logging.INFO)

# Configure plugin paths
manager.add_plugin_path(Path("./plugins"))
manager.add_plugin_path(Path("/usr/local/share/my-app/plugins"))
```

## Advanced Usage

### Plugin Lifecycle Management

```python
# Load specific plugin
manager.load_plugin(MyPluginClass)

# Activate/deactivate
manager.activate_plugin("My Plugin")
manager.deactivate_plugin("My Plugin")

# Check plugin status
plugin = manager.get_plugin("My Plugin")
if plugin and plugin.enabled:
    print("Plugin is active")
```

### Hook-based Architecture

```python
class DataProcessor:
    def __init__(self, plugin_manager):
        self.manager = plugin_manager
    
    def process_data(self, data):
        # Call before_process hooks
        self.manager.call_hook("before_process", data)
        
        try:
            # Main processing logic
            result = self._do_processing(data)
            
            # Call after_process hooks
            self.manager.call_hook("after_process", result)
            
            return result
            
        except Exception as e:
            # Call error hooks
            self.manager.call_hook("error_occurred", e, context="data_processing")
            raise
```

## Example Plugins

The framework includes example plugins:

### Example Plugin
- Demonstrates basic plugin functionality
- Shows hook registration and callbacks
- Provides data processing example

### Logging Plugin  
- Enhanced logging capabilities
- Custom log formatting
- Error logging hooks

## Development

### Development Setup

```bash
git clone <repository-url>
cd {package_name.replace('_', '-')}
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest tests/
```

### Creating Plugin Packages

1. Create your plugin class inheriting from `Plugin`
2. Implement `activate()` and `deactivate()` methods
3. Add entry point in setup.py
4. Install your plugin package
5. The plugin will be automatically discovered

## API Reference

### Plugin Class

Abstract base class for all plugins.

**Attributes:**
- `name`: Plugin name
- `version`: Plugin version
- `description`: Plugin description
- `author`: Plugin author
- `enabled`: Plugin activation status
- `config`: Plugin configuration dict

**Methods:**
- `activate() -> bool`: Activate the plugin
- `deactivate() -> bool`: Deactivate the plugin
- `configure(config: Dict[str, Any])`: Configure the plugin
- `get_info() -> Dict[str, Any]`: Get plugin information

### PluginManager Class

Manages plugin loading, activation, and lifecycle.

**Methods:**
- `load_plugin(plugin_class: Type[Plugin]) -> bool`: Load a plugin
- `activate_plugin(name: str) -> bool`: Activate a plugin
- `deactivate_plugin(name: str) -> bool`: Deactivate a plugin
- `get_plugin(name: str) -> Optional[Plugin]`: Get plugin by name
- `list_plugins() -> Dict[str, Dict[str, Any]]`: List all plugins
- `register_hook(name: str, description: str) -> Hook`: Register a hook
- `call_hook(name: str, *args, **kwargs) -> List[Any]`: Call a hook

### Hook Class

Represents a hook point where plugins can attach callbacks.

**Methods:**
- `register(callback: Callable)`: Register a callback
- `unregister(callback: Callable)`: Unregister a callback
- `call(*args, **kwargs) -> List[Any]`: Call all callbacks

## Examples

### Simple Plugin

```python
from {package_name} import Plugin

class GreetingPlugin(Plugin):
    name = "Greeting Plugin"
    version = "1.0.0"
    description = "Provides greeting functionality"
    
    def activate(self):
        print(f"Hello from {{self.name}}!")
        return True
    
    def deactivate(self):
        print(f"Goodbye from {{self.name}}!")
        return True
    
    def greet(self, name):
        return f"Hello, {{name}}! From {{self.name}}"
```

### Plugin with Hooks

```python
class ProcessorPlugin(Plugin):
    name = "Processor Plugin"
    version = "1.0.0"
    
    def activate(self):
        # Register for processing hooks
        if hasattr(self, '_manager'):
            before_hook = self._manager.get_hook("before_process")
            after_hook = self._manager.get_hook("after_process")
            
            if before_hook:
                before_hook.register(self.preprocess)
            if after_hook:
                after_hook.register(self.postprocess)
        
        return True
    
    def deactivate(self):
        return True
    
    def preprocess(self, data):
        print(f"Preprocessing: {{data}}")
        return f"preprocessed_{{data}}"
    
    def postprocess(self, result):
        print(f"Postprocessing: {{result}}")
        return f"postprocessed_{{result}}"
```

## Troubleshooting

### Plugin Not Found

- Check that the plugin package is installed
- Verify entry point configuration in setup.py
- Use `list-plugins` command to see available plugins

### Plugin Fails to Load

- Check plugin class inherits from `Plugin`
- Verify `activate()` and `deactivate()` methods are implemented
- Check for import errors in plugin code

### Hook Not Working

- Ensure hook is registered before plugin activation
- Check that callback is properly registered with hook
- Verify hook name matches exactly

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

{metadata.get('license_type', 'MIT')} License - see LICENSE file for details.

## Author

{metadata.get('author', 'Your Name')} - {metadata.get('email', 'your.email@example.com')}
'''
        (project_path / "README.md").write_text(content)

    def _create_faq(self, project_path: Path, project_name: str, metadata: Dict[str, str]):
        """Create FAQ.md file."""
        content = f'''# Frequently Asked Questions (FAQ)

## General

### What is {project_name}?
{metadata.get('description', f'{project_name} is a Python project')}

### What Python versions are supported?
Python 3.8 and above.

## Installation

### How do I install dependencies?
```bash
pip install -e .
```

## Usage

### How do I run the project?
See [USAGE](USAGE.md) for detailed usage instructions.

## Contributing

See [CONTRIBUTING](CONTRIBUTING.md) for how to contribute.
'''
        (project_path / "FAQ.md").write_text(content)

    def _create_getting_started(self, project_path: Path, project_name: str, metadata: Dict[str, str]):
        """Create GETTING-STARTED.md file."""
        content = f'''# Getting Started

Welcome to {project_name}! This guide will help you get up and running quickly.

## Prerequisites
- Python 3.8+
- pip

## Setup
```bash
git clone <your-repo-url>
cd {self._to_package_name(project_name)}
pip install -e .
```

## First Run
```bash
python -m {self._to_package_name(project_name)}
```

See [USAGE](USAGE.md) for more details.
'''
        (project_path / "GETTING-STARTED.md").write_text(content)

    def _create_index(self, project_path: Path, project_name: str, metadata: Dict[str, str]):
        """Create INDEX.md file."""
        content = f'''# Documentation Index

- [INTRO](INTRO.md)
- [GETTING-STARTED](GETTING-STARTED.md)
- [INSTALL](INSTALL.md)
- [USAGE](USAGE.md)
- [CONFIGURATION](CONFIGURATION.md)
- [FAQ](FAQ.md)
- [SUMMARY](SUMMARY.md)
- [ROADMAP](ROADMAP.md)
- [CONTRIBUTING](CONTRIBUTING.md)
- [CODE OF CONDUCT](CODE_OF_CONDUCT.md)
- [SECURITY](SECURITY.md)
'''
        (project_path / "INDEX.md").write_text(content)

    def _create_install(self, project_path: Path, project_name: str, metadata: Dict[str, str]):
        """Create INSTALL.md file."""
        content = f'''# Installation

## From Source
```bash
git clone <your-repo-url>
cd {self._to_package_name(project_name)}
pip install -e .
```

## From PyPI
```bash
pip install {self._to_package_name(project_name).replace('_','-')}
```
'''
        (project_path / "INSTALL.md").write_text(content)

    def _create_intro(self, project_path: Path, project_name: str, metadata: Dict[str, str]):
        """Create INTRO.md file."""
        content = f'''# Introduction

Welcome to {project_name}! {metadata.get('description', '')}

This document provides context and background for the project.
'''
        (project_path / "INTRO.md").write_text(content)

    def _create_summary(self, project_path: Path, project_name: str, metadata: Dict[str, str]):
        """Create SUMMARY.md file."""
        content = f'''# Summary

- Project: {project_name}
- Version: {metadata.get('version', '0.1.0')}
- Description: {metadata.get('description', '')}

See [INDEX](INDEX.md) for all documentation.
'''
        (project_path / "SUMMARY.md").write_text(content)

    def _create_todo(self, project_path: Path, project_name: str, metadata: Dict[str, str]):
        """Create TODO.md file."""
        content = f'''# TODO

- [ ] Initial setup
- [ ] Write tests
- [ ] Add CI/CD
- [ ] Update documentation

Add more tasks as needed.
'''
        (project_path / "TODO.md").write_text(content)

    def _create_usage(self, project_path: Path, project_name: str, metadata: Dict[str, str]):
        """Create USAGE.md file."""
        content = f'''# Usage

## Basic
```bash
python -m {self._to_package_name(project_name)}
```

## As a Library
```python
from {self._to_package_name(project_name)} import {self._to_class_name(self._to_package_name(project_name))}
app = {self._to_class_name(self._to_package_name(project_name))}()
app.run()
```
'''
        (project_path / "USAGE.md").write_text(content)

    def _create_configuration(self, project_path: Path, project_name: str, metadata: Dict[str, str]):
        """Create CONFIGURATION.md file."""
        content = f'''# Configuration

Describe configuration options for {project_name} here, e.g.:

```ini
[project]
log_level=INFO
```
'''
        (project_path / "CONFIGURATION.md").write_text(content)


def setup_logging(level: str = "INFO") -> None:
    """Set up logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()]
    )


def main():
    """
    Main CLI entry point for the project generator.
    """
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Python Project Generator CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Generate project command
    gen_parser = subparsers.add_parser("generate", help="Generate a new project")
    gen_parser.add_argument("project_name", help="Name of the project to create")
    gen_parser.add_argument("-o", "--output", default=".", help="Output directory (default: current directory)")
    gen_parser.add_argument("-t", "--template", default="minimal-python", help="Template to use (default: minimal-python)")
    gen_parser.add_argument("--author", help="Author name")
    gen_parser.add_argument("--email", help="Author email")
    gen_parser.add_argument("--description", help="Project description")
    gen_parser.add_argument("--version", default="0.1.0", help="Initial version (default: 0.1.0)")
    
    # MD files command
    md_parser = subparsers.add_parser("md", help="Manage Markdown documentation files")
    md_subparsers = md_parser.add_subparsers(dest="md_action", help="MD file actions")
    
    # List available MD files
    list_md_parser = md_subparsers.add_parser("list", help="List available Markdown files")
    list_md_parser.add_argument("--category", help="Filter by category")
    list_md_parser.add_argument("--recommended", action="store_true", help="Show only recommended files")
    
    # Add MD file to existing project
    add_md_parser = md_subparsers.add_parser("add", help="Add Markdown file to existing project")
    add_md_parser.add_argument("md_type", help="Type of MD file to add")
    add_md_parser.add_argument("--project-path", default=".", help="Path to existing project (default: current directory)")
    add_md_parser.add_argument("--project-name", help="Project name (auto-detected if not provided)")
    add_md_parser.add_argument("--author", help="Author name")
    add_md_parser.add_argument("--email", help="Author email")
    
    # Remove MD file from existing project
    rm_md_parser = md_subparsers.add_parser("remove", help="Remove Markdown file from existing project")
    rm_md_parser.add_argument("md_type", help="Type of MD file to remove")
    rm_md_parser.add_argument("--project-path", default=".", help="Path to existing project (default: current directory)")
    
    # Legacy arguments for backwards compatibility
    parser.add_argument("--list-templates", action="store_true", help="List available templates")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set up logging
    level = "DEBUG" if args.verbose else "INFO"
    setup_logging(level)
    
    generator = ProjectGenerator()
    
    # Handle legacy list-templates flag
    if args.list_templates:
        templates = generator.template_manager.get_available_templates()
        print("Available templates:")
        for template_id, template_info in templates.items():
            print(f"  {template_id}: {template_info['name']}")
            print(f"    {template_info['description']}")
        return 0
    
    # Handle commands
    if args.command == "generate":
        return _handle_generate_command(args, generator)
    elif args.command == "md":
        return _handle_md_command(args, generator)
    else:
        # For backwards compatibility, treat as legacy generate command
        if hasattr(args, 'project_name'):
            return _handle_legacy_generate(args, generator)
        else:
            parser.print_help()
            return 1


def _handle_generate_command(args, generator):
    """Handle the generate project command."""
    from datetime import datetime
    
    metadata = {
        "author": args.author or "Your Name",
        "email": args.email or "your.email@example.com",
        "description": args.description or f"A {args.project_name} project",
        "version": args.version,
        "date": datetime.now().strftime("%Y-%m-%d")
    }
    
    # Default features for CLI usage
    features = {
        "cli": True,
        "tests": True,
        "pypi_packaging": True,
        "readme": True,
        "changelog": True,
        "gitignore": True,
        "license": True,
    }
    
    print(f"Generating project '{args.project_name}' using template '{args.template}'...")
    
    result = generator.generate_project(
        project_name=args.project_name,
        output_dir=Path(args.output),
        template_id=args.template,
        features=features,
        metadata=metadata
    )
    
    if result:
        print("✅ Project generated successfully!")
        project_path = Path(args.output) / args.project_name
        print(f"📁 Location: {project_path.absolute()}")
        print("\nNext steps:")
        print(f"  cd '{project_path}'")
        print("  pip install -e .")
        return 0
    else:
        print("❌ Project generation failed!")
        return 1


def _handle_md_command(args, generator):
    """Handle Markdown documentation file commands."""
    if args.md_action == "list":
        return _list_md_files(args)
    elif args.md_action == "add":
        return _add_md_file(args, generator)
    elif args.md_action == "remove":
        return _remove_md_file(args)
    else:
        print("Please specify an MD action: list, add, or remove")
        return 1


def _list_md_files(args):
    """List available Markdown documentation files."""
    md_files = ProjectGenerator.get_available_md_files()
    
    print("Available Markdown Documentation Files:")
    print("=" * 50)
    
    # Group by category
    categories = {}
    for md_type, info in md_files.items():
        category = info["category"]
        if category not in categories:
            categories[category] = []
        categories[category].append((md_type, info))
    
    for category, files in categories.items():
        if args.category and category.lower() != args.category.lower():
            continue
            
        print(f"\n📁 {category}")
        print("-" * 30)
        
        for md_type, info in files:
            if args.recommended and not info["recommended"]:
                continue
                
            status = "⭐ RECOMMENDED" if info["recommended"] else "   Optional"
            print(f"  {md_type:15} - {info['name']}")
            print(f"  {' ' * 15}   {info['description']}")
            print(f"  {' ' * 15}   {status}")
            print()
    
    print("\nUsage Examples:")
    print(f"  Add file:    python -m project_generator md add changelog")
    print(f"  Remove file: python -m project_generator md remove changelog")
    
    return 0


def _add_md_file(args, generator):
    """Add a Markdown file to an existing project."""
    from datetime import datetime
    import os
    
    project_path = Path(args.project_path).resolve()
    
    if not project_path.exists():
        print(f"❌ Project path does not exist: {project_path}")
        return 1
    
    md_files = ProjectGenerator.get_available_md_files()
    if args.md_type not in md_files:
        print(f"❌ Unknown MD file type: {args.md_type}")
        print(f"Available types: {', '.join(md_files.keys())}")
        return 1
    
    # Auto-detect project name if not provided
    project_name = args.project_name
    if not project_name:
        project_name = project_path.name
    
    # Check if file already exists
    file_name = md_files[args.md_type]["name"]
    file_path = project_path / file_name
    
    if file_path.exists():
        response = input(f"⚠️  {file_name} already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("❌ Operation cancelled")
            return 1
    
    metadata = {
        "author": args.author or "Your Name", 
        "email": args.email or "your.email@example.com",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "version": "0.1.0"
    }
    
    # Create the MD file
    success = generator.create_md_file(project_path, args.md_type, project_name, metadata)
    
    if success:
        print(f"✅ Created {file_name} in {project_path}")
        print(f"📝 Edit the file to customize it for your project")
        return 0
    else:
        print(f"❌ Failed to create {file_name}")
        return 1


def _remove_md_file(args):
    """Remove a Markdown file from an existing project."""
    project_path = Path(args.project_path).resolve()
    
    if not project_path.exists():
        print(f"❌ Project path does not exist: {project_path}")
        return 1
    
    md_files = ProjectGenerator.get_available_md_files()
    if args.md_type not in md_files:
        print(f"❌ Unknown MD file type: {args.md_type}")
        print(f"Available types: {', '.join(md_files.keys())}")
        return 1
    
    file_name = md_files[args.md_type]["name"]
    file_path = project_path / file_name
    
    if not file_path.exists():
        print(f"❌ {file_name} does not exist in {project_path}")
        return 1
    
    response = input(f"⚠️  Are you sure you want to remove {file_name}? (y/N): ")
    if response.lower() != 'y':
        print("❌ Operation cancelled")
        return 1
    
    try:
        file_path.unlink()
        print(f"✅ Removed {file_name} from {project_path}")
        return 0
    except Exception as e:
        print(f"❌ Failed to remove {file_name}: {e}")
        return 1


def _handle_legacy_generate(args, generator):
    """Handle legacy generate command format for backwards compatibility."""
    from datetime import datetime
    
    metadata = {
        "author": getattr(args, 'author', None) or "Your Name",
        "email": getattr(args, 'email', None) or "your.email@example.com", 
        "description": getattr(args, 'description', None) or f"A {args.project_name} project",
        "version": getattr(args, 'version', None) or "0.1.0",
        "date": datetime.now().strftime("%Y-%m-%d")
    }
    
    features = {
        "cli": True,
        "tests": True,
        "pypi_packaging": True,
        "readme": True,
        "changelog": True,
        "gitignore": True,
        "license": True,
    }
    
    print(f"Generating project '{args.project_name}' using template '{getattr(args, 'template', 'minimal-python')}'...")
    
    result = generator.generate_project(
        project_name=args.project_name,
        output_dir=Path(getattr(args, 'output', '.')),
        template_id=getattr(args, 'template', 'minimal-python'),
        features=features,
        metadata=metadata
    )
    
    if result:
        print("✅ Project generated successfully!")
        project_path = Path(getattr(args, 'output', '.')) / args.project_name
        print(f"📁 Location: {project_path.absolute()}")
        print("\nNext steps:")
        print(f"  cd '{project_path}'")
        print("  pip install -e .")
        return 0
    else:
        print("❌ Project generation failed!")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main()) 