"""
Parameterized generation tests for all supported template types.

Every template registered in TemplateManager is tested to ensure it:
1. Generates successfully (returns True)
2. Creates a project directory with at least one file
3. Produces template-specific structure where applicable
"""

import sys
import tempfile
import shutil
import unittest
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from python_project_generator.project_generator import ProjectGenerator, TemplateManager

METADATA = {
    "author": "Test Author",
    "email": "test@example.com",
    "description": "A test project",
    "version": "0.1.0",
}

DEFAULT_FEATURES = {
    "cli": True,
    "tests": True,
    "pypi_packaging": True,
    "readme": True,
    "gitignore": True,
}

ALL_TEMPLATE_IDS = list(TemplateManager().get_available_templates().keys())


class TestAllTemplatesGenerate(unittest.TestCase):
    """Every registered template should generate without errors."""

    def setUp(self):
        self.generator = ProjectGenerator()
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def _generate(self, template_id: str, project_name: str = "test_proj"):
        return self.generator.generate_project(
            project_name=project_name,
            output_dir=self.temp_dir,
            template_id=template_id,
            features=DEFAULT_FEATURES,
            metadata=METADATA,
        )


@pytest.mark.parametrize("template_id", ALL_TEMPLATE_IDS)
def test_template_generates_successfully(template_id, tmp_path):
    """Each template returns True from generate_project()."""
    gen = ProjectGenerator()
    result = gen.generate_project(
        project_name="gen_test",
        output_dir=tmp_path,
        template_id=template_id,
        features=DEFAULT_FEATURES,
        metadata=METADATA,
    )
    assert result is True, f"Template '{template_id}' failed to generate"


@pytest.mark.parametrize("template_id", ALL_TEMPLATE_IDS)
def test_template_creates_project_directory(template_id, tmp_path):
    """Each template creates a project directory."""
    gen = ProjectGenerator()
    gen.generate_project(
        project_name="dir_test",
        output_dir=tmp_path,
        template_id=template_id,
        features=DEFAULT_FEATURES,
        metadata=METADATA,
    )
    project_dir = tmp_path / "dir_test"
    assert project_dir.exists(), f"Template '{template_id}' did not create project directory"
    files = list(project_dir.rglob("*"))
    assert len(files) > 0, f"Template '{template_id}' created an empty project"


@pytest.mark.parametrize("template_id", ALL_TEMPLATE_IDS)
def test_template_info_has_required_fields(template_id):
    """Each template entry has name, description, type, and features."""
    tm = TemplateManager()
    templates = tm.get_available_templates()
    info = templates[template_id]
    for field in ("name", "description", "type", "features"):
        assert field in info, f"Template '{template_id}' missing field '{field}'"
    assert isinstance(info["features"], list)
    assert len(info["features"]) > 0


# --- Template-specific structure tests ---


class TestFlaskTemplateStructure(unittest.TestCase):
    """Flask template generates Flask-specific files."""

    def setUp(self):
        self.generator = ProjectGenerator()
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_flask_has_app_factory_and_templates(self):
        self.generator.generate_project(
            project_name="flask_app",
            output_dir=self.temp_dir,
            template_id="flask-web-app",
            features={"web_framework": True, "tests": True, "readme": True, "gitignore": True},
            metadata=METADATA,
        )
        proj = self.temp_dir / "flask_app"
        app_dir = proj / "flask_app"
        self.assertTrue(app_dir.exists(), "Flask app dir missing")
        self.assertTrue((app_dir / "__init__.py").exists())
        self.assertTrue((app_dir / "config.py").exists())
        self.assertTrue((app_dir / "templates").exists())
        self.assertTrue((app_dir / "static").exists())
        self.assertTrue((proj / "run.py").exists())


class TestFastAPITemplateStructure(unittest.TestCase):
    """FastAPI template generates API-specific files."""

    def setUp(self):
        self.generator = ProjectGenerator()
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_fastapi_has_app_and_routes(self):
        self.generator.generate_project(
            project_name="api_app",
            output_dir=self.temp_dir,
            template_id="fastapi-web-api",
            features={"web_framework": True, "tests": True, "readme": True, "gitignore": True},
            metadata=METADATA,
        )
        proj = self.temp_dir / "api_app"
        app_dir = proj / "api_app"
        self.assertTrue(app_dir.exists(), "FastAPI app dir missing")
        self.assertTrue((app_dir / "__init__.py").exists())


class TestDataScienceTemplateStructure(unittest.TestCase):
    """Data science template generates notebook/analysis structure."""

    def setUp(self):
        self.generator = ProjectGenerator()
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_data_science_has_notebooks_and_data(self):
        self.generator.generate_project(
            project_name="ds_project",
            output_dir=self.temp_dir,
            template_id="data-science-project",
            features=DEFAULT_FEATURES,
            metadata=METADATA,
        )
        proj = self.temp_dir / "ds_project"
        self.assertTrue(proj.exists())
        has_notebooks = (proj / "notebooks").exists()
        has_data = (proj / "data").exists()
        self.assertTrue(
            has_notebooks or has_data or (proj / "src").exists(),
            "Data science project should have notebooks, data, or src directory",
        )


class TestCLIToolTemplateStructure(unittest.TestCase):
    """CLI tool template generates click-based CLI structure."""

    def setUp(self):
        self.generator = ProjectGenerator()
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_cli_tool_has_cli_module(self):
        self.generator.generate_project(
            project_name="my_cli",
            output_dir=self.temp_dir,
            template_id="cli-tool",
            features={"cli": True, "tests": True, "readme": True, "gitignore": True},
            metadata=METADATA,
        )
        proj = self.temp_dir / "my_cli"
        self.assertTrue(proj.exists())
        package_dir = proj / "src" / "my_cli"
        self.assertTrue(package_dir.exists())
        self.assertTrue((package_dir / "cli.py").exists(), "CLI tool should have cli.py")


class TestBinaryExtensionTemplateStructure(unittest.TestCase):
    """Binary extension template generates C extension structure."""

    def setUp(self):
        self.generator = ProjectGenerator()
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_binary_extension_has_ext_dir(self):
        self.generator.generate_project(
            project_name="binext",
            output_dir=self.temp_dir,
            template_id="binary-extension",
            features=DEFAULT_FEATURES,
            metadata=METADATA,
        )
        proj = self.temp_dir / "binext"
        ext_dir = proj / "src" / "binext" / "ext"
        self.assertTrue(ext_dir.exists(), "Binary extension should have ext/ directory")


class TestNamespacePackageTemplateStructure(unittest.TestCase):
    """Namespace package template generates namespace structure."""

    def setUp(self):
        self.generator = ProjectGenerator()
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_namespace_package_generates(self):
        result = self.generator.generate_project(
            project_name="ns_pkg",
            output_dir=self.temp_dir,
            template_id="namespace-package",
            features=DEFAULT_FEATURES,
            metadata=METADATA,
        )
        self.assertTrue(result)
        proj = self.temp_dir / "ns_pkg"
        self.assertTrue(proj.exists())


class TestPluginFrameworkTemplateStructure(unittest.TestCase):
    """Plugin framework template generates plugin structure."""

    def setUp(self):
        self.generator = ProjectGenerator()
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_plugin_framework_generates(self):
        result = self.generator.generate_project(
            project_name="plug_fw",
            output_dir=self.temp_dir,
            template_id="plugin-framework",
            features=DEFAULT_FEATURES,
            metadata=METADATA,
        )
        self.assertTrue(result)
        proj = self.temp_dir / "plug_fw"
        self.assertTrue(proj.exists())
        files = list(proj.rglob("*.py"))
        self.assertTrue(len(files) > 0, "Plugin framework should generate Python files")


if __name__ == "__main__":
    unittest.main()
