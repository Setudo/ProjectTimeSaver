from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QProgressBar, QScrollArea, QTextEdit, QTreeWidget, QTreeWidgetItem, QSplitter, QFormLayout, QSpinBox, QDoubleSpinBox, QInputDialog, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QMessageBox
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QFont
from pathlib import Path
import os
from explain import collect_code_file_paths
from config import load_config, save_config
from tester import get_test_sets_list, read_test_csv, get_next_test_set_number
from aihandler import get_available_models

# Modern dark theme with programmer-focused design
GRADIENT_BACKGROUND = """
QWidget {
    background-color: #0f1419;
}
"""

COLOR_PRIMARY_DARK = "#0f1419"
COLOR_SURFACE = "#1a1f2e"
COLOR_SURFACE_LIGHT = "#252d3d"
COLOR_ACCENT_BLUE = "#00a8e8"
COLOR_ACCENT_DARK_BLUE = "#0d47a1"
COLOR_TEXT_PRIMARY = "#e0e0e0"
COLOR_TEXT_SECONDARY = "#a0a0a0"
COLOR_ERROR = "#ff5252"
COLOR_SUCCESS = "#4caf50"
COLOR_WARNING = "#ff9800"
COLOR_ACCENT_RED = "#c41c3b"
COLOR_ACCENT_GREEN = "#4caf50"


def generate_tree_structure(folder_path, prefix="", max_depth=10, current_depth=0, ignore_folders={'.git', '__pycache__', '.pytest_cache', 'node_modules', '.venv', 'venv'}):
    """
    Generate a tree structure representation of a folder.
    Returns a list of strings representing the tree.
    
    Args:
        folder_path: The root path to scan
        prefix: Current prefix for tree formatting
        max_depth: Maximum depth to traverse
        current_depth: Current recursion depth
        ignore_folders: Set of folder names to ignore
    """
    if current_depth >= max_depth:
        return []
    
    tree_lines = []
    
    try:
        # Get all items in the directory
        items = []
        if os.path.isdir(folder_path):
            try:
                items = sorted(os.listdir(folder_path))
            except (PermissionError, OSError):
                return [f"{prefix}├── [Permission Denied]"]
        
        # Filter out ignored folders
        items = [item for item in items if item not in ignore_folders]
        
        # Separate directories and files, with directories first
        dirs = [item for item in items if os.path.isdir(os.path.join(folder_path, item))]
        files = [item for item in items if os.path.isfile(os.path.join(folder_path, item))]
        
        all_items = dirs + files
        
        for idx, item in enumerate(all_items):
            item_path = os.path.join(folder_path, item)
            is_last = idx == len(all_items) - 1
            
            # Determine the connector
            connector = "└── " if is_last else "├── "
            
            # Determine the icon
            if os.path.isdir(item_path):
                icon = "📁 "
                tree_lines.append(f"{prefix}{connector}{icon}{item}/")
                
                # Recurse into subdirectories
                extension = "    " if is_last else "│   "
                sub_tree = generate_tree_structure(
                    item_path, 
                    prefix + extension,
                    max_depth,
                    current_depth + 1,
                    ignore_folders
                )
                tree_lines.extend(sub_tree)
            else:
                icon = "📄 "
                tree_lines.append(f"{prefix}{connector}{icon}{item}")
        
        # If folder is empty
        if not all_items and current_depth > 0:
            tree_lines.append(f"{prefix}└── [empty]")
    
    except Exception as e:
        tree_lines.append(f"{prefix}[Error: {str(e)[:20]}...]")
    
    return tree_lines



class BaseScreen(QWidget):
    """Base class for all screens with a back button."""
    back_pressed = Signal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top bar with back button and repo indicator
        top_bar = QWidget()
        top_bar.setStyleSheet(f"background-color: {COLOR_SURFACE}; border-bottom: 1px solid {COLOR_SURFACE_LIGHT};")
        top_bar.setFixedHeight(56)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 0, 20, 0)

        back_button = QPushButton("← Back")
        back_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_SURFACE_LIGHT};
                border-radius: 0px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 500;
                font-family: 'Courier New', monospace;
            }}
            QPushButton:hover {{
                background-color: {COLOR_SURFACE_LIGHT};
                border: 1px solid {COLOR_ACCENT_BLUE};
                color: {COLOR_ACCENT_BLUE};
            }}
            QPushButton:pressed {{
                background-color: {COLOR_ACCENT_DARK_BLUE};
                border: 1px solid {COLOR_ACCENT_BLUE};
                color: {COLOR_ACCENT_BLUE};
            }}
        """)
        back_button.setCursor(Qt.PointingHandCursor)
        back_button.clicked.connect(self.back_pressed.emit)
        back_button.setFixedWidth(100)

        top_layout.addWidget(back_button)
        
        # Repo indicator (center)
        self.repo_indicator = QLabel()
        self.repo_indicator.setAlignment(Qt.AlignCenter)
        self.repo_indicator.setStyleSheet(f"""
            QLabel {{
                background-color: transparent;
                color: {COLOR_ACCENT_BLUE};
                border: 1px solid {COLOR_ACCENT_DARK_BLUE};
                border-radius: 0px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 500;
                font-family: 'Courier New', monospace;
            }}
        """)
        self.repo_indicator.setVisible(False)
        top_layout.addWidget(self.repo_indicator)
        
        top_layout.addStretch()

        main_layout.addWidget(top_bar)

        # Content area
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background-color: transparent;")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        main_layout.addWidget(self.content_widget)

    def add_content(self, widget):
        """Add a widget to the content area."""
        self.content_layout.addWidget(widget)

    def add_stretch(self):
        """Add stretch to the content layout."""
        self.content_layout.addStretch()
    
    def set_repo_info(self, repo_url):
        """Display repo information in the top bar."""
        if repo_url:
            # Extract repo name from URL
            repo_name = repo_url.rstrip('/').split('/')[-1]
            self.repo_indicator.setText(f"Repo: {repo_name} currently linked")
            self.repo_indicator.setVisible(True)
        else:
            self.repo_indicator.setVisible(False)


class BlueScreen(BaseScreen):
    repo_overview_requested = Signal()
    file_overview_requested = Signal(str)

    def __init__(self):
        super().__init__()
        self.setStyleSheet(GRADIENT_BACKGROUND)
        self.repo_folder_path = None
        self.selected_file_path = None

        scroll_style = f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {COLOR_SURFACE};
                width: 8px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background-color: {COLOR_SURFACE_LIGHT};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {COLOR_ACCENT_BLUE};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet(scroll_style)

        scroll_container = QWidget()
        scroll_container.setStyleSheet("background-color: transparent;")
        scroll_layout = QVBoxLayout(scroll_container)
        scroll_layout.setContentsMargins(40, 40, 40, 40)
        scroll_layout.setSpacing(20)

        # Add content
        title = QLabel("Repository Overview")
        title.setStyleSheet(f"background-color: transparent; font-size: 32px; font-weight: bold; color: {COLOR_ACCENT_BLUE};")
        title.setFont(QFont("Courier New", 28, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        scroll_layout.addWidget(title)
        
        description = QLabel("View the file structure and generate an instruction set for your repository.")
        description.setStyleSheet(f"background-color: transparent; font-size: 14px; color: {COLOR_TEXT_SECONDARY}; text-align: center;")
        description.setAlignment(Qt.AlignCenter)
        scroll_layout.addWidget(description)

        controls_container = QWidget()
        controls_container.setStyleSheet("background-color: transparent;")
        controls_layout = QHBoxLayout(controls_container)
        controls_layout.setSpacing(12)
        controls_layout.setContentsMargins(0, 0, 0, 0)

        button_style = f"""
            QPushButton {{
                background-color: {COLOR_SURFACE};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_SURFACE_LIGHT};
                border-radius: 0px;
                padding: 10px 16px;
                font-size: 12px;
                font-weight: 600;
                font-family: 'Courier New', monospace;
            }}
            QPushButton:hover {{
                background-color: {COLOR_SURFACE_LIGHT};
                border: 1px solid {COLOR_ACCENT_BLUE};
                color: {COLOR_ACCENT_BLUE};
            }}
            QPushButton:pressed {{
                background-color: {COLOR_ACCENT_BLUE};
                color: #0f1419;
            }}
        """

        self.overview_button = QPushButton("Generate repo overview")
        self.overview_button.setStyleSheet(button_style)
        self.overview_button.setCursor(Qt.PointingHandCursor)
        self.overview_button.setEnabled(False)
        self.overview_button.clicked.connect(self._on_overview_button_clicked)
        controls_layout.addWidget(self.overview_button)

        self.clear_selection_button = QPushButton("Clear selection")
        self.clear_selection_button.setStyleSheet(button_style)
        self.clear_selection_button.setCursor(Qt.PointingHandCursor)
        self.clear_selection_button.setVisible(False)
        self.clear_selection_button.clicked.connect(self.clear_file_selection)
        controls_layout.addWidget(self.clear_selection_button)

        self.instructions_button = QPushButton("Usage instructions")
        self.instructions_button.setStyleSheet(button_style)
        self.instructions_button.setCursor(Qt.PointingHandCursor)
        self.instructions_button.setEnabled(False)
        self.instructions_button.setToolTip("Coming soon")
        controls_layout.addWidget(self.instructions_button)

        self.tree_button = QPushButton("Toggle file tree")
        self.tree_button.setStyleSheet(button_style)
        self.tree_button.setCursor(Qt.PointingHandCursor)
        self.tree_button.setEnabled(False)
        self.tree_button.clicked.connect(self.toggle_file_tree)
        self.tree_button.setToolTip("Show or hide the repository file tree")
        controls_layout.addWidget(self.tree_button)

        scroll_layout.addWidget(controls_container)

        self.file_tree_label = QLabel("Repository file tree")
        self.file_tree_label.setStyleSheet(f"background-color: transparent; font-size: 13px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        self.file_tree_label.setAlignment(Qt.AlignLeft)
        self.file_tree_label.setVisible(False)
        scroll_layout.addWidget(self.file_tree_label)

        self.selected_file_label = QLabel("No file selected.")
        self.selected_file_label.setStyleSheet(f"background-color: transparent; font-size: 11px; color: {COLOR_TEXT_SECONDARY};")
        self.selected_file_label.setAlignment(Qt.AlignLeft)
        self.selected_file_label.setVisible(False)
        scroll_layout.addWidget(self.selected_file_label)

        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderHidden(True)
        self.file_tree.setVisible(False)
        self.file_tree.setStyleSheet(f"background-color: {COLOR_SURFACE}; color: {COLOR_TEXT_PRIMARY}; border: 1px solid {COLOR_SURFACE_LIGHT}; font-family: 'Courier New', monospace; font-size: 11px;")
        self.file_tree.setSelectionMode(QTreeWidget.SingleSelection)
        self.file_tree.itemSelectionChanged.connect(self._on_tree_selection_changed)

        self.file_preview = QTextEdit()
        self.file_preview.setReadOnly(True)
        self.file_preview.setVisible(False)
        self.file_preview.setMinimumHeight(280)
        self.file_preview.setStyleSheet(f"background-color: {COLOR_SURFACE}; color: {COLOR_TEXT_PRIMARY}; border: 1px solid {COLOR_SURFACE_LIGHT}; font-family: 'Courier New', monospace; font-size: 11px;")
        self.file_preview.setPlaceholderText("Select a file to preview its contents.")

        self.file_tree_splitter = QSplitter(Qt.Horizontal)
        self.file_tree_splitter.addWidget(self.file_tree)
        self.file_tree_splitter.addWidget(self.file_preview)
        self.file_tree_splitter.setStretchFactor(0, 1)
        self.file_tree_splitter.setStretchFactor(1, 2)
        self.file_tree_splitter.setVisible(False)
        scroll_layout.addWidget(self.file_tree_splitter)

        # Progress bar + cancel button (hidden by default)
        progress_row = QWidget()
        progress_row.setStyleSheet("background-color: transparent;")
        progress_layout = QHBoxLayout(progress_row)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(10)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Generating... %p%")
        self.progress_bar.setMinimumHeight(24)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLOR_SURFACE};
                border: 1px solid {COLOR_SURFACE_LIGHT};
                border-radius: 0px;
                color: {COLOR_TEXT_PRIMARY};
                font-family: 'Courier New', monospace;
                font-size: 11px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {COLOR_ACCENT_BLUE};
            }}
        """)
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)

        self.cancel_gen_button = QPushButton("Cancel")
        self.cancel_gen_button.setFixedWidth(80)
        self.cancel_gen_button.setMinimumHeight(24)
        self.cancel_gen_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_SURFACE};
                color: {COLOR_ERROR};
                border: 1px solid {COLOR_SURFACE_LIGHT};
                border-radius: 0px;
                font-size: 11px;
                font-weight: 500;
                font-family: 'Courier New', monospace;
            }}
            QPushButton:hover {{
                background-color: {COLOR_ERROR};
                border: 1px solid {COLOR_ERROR};
                color: #0f1419;
            }}
            QPushButton:pressed {{
                background-color: {COLOR_ERROR};
                border: 1px solid {COLOR_ERROR};
                color: #0f1419;
            }}
        """)
        self.cancel_gen_button.setCursor(Qt.PointingHandCursor)
        self.cancel_gen_button.setVisible(False)
        progress_layout.addWidget(self.cancel_gen_button)

        scroll_layout.addWidget(progress_row)

        self.overview_output = QTextEdit()
        self.overview_output.setReadOnly(True)
        self.overview_output.setMinimumHeight(260)
        self.overview_output.setStyleSheet(f"background-color: {COLOR_SURFACE}; color: {COLOR_TEXT_PRIMARY}; border: 1px solid {COLOR_SURFACE_LIGHT}; font-family: 'Courier New', monospace; font-size: 12px;")
        self.overview_output.setPlaceholderText("Repository overview will appear here after generation.")
        scroll_layout.addWidget(self.overview_output)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_container)
        self.add_content(scroll_area)

    def _on_overview_button_clicked(self):
        if self.selected_file_path:
            self.file_overview_requested.emit(self.selected_file_path)
        else:
            self.repo_overview_requested.emit()

    def set_repo_ready_state(self, enabled: bool):
        self.overview_button.setEnabled(enabled)
        self.tree_button.setEnabled(enabled)
        if not enabled:
            self.clear_file_selection()
            self.overview_output.clear()
            self.overview_output.setPlaceholderText("Link a repository to enable overview generation.")
            self.hide_file_tree()

    def set_overview_text(self, text: str):
        self.overview_output.setPlainText(text)

    def show_file_tree(self, repo_folder_path: str):
        self.repo_folder_path = repo_folder_path
        self.selected_file_path = None
        self.file_tree.clear()
        self.selected_file_label.setText("No file selected.")
        self.selected_file_label.setVisible(True)
        self.clear_selection_button.setVisible(False)
        self.file_preview.clear()
        self.file_preview.setPlaceholderText("Select a file to preview its contents.")
        self.file_tree.setVisible(True)
        self.file_preview.setVisible(True)
        self.file_tree_splitter.setVisible(True)
        self.file_tree_label.setVisible(True)
        self.tree_button.setText("Hide file tree")
        self._update_overview_button_label()

        root_item = self._build_tree_item(Path(repo_folder_path))
        if root_item is not None:
            self.file_tree.addTopLevelItem(root_item)

        # Start with the tree hidden
        self.file_tree_splitter.setVisible(False)
        self.file_tree_label.setVisible(False)
        self.selected_file_label.setVisible(False)
        self.tree_button.setText("Show file tree")


    def hide_file_tree(self):
        self.file_tree.setVisible(False)
        self.file_preview.setVisible(False)
        self.file_tree_splitter.setVisible(False)
        self.file_tree_label.setVisible(False)
        self.selected_file_label.setVisible(False)
        self.clear_selection_button.setVisible(False)
        self.tree_button.setText("Show file tree")
        self.repo_folder_path = None
        self.selected_file_path = None

    def toggle_file_tree(self):
        if self.file_tree_splitter.isVisible():
            self.file_tree_splitter.setVisible(False)
            self.file_tree_label.setVisible(False)
            self.selected_file_label.setVisible(False)
            self.clear_selection_button.setVisible(False)
            self.tree_button.setText("Show file tree")
        else:
            self.file_tree_splitter.setVisible(True)
            self.file_tree_label.setVisible(True)
            self.selected_file_label.setVisible(True)
            if self.selected_file_path:
                self.clear_selection_button.setVisible(True)
            self.tree_button.setText("Hide file tree")

    def _build_tree_item(self, path: Path, depth: int = 0, max_depth: int = 5):
        if depth > max_depth:
            return None
        item = QTreeWidgetItem([path.name or str(path)])
        item.setData(0, Qt.UserRole, str(path))
        if path.is_dir():
            try:
                entries = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            except Exception:
                return item
            ignore_dirs = {'.git', '__pycache__', '.pytest_cache', 'node_modules', '.venv', 'venv', 'dist', 'build', 'migrations', 'tests', 'test'}
            for child in entries:
                if child.name in ignore_dirs or child.name.startswith('.'):
                    continue
                child_item = self._build_tree_item(child, depth + 1, max_depth)
                if child_item is not None:
                    item.addChild(child_item)
        return item

    def _on_tree_selection_changed(self):
        selected_items = self.file_tree.selectedItems()
        if not selected_items:
            self.clear_file_selection()
            return
        item = selected_items[0]
        file_path = item.data(0, Qt.UserRole)
        if not file_path or not os.path.isfile(file_path):
            self.clear_file_selection()
            return
        self.selected_file_path = file_path
        self.selected_file_label.setText(f"Selected file: {os.path.relpath(file_path, self.repo_folder_path)}")
        self.clear_selection_button.setVisible(True)
        self._update_overview_button_label()
        self._load_file_preview(file_path)

    def _load_file_preview(self, file_path: str):
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
        file_suffix = Path(file_path).suffix.lower()
        try:
            if file_suffix in image_extensions:
                image_url = QUrl.fromLocalFile(file_path).toString()
                self.file_preview.setHtml(
                    f"<div style='background-color: {COLOR_SURFACE}; color: {COLOR_TEXT_PRIMARY};'>"
                    f"<img src='{image_url}' style='max-width: 100%; max-height: 100%; display:block; margin:auto;' />"
                    "</div>"
                )
            else:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as fh:
                    content = fh.read(14000)
                self.file_preview.setPlainText(content or "[File is empty or could not be read.]")
        except Exception as exc:
            self.file_preview.setPlainText(f"Unable to preview file: {exc}")

    def clear_file_selection(self):
        self.selected_file_path = None
        self.file_tree.clearSelection()
        self.selected_file_label.setText("No file selected.")
        self.clear_selection_button.setVisible(False)
        self.file_preview.clear()
        self.file_preview.setPlaceholderText("Select a file to preview its contents.")
        self._update_overview_button_label()

    def _update_overview_button_label(self):
        if self.selected_file_path:
            self.overview_button.setText("Generate file overview")
        else:
            self.overview_button.setText("Generate repo overview")

    def show_generation_progress(self):
        """Show the progress bar and cancel button, disable generate button."""
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Generating... %p%")
        self.progress_bar.setVisible(True)
        self.cancel_gen_button.setVisible(True)
        self.overview_button.setEnabled(False)

    def update_generation_progress(self, value: int):
        """Update the progress bar value (0-100)."""
        self.progress_bar.setValue(value)

    def hide_generation_progress(self, cancelled: bool = False):
        """Hide the progress bar and cancel button, re-enable generate button."""
        self.progress_bar.setVisible(False)
        self.cancel_gen_button.setVisible(False)
        self.overview_button.setEnabled(True)
        if cancelled:
            self.overview_output.setPlaceholderText("Generation cancelled.")


class SettingsScreen(BaseScreen):
    """Screen for editing config.toml values."""

    def __init__(self):
        super().__init__()
        self.setStyleSheet(GRADIENT_BACKGROUND)
        self.init_settings_ui()
        self.load_settings()

    def init_settings_ui(self):
        # Shared styles for form labels and input widgets
        label_style = f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px; font-family: 'Courier New', monospace; background-color: transparent;"
        spinbox_style = f"""
            QSpinBox, QDoubleSpinBox {{
                background-color: {COLOR_SURFACE_LIGHT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_SURFACE_LIGHT};
                border-radius: 0px;
                padding: 4px 8px;
                font-size: 13px;
                font-family: 'Courier New', monospace;
                min-width: 120px;
            }}
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border: 1px solid {COLOR_ACCENT_BLUE};
            }}
            QSpinBox::up-button, QDoubleSpinBox::up-button,
            QSpinBox::down-button, QDoubleSpinBox::down-button {{
                background-color: {COLOR_SURFACE};
                border: none;
                width: 18px;
            }}
            QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 5px solid {COLOR_TEXT_PRIMARY};
            }}
            QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {COLOR_TEXT_PRIMARY};
            }}
        """

        # Outer wrapper to restore padding for the settings header and save button
        outer_container = QWidget()
        outer_container.setStyleSheet("background-color: transparent;")
        outer_layout = QVBoxLayout(outer_container)
        outer_layout.setContentsMargins(40, 40, 40, 40)
        outer_layout.setSpacing(20)

        title = QLabel("Settings")
        title.setStyleSheet(f"background-color: transparent; font-size: 32px; font-weight: bold; color: {COLOR_TEXT_SECONDARY};")
        title.setFont(QFont("Courier New", 28, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        outer_layout.addWidget(title)

        description = QLabel("Update configuration values stored in config.toml.")
        description.setStyleSheet(f"background-color: transparent; font-size: 14px; color: {COLOR_TEXT_SECONDARY};")
        description.setAlignment(Qt.AlignCenter)
        outer_layout.addWidget(description)

        # --- Scrollable form area ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {COLOR_SURFACE};
                width: 8px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background-color: {COLOR_SURFACE_LIGHT};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {COLOR_ACCENT_BLUE};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        form_container = QWidget()
        form_container.setStyleSheet(f"background-color: {COLOR_SURFACE}; border: 1px solid {COLOR_SURFACE_LIGHT};")
        form_layout = QFormLayout(form_container)
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        form_layout.setHorizontalSpacing(24)
        form_layout.setVerticalSpacing(18)
        form_layout.setContentsMargins(24, 24, 24, 24)

        def make_label(text):
            lbl = QLabel(text)
            lbl.setStyleSheet(label_style)
            return lbl

        self.max_tokens_input = QSpinBox()
        self.max_tokens_input.setRange(1, 32768)
        self.max_tokens_input.setStyleSheet(spinbox_style)
        self.max_tokens_input.setToolTip("Global max tokens fallback for the AI completion engine.")
        form_layout.addRow(make_label("AI max tokens (global):"), self.max_tokens_input)

        self.overview_max_tokens_input = QSpinBox()
        self.overview_max_tokens_input.setRange(1, 32768)
        self.overview_max_tokens_input.setStyleSheet(spinbox_style)
        self.overview_max_tokens_input.setToolTip("Max tokens used when generating repository/file overviews.")
        form_layout.addRow(make_label("Overview max tokens:"), self.overview_max_tokens_input)

        self.explain_max_tokens_input = QSpinBox()
        self.explain_max_tokens_input.setRange(1, 32768)
        self.explain_max_tokens_input.setStyleSheet(spinbox_style)
        self.explain_max_tokens_input.setToolTip("Minimum tokens used when generating code explanations and annotations. For annotation, the actual limit scales to at least 1.5× the file size, so this acts as a floor.")
        form_layout.addRow(make_label("Code explanation max tokens:"), self.explain_max_tokens_input)

        self.test_max_tokens_input = QSpinBox()
        self.test_max_tokens_input.setRange(1, 32768)
        self.test_max_tokens_input.setStyleSheet(spinbox_style)
        self.test_max_tokens_input.setToolTip("Max tokens used when generating test scenarios and code templates.")
        form_layout.addRow(make_label("Test creation max tokens:"), self.test_max_tokens_input)

        self.temperature_input = QDoubleSpinBox()
        self.temperature_input.setDecimals(2)
        self.temperature_input.setRange(0.0, 2.0)
        self.temperature_input.setSingleStep(0.05)
        self.temperature_input.setStyleSheet(spinbox_style)
        self.temperature_input.setToolTip("Temperature for AI completion sampling.")
        form_layout.addRow(make_label("AI temperature:"), self.temperature_input)

        self.repeat_penalty_input = QDoubleSpinBox()
        self.repeat_penalty_input.setDecimals(2)
        self.repeat_penalty_input.setRange(1.0, 2.0)
        self.repeat_penalty_input.setSingleStep(0.05)
        self.repeat_penalty_input.setStyleSheet(spinbox_style)
        self.repeat_penalty_input.setToolTip(
            "Penalises repeated tokens to prevent the model looping. "
            "1.0 = no penalty, 1.1–1.3 recommended for small models."
        )
        form_layout.addRow(make_label("Repeat penalty:"), self.repeat_penalty_input)

        self.max_download_size_input = QSpinBox()
        self.max_download_size_input.setRange(1, 4096)
        self.max_download_size_input.setSuffix(" MB")
        self.max_download_size_input.setStyleSheet(spinbox_style)
        self.max_download_size_input.setToolTip("Maximum repository download size.")
        form_layout.addRow(make_label("Max download size:"), self.max_download_size_input)

        # Model selector — populated from the models directory
        combobox_style = f"""
            QComboBox {{
                background-color: {COLOR_SURFACE_LIGHT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_SURFACE_LIGHT};
                border-radius: 0px;
                padding: 4px 8px;
                font-size: 13px;
                font-family: 'Courier New', monospace;
                min-width: 300px;
            }}
            QComboBox:focus {{
                border: 1px solid {COLOR_ACCENT_BLUE};
            }}
            QComboBox::drop-down {{
                background-color: {COLOR_SURFACE};
                border: none;
                width: 24px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLOR_SURFACE};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_SURFACE_LIGHT};
                selection-background-color: {COLOR_ACCENT_DARK_BLUE};
                selection-color: {COLOR_TEXT_PRIMARY};
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }}
        """
        self.model_selector = QComboBox()
        self.model_selector.setStyleSheet(combobox_style)
        self.model_selector.setToolTip("Select which model to use for AI generation. Changes take effect on next generation.")
        self._populate_model_selector()
        form_layout.addRow(make_label("AI model:"), self.model_selector)

        scroll_area.setWidget(form_container)
        outer_layout.addWidget(scroll_area)

        # --- Save button row (always visible, outside scroll area) ---
        button_row = QWidget()
        button_row.setStyleSheet("background-color: transparent;")
        button_layout = QHBoxLayout(button_row)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(12)

        self.save_button = QPushButton("Save settings")
        self.save_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_SURFACE};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_SURFACE_LIGHT};
                border-radius: 0px;
                padding: 10px 16px;
                font-size: 12px;
                font-weight: 600;
                font-family: 'Courier New', monospace;
            }}
            QPushButton:hover {{
                background-color: {COLOR_SURFACE_LIGHT};
                border: 1px solid {COLOR_ACCENT_BLUE};
                color: {COLOR_ACCENT_BLUE};
            }}
            QPushButton:pressed {{
                background-color: {COLOR_ACCENT_GREEN};
                color: #0f1419;
            }}
        """)
        self.save_button.setCursor(Qt.PointingHandCursor)
        self.save_button.clicked.connect(self._on_save_clicked)
        button_layout.addWidget(self.save_button)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"background-color: transparent; color: {COLOR_TEXT_SECONDARY}; font-size: 12px;")
        self.status_label.setAlignment(Qt.AlignLeft)
        button_layout.addWidget(self.status_label)

        outer_layout.addWidget(button_row)
        self.add_content(outer_container)

    def _populate_model_selector(self):
        """Fill the model dropdown with available .gguf files from the models directory."""
        self.model_selector.clear()
        models = get_available_models()
        if not models:
            self.model_selector.addItem("(no models found)")
            self.model_selector.setEnabled(False)
        else:
            self.model_selector.setEnabled(True)
            for name in models:
                self.model_selector.addItem(name)

    def load_settings(self):
        try:
            config_values = load_config()
            self.max_tokens_input.setValue(int(config_values["ai"]["max_tokens"]))
            self.overview_max_tokens_input.setValue(int(config_values["ai"]["overview_max_tokens"]))
            self.explain_max_tokens_input.setValue(int(config_values["ai"]["explain_max_tokens"]))
            self.test_max_tokens_input.setValue(int(config_values["ai"]["test_max_tokens"]))
            self.temperature_input.setValue(float(config_values["ai"]["temperature"]))
            self.repeat_penalty_input.setValue(float(config_values["ai"].get("repeat_penalty", 1.15)))
            self.max_download_size_input.setValue(int(config_values["repo"]["max_download_size_mb"]))

            # Restore saved model selection
            saved_model = config_values["ai"].get("selected_model", "")
            if saved_model:
                idx = self.model_selector.findText(saved_model)
                if idx >= 0:
                    self.model_selector.setCurrentIndex(idx)

            self.set_status_text("Loaded settings from config.toml.")
        except Exception as e:
            self.set_status_text(f"Unable to load settings: {e}")

    def _on_save_clicked(self):
        try:
            selected_model = self.model_selector.currentText() if self.model_selector.isEnabled() else ""
            new_settings = {
                "ai": {
                    "max_tokens": int(self.max_tokens_input.value()),
                    "overview_max_tokens": int(self.overview_max_tokens_input.value()),
                    "explain_max_tokens": int(self.explain_max_tokens_input.value()),
                    "test_max_tokens": int(self.test_max_tokens_input.value()),
                    "temperature": float(self.temperature_input.value()),
                    "repeat_penalty": float(self.repeat_penalty_input.value()),
                    "selected_model": selected_model,
                },
                "repo": {
                    "max_download_size_mb": int(self.max_download_size_input.value()),
                },
            }
            save_config(new_settings)
            self.set_status_text("Settings saved. Restart may be required for all modules.")
        except Exception as e:
            self.set_status_text(f"Failed to save settings: {e}")

    def set_status_text(self, text: str):
        self.status_label.setText(text)


class RedScreen(BaseScreen):
    refresh_files_requested = Signal()
    code_explanation_requested = Signal(str)
    annotate_file_requested = Signal(str)
    save_annotated_file_requested = Signal(str, str, str)

    def __init__(self):
        super().__init__()
        self.setStyleSheet(GRADIENT_BACKGROUND)
        self.repo_folder_path = None
        self.selected_file_path = None
        self.annotated_content = ""

        scroll_style = f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {COLOR_SURFACE};
                width: 8px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background-color: {COLOR_SURFACE_LIGHT};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {COLOR_ACCENT_BLUE};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet(scroll_style)

        scroll_container = QWidget()
        scroll_container.setStyleSheet("background-color: transparent;")
        scroll_layout = QVBoxLayout(scroll_container)
        scroll_layout.setContentsMargins(40, 40, 40, 40)
        scroll_layout.setSpacing(20)

        # Add content
        title = QLabel("Code Annoation")
        title.setStyleSheet(f"background-color: transparent; font-size: 32px; font-weight: bold; color: {COLOR_ACCENT_RED};")
        title.setFont(QFont("Courier New", 28, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        scroll_layout.addWidget(title)

        description = QLabel("Browse repository code files, generate explanations, annotate functions, and save annotated versions.")
        description.setStyleSheet(f"background-color: transparent; font-size: 14px; color: {COLOR_TEXT_SECONDARY}; text-align: center;")
        description.setAlignment(Qt.AlignCenter)
        scroll_layout.addWidget(description)

        control_row = QWidget()
        control_row.setStyleSheet("background-color: transparent;")
        control_layout = QHBoxLayout(control_row)
        control_layout.setSpacing(12)
        control_layout.setContentsMargins(0, 0, 0, 0)

        button_style = f"""
            QPushButton {{
                background-color: {COLOR_SURFACE};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_SURFACE_LIGHT};
                border-radius: 0px;
                padding: 10px 16px;
                font-size: 12px;
                font-weight: 600;
                font-family: 'Courier New', monospace;
            }}
            QPushButton:hover {{
                background-color: {COLOR_SURFACE_LIGHT};
                border: 1px solid {COLOR_ACCENT_BLUE};
                color: {COLOR_ACCENT_BLUE};
            }}
            QPushButton:pressed {{
                background-color: {COLOR_ACCENT_RED};
                color: #0f1419;
            }}
        """

        self.refresh_button = QPushButton("Refresh file list")
        self.refresh_button.setStyleSheet(button_style)
        self.refresh_button.setCursor(Qt.PointingHandCursor)
        self.refresh_button.clicked.connect(self.refresh_files_requested.emit)
        control_layout.addWidget(self.refresh_button)

        self.explain_button = QPushButton("Generate explanation")
        self.explain_button.setStyleSheet(button_style)
        self.explain_button.setCursor(Qt.PointingHandCursor)
        self.explain_button.setEnabled(False)
        self.explain_button.clicked.connect(self._on_explain_clicked)
        control_layout.addWidget(self.explain_button)

        self.annotate_button = QPushButton("Annotate with comments")
        self.annotate_button.setStyleSheet(button_style)
        self.annotate_button.setCursor(Qt.PointingHandCursor)
        self.annotate_button.setEnabled(False)
        self.annotate_button.clicked.connect(self._on_annotate_clicked)
        control_layout.addWidget(self.annotate_button)

        self.save_button = QPushButton("Save annotated file")
        self.save_button.setStyleSheet(button_style)
        self.save_button.setCursor(Qt.PointingHandCursor)
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self._on_save_clicked)
        control_layout.addWidget(self.save_button)

        scroll_layout.addWidget(control_row)

        self.status_label = QLabel("Link a repository to load code files.")
        self.status_label.setStyleSheet(f"background-color: transparent; font-size: 12px; color: {COLOR_TEXT_SECONDARY};")
        self.status_label.setAlignment(Qt.AlignLeft)
        scroll_layout.addWidget(self.status_label)

        self.file_tree_label = QLabel("Code files in repository")
        self.file_tree_label.setStyleSheet(f"background-color: transparent; font-size: 13px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        self.file_tree_label.setAlignment(Qt.AlignLeft)
        self.file_tree_label.setVisible(False)
        scroll_layout.addWidget(self.file_tree_label)

        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderHidden(True)
        self.file_tree.setStyleSheet(f"background-color: {COLOR_SURFACE}; color: {COLOR_TEXT_PRIMARY}; border: 1px solid {COLOR_SURFACE_LIGHT}; font-family: 'Courier New', monospace; font-size: 11px;")
        self.file_tree.setSelectionMode(QTreeWidget.SingleSelection)
        self.file_tree.itemSelectionChanged.connect(self._on_file_selection_changed)

        self.file_preview = QTextEdit()
        self.file_preview.setReadOnly(True)
        self.file_preview.setStyleSheet(f"background-color: {COLOR_SURFACE}; color: {COLOR_TEXT_PRIMARY}; border: 1px solid {COLOR_SURFACE_LIGHT}; font-family: 'Courier New', monospace; font-size: 11px;")
        self.file_preview.setMinimumHeight(260)
        self.file_preview.setPlaceholderText("Select a file to preview its contents.")

        self.tree_splitter = QSplitter(Qt.Horizontal)
        self.tree_splitter.addWidget(self.file_tree)
        self.tree_splitter.addWidget(self.file_preview)
        self.tree_splitter.setStretchFactor(0, 1)
        self.tree_splitter.setStretchFactor(1, 2)
        self.tree_splitter.setVisible(False)
        scroll_layout.addWidget(self.tree_splitter)

        # Progress bar + cancel button (hidden by default)
        red_progress_row = QWidget()
        red_progress_row.setStyleSheet("background-color: transparent;")
        red_progress_layout = QHBoxLayout(red_progress_row)
        red_progress_layout.setContentsMargins(0, 0, 0, 0)
        red_progress_layout.setSpacing(10)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Generating... %p%")
        self.progress_bar.setMinimumHeight(24)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLOR_SURFACE};
                border: 1px solid {COLOR_SURFACE_LIGHT};
                border-radius: 0px;
                color: {COLOR_TEXT_PRIMARY};
                font-family: 'Courier New', monospace;
                font-size: 11px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {COLOR_ACCENT_RED};
            }}
        """)
        self.progress_bar.setVisible(False)
        red_progress_layout.addWidget(self.progress_bar)

        self.cancel_gen_button = QPushButton("Cancel")
        self.cancel_gen_button.setFixedWidth(80)
        self.cancel_gen_button.setMinimumHeight(24)
        self.cancel_gen_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_SURFACE};
                color: {COLOR_ERROR};
                border: 1px solid {COLOR_SURFACE_LIGHT};
                border-radius: 0px;
                font-size: 11px;
                font-weight: 500;
                font-family: 'Courier New', monospace;
            }}
            QPushButton:hover {{
                background-color: {COLOR_ERROR};
                border: 1px solid {COLOR_ERROR};
                color: #0f1419;
            }}
            QPushButton:pressed {{
                background-color: {COLOR_ERROR};
                border: 1px solid {COLOR_ERROR};
                color: #0f1419;
            }}
        """)
        self.cancel_gen_button.setCursor(Qt.PointingHandCursor)
        self.cancel_gen_button.setVisible(False)
        red_progress_layout.addWidget(self.cancel_gen_button)

        scroll_layout.addWidget(red_progress_row)

        self.explanation_output = QTextEdit()
        self.explanation_output.setReadOnly(True)
        self.explanation_output.setMinimumHeight(260)
        self.explanation_output.setStyleSheet(f"background-color: {COLOR_SURFACE}; color: {COLOR_TEXT_PRIMARY}; border: 1px solid {COLOR_SURFACE_LIGHT}; font-family: 'Courier New', monospace; font-size: 12px;")
        self.explanation_output.setPlaceholderText("Explanation and annotated content will appear here.")
        self.explanation_output.setVisible(False)
        scroll_layout.addWidget(self.explanation_output)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_container)
        self.add_content(scroll_area)

    def set_repo_ready_state(self, enabled: bool):
        self.refresh_button.setEnabled(enabled)
        self.explain_button.setEnabled(enabled and bool(self.selected_file_path))
        self.annotate_button.setEnabled(enabled and bool(self.selected_file_path))
        self.save_button.setEnabled(enabled and bool(self.annotated_content))
        if not enabled:
            self.clear_selection()
            self.file_tree.clear()
            self.file_tree.setVisible(False)
            self.file_tree_label.setVisible(False)
            self.tree_splitter.setVisible(False)
            self.explanation_output.clear()
            self.explanation_output.setVisible(False)
            self.status_label.setText("Link a repository to load code files.")

    def show_code_files(self, repo_folder_path: str):
        self.repo_folder_path = repo_folder_path
        self.file_tree.clear()
        self.selected_file_path = None
        self.annotated_content = ""
        self.set_save_enabled(False)
        self.file_tree_label.setVisible(True)
        self.status_label.setText("Loaded code files. Select a file to preview and explain.")
        self.file_tree.setVisible(True)
        self.tree_splitter.setVisible(True)
        self.explanation_output.setVisible(True)

        code_files = collect_code_file_paths(repo_folder_path)
        for rel_path in code_files:
            item = QTreeWidgetItem([rel_path])
            item.setData(0, Qt.UserRole, os.path.join(repo_folder_path, rel_path))
            self.file_tree.addTopLevelItem(item)

        self.set_repo_ready_state(bool(code_files))

    def _on_file_selection_changed(self):
        selected_items = self.file_tree.selectedItems()
        if not selected_items:
            self.clear_selection()
            return
        item = selected_items[0]
        file_path = item.data(0, Qt.UserRole)
        if not file_path or not os.path.isfile(file_path):
            self.clear_selection()
            return
        self.selected_file_path = file_path
        self.status_label.setText(f"Selected file: {os.path.relpath(file_path, self.repo_folder_path)}")
        self._load_file_preview(file_path)
        self.explain_button.setEnabled(True)
        self.annotate_button.setEnabled(True)
        self.save_button.setEnabled(bool(self.annotated_content))

    def _load_file_preview(self, file_path: str):
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
        file_suffix = Path(file_path).suffix.lower()
        try:
            if file_suffix in image_extensions:
                image_url = QUrl.fromLocalFile(file_path).toString()
                self.file_preview.setHtml(
                    f"<div style='background-color: {COLOR_SURFACE}; color: {COLOR_TEXT_PRIMARY};'>"
                    f"<img src='{image_url}' style='max-width: 100%; max-height: 100%; display:block; margin:auto;' />"
                    "</div>"
                )
            else:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as fh:
                    content = fh.read(14000)
                self.file_preview.setPlainText(content or "[File is empty or could not be read.]")
        except Exception as exc:
            self.file_preview.setPlainText(f"Unable to preview file: {exc}")

    def _on_explain_clicked(self):
        if self.selected_file_path:
            self.code_explanation_requested.emit(self.selected_file_path)

    def _on_annotate_clicked(self):
        if self.selected_file_path:
            self.annotate_file_requested.emit(self.selected_file_path)

    def _on_save_clicked(self):
        if not self.selected_file_path or not self.annotated_content:
            return

        source = Path(self.selected_file_path)
        annotated_path = str(source.parent / f"{source.stem}_annotated{source.suffix}")

        # Build a themed dialog asking how to save
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Save annotated file")
        dialog.setText(
            f"How would you like to save the annotated version of <b>{source.name}</b>?"
        )
        dialog.setInformativeText(
            f"<b>Replace original</b> — overwrite <i>{source.name}</i><br>"
            f"<b>Save as annotated</b> — save as <i>{source.stem}_annotated{source.suffix}</i>"
        )
        dialog.setStyleSheet(f"""
            QMessageBox {{
                background-color: {COLOR_PRIMARY_DARK};
                color: {COLOR_TEXT_PRIMARY};
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }}
            QMessageBox QLabel {{
                background-color: transparent;
                color: {COLOR_TEXT_PRIMARY};
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }}
            QPushButton {{
                background-color: {COLOR_SURFACE};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_SURFACE_LIGHT};
                border-radius: 0px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 600;
                font-family: 'Courier New', monospace;
                min-width: 140px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_SURFACE_LIGHT};
                border: 1px solid {COLOR_ACCENT_RED};
                color: {COLOR_ACCENT_RED};
            }}
            QPushButton:pressed {{
                background-color: {COLOR_ACCENT_RED};
                color: #0f1419;
            }}
        """)

        replace_btn = dialog.addButton("Replace original", QMessageBox.AcceptRole)
        annotated_btn = dialog.addButton("Save as annotated", QMessageBox.AcceptRole)
        dialog.addButton("Cancel", QMessageBox.RejectRole)

        dialog.exec()
        clicked = dialog.clickedButton()

        if clicked is replace_btn:
            target_path = self.selected_file_path
        elif clicked is annotated_btn:
            target_path = annotated_path
        else:
            return  # Cancelled — do nothing

        self.save_annotated_file_requested.emit(self.selected_file_path, self.annotated_content, target_path)

    def set_status_text(self, text: str):
        self.status_label.setText(text)

    def set_explanation_text(self, text: str):
        self.explanation_output.setVisible(True)
        self.explanation_output.setPlainText(text)

    def set_annotated_text(self, text: str):
        self.annotated_content = text
        self.set_explanation_text(text)
        self.set_save_enabled(True)

    def set_save_enabled(self, enabled: bool):
        self.save_button.setEnabled(enabled and bool(self.selected_file_path))

    def clear_selection(self):
        self.selected_file_path = None
        self.file_tree.clearSelection()
        self.status_label.setText("Select a code file to generate an explanation.")
        self.file_preview.clear()
        self.file_preview.setPlaceholderText("Select a file to preview its contents.")
        self.explain_button.setEnabled(False)
        self.annotate_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.annotated_content = ""
        self.explanation_output.clear()

    def show_generation_progress(self):
        """Show the progress bar and cancel button, disable action buttons."""
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Generating... %p%")
        self.progress_bar.setVisible(True)
        self.cancel_gen_button.setVisible(True)
        self.explain_button.setEnabled(False)
        self.annotate_button.setEnabled(False)

    def update_generation_progress(self, value: int):
        """Update the progress bar value (0-100)."""
        self.progress_bar.setValue(value)

    def hide_generation_progress(self, cancelled: bool = False):
        """Hide the progress bar and cancel button, re-enable action buttons."""
        self.progress_bar.setVisible(False)
        self.cancel_gen_button.setVisible(False)
        has_file = bool(self.selected_file_path)
        self.explain_button.setEnabled(has_file)
        self.annotate_button.setEnabled(has_file)
        if cancelled:
            self.status_label.setText("Generation cancelled.")


class GreenScreen(BaseScreen):
    test_scenarios_requested = Signal()
    code_templates_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet(GRADIENT_BACKGROUND)
        self.repo_folder_path = None
        self.selected_file_path = None
        self.test_sets_folder = None

        scroll_style = f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {COLOR_SURFACE};
                width: 8px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background-color: {COLOR_SURFACE_LIGHT};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {COLOR_ACCENT_BLUE};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet(scroll_style)

        scroll_container = QWidget()
        scroll_container.setStyleSheet("background-color: transparent;")
        scroll_layout = QVBoxLayout(scroll_container)
        scroll_layout.setContentsMargins(40, 40, 40, 40)
        scroll_layout.setSpacing(20)

        # Add content
        title = QLabel("Test Creator")
        title.setStyleSheet(f"background-color: transparent; font-size: 32px; font-weight: bold; color: {COLOR_SUCCESS};")
        title.setFont(QFont("Courier New", 28, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        scroll_layout.addWidget(title)

        description = QLabel("Generate test scenarios and code templates, then save them as CSV files for your repository.")
        description.setStyleSheet(f"background-color: transparent; font-size: 14px; color: {COLOR_TEXT_SECONDARY}; text-align: center;")
        description.setAlignment(Qt.AlignCenter)
        scroll_layout.addWidget(description)

        control_row = QWidget()
        control_row.setStyleSheet("background-color: transparent;")
        control_layout = QHBoxLayout(control_row)
        control_layout.setSpacing(12)
        control_layout.setContentsMargins(0, 0, 0, 0)

        button_style = f"""
            QPushButton {{
                background-color: {COLOR_SURFACE};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_SURFACE_LIGHT};
                border-radius: 0px;
                padding: 10px 16px;
                font-size: 12px;
                font-weight: 600;
                font-family: 'Courier New', monospace;
            }}
            QPushButton:hover {{
                background-color: {COLOR_SURFACE_LIGHT};
                border: 1px solid {COLOR_ACCENT_BLUE};
                color: {COLOR_ACCENT_BLUE};
            }}
            QPushButton:pressed {{
                background-color: {COLOR_SUCCESS};
                color: #0f1419;
            }}
        """

        self.scenarios_button = QPushButton("Generate test scenarios")
        self.scenarios_button.setStyleSheet(button_style)
        self.scenarios_button.setCursor(Qt.PointingHandCursor)
        self.scenarios_button.setEnabled(False)
        self.scenarios_button.clicked.connect(self.test_scenarios_requested.emit)
        control_layout.addWidget(self.scenarios_button)

        self.templates_button = QPushButton("Generate code templates")
        self.templates_button.setStyleSheet(button_style)
        self.templates_button.setCursor(Qt.PointingHandCursor)
        self.templates_button.setEnabled(False)
        self.templates_button.clicked.connect(self.code_templates_requested.emit)
        control_layout.addWidget(self.templates_button)

        self.refresh_button = QPushButton("Refresh file list")
        self.refresh_button.setStyleSheet(button_style)
        self.refresh_button.setCursor(Qt.PointingHandCursor)
        self.refresh_button.clicked.connect(self._on_refresh_clicked)
        control_layout.addWidget(self.refresh_button)

        scroll_layout.addWidget(control_row)

        self.status_label = QLabel("Link a repository to generate test sets.")
        self.status_label.setStyleSheet(f"background-color: transparent; font-size: 12px; color: {COLOR_TEXT_SECONDARY};")
        self.status_label.setAlignment(Qt.AlignLeft)
        scroll_layout.addWidget(self.status_label)

        self.files_label = QLabel("Saved test sets")
        self.files_label.setStyleSheet(f"background-color: transparent; font-size: 13px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        self.files_label.setAlignment(Qt.AlignLeft)
        self.files_label.setVisible(False)
        scroll_layout.addWidget(self.files_label)

        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderHidden(True)
        self.file_tree.setStyleSheet(f"background-color: {COLOR_SURFACE}; color: {COLOR_TEXT_PRIMARY}; border: 1px solid {COLOR_SURFACE_LIGHT}; font-family: 'Courier New', monospace; font-size: 11px;")
        self.file_tree.setSelectionMode(QTreeWidget.SingleSelection)
        self.file_tree.itemSelectionChanged.connect(self._on_file_selection_changed)
        self.file_tree.setVisible(False)
        scroll_layout.addWidget(self.file_tree)

        self.file_preview = QTableWidget()
        self.file_preview.setEditTriggers(QTableWidget.NoEditTriggers)
        self.file_preview.setSelectionBehavior(QTableWidget.SelectRows)
        self.file_preview.setAlternatingRowColors(True)
        self.file_preview.setMinimumHeight(260)
        self.file_preview.setVisible(False)
        self.file_preview.horizontalHeader().setStretchLastSection(True)
        self.file_preview.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.file_preview.verticalHeader().setVisible(False)
        self.file_preview.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLOR_SURFACE};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_SURFACE_LIGHT};
                font-family: 'Courier New', monospace;
                font-size: 11px;
                gridline-color: {COLOR_SURFACE_LIGHT};
                alternate-background-color: {COLOR_SURFACE_LIGHT};
            }}
            QTableWidget::item {{
                padding: 6px 10px;
                border: none;
            }}
            QTableWidget::item:selected {{
                background-color: {COLOR_ACCENT_DARK_BLUE};
                color: {COLOR_TEXT_PRIMARY};
            }}
            QHeaderView::section {{
                background-color: {COLOR_SURFACE_LIGHT};
                color: {COLOR_ACCENT_BLUE};
                border: none;
                border-right: 1px solid {COLOR_SURFACE};
                border-bottom: 1px solid {COLOR_SURFACE};
                padding: 6px 10px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                font-weight: bold;
            }}
            QScrollBar:vertical {{
                background-color: {COLOR_SURFACE};
                width: 8px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background-color: {COLOR_SURFACE_LIGHT};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {COLOR_ACCENT_BLUE};
            }}
            QScrollBar:horizontal {{
                background-color: {COLOR_SURFACE};
                height: 8px;
                border: none;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {COLOR_SURFACE_LIGHT};
                border-radius: 4px;
                min-width: 20px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {COLOR_ACCENT_BLUE};
            }}
        """)
        scroll_layout.addWidget(self.file_preview)

        # Progress bar + cancel button (hidden by default)
        progress_row = QWidget()
        progress_row.setStyleSheet("background-color: transparent;")
        progress_layout = QHBoxLayout(progress_row)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(10)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Generating... %p%")
        self.progress_bar.setMinimumHeight(24)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLOR_SURFACE};
                border: 1px solid {COLOR_SURFACE_LIGHT};
                border-radius: 0px;
                color: {COLOR_TEXT_PRIMARY};
                font-family: 'Courier New', monospace;
                font-size: 11px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {COLOR_SUCCESS};
            }}
        """)
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)

        self.cancel_gen_button = QPushButton("Cancel")
        self.cancel_gen_button.setFixedWidth(80)
        self.cancel_gen_button.setMinimumHeight(24)
        self.cancel_gen_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_SURFACE};
                color: {COLOR_ERROR};
                border: 1px solid {COLOR_SURFACE_LIGHT};
                border-radius: 0px;
                font-size: 11px;
                font-weight: 500;
                font-family: 'Courier New', monospace;
            }}
            QPushButton:hover {{
                background-color: {COLOR_ERROR};
                border: 1px solid {COLOR_ERROR};
                color: #0f1419;
            }}
            QPushButton:pressed {{
                background-color: {COLOR_ERROR};
                border: 1px solid {COLOR_ERROR};
                color: #0f1419;
            }}
        """)
        self.cancel_gen_button.setCursor(Qt.PointingHandCursor)
        self.cancel_gen_button.setVisible(False)
        progress_layout.addWidget(self.cancel_gen_button)

        scroll_layout.addWidget(progress_row)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_container)
        self.add_content(scroll_area)

    def clear_selection(self):
        """Reset the selected file path."""
        self.selected_file_path = None

    def set_repo_ready_state(self, enabled: bool):
        """Enable/disable generation buttons based on repo state."""
        self.scenarios_button.setEnabled(enabled)
        self.templates_button.setEnabled(enabled)
        if not enabled:
            self.clear_selection()
            self.file_tree.clear()
            self.file_tree.setVisible(False)
            self.files_label.setVisible(False)
            self.file_preview.clear()
            self.file_preview.setVisible(False)
            self.status_label.setText("Link a repository to generate test sets.")

    def setup_repo(self, repo_folder_path: str, test_sets_folder: str):
        """Initialize the screen with repo and test_sets folder paths."""
        self.repo_folder_path = repo_folder_path
        self.test_sets_folder = test_sets_folder
        self.selected_file_path = None
        self.set_repo_ready_state(True)
        self.show_test_files()

    def show_test_files(self):
        """Load and display available test set files."""
        if not self.test_sets_folder:
            return

        self.file_tree.clear()
        self.selected_file_path = None
        self.file_preview.clear()

        test_files = get_test_sets_list(self.test_sets_folder)

        if not test_files:
            self.files_label.setVisible(False)
            self.file_tree.setVisible(False)
            self.file_preview.setVisible(False)
            self.status_label.setText("No test sets saved yet. Generate one to get started.")
            return

        self.files_label.setVisible(True)
        self.file_tree.setVisible(True)
        self.status_label.setText(f"Loaded {len(test_files)} test set(s). Select one to preview.")

        for filename, full_path, file_size, mod_time in test_files:
            item = QTreeWidgetItem([filename])
            item.setData(0, Qt.UserRole, full_path)
            self.file_tree.addTopLevelItem(item)

    def _on_file_selection_changed(self):
        """Handle test set file selection."""
        selected_items = self.file_tree.selectedItems()
        if not selected_items:
            self.file_preview.clear()
            self.file_preview.setVisible(False)
            return

        item = selected_items[0]
        file_path = item.data(0, Qt.UserRole)
        if not file_path or not os.path.isfile(file_path):
            return

        self.selected_file_path = file_path
        self.status_label.setText(f"Selected: {os.path.basename(file_path)}")
        self._load_file_preview(file_path)

    def _load_file_preview(self, file_path: str):
        """Load and display CSV file as a table."""
        import csv as _csv
        self.file_preview.clear()
        self.file_preview.setRowCount(0)
        self.file_preview.setColumnCount(0)
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore', newline='') as fh:
                reader = _csv.reader(fh)
                rows = list(reader)

            if not rows:
                self.file_preview.setVisible(False)
                return

            headers = rows[0]
            data_rows = rows[1:]

            self.file_preview.setColumnCount(len(headers))
            self.file_preview.setHorizontalHeaderLabels(headers)
            self.file_preview.setRowCount(len(data_rows))

            for row_idx, row in enumerate(data_rows):
                for col_idx, cell in enumerate(row):
                    item = QTableWidgetItem(cell)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    # Wrap long text in cells
                    item.setToolTip(cell)
                    self.file_preview.setItem(row_idx, col_idx, item)

            # Resize columns to content, but cap width so the table stays readable
            self.file_preview.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            self.file_preview.resizeRowsToContents()
            self.file_preview.setVisible(True)
        except Exception as exc:
            # Fall back to a single-cell error message
            self.file_preview.setColumnCount(1)
            self.file_preview.setHorizontalHeaderLabels(["Error"])
            self.file_preview.setRowCount(1)
            self.file_preview.setItem(0, 0, QTableWidgetItem(f"Unable to preview file: {exc}"))
            self.file_preview.setVisible(True)

    def _on_refresh_clicked(self):
        """Refresh the test files list."""
        self.show_test_files()
        self.status_label.setText("Test set list refreshed.")

    def show_generation_progress(self):
        """Show the progress bar and cancel button."""
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Generating... %p%")
        self.progress_bar.setVisible(True)
        self.cancel_gen_button.setVisible(True)
        self.scenarios_button.setEnabled(False)
        self.templates_button.setEnabled(False)
        self.refresh_button.setEnabled(False)

    def update_generation_progress(self, value: int):
        """Update the progress bar value (0-100)."""
        self.progress_bar.setValue(value)

    def hide_generation_progress(self, cancelled: bool = False):
        """Hide the progress bar and cancel button."""
        self.progress_bar.setVisible(False)
        self.cancel_gen_button.setVisible(False)
        self.scenarios_button.setEnabled(True)
        self.templates_button.setEnabled(True)
        self.refresh_button.setEnabled(True)
        if cancelled:
            self.status_label.setText("Generation cancelled.")

    def set_status_text(self, text: str):
        """Update status label."""
        self.status_label.setText(text)




class GitHubScreen(BaseScreen):
    repo_linked = Signal(str)
    repo_unlinked = Signal()
    cancel_download = Signal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet(GRADIENT_BACKGROUND)
        self.repo_folder_path = None

        scroll_style = f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {COLOR_SURFACE};
                width: 8px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background-color: {COLOR_SURFACE_LIGHT};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {COLOR_ACCENT_BLUE};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet(scroll_style)

        scroll_container = QWidget()
        scroll_container.setStyleSheet("background-color: transparent;")
        scroll_layout = QVBoxLayout(scroll_container)
        scroll_layout.setContentsMargins(40, 40, 40, 40)
        scroll_layout.setSpacing(20)

        # Title
        title = QLabel("Link GitHub Repository")
        title.setStyleSheet(f"background-color: transparent; font-size: 32px; font-weight: bold; color: {COLOR_ACCENT_BLUE};")
        title.setAlignment(Qt.AlignCenter)
        scroll_layout.addWidget(title)

        # Description
        description = QLabel("Enter your GitHub repository URL to link it to this project")
        description.setStyleSheet(f"background-color: transparent; font-size: 13px; color: {COLOR_TEXT_SECONDARY};")
        description.setAlignment(Qt.AlignCenter)
        scroll_layout.addWidget(description)

        spacer = QLabel()
        spacer.setStyleSheet("background-color: transparent;")
        scroll_layout.addWidget(spacer)

        # Input container
        input_container = QWidget()
        input_container.setStyleSheet("background-color: transparent;")
        input_layout = QHBoxLayout(input_container)
        input_layout.setSpacing(10)

        # Text input for GitHub URL
        from PySide6.QtWidgets import QLineEdit
        self.repo_input = QLineEdit()
        self.repo_input.setPlaceholderText("https://github.com/username/repository")
        self.repo_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLOR_SURFACE};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_SURFACE_LIGHT};
                border-radius: 0px;
                padding: 10px;
                font-size: 12px;
                font-family: 'Courier New', monospace;
            }}
            QLineEdit:focus {{
                border: 1px solid {COLOR_ACCENT_BLUE};
                background-color: {COLOR_SURFACE_LIGHT};
            }}
            QLineEdit::placeholder {{
                color: {COLOR_TEXT_SECONDARY};
            }}
        """)
        self.repo_input.setMinimumHeight(40)
        input_layout.addWidget(self.repo_input)

        # Link button
        self.link_button = QPushButton("Link Repository")
        self.link_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_ACCENT_DARK_BLUE};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_ACCENT_BLUE};
                border-radius: 0px;
                padding: 10px 20px;
                font-size: 12px;
                font-weight: 500;
                font-family: 'Courier New', monospace;
            }}
            QPushButton:hover {{
                background-color: {COLOR_ACCENT_BLUE};
                color: #0f1419;
                border: 1px solid {COLOR_ACCENT_BLUE};
            }}
            QPushButton:pressed {{
                background-color: {COLOR_ACCENT_BLUE};
                color: #0f1419;
            }}
        """)
        self.link_button.setCursor(Qt.PointingHandCursor)
        self.link_button.setFixedWidth(150)
        self.link_button.clicked.connect(self.on_link_clicked)
        input_layout.addWidget(self.link_button)

        scroll_layout.addWidget(input_container)

        # Progress bar (hidden by default)
        progress_container = QWidget()
        progress_container.setStyleSheet("background-color: transparent;")
        progress_layout = QHBoxLayout(progress_container)
        progress_layout.setSpacing(10)
        progress_layout.setContentsMargins(0, 0, 0, 0)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLOR_SURFACE};
                border: 1px solid {COLOR_SURFACE_LIGHT};
                border-radius: 0px;
                height: 20px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {COLOR_ACCENT_BLUE};
                border-radius: 0px;
            }}
        """)
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(25)
        progress_layout.addWidget(self.progress_bar)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_SURFACE};
                color: {COLOR_ERROR};
                border: 1px solid {COLOR_SURFACE_LIGHT};
                border-radius: 0px;
                padding: 5px 15px;
                font-size: 11px;
                font-weight: 500;
                font-family: 'Courier New', monospace;
            }}
            QPushButton:hover {{
                background-color: {COLOR_ERROR};
                border: 1px solid {COLOR_ERROR};
                color: #0f1419;
            }}
            QPushButton:pressed {{
                background-color: {COLOR_ERROR};
                border: 1px solid {COLOR_ERROR};
                color: #0f1419;
            }}
        """)
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        self.cancel_button.setFixedWidth(80)
        self.cancel_button.setVisible(False)
        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        progress_layout.addWidget(self.cancel_button)

        scroll_layout.addWidget(progress_container)

        # Status label
        self.status_label = QLabel()
        self.status_label.setStyleSheet(f"background-color: transparent; font-size: 11px; color: {COLOR_TEXT_SECONDARY};")
        self.status_label.setAlignment(Qt.AlignCenter)
        scroll_layout.addWidget(self.status_label)

        # Unlink button container (hidden by default)
        unlink_container = QWidget()
        unlink_container.setStyleSheet("background-color: transparent;")
        unlink_layout = QHBoxLayout(unlink_container)
        unlink_layout.setSpacing(10)
        unlink_layout.setContentsMargins(0, 0, 0, 0)

        unlink_layout.addStretch()

        self.unlink_repo_button = QPushButton("✕ Unlink Repository")
        self.unlink_repo_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_SURFACE};
                color: {COLOR_ERROR};
                border: 1px solid {COLOR_SURFACE_LIGHT};
                border-radius: 0px;
                padding: 8px 15px;
                font-size: 11px;
                font-weight: 500;
                font-family: 'Courier New', monospace;
            }}
            QPushButton:hover {{
                background-color: {COLOR_ERROR};
                border: 1px solid {COLOR_ERROR};
                color: #0f1419;
            }}
            QPushButton:pressed {{
                background-color: {COLOR_ERROR};
                border: 1px solid {COLOR_ERROR};
                color: #0f1419;
            }}
        """)
        self.unlink_repo_button.setCursor(Qt.PointingHandCursor)
        self.unlink_repo_button.setVisible(False)
        unlink_layout.addWidget(self.unlink_repo_button)

        unlink_layout.addStretch()

        scroll_layout.addWidget(unlink_container)

        # File tree section (hidden by default)
        self.tree_section_label = QLabel("Repository Structure")
        self.tree_section_label.setStyleSheet(f"background-color: transparent; font-size: 12px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        self.tree_section_label.setAlignment(Qt.AlignLeft)
        self.tree_section_label.setVisible(False)
        scroll_layout.addWidget(self.tree_section_label)

        # Tree view in a scrollable area
        self.tree_scroll = QScrollArea()
        self.tree_scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {COLOR_SURFACE};
                border: 1px solid {COLOR_SURFACE_LIGHT};
                border-radius: 0px;
            }}
            QScrollBar:vertical {{
                background-color: {COLOR_SURFACE};
                border-radius: 0px;
                width: 8px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {COLOR_SURFACE_LIGHT};
                border-radius: 0px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {COLOR_ACCENT_BLUE};
            }}
        """)
        self.tree_scroll.setWidgetResizable(True)
        self.tree_scroll.setMaximumHeight(500)
        self.tree_scroll.setVisible(False)

        self.tree_text = QLabel()
        self.tree_text.setStyleSheet(f"""
            QLabel {{
                background-color: transparent;
                color: {COLOR_TEXT_PRIMARY};
                font-family: 'Courier New', monospace;
                font-size: 10px;
                padding: 10px;
            }}
        """)
        self.tree_text.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.tree_text.setWordWrap(False)
        self.tree_scroll.setWidget(self.tree_text)

        scroll_layout.addWidget(self.tree_scroll)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_container)
        self.add_content(scroll_area)
    
    def on_link_clicked(self):
        """Handle the link repository button click."""
        repo_url = self.repo_input.text().strip()
        if repo_url:
            self.repo_linked.emit(repo_url)
    
    def on_cancel_clicked(self):
        """Handle the cancel button click."""
        self.cancel_download.emit()
    
    def show_progress(self):
        """Show the progress bar and cancel button."""
        self.progress_bar.setVisible(True)
        self.cancel_button.setVisible(True)
        self.repo_input.setEnabled(False)
        self.link_button.setEnabled(False)
        self.progress_bar.setValue(0)
    
    def hide_progress(self):
        """Hide the progress bar and cancel button."""
        self.progress_bar.setVisible(False)
        self.cancel_button.setVisible(False)
        self.repo_input.setEnabled(True)
        self.link_button.setEnabled(True)
    
    def update_progress(self, bytes_downloaded: int, total_bytes: int):
        """Update the progress bar."""
        if total_bytes > 0:
            percent = int((bytes_downloaded / total_bytes) * 100)
            self.progress_bar.setValue(percent)
            mb_downloaded = bytes_downloaded / (1024 * 1024)
            mb_total = total_bytes / (1024 * 1024)
            self.status_label.setText(f"Downloading: {mb_downloaded:.1f} / {mb_total:.1f} MiB ({percent}%)")
    
    def set_linked_status(self, repo_url):
        """Update UI to show a linked repository."""
        self.hide_progress()
        self.status_label.setText(f"✓ Linked to: {repo_url}")
        self.status_label.setStyleSheet(f"background-color: transparent; font-size: 11px; color: {COLOR_SUCCESS};")
        self.repo_input.setEnabled(False)
        self.link_button.setEnabled(False)
        self.unlink_repo_button.setVisible(True)
    
    def set_unlinked_status(self):
        """Update UI to show no linked repository."""
        self.hide_progress()
        self.update_status("", is_error=False)  # Clear status label
        self.repo_input.setEnabled(True)
        self.link_button.setEnabled(True)
        self.unlink_repo_button.setVisible(False)
        self.repo_input.clear()
        self.set_repo_info(None)
        self.hide_file_tree()

    def update_status(self, text: str, is_error: bool = False):
        """Update the status label with optional error styling."""
        self.status_label.setText(text)
        if is_error:
            self.status_label.setStyleSheet(f"background-color: transparent; font-size: 11px; color: {COLOR_ERROR};")
        else:
            self.status_label.setStyleSheet(f"background-color: transparent; font-size: 11px; color: {COLOR_TEXT_SECONDARY};")
    
    def show_file_tree(self, repo_folder_path):
        """Display the repository file structure."""
        self.repo_folder_path = repo_folder_path
        
        if not os.path.exists(repo_folder_path):
            self.tree_text.setText("[Repository folder not found]")
            self.tree_section_label.setVisible(False)
            self.tree_scroll.setVisible(False)
            return
        
        # Generate tree structure
        tree_lines = generate_tree_structure(repo_folder_path, max_depth=4)
        
        if tree_lines:
            tree_html = "\n".join(tree_lines)
            self.tree_text.setText(tree_html)
            self.tree_section_label.setVisible(True)
            self.tree_scroll.setVisible(True)
        else:
            self.tree_text.setText("[Empty repository]")
            self.tree_section_label.setVisible(False)
            self.tree_scroll.setVisible(False)
    
    def hide_file_tree(self):
        """Hide the file tree display."""
        self.tree_text.setText("")
        self.tree_section_label.setVisible(False)
        self.tree_scroll.setVisible(False)
        self.repo_folder_path = None
