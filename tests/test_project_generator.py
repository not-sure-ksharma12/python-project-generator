"""
Tests for the project generator module.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import sys


# Ensure src/ is on sys.path when running this file directly with `python tests/...`
_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from python_project_generator.project_generator import ProjectGenerator, TemplateManager, setup_logging


class TestTemplateManager(unittest.TestCase):
    """Test the TemplateManager class."""
    
    def setUp(self):
        """Set up test fixtures."""

        self.template_manager = TemplateManager()
    
    def test_get_available_templates(self):
        """Test getting available templates."""

        templates = self.template_manager.get_available_templates()
        self.assertIsInstance(templates, dict)
        self.assertIn("minimal-python", templates)
        self.assertIn("flask-web-app", templates)
        self.assertIn("fastapi-web-api", templates)
        
        # Check template structure
        for template_id, template_info in templates.items():
            self.assertIn("name", template_info)
            self.assertIn("description", template_info)
            self.assertIn("type", template_info)
            self.assertIn("features", template_info)


class TestProjectGenerator(unittest.TestCase):
    """Test the ProjectGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""

        self.generator = ProjectGenerator()
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Clean up test fixtures."""

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_generate_minimal_project(self):
        """Test generating a minimal project."""

        project_name = "test_project"
        features = {
            "cli": False,
            "tests": True,
            "pypi_packaging": True,
            "readme": True,
            "gitignore": True
        }
        metadata = {
            "author": "Test Author",
            "email": "test@example.com",
            "description": "A test project",
            "version": "0.1.0"
        }
        
        result = self.generator.generate_project(
            project_name=project_name,
            output_dir=self.temp_dir,
            template_id="minimal-python",
            features=features,
            metadata=metadata
        )
        
        self.assertTrue(result)
        
        # Check that project directory was created
        project_path = self.temp_dir / project_name
        self.assertTrue(project_path.exists())
        
        # Check basic structure
        src_dir = project_path / "src" / "test_project"
        self.assertTrue(src_dir.exists())
        self.assertTrue((src_dir / "__init__.py").exists())
        self.assertTrue((src_dir / "core.py").exists())
        
        # Check files based on features
        if features.get("tests"):
            self.assertTrue((project_path / "tests").exists())
        
        if features.get("readme"):
            self.assertTrue((project_path / "README.md").exists())
        
        if features.get("gitignore"):
            self.assertTrue((project_path / ".gitignore").exists())
    
    def test_generate_flask_project(self):
        """Test generating a Flask project."""

        project_name = "test_flask_app"
        features = {
            "web_framework": True,
            "tests": True,
            "readme": True,
            "gitignore": True
        }
        metadata = {
            "author": "Test Author",
            "email": "test@example.com",
            "description": "A test Flask app",
            "version": "0.1.0"
        }
        
        result = self.generator.generate_project(
            project_name=project_name,
            output_dir=self.temp_dir,
            template_id="flask-web-app",
            features=features,
            metadata=metadata
        )
        
        self.assertTrue(result)
        
        # Check that project directory was created
        project_path = self.temp_dir / project_name
        self.assertTrue(project_path.exists())
        
        # Check Flask-specific structure
        app_dir = project_path / "test_flask_app"
        self.assertTrue(app_dir.exists())
        self.assertTrue((app_dir / "__init__.py").exists())
        self.assertTrue((app_dir / "config.py").exists())
        self.assertTrue((app_dir / "main").exists())
        self.assertTrue((app_dir / "templates").exists())
        self.assertTrue((app_dir / "static").exists())
        self.assertTrue((project_path / "run.py").exists())
    
    def test_package_name_conversion(self):
        """Test package name conversion."""

        test_cases = [
            ("my-project", "my_project"),
            ("My Project", "my_project"),
            ("my_project", "my_project"),
            ("My-Complex_Project Name", "my_complex_project_name"),
        ]
        
        for input_name, expected in test_cases:
            result = self.generator._to_package_name(input_name)
            self.assertEqual(result, expected)
    
    def test_class_name_conversion(self):
        """Test class name conversion."""
        
        test_cases = [
            ("my_project", "MyProject"),
            ("simple", "Simple"),
            ("complex_package_name", "ComplexPackageName"),
        ]
        
        for input_name, expected in test_cases:
            result = self.generator._to_class_name(input_name)
            self.assertEqual(result, expected)
    
    def test_update_file_content_skips_path_outside_project(self):
        """Paths that resolve outside the project root must not be read or written (S2083)."""
        root = self.temp_dir / "proj"
        root.mkdir()
        outside_dir = self.temp_dir / "outside"
        outside_dir.mkdir()
        outside_file = outside_dir / "secret.txt"
        outside_file.write_text("skeleton-unchanged", encoding="utf-8")
        traversal_path = root / ".." / "outside" / "secret.txt"
        self.generator._update_file_content(
            root,
            traversal_path,
            {"skeleton-unchanged": "tampered"},
        )
        self.assertEqual(outside_file.read_text(encoding="utf-8"), "skeleton-unchanged")
    
    def test_update_file_content_updates_file_inside_project(self):
        """In-project paths still receive placeholder replacement."""
        root = self.temp_dir / "proj"
        root.mkdir()
        target = root / "setup.py"
        target.write_text("skeleton line", encoding="utf-8")
        self.generator._update_file_content(root, target, {"skeleton": "my_pkg"})
        self.assertEqual(target.read_text(encoding="utf-8"), "my_pkg line")
    
    def test_setup_logging_is_single_definition_and_runs(self):
        """setup_logging must be callable with no duplicate module-level definitions (#23)."""
        setup_logging()
        setup_logging("DEBUG")


if __name__ == "__main__":
    unittest.main() 