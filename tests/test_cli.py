"""
Tests for the CLI entry point (__main__.py) and argument parsing.

Covers: --gui flag, --cli flag, --version flag, --help output,
        CLI project generation workflow, and invalid argument handling.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from python_project_generator.__main__ import main


class TestVersionAndHelp(unittest.TestCase):
    """Tests for --version and --help flags."""

    def test_version_flag_exits_zero(self):
        """--version prints version info and exits with code 0."""
        with patch("sys.argv", ["prog", "--version"]):
            with self.assertRaises(SystemExit) as ctx:
                main()
            self.assertEqual(ctx.exception.code, 0)

    def test_help_flag_exits_zero(self):
        """--help prints usage and exits with code 0."""
        with patch("sys.argv", ["prog", "--help"]):
            with self.assertRaises(SystemExit) as ctx:
                main()
            self.assertEqual(ctx.exception.code, 0)


class TestCLIFlag(unittest.TestCase):
    """Tests for --cli flag routing."""

    def test_cli_flag_calls_project_generator_main(self):
        """--cli loads and delegates to project_generator.main()."""
        with patch("sys.argv", ["prog", "--cli"]):
            with patch(
                "python_project_generator.project_generator.main", return_value=0
            ) as mock_main:
                result = main()
        mock_main.assert_called_once()
        self.assertEqual(result, 0)

    def test_cli_flag_returns_exit_code_from_module(self):
        """--cli returns whatever exit code project_generator.main() returns."""
        with patch("sys.argv", ["prog", "--cli"]):
            with patch(
                "python_project_generator.project_generator.main", return_value=42
            ):
                result = main()
        self.assertEqual(result, 42)

    def test_cli_flag_forwards_remaining_args(self):
        """--cli forwards remaining args to project_generator via sys.argv."""
        captured_argv = None

        def capture_argv():
            nonlocal captured_argv
            captured_argv = sys.argv[:]
            return 0

        with patch("sys.argv", ["prog", "--cli", "generate", "myproj", "-o", "/tmp"]):
            with patch(
                "python_project_generator.project_generator.main",
                side_effect=capture_argv,
            ) as mock_main:
                result = main()
        mock_main.assert_called_once()
        self.assertEqual(result, 0)
        self.assertEqual(captured_argv, ["prog", "generate", "myproj", "-o", "/tmp"])

    def test_cli_flag_with_no_subcommand_shows_help(self):
        """--cli with no subcommand delegates to project_generator.main() which shows help."""
        with patch("sys.argv", ["prog", "--cli"]):
            with patch(
                "python_project_generator.project_generator.main", return_value=1
            ) as mock_main:
                result = main()
        mock_main.assert_called_once()
        self.assertEqual(result, 1)


class TestGUIFlag(unittest.TestCase):
    """Tests for --gui / default GUI launch path."""

    def test_gui_returns_1_when_wx_missing(self):
        """Default path (no --cli) returns 1 when wxPython is not installed."""
        args = MagicMock(cli=False, gui=False)
        with patch(
            "python_project_generator.__main__.argparse.ArgumentParser.parse_known_args",
            return_value=(args, []),
        ):
            real_import = __import__

            def no_wx_import(name, globals=None, locals=None, fromlist=(), level=0):
                if name == "wx":
                    raise ImportError("No module named 'wx'")
                return real_import(name, globals, locals, fromlist, level)

            saved_wx = sys.modules.pop("wx", None)
            try:
                with patch("builtins.__import__", side_effect=no_wx_import):
                    result = main()
                self.assertEqual(result, 1)
            finally:
                if saved_wx is not None:
                    sys.modules["wx"] = saved_wx

    def test_gui_flag_attempts_wx_import(self):
        """--gui path tries to import wx; when missing, returns 1 with helpful message."""
        with patch("sys.argv", ["prog", "--gui"]):
            real_import = __import__

            def no_wx(name, globals=None, locals=None, fromlist=(), level=0):
                if name == "wx":
                    raise ImportError("No module named 'wx'")
                return real_import(name, globals, locals, fromlist, level)

            saved_wx = sys.modules.pop("wx", None)
            try:
                with patch("builtins.__import__", side_effect=no_wx):
                    result = main()
                self.assertEqual(result, 1)
            finally:
                if saved_wx is not None:
                    sys.modules["wx"] = saved_wx


class TestCLIProjectGeneration(unittest.TestCase):
    """Tests for the CLI-driven project generation workflow."""

    def test_cli_generate_command(self):
        """--cli generate myproject calls project_generator.main()."""
        with patch("sys.argv", ["prog", "--cli", "generate", "myproject"]):
            with patch(
                "python_project_generator.project_generator.main", return_value=0
            ) as mock_main:
                result = main()
        mock_main.assert_called_once()
        self.assertEqual(result, 0)

    def test_cli_list_templates(self):
        """--cli --list-templates calls project_generator.main()."""
        with patch("sys.argv", ["prog", "--cli", "--list-templates"]):
            with patch(
                "python_project_generator.project_generator.main", return_value=0
            ) as mock_main:
                result = main()
        mock_main.assert_called_once()
        self.assertEqual(result, 0)

    def test_cli_verbose_flag(self):
        """--cli --verbose is forwarded to project_generator.main()."""
        with patch("sys.argv", ["prog", "--cli", "--verbose"]):
            with patch(
                "python_project_generator.project_generator.main", return_value=0
            ) as mock_main:
                result = main()
        mock_main.assert_called_once()
        self.assertEqual(result, 0)


class TestModuleExecution(unittest.TestCase):
    """Tests for `python -m python_project_generator` execution."""

    def test_main_is_callable(self):
        """main() is importable and callable."""
        self.assertTrue(callable(main))

    def test_main_returns_int_on_wx_missing(self):
        """main() returns an integer exit code when wx is unavailable."""
        args = MagicMock(cli=False, gui=False)
        with patch(
            "python_project_generator.__main__.argparse.ArgumentParser.parse_known_args",
            return_value=(args, []),
        ):
            real_import = __import__

            def no_wx(name, globals=None, locals=None, fromlist=(), level=0):
                if name == "wx":
                    raise ImportError("no wx")
                return real_import(name, globals, locals, fromlist, level)

            saved_wx = sys.modules.pop("wx", None)
            try:
                with patch("builtins.__import__", side_effect=no_wx):
                    result = main()
            finally:
                if saved_wx is not None:
                    sys.modules["wx"] = saved_wx
        self.assertIsInstance(result, int)

    def test_if_name_main_block(self):
        """The module has a __name__ == '__main__' guard."""
        import inspect
        import python_project_generator.__main__ as mod

        source = inspect.getsource(mod)
        self.assertIn('if __name__ == "__main__"', source)


if __name__ == "__main__":
    unittest.main()
