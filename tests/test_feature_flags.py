"""
Tests for feature-flag file generation and metadata placeholder replacement.

Verifies that each feature flag correctly enables/disables the corresponding
files, and that project metadata (author, email, version, etc.) is properly
injected into generated content.
"""

import re
import sys
import tempfile
import shutil
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from python_project_generator.project_generator import ProjectGenerator

METADATA = {
    "author": "Jane Doe",
    "email": "jane@example.com",
    "description": "A test project for feature flags",
    "version": "2.5.0",
}


class _FeatureFlagTestBase(unittest.TestCase):
    """Shared setup/teardown for feature-flag tests."""

    def setUp(self):
        self.generator = ProjectGenerator()
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_name = "flag_test_project"

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def _generate(self, features):
        result = self.generator.generate_project(
            project_name=self.project_name,
            output_dir=self.temp_dir,
            template_id="minimal-python",
            features=features,
            metadata=METADATA,
        )
        self.assertTrue(result, "generate_project should return True")
        return self.temp_dir / self.project_name


class TestFeatureFlagEnablesFile(_FeatureFlagTestBase):
    """Each feature flag creates its corresponding files when enabled."""

    def test_cli_flag_creates_cli_module(self):
        project = self._generate({"cli": True})
        package_dir = project / "src" / "flag_test_project"
        self.assertTrue(
            (package_dir / "cli.py").exists(),
            "cli=True should create cli.py",
        )

    def test_tests_flag_creates_test_directory(self):
        project = self._generate({"tests": True})
        self.assertTrue(
            (project / "tests").exists(),
            "tests=True should create tests/ directory",
        )

    def test_pypi_packaging_creates_setup_files(self):
        project = self._generate({"pypi_packaging": True})
        has_setup = (project / "setup.py").exists() or (project / "pyproject.toml").exists()
        self.assertTrue(has_setup, "pypi_packaging=True should create setup.py or pyproject.toml")

    def test_readme_flag_creates_readme(self):
        project = self._generate({"readme": True})
        self.assertTrue(
            (project / "README.md").exists(),
            "readme=True should create README.md",
        )

    def test_changelog_flag_creates_changelog(self):
        project = self._generate({"changelog": True})
        self.assertTrue(
            (project / "CHANGELOG.md").exists(),
            "changelog=True should create CHANGELOG.md",
        )

    def test_gitignore_flag_creates_gitignore(self):
        project = self._generate({"gitignore": True})
        self.assertTrue(
            (project / ".gitignore").exists(),
            "gitignore=True should create .gitignore",
        )

    def test_contributors_flag_creates_file(self):
        project = self._generate({"contributors": True})
        self.assertTrue(
            (project / "CONTRIBUTORS.md").exists(),
            "contributors=True should create CONTRIBUTORS.md",
        )

    def test_code_of_conduct_flag_creates_file(self):
        project = self._generate({"code_of_conduct": True})
        self.assertTrue(
            (project / "CODE_OF_CONDUCT.md").exists(),
            "code_of_conduct=True should create CODE_OF_CONDUCT.md",
        )

    def test_security_flag_creates_file(self):
        project = self._generate({"security": True})
        self.assertTrue(
            (project / "SECURITY.md").exists(),
            "security=True should create SECURITY.md",
        )


class TestFeatureFlagDisablesFile(_FeatureFlagTestBase):
    """Disabled feature flags should NOT create their corresponding files."""

    ALL_OFF = {
        "cli": False,
        "tests": False,
        "pypi_packaging": False,
        "readme": False,
        "changelog": False,
        "gitignore": False,
        "contributors": False,
        "code_of_conduct": False,
        "security": False,
    }

    def test_no_cli_when_disabled(self):
        project = self._generate(self.ALL_OFF)
        package_dir = project / "src" / "flag_test_project"
        self.assertFalse(
            (package_dir / "cli.py").exists(),
            "cli=False should not create cli.py",
        )

    def test_no_tests_when_disabled(self):
        project = self._generate(self.ALL_OFF)
        self.assertFalse(
            (project / "tests").exists(),
            "tests=False should not create tests/ directory",
        )

    def test_no_readme_when_disabled(self):
        project = self._generate(self.ALL_OFF)
        self.assertFalse(
            (project / "README.md").exists(),
            "readme=False should not create README.md",
        )

    def test_no_gitignore_when_disabled(self):
        project = self._generate(self.ALL_OFF)
        self.assertFalse(
            (project / ".gitignore").exists(),
            "gitignore=False should not create .gitignore",
        )


class TestFeatureCombinations(_FeatureFlagTestBase):
    """Feature combinations work correctly together."""

    def test_cli_and_tests_together(self):
        project = self._generate({"cli": True, "tests": True})
        package_dir = project / "src" / "flag_test_project"
        self.assertTrue((package_dir / "cli.py").exists())
        self.assertTrue((project / "tests").exists())

    def test_full_feature_set(self):
        all_on = {
            "cli": True,
            "tests": True,
            "pypi_packaging": True,
            "readme": True,
            "changelog": True,
            "gitignore": True,
            "contributors": True,
            "code_of_conduct": True,
            "security": True,
        }
        project = self._generate(all_on)
        package_dir = project / "src" / "flag_test_project"
        self.assertTrue((package_dir / "cli.py").exists())
        self.assertTrue((project / "tests").exists())
        self.assertTrue((project / "README.md").exists())
        self.assertTrue((project / "CHANGELOG.md").exists())
        self.assertTrue((project / ".gitignore").exists())
        self.assertTrue((project / "CONTRIBUTORS.md").exists())
        self.assertTrue((project / "CODE_OF_CONDUCT.md").exists())
        self.assertTrue((project / "SECURITY.md").exists())

    def test_packaging_without_readme(self):
        project = self._generate({"pypi_packaging": True, "readme": False})
        has_setup = (project / "setup.py").exists() or (project / "pyproject.toml").exists()
        self.assertTrue(has_setup)
        self.assertFalse((project / "README.md").exists())


class TestMetadataPlaceholderReplacement(_FeatureFlagTestBase):
    """Metadata values are injected into generated files correctly."""

    def _all_text_files(self, root: Path):
        """Yield (path, content) for every text file under root."""
        for p in root.rglob("*"):
            if p.is_file():
                try:
                    yield p, p.read_text(encoding="utf-8")
                except (UnicodeDecodeError, PermissionError):
                    continue

    def test_author_appears_in_generated_files(self):
        project = self._generate({"readme": True, "pypi_packaging": True})
        found_author = False
        for _, content in self._all_text_files(project):
            if METADATA["author"] in content:
                found_author = True
                break
        self.assertTrue(found_author, "Author name should appear in at least one generated file")

    def test_email_appears_in_generated_files(self):
        project = self._generate({"pypi_packaging": True})
        found_email = False
        for _, content in self._all_text_files(project):
            if METADATA["email"] in content:
                found_email = True
                break
        self.assertTrue(found_email, "Email should appear in at least one generated file")

    def test_version_appears_in_init(self):
        project = self._generate({})
        init_file = project / "src" / "flag_test_project" / "__init__.py"
        self.assertTrue(init_file.exists())
        content = init_file.read_text()
        self.assertIn(METADATA["version"], content)

    def test_description_appears_in_init(self):
        project = self._generate({})
        init_file = project / "src" / "flag_test_project" / "__init__.py"
        content = init_file.read_text()
        self.assertIn(METADATA["description"], content)

    def test_no_unresolved_placeholder_patterns(self):
        """No {{placeholder}} patterns should remain in generated files."""
        project = self._generate({
            "cli": True,
            "tests": True,
            "pypi_packaging": True,
            "readme": True,
            "changelog": True,
            "gitignore": True,
        })
        unresolved_pattern = re.compile(r"\{\{(project_name|author|email|description|version|package_name|class_name)\}\}")
        violations = []
        for path, content in self._all_text_files(project):
            matches = unresolved_pattern.findall(content)
            if matches:
                violations.append((path.relative_to(project), matches))
        self.assertEqual(
            violations,
            [],
            f"Found unresolved placeholders: {violations}",
        )

    def test_project_name_in_readme(self):
        project = self._generate({"readme": True})
        readme = project / "README.md"
        content = readme.read_text()
        self.assertIn(
            self.project_name,
            content,
            "Project name should appear in README.md",
        )


if __name__ == "__main__":
    unittest.main()
