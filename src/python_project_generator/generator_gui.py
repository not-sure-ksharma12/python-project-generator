"""
GUI for the Python Project Generator.
A standalone application for creating Python projects from templates.
"""

import sys
import os
import threading
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import wx
    import wx.lib.scrolledpanel as scrolled
    WX_AVAILABLE = True
except ImportError:
    wx = None
    scrolled = None
    WX_AVAILABLE = False

# Support running as a package (preferred) and also directly for dev
try:
    from .project_generator import ProjectGenerator, TemplateManager, setup_logging  # type: ignore
except Exception:
    try:
        # When executed via plain python on installed package name
        from python_project_generator.project_generator import ProjectGenerator, TemplateManager, setup_logging  # type: ignore
    except Exception:
        import sys as _sys
        import os as _os
        # Add src/ parent of package to path for direct file execution in repo
        _repo_root = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", ".."))
        _src_dir = _os.path.join(_repo_root, "src")
        if _src_dir not in _sys.path:
            _sys.path.insert(0, _src_dir)
        from python_project_generator.project_generator import ProjectGenerator, TemplateManager, setup_logging  # type: ignore

__version__ = "1.0.0"


if WX_AVAILABLE:
    class ProjectGeneratorFrame(wx.Frame):
        """Main frame for the project generator GUI."""
        
        def __init__(self):
            super().__init__(
                None,
                title=f"Python Project Generator v{__version__}",
                size=(1200, 800)
            )
            
            self.generator = ProjectGenerator()
            self.template_manager = TemplateManager()
            self.setup_ui()
            self.setup_menubar()
            self.setup_statusbar()
            self.center_on_screen()
            
        def setup_ui(self):
            """Set up the user interface."""
            # Create main panel with notebook for tabs
            self.panel = wx.Panel(self)
            main_sizer = wx.BoxSizer(wx.VERTICAL)
            
            # Title
            title_label = wx.StaticText(
                self.panel,
                label="Python Project Generator",
                style=wx.ALIGN_CENTER
            )
            title_font = title_label.GetFont()
            title_font.SetPointSize(18)
            title_font.SetWeight(wx.FONTWEIGHT_BOLD)
            title_label.SetFont(title_font)
            
            # Create notebook for different sections
            self.notebook = wx.Notebook(self.panel)
            
            # Template Selection Tab
            self.template_panel = self.create_template_selection_panel()
            self.notebook.AddPage(self.template_panel, "Template")
            
            # Project Info Tab
            self.info_panel = self.create_project_info_panel()
            self.notebook.AddPage(self.info_panel, "Project Info")
            
            # Features Tab
            self.features_panel = self.create_features_panel()
            self.notebook.AddPage(self.features_panel, "Features")
            
            # Output Tab
            self.output_panel = self.create_output_panel()
            self.notebook.AddPage(self.output_panel, "Output")
            
            # Buttons
            button_sizer = wx.BoxSizer(wx.HORIZONTAL)
            
            self.preview_button = wx.Button(self.panel, label="Preview Structure")
            self.generate_button = wx.Button(self.panel, label="Generate Project")
            self.clear_button = wx.Button(self.panel, label="Clear Form")
            
            button_sizer.Add(self.preview_button, 0, wx.ALL, 5)
            button_sizer.Add(self.generate_button, 0, wx.ALL, 5)
            button_sizer.Add(self.clear_button, 0, wx.ALL, 5)
            
            # Layout
            main_sizer.Add(title_label, 0, wx.ALL | wx.CENTER, 10)
            main_sizer.Add(self.notebook, 1, wx.ALL | wx.EXPAND, 5)
            main_sizer.Add(button_sizer, 0, wx.ALL | wx.CENTER, 10)
            
            self.panel.SetSizer(main_sizer)
            
            # Bind events
            self.preview_button.Bind(wx.EVT_BUTTON, self.on_preview)
            self.generate_button.Bind(wx.EVT_BUTTON, self.on_generate)
            self.clear_button.Bind(wx.EVT_BUTTON, self.on_clear)
        
        def create_template_selection_panel(self):
            """Create the template selection panel."""
            panel = scrolled.ScrolledPanel(self.notebook)
            panel.SetupScrolling()
            sizer = wx.BoxSizer(wx.VERTICAL)
            
            # Template selection
            template_label = wx.StaticText(panel, label="Choose Project Template:")
            template_font = template_label.GetFont()
            template_font.SetWeight(wx.FONTWEIGHT_BOLD)
            template_label.SetFont(template_font)
            
            templates = self.template_manager.get_available_templates()
            template_choices = []
            self.template_ids = []
            
            for template_id, template_info in templates.items():
                choice_text = f"{template_info['name']}"
                template_choices.append(choice_text)
                self.template_ids.append(template_id)
            
            self.template_choice = wx.Choice(panel, choices=template_choices)
            self.template_choice.SetSelection(0)  # Default to first template
            self.template_choice.Bind(wx.EVT_CHOICE, self.on_template_changed)
            
            # Create a horizontal layout for template info and structure
            info_sizer = wx.BoxSizer(wx.HORIZONTAL)
            
            # Left side: Template description and info
            left_panel = wx.Panel(panel)
            left_sizer = wx.BoxSizer(wx.VERTICAL)
            
            # Template description
            desc_label = wx.StaticText(left_panel, label="Description:")
            desc_font = desc_label.GetFont()
            desc_font.SetWeight(wx.FONTWEIGHT_BOLD)
            desc_label.SetFont(desc_font)
            
            self.template_desc = wx.StaticText(left_panel, label="")
            self.template_desc.Wrap(300)
            
            # Key features
            features_label = wx.StaticText(left_panel, label="Key Features:")
            features_font = features_label.GetFont()
            features_font.SetWeight(wx.FONTWEIGHT_BOLD)
            features_label.SetFont(features_font)
            
            self.template_features = wx.StaticText(left_panel, label="")
            self.template_features.Wrap(300)
            
            # Use cases
            cases_label = wx.StaticText(left_panel, label="Use Cases:")
            cases_font = cases_label.GetFont()
            cases_font.SetWeight(wx.FONTWEIGHT_BOLD)
            cases_label.SetFont(cases_font)
            
            self.template_cases = wx.StaticText(left_panel, label="")
            self.template_cases.Wrap(300)
            
            # Dependencies
            deps_label = wx.StaticText(left_panel, label="Main Dependencies:")
            deps_font = deps_label.GetFont()
            deps_font.SetWeight(wx.FONTWEIGHT_BOLD)
            deps_label.SetFont(deps_font)
            
            self.template_deps = wx.StaticText(left_panel, label="")
            self.template_deps.Wrap(300)
            
            left_sizer.Add(desc_label, 0, wx.ALL, 5)
            left_sizer.Add(self.template_desc, 0, wx.ALL, 5)
            left_sizer.Add(features_label, 0, wx.ALL, 5)
            left_sizer.Add(self.template_features, 0, wx.ALL, 5)
            left_sizer.Add(cases_label, 0, wx.ALL, 5)
            left_sizer.Add(self.template_cases, 0, wx.ALL, 5)
            left_sizer.Add(deps_label, 0, wx.ALL, 5)
            left_sizer.Add(self.template_deps, 0, wx.ALL, 5)
            left_panel.SetSizer(left_sizer)
            
            # Right side: Project structure
            right_panel = wx.Panel(panel)
            right_sizer = wx.BoxSizer(wx.VERTICAL)
            
            structure_label = wx.StaticText(right_panel, label="Project Structure:")
            structure_font = structure_label.GetFont()
            structure_font.SetWeight(wx.FONTWEIGHT_BOLD)
            structure_label.SetFont(structure_font)
            
            # Use a text control with monospace font for the structure
            self.template_structure = wx.TextCtrl(
                right_panel, 
                style=wx.TE_MULTILINE | wx.TE_READONLY,
                size=(400, 300)
            )
            structure_font = wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
            self.template_structure.SetFont(structure_font)
            
            right_sizer.Add(structure_label, 0, wx.ALL, 5)
            right_sizer.Add(self.template_structure, 1, wx.ALL | wx.EXPAND, 5)
            right_panel.SetSizer(right_sizer)
            
            # Add both panels to horizontal sizer
            info_sizer.Add(left_panel, 1, wx.ALL | wx.EXPAND, 5)
            info_sizer.Add(right_panel, 1, wx.ALL | wx.EXPAND, 5)
            
            # MD files info button
            md_button_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.view_md_button = wx.Button(panel, label="View Common MD Files")
            self.view_md_button.SetToolTip("Show a categorized list of common Markdown documentation files")
            self.view_md_button.Bind(wx.EVT_BUTTON, self.on_view_md_files)
            md_button_sizer.Add(self.view_md_button, 0, wx.ALL, 5)
            
            # Update info for default selection
            self.update_template_info()
            
            # Layout
            sizer.Add(template_label, 0, wx.ALL, 10)
            sizer.Add(self.template_choice, 0, wx.ALL | wx.EXPAND, 10)
            sizer.Add(md_button_sizer, 0, wx.ALL | wx.ALIGN_LEFT, 5)
            sizer.Add(info_sizer, 1, wx.ALL | wx.EXPAND, 10)
            
            panel.SetSizer(sizer)
            return panel
        
        def create_project_info_panel(self):
            """Create the project information panel."""
            panel = scrolled.ScrolledPanel(self.notebook)
            panel.SetupScrolling()
            
            sizer = wx.BoxSizer(wx.VERTICAL)
            
            # Project Name
            name_sizer = wx.BoxSizer(wx.HORIZONTAL)
            name_label = wx.StaticText(panel, label="Project Name:")
            name_label.SetMinSize((120, -1))
            self.name_ctrl = wx.TextCtrl(panel, size=(300, -1))
            self.name_ctrl.SetToolTip("Enter the name of your Python project")
            name_sizer.Add(name_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
            name_sizer.Add(self.name_ctrl, 1, wx.ALL | wx.EXPAND, 5)
            
            # Description
            desc_sizer = wx.BoxSizer(wx.HORIZONTAL)
            desc_label = wx.StaticText(panel, label="Description:")
            desc_label.SetMinSize((120, -1))
            self.desc_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE, size=(300, 60))
            self.desc_ctrl.SetToolTip("Brief description of your project")
            desc_sizer.Add(desc_label, 0, wx.ALL | wx.ALIGN_TOP, 5)
            desc_sizer.Add(self.desc_ctrl, 1, wx.ALL | wx.EXPAND, 5)
            
            # Author
            author_sizer = wx.BoxSizer(wx.HORIZONTAL)
            author_label = wx.StaticText(panel, label="Author:")
            author_label.SetMinSize((120, -1))
            self.author_ctrl = wx.TextCtrl(panel, size=(300, -1))
            self.author_ctrl.SetToolTip("Your name")
            author_sizer.Add(author_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
            author_sizer.Add(self.author_ctrl, 1, wx.ALL | wx.EXPAND, 5)
            
            # Email
            email_sizer = wx.BoxSizer(wx.HORIZONTAL)
            email_label = wx.StaticText(panel, label="Email:")
            email_label.SetMinSize((120, -1))
            self.email_ctrl = wx.TextCtrl(panel, size=(300, -1))
            self.email_ctrl.SetToolTip("Your email address")
            email_sizer.Add(email_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
            email_sizer.Add(self.email_ctrl, 1, wx.ALL | wx.EXPAND, 5)
            
            # Version
            version_sizer = wx.BoxSizer(wx.HORIZONTAL)
            version_label = wx.StaticText(panel, label="Version:")
            version_label.SetMinSize((120, -1))
            self.version_ctrl = wx.TextCtrl(panel, value="0.1.0", size=(300, -1))
            self.version_ctrl.SetToolTip("Initial version number")
            version_sizer.Add(version_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
            version_sizer.Add(self.version_ctrl, 1, wx.ALL | wx.EXPAND, 5)
            
            # URL
            url_sizer = wx.BoxSizer(wx.HORIZONTAL)
            url_label = wx.StaticText(panel, label="URL:")
            url_label.SetMinSize((120, -1))
            self.url_ctrl = wx.TextCtrl(panel, size=(300, -1))
            self.url_ctrl.SetToolTip("Project homepage or repository URL")
            url_sizer.Add(url_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
            url_sizer.Add(self.url_ctrl, 1, wx.ALL | wx.EXPAND, 5)
            
            # License Type
            license_sizer = wx.BoxSizer(wx.HORIZONTAL)
            license_label = wx.StaticText(panel, label="License:")
            license_label.SetMinSize((120, -1))
            license_choices = ["MIT", "Apache-2.0", "GPL-3.0", "BSD-3-Clause", "Custom"]
            self.license_ctrl = wx.Choice(panel, choices=license_choices)
            self.license_ctrl.SetSelection(0)  # Default to MIT
            self.license_ctrl.SetToolTip("Choose a license for your project")
            license_sizer.Add(license_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
            license_sizer.Add(self.license_ctrl, 1, wx.ALL | wx.EXPAND, 5)
            
            # Output Directory
            output_sizer = wx.BoxSizer(wx.HORIZONTAL)
            output_label = wx.StaticText(panel, label="Output Dir:")
            output_label.SetMinSize((120, -1))
            self.output_ctrl = wx.TextCtrl(panel, value=str(Path.home() / "Projects"), size=(250, -1))
            self.output_browse = wx.Button(panel, label="Browse...", size=(80, -1))
            self.output_browse.Bind(wx.EVT_BUTTON, self.on_browse_output)
            output_sizer.Add(output_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
            output_sizer.Add(self.output_ctrl, 1, wx.ALL | wx.EXPAND, 5)
            output_sizer.Add(self.output_browse, 0, wx.ALL, 5)
            
            # Add all to main sizer
            sizer.Add(name_sizer, 0, wx.ALL | wx.EXPAND, 5)
            sizer.Add(desc_sizer, 0, wx.ALL | wx.EXPAND, 5)
            sizer.Add(author_sizer, 0, wx.ALL | wx.EXPAND, 5)
            sizer.Add(email_sizer, 0, wx.ALL | wx.EXPAND, 5)
            sizer.Add(version_sizer, 0, wx.ALL | wx.EXPAND, 5)
            sizer.Add(url_sizer, 0, wx.ALL | wx.EXPAND, 5)
            sizer.Add(license_sizer, 0, wx.ALL | wx.EXPAND, 5)
            sizer.Add(output_sizer, 0, wx.ALL | wx.EXPAND, 5)
            
            panel.SetSizer(sizer)
            return panel
            
        def create_features_panel(self):
            """Create the features selection panel."""
            panel = scrolled.ScrolledPanel(self.notebook)
            panel.SetupScrolling()
            
            sizer = wx.BoxSizer(wx.VERTICAL)
            
            # Create feature checkboxes
            self.feature_checkboxes = {}
            
            # Core features (non-doc)
            core_features = [
                ("cli", "Command Line Interface (CLI)", True, "Add a CLI with argument parsing"),
                ("gui", "Graphical User Interface (GUI)", False, "Add a wxPython-based GUI"),
                ("tests", "Unit Tests", True, "Include pytest test framework"),
                ("executable", "Executable Building", False, "Add PyInstaller scripts for creating executables"),
                ("pypi_packaging", "PyPI Packaging", True, "Include setup.py and pyproject.toml for PyPI"),
                ("dev_requirements", "Development Requirements", True, "Include development dependencies"),
                ("license", "License File", True, "Include LICENSE file"),
                ("makefile", "Makefile", False, "Include Makefile for common tasks"),
                ("gitignore", ".gitignore", True, "Include .gitignore file"),
                ("github_actions", "GitHub Actions CI", False, "Include GitHub Actions workflow"),
            ]

            # Build & Utilities features
            utilities_features = [
                ("mac_app_bundle", "macOS .app Bundle Script", False, "Add scripts/create_app_bundle.py to build a .app (macOS)"),
                ("icon_generator", "Icon Generator Script", False, "Add scripts/create_icon.py to generate icons"),
                ("remove_git_tracking", "Delete Git Tracking Helper", False, "Add scripts/delete_git_tracking.txt with rm -rf .git"),
                ("freeze_requirements", "Freeze requirements script", False, "Add scripts/freeze_requirements.py to write requirements.txt"),
                ("setup_build_script", "Build with setup.py script", False, "Add scripts/build_with_setup.py helper"),
            ]

            # Documentation features (MD files)
            md_info = ProjectGenerator.get_available_md_files()
            # Sort by file name alphabetically
            sorted_md = sorted(md_info.items(), key=lambda kv: kv[1]["name"].lower())
            documentation_features = []
            for feature_id, info in sorted_md:
                # Map md feature id to checkbox default: recommend true if recommended, else False
                default = info.get("recommended", False)
                documentation_features.append((feature_id, info["name"], default, info["description"]))

            # Core features header
            core_header = wx.StaticText(panel, label="Core Features")
            core_font = core_header.GetFont()
            core_font.SetWeight(wx.FONTWEIGHT_BOLD)
            core_header.SetFont(core_font)
            sizer.Add(core_header, 0, wx.LEFT | wx.TOP, 10)

            for feature_id, label, default, tooltip in core_features:
                checkbox = wx.CheckBox(panel, label=label)
                checkbox.SetValue(default)
                checkbox.SetToolTip(tooltip)
                self.feature_checkboxes[feature_id] = checkbox
                sizer.Add(checkbox, 0, wx.ALL, 5)

            # Bind auto-select for freeze_requirements when dev_requirements is checked
            if 'dev_requirements' in self.feature_checkboxes:
                self.feature_checkboxes['dev_requirements'].Bind(wx.EVT_CHECKBOX, self._on_dev_requirements_toggle)

            sizer.Add(wx.StaticLine(panel), 0, wx.ALL | wx.EXPAND, 10)

            # Utilities header
            utilities_header = wx.StaticText(panel, label="Build & Utilities")
            utilities_font = utilities_header.GetFont()
            utilities_font.SetWeight(wx.FONTWEIGHT_BOLD)
            utilities_header.SetFont(utilities_font)
            sizer.Add(utilities_header, 0, wx.LEFT | wx.TOP, 10)

            for feature_id, label, default, tooltip in utilities_features:
                checkbox = wx.CheckBox(panel, label=label)
                checkbox.SetValue(default)
                checkbox.SetToolTip(tooltip)
                self.feature_checkboxes[feature_id] = checkbox
                sizer.Add(checkbox, 0, wx.ALL, 5)

            # Documentation features header
            docs_header_sizer = wx.BoxSizer(wx.HORIZONTAL)
            docs_header = wx.StaticText(panel, label="Documentation (Markdown) Files")
            docs_font = docs_header.GetFont()
            docs_font.SetWeight(wx.FONTWEIGHT_BOLD)
            docs_header.SetFont(docs_font)
            docs_header_sizer.Add(docs_header, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10)
            # Quick buttons to select all/none docs
            docs_select_all = wx.Button(panel, label="Select All Docs")
            docs_select_none = wx.Button(panel, label="Select No Docs")
            docs_select_all.Bind(wx.EVT_BUTTON, lambda e: self._set_doc_checkboxes(True))
            docs_select_none.Bind(wx.EVT_BUTTON, lambda e: self._set_doc_checkboxes(False))
            docs_header_sizer.Add(docs_select_all, 0, wx.RIGHT, 5)
            docs_header_sizer.Add(docs_select_none, 0)
            sizer.Add(docs_header_sizer, 0, wx.LEFT | wx.TOP | wx.BOTTOM, 10)

            for feature_id, label, default, tooltip in documentation_features:
                checkbox = wx.CheckBox(panel, label=label)
                checkbox.SetValue(default)
                checkbox.SetToolTip(tooltip)
                self.feature_checkboxes[feature_id] = checkbox
                sizer.Add(checkbox, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

            # Add buttons for selecting all/none (global)
            button_sizer = wx.BoxSizer(wx.HORIZONTAL)
            select_all_btn = wx.Button(panel, label="Select All")
            select_none_btn = wx.Button(panel, label="Select None")
            
            select_all_btn.Bind(wx.EVT_BUTTON, self.on_select_all)
            select_none_btn.Bind(wx.EVT_BUTTON, self.on_select_none)
            
            button_sizer.Add(select_all_btn, 0, wx.ALL, 5)
            button_sizer.Add(select_none_btn, 0, wx.ALL, 5)
            
            sizer.Add(wx.StaticLine(panel), 0, wx.ALL | wx.EXPAND, 10)
            sizer.Add(button_sizer, 0, wx.ALL | wx.CENTER, 5)
            
            panel.SetSizer(sizer)
            return panel

        def _set_doc_checkboxes(self, value: bool) -> None:
            """Helper to set only documentation feature checkboxes to value."""
            md_keys = set(ProjectGenerator.get_available_md_files().keys())
            for key, checkbox in self.feature_checkboxes.items():
                if key in md_keys:
                    checkbox.SetValue(value)

        def _on_dev_requirements_toggle(self, event):
            """Auto-enable freeze_requirements when dev_requirements is selected."""
            dev_cb = self.feature_checkboxes.get('dev_requirements')
            freeze_cb = self.feature_checkboxes.get('freeze_requirements')
            if dev_cb and freeze_cb and dev_cb.GetValue():
                freeze_cb.SetValue(True)

        def on_view_md_files(self, event):
            """Show a dialog listing and allowing selection of common Markdown files."""
            md_files = ProjectGenerator.get_available_md_files()

            dialog = wx.Dialog(self, title="Select Documentation Files", size=(700, 600))
            dlg_sizer = wx.BoxSizer(wx.VERTICAL)

            # Instructions
            instructions = wx.StaticText(dialog, label="Select the documentation files to include in your project:")
            dlg_sizer.Add(instructions, 0, wx.ALL, 10)

            # Scrolled area with checkboxes
            scroller = scrolled.ScrolledPanel(dialog, size=(-1, 450))
            scroller.SetupScrolling()
            sc_sizer = wx.BoxSizer(wx.VERTICAL)

            # Sort md files by name
            sorted_md = sorted(md_files.items(), key=lambda kv: kv[1]['name'].lower())
            self._md_dialog_checkboxes = {}
            for md_key, info in sorted_md:
                cb = wx.CheckBox(scroller, label=f"{info['name']}")
                # Initialize to current feature checkbox value if exists
                current_val = False
                if md_key in self.feature_checkboxes:
                    current_val = self.feature_checkboxes[md_key].GetValue()
                else:
                    # default to recommended
                    current_val = info.get('recommended', False)
                cb.SetValue(current_val)
                cb.SetToolTip(info['description'])
                self._md_dialog_checkboxes[md_key] = cb
                sc_sizer.Add(cb, 0, wx.ALL, 5)

            scroller.SetSizer(sc_sizer)
            dlg_sizer.Add(scroller, 1, wx.ALL | wx.EXPAND, 10)

            # Dialog buttons
            btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
            select_all = wx.Button(dialog, label="Select All")
            select_none = wx.Button(dialog, label="Select None")
            apply_btn = wx.Button(dialog, label="Apply")
            close_btn = wx.Button(dialog, label="Close")

            def set_all(val: bool):
                for cb in self._md_dialog_checkboxes.values():
                    cb.SetValue(val)

            select_all.Bind(wx.EVT_BUTTON, lambda e: set_all(True))
            select_none.Bind(wx.EVT_BUTTON, lambda e: set_all(False))

            def apply_changes(evt):
                # Sync dialog selections into feature checkboxes
                for md_key, cb in self._md_dialog_checkboxes.items():
                    if md_key in self.feature_checkboxes:
                        self.feature_checkboxes[md_key].SetValue(cb.GetValue())
                dialog.EndModal(wx.ID_OK)

            apply_btn.Bind(wx.EVT_BUTTON, apply_changes)
            close_btn.Bind(wx.EVT_BUTTON, lambda e: dialog.EndModal(wx.ID_CANCEL))

            btn_sizer.Add(select_all, 0, wx.ALL, 5)
            btn_sizer.Add(select_none, 0, wx.ALL, 5)
            btn_sizer.AddStretchSpacer(1)
            btn_sizer.Add(apply_btn, 0, wx.ALL, 5)
            btn_sizer.Add(close_btn, 0, wx.ALL, 5)

            dlg_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

            dialog.SetSizer(dlg_sizer)
            dialog.Layout()
            dialog.ShowModal()
            dialog.Destroy()
        
        def create_output_panel(self):
            """Create the output/log panel."""
            panel = wx.Panel(self.notebook)
            sizer = wx.BoxSizer(wx.VERTICAL)
            
            # Output text area
            self.output_text = wx.TextCtrl(
                panel,
                style=wx.TE_MULTILINE | wx.TE_READONLY,
                size=(-1, 400)
            )
            self.output_text.SetFont(wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            
            # Clear output button
            clear_output_btn = wx.Button(panel, label="Clear Output")
            clear_output_btn.Bind(wx.EVT_BUTTON, self.on_clear_output)
            
            sizer.Add(self.output_text, 1, wx.ALL | wx.EXPAND, 5)
            sizer.Add(clear_output_btn, 0, wx.ALL | wx.CENTER, 5)
            
            panel.SetSizer(sizer)
            return panel
        
        def setup_menubar(self):
            """Set up the menu bar."""
            menubar = wx.MenuBar()
            
            # File menu
            file_menu = wx.Menu()
            file_menu.Append(wx.ID_NEW, "New Project\tCtrl+N", "Start a new project")
            file_menu.AppendSeparator()
            file_menu.Append(wx.ID_EXIT, "Exit\tCtrl+Q", "Exit the application")
            menubar.Append(file_menu, "&File")
            
            # Templates menu
            templates_menu = wx.Menu()
            templates_menu.Append(wx.ID_REFRESH, "Refresh Templates\tF5", "Refresh template list")
            menubar.Append(templates_menu, "&Templates")
            
            # Help menu
            help_menu = wx.Menu()
            help_menu.Append(wx.ID_ABOUT, "About\tF1", "About this application")
            menubar.Append(help_menu, "&Help")
            
            self.SetMenuBar(menubar)
            
            # Bind menu events
            self.Bind(wx.EVT_MENU, self.on_clear, id=wx.ID_NEW)
            self.Bind(wx.EVT_MENU, self.on_exit, id=wx.ID_EXIT)
            self.Bind(wx.EVT_MENU, self.on_refresh_templates, id=wx.ID_REFRESH)
            self.Bind(wx.EVT_MENU, self.on_about, id=wx.ID_ABOUT)
        
        def setup_statusbar(self):
            """Set up the status bar."""
            self.statusbar = self.CreateStatusBar(2)
            self.statusbar.SetStatusText("Ready to generate projects", 0)
            self.statusbar.SetStatusText(f"v{__version__}", 1)
        
        def center_on_screen(self):
            """Center the window on the screen."""
            self.Center()
        
        def log_to_output(self, message: str):
            """Add a message to the output text area."""
            wx.CallAfter(self._append_to_output, message)
        
        def _append_to_output(self, message: str):
            """Append message to output (called from main thread)."""
            self.output_text.AppendText(f"{message}\n")
        
        def on_template_changed(self, event):
            """Handle template selection change."""
            self.update_template_info()
        
        def update_template_info(self):
            """Update the template information display."""
            if not (hasattr(self, 'template_choice') and hasattr(self, 'template_ids')):
                return
            selection = self.template_choice.GetSelection()
            if selection < 0 or selection >= len(self.template_ids):
                return
            template_id = self.template_ids[selection]
            detailed_info = self.template_manager.get_template_detailed_info(template_id)
            if "error" in detailed_info:
                self._clear_template_info_display()
            else:
                self._apply_template_detailed_info(detailed_info)
        
        def _clear_template_info_display(self):
            """Show unavailable template message and clear detail widgets."""
            self.template_desc.SetLabel("Template information not available")
            if hasattr(self, 'template_features'):
                self.template_features.SetLabel("")
                self.template_cases.SetLabel("")
                self.template_deps.SetLabel("")
                self.template_structure.SetValue("")
        
        def _apply_template_detailed_info(self, detailed_info: Dict[str, Any]):
            """Populate template detail widgets from API result."""
            self.template_desc.SetLabel(detailed_info['description'])
            features_text = "\n".join(f"• {feature}" for feature in detailed_info['key_features'])
            self.template_features.SetLabel(features_text)
            cases_text = "\n".join(f"• {case}" for case in detailed_info['use_cases'])
            self.template_cases.SetLabel(cases_text)
            deps_text = ", ".join(detailed_info['dependencies'])
            self.template_deps.SetLabel(deps_text)
            structure_text = "\n".join(detailed_info['project_structure'])
            self.template_structure.SetValue(structure_text)
            if hasattr(self, 'template_panel'):
                self.template_panel.Layout()
                self.template_panel.FitInside()
        
        def on_browse_output(self, event):
            """Handle browse output directory button."""
            with wx.DirDialog(self, "Choose output directory") as dialog:
                if dialog.ShowModal() == wx.ID_OK:
                    self.output_ctrl.SetValue(dialog.GetPath())
        
        def on_select_all(self, event):
            """Select all features."""
            for checkbox in self.feature_checkboxes.values():
                checkbox.SetValue(True)
        
        def on_select_none(self, event):
            """Deselect all features."""
            for checkbox in self.feature_checkboxes.values():
                checkbox.SetValue(False)
        
        def on_clear_output(self, event):
            """Clear the output text."""
            self.output_text.Clear()
        
        def on_refresh_templates(self, event):
            """Refresh the template list."""
            self.log_to_output("Refreshing templates...")
            # In a real implementation, this would refresh templates from remote sources
            self.log_to_output("Templates refreshed.")
        
        def on_preview(self, event):
            """Preview the project structure."""
            project_name = self.name_ctrl.GetValue().strip()
            if not project_name:
                wx.MessageBox("Please enter a project name", "Missing Information", wx.OK | wx.ICON_WARNING)
                return
            
            self.log_to_output(f"=== Project Structure Preview for '{project_name}' ===")
            self.log_to_output(f"Template: {self.get_selected_template()}")
            self.log_to_output("")
            
            features = self.get_selected_features()
            package_name = project_name.lower().replace('-', '_').replace(' ', '_')
            
            self.log_to_output(f"{project_name}/")
            self.log_to_output("├── src/")
            self.log_to_output(f"│   └── {package_name}/")
            self.log_to_output("│       ├── __init__.py")
            self.log_to_output("│       └── core.py")
            
            if features.get('cli'):
                self.log_to_output("│       ├── cli.py")
            if features.get('gui'):
                self.log_to_output("│       └── gui.py")
            
            if features.get('tests'):
                self.log_to_output("├── tests/")
                self.log_to_output("│   ├── __init__.py")
                self.log_to_output("│   └── test_core.py")
            
            if features.get('pypi_packaging'):
                self.log_to_output("├── setup.py")
                self.log_to_output("└── requirements.txt")
            
            if features.get('readme'):
                self.log_to_output("├── README.md")
            
            if features.get('license'):
                self.log_to_output("├── LICENSE")
            
            if features.get('gitignore'):
                self.log_to_output("├── .gitignore")

            # Optional helper scripts
            # Optional helper scripts under scripts/
            if any([
                features.get('mac_app_bundle'),
                features.get('icon_generator'),
                features.get('remove_git_tracking'),
                features.get('freeze_requirements'),
                features.get('setup_build_script')
            ]):
                self.log_to_output("├── scripts/")
                if features.get('mac_app_bundle'):
                    self.log_to_output("│   ├── create_app_bundle.py")
                if features.get('icon_generator'):
                    self.log_to_output("│   ├── create_icon.py")
                if features.get('remove_git_tracking'):
                    self.log_to_output("│   ├── delete_git_tracking.txt")
                if features.get('freeze_requirements'):
                    self.log_to_output("│   ├── freeze_requirements.py")
                if features.get('setup_build_script'):
                    self.log_to_output("│   └── build_with_setup.py")
            
            self.log_to_output("")
            self.log_to_output("=== End Preview ===")
            self.log_to_output("")
        
        def on_generate(self, event):
            """Generate the project."""
            # Validate input
            project_name = self.name_ctrl.GetValue().strip()
            if not project_name:
                wx.MessageBox("Please enter a project name", "Missing Information", wx.OK | wx.ICON_WARNING)
                return
            
            output_dir = Path(self.output_ctrl.GetValue().strip())
            if not output_dir.exists():
                wx.MessageBox("Output directory does not exist", "Invalid Directory", wx.OK | wx.ICON_ERROR)
                return
            
            # Check if project directory already exists
            project_path = output_dir / project_name
            if project_path.exists():
                result = wx.MessageBox(
                    f"Directory '{project_path}' already exists. Continue anyway?",
                    "Directory Exists",
                    wx.YES_NO | wx.ICON_QUESTION
                )
                if result == wx.NO:
                    return
            
            # Disable generate button during generation
            self.generate_button.Enable(False)
            self.statusbar.SetStatusText("Generating project...", 0)
            
            # Run generation in separate thread
            def generate_project():
                try:
                    template_id = self.get_selected_template()
                    features = self.get_selected_features()
                    metadata = self.get_project_metadata()
                    
                    self.log_to_output(f"Starting generation of '{project_name}'...")
                    self.log_to_output(f"Template: {template_id}")
                    self.log_to_output(f"Output directory: {output_dir}")
                    self.log_to_output("")
                    
                    success = self.generator.generate_project(
                        project_name=project_name,
                        output_dir=output_dir,
                        template_id=template_id,
                        features=features,
                        metadata=metadata
                    )
                    
                    if success:
                        self.log_to_output("")
                        self.log_to_output("✅ Project generated successfully!")
                        self.log_to_output(f"📁 Location: {project_path}")
                        self.log_to_output("")
                        self.log_to_output("Next steps:")
                        self.log_to_output(f"  cd '{project_path}'")
                        if features.get('dev_requirements'):
                            self.log_to_output("  pip install -r requirements-dev.txt")
                        self.log_to_output("  pip install -e .")
                        
                        wx.CallAfter(
                            wx.MessageBox,
                            f"Project '{project_name}' generated successfully!\n\nLocation: {project_path}",
                            "Success",
                            wx.OK | wx.ICON_INFORMATION
                        )
                    else:
                        self.log_to_output("")
                        self.log_to_output("❌ Project generation failed!")
                        wx.CallAfter(
                            wx.MessageBox,
                            "Project generation failed. Check the output for details.",
                            "Error",
                            wx.OK | wx.ICON_ERROR
                        )
                
                except Exception as e:
                    self.log_to_output(f"❌ Error: {str(e)}")
                    wx.CallAfter(
                        wx.MessageBox,
                        f"An error occurred: {str(e)}",
                        "Error",
                        wx.OK | wx.ICON_ERROR
                    )
                finally:
                    wx.CallAfter(self.generate_button.Enable, True)
                    wx.CallAfter(self.statusbar.SetStatusText, "Ready to generate projects", 0)
            
            thread = threading.Thread(target=generate_project)
            thread.daemon = True
            thread.start()
        
        def on_clear(self, event):
            """Clear the form."""
            # Clear project info
            self.name_ctrl.Clear()
            self.desc_ctrl.Clear()
            self.author_ctrl.Clear()
            self.email_ctrl.Clear()
            self.version_ctrl.SetValue("0.1.0")
            self.url_ctrl.Clear()
            self.license_ctrl.SetSelection(0)
            self.output_ctrl.SetValue(str(Path.home() / "Projects"))
            
            # Reset template selection
            self.template_choice.SetSelection(0)
            self.on_template_changed(None)
            
            # Reset features to defaults
            defaults = {
                'cli': True, 'gui': False, 'tests': True, 'executable': False,
                'pypi_packaging': True, 'dev_requirements': True, 'license': True,
                'readme': True, 'makefile': False, 'gitignore': True, 'github_actions': False,
                'mac_app_bundle': False, 'icon_generator': False, 'remove_git_tracking': False,
                'freeze_requirements': False, 'setup_build_script': False
            }
            
            for feature_id, checkbox in self.feature_checkboxes.items():
                checkbox.SetValue(defaults.get(feature_id, False))
            
            self.log_to_output("Form cleared.")
        
        def on_exit(self, event):
            """Handle exit menu item."""
            self.Close()
        
        def on_about(self, event):
            """Handle about menu item."""
            about_info = wx.adv.AboutDialogInfo()
            about_info.SetName("Python Project Generator")
            about_info.SetVersion(__version__)
            about_info.SetDescription(
                "A standalone GUI tool for generating customizable Python project skeletons.\n\n"
                "Features:\n"
                "• Multiple project templates\n"
                "• Customizable feature selection\n"
                "• Professional project structure\n"
                "• Ready for PyPI and development\n\n"
                "Create professional Python projects in seconds!"
            )
            about_info.SetCopyright("(C) 2024 Python Project Generator")
            about_info.AddDeveloper("Built with wxPython")
            
            wx.adv.AboutBox(about_info)
        
        def get_selected_template(self) -> str:
            """Get the selected template ID."""
            selection = self.template_choice.GetSelection()
            if selection >= 0 and selection < len(self.template_ids):
                return self.template_ids[selection]
            return "minimal-python"  # fallback
        
        def get_selected_features(self) -> Dict[str, bool]:
            """Get the selected features as a dictionary."""
            return {
                feature_id: checkbox.GetValue()
                for feature_id, checkbox in self.feature_checkboxes.items()
            }
        
        def get_project_metadata(self) -> Dict[str, str]:
            """Get the project metadata as a dictionary."""
            license_choices = ["MIT", "Apache-2.0", "GPL-3.0", "BSD-3-Clause", "Custom"]
            selected_license = license_choices[self.license_ctrl.GetSelection()]
            
            return {
                "description": self.desc_ctrl.GetValue().strip(),
                "author": self.author_ctrl.GetValue().strip(),
                "email": self.email_ctrl.GetValue().strip(),
                "version": self.version_ctrl.GetValue().strip(),
                "url": self.url_ctrl.GetValue().strip(),
                "license_type": selected_license,
            }

        def on_view_md_files(self, event):
            """Show a dialog listing common Markdown documentation files."""
            md_files = ProjectGenerator.get_available_md_files()
            
            # Build categorized text
            categories = {}
            for md_type, info in md_files.items():
                category = info.get("category", "Other")
                categories.setdefault(category, []).append((md_type, info))
            
            text_lines = []
            text_lines.append("Common Markdown Documentation Files\n")
            for category in sorted(categories.keys()):
                text_lines.append(f"=== {category} ===")
                for md_type, info in sorted(categories[category], key=lambda x: x[1]['name']):
                    star = "⭐" if info.get("recommended") else "-"
                    text_lines.append(f"{star} {info['name']} ({md_type})")
                    text_lines.append(f"    {info['description']}")
                text_lines.append("")
            
            # Fallback simple modal dialog using a read-only multiline TextCtrl
            dialog = wx.Dialog(self, title="Common MD Files", size=(750, 550))
            vbox = wx.BoxSizer(wx.VERTICAL)
            text_ctrl = wx.TextCtrl(
                dialog,
                value="\n".join(text_lines),
                style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL,
                size=(-1, 460)
            )
            # Use monospaced font
            text_ctrl.SetFont(wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            vbox.Add(text_ctrl, 1, wx.ALL | wx.EXPAND, 10)
            btn = wx.Button(dialog, wx.ID_OK, label="Close")
            vbox.Add(btn, 0, wx.ALIGN_RIGHT | wx.ALL, 10)
            dialog.SetSizer(vbox)
            dialog.Layout()
            dialog.ShowModal()
            dialog.Destroy()


    class ProjectGeneratorApp(wx.App):
        """Main wxPython application class for the project generator."""
        
        def OnInit(self):
            """Initialize the application."""
            frame = ProjectGeneratorFrame()
            frame.Show()
            return True

else:
    # Dummy classes when wxPython is not available
    class ProjectGeneratorFrame:
        """Dummy frame class when wxPython is not available."""
        pass
    
    class ProjectGeneratorApp:
        """Dummy app class when wxPython is not available."""
        pass


def main() -> int:
    """
    Main entry point for the project generator GUI.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    if not WX_AVAILABLE:
        print("Error: wxPython is not installed.")
        print("Install it with: pip install wxpython")
        print("")
        print("On macOS, you might need to use:")
        print("  pip install -U wxpython")
        print("")
        print("On Linux, you might need to install system dependencies first:")
        print("  sudo apt-get install libgtk-3-dev libwebkitgtk-3.0-dev")
        print("  pip install wxpython")
        return 1
    
    setup_logging(level="INFO")
    
    app = ProjectGeneratorApp()
    app.MainLoop()
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 