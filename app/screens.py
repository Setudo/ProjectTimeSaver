from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QProgressBar, QScrollArea, QTextEdit
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import os

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
        self.content_layout.setContentsMargins(40, 40, 40, 40)
        self.content_layout.setSpacing(20)

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

    def __init__(self):
        super().__init__()
        self.setStyleSheet(GRADIENT_BACKGROUND)
        
        # Add content
        title = QLabel("Repository Overview")
        title.setStyleSheet(f"background-color: transparent; font-size: 32px; font-weight: bold; color: {COLOR_ACCENT_BLUE};")
        title.setFont(QFont("Courier New", 28, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        self.add_content(title)
        
        description = QLabel("View the file structure and generate an instruction set for your repository.")
        description.setStyleSheet(f"background-color: transparent; font-size: 14px; color: {COLOR_TEXT_SECONDARY}; text-align: center;")
        description.setAlignment(Qt.AlignCenter)
        self.add_content(description)

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
        self.overview_button.clicked.connect(lambda checked=False: self.repo_overview_requested.emit())
        controls_layout.addWidget(self.overview_button)

        self.instructions_button = QPushButton("Usage instructions")
        self.instructions_button.setStyleSheet(button_style)
        self.instructions_button.setCursor(Qt.PointingHandCursor)
        self.instructions_button.setEnabled(False)
        self.instructions_button.setToolTip("Coming soon")
        controls_layout.addWidget(self.instructions_button)

        self.tree_button = QPushButton("Interactive tree")
        self.tree_button.setStyleSheet(button_style)
        self.tree_button.setCursor(Qt.PointingHandCursor)
        self.tree_button.setEnabled(False)
        self.tree_button.setToolTip("Coming soon")
        controls_layout.addWidget(self.tree_button)

        self.add_content(controls_container)

        self.overview_output = QTextEdit()
        self.overview_output.setReadOnly(True)
        self.overview_output.setMinimumHeight(260)
        self.overview_output.setStyleSheet(f"background-color: {COLOR_SURFACE}; color: {COLOR_TEXT_PRIMARY}; border: 1px solid {COLOR_SURFACE_LIGHT}; font-family: 'Courier New', monospace; font-size: 12px;")
        self.overview_output.setPlaceholderText("Repository overview will appear here after generation.")
        self.add_content(self.overview_output)

        self.add_stretch()

    def set_repo_ready_state(self, enabled: bool):
        self.overview_button.setEnabled(enabled)
        if not enabled:
            self.overview_output.clear()
            self.overview_output.setPlaceholderText("Link a repository to enable overview generation.")

    def set_overview_text(self, text: str):
        self.overview_output.setPlainText(text)


class RedScreen(BaseScreen):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(GRADIENT_BACKGROUND)
        
        # Add content
        title = QLabel("Fix #2")
        title.setStyleSheet(f"background-color: transparent; font-size: 32px; font-weight: bold; color: {COLOR_ACCENT_RED};")
        title.setFont(QFont("Courier New", 28, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        self.add_content(title)
        
        description = QLabel("This is the red screen for Fix #2\nYour implementation goes here")
        description.setStyleSheet(f"background-color: transparent; font-size: 14px; color: {COLOR_TEXT_SECONDARY}; text-align: center;")
        description.setAlignment(Qt.AlignCenter)
        self.add_content(description)
        
        self.add_stretch()


class GreenScreen(BaseScreen):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(GRADIENT_BACKGROUND)
        
        # Add content
        title = QLabel("Fix #3")
        title.setStyleSheet(f"background-color: transparent; font-size: 32px; font-weight: bold; color: {COLOR_SUCCESS};")
        title.setFont(QFont("Courier New", 28, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        self.add_content(title)
        
        description = QLabel("This is the green screen for Fix #3\nYour implementation goes here")
        description.setStyleSheet(f"background-color: transparent; font-size: 14px; color: {COLOR_TEXT_SECONDARY}; text-align: center;")
        description.setAlignment(Qt.AlignCenter)
        self.add_content(description)
        
        self.add_stretch()


class GitHubScreen(BaseScreen):
    repo_linked = Signal(str)
    repo_unlinked = Signal()
    cancel_download = Signal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet(GRADIENT_BACKGROUND)
        self.repo_folder_path = None
        
        # Title
        title = QLabel("Link GitHub Repository")
        title.setStyleSheet(f"background-color: transparent; font-size: 32px; font-weight: bold; color: {COLOR_ACCENT_BLUE};")
        title.setAlignment(Qt.AlignCenter)
        self.add_content(title)
        
        # Description
        description = QLabel("Enter your GitHub repository URL to link it to this project")
        description.setStyleSheet(f"background-color: transparent; font-size: 13px; color: {COLOR_TEXT_SECONDARY};")
        description.setAlignment(Qt.AlignCenter)
        self.add_content(description)
        
        spacer = QLabel()
        spacer.setStyleSheet("background-color: transparent;")
        self.add_content(spacer)
        
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
        
        self.add_content(input_container)
        
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
        
        self.add_content(progress_container)
        
        # Status label
        self.status_label = QLabel()
        self.status_label.setStyleSheet(f"background-color: transparent; font-size: 11px; color: {COLOR_TEXT_SECONDARY};")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.add_content(self.status_label)
        
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
        
        self.add_content(unlink_container)
        
        # File tree section (hidden by default)
        self.tree_section_label = QLabel("Repository Structure")
        self.tree_section_label.setStyleSheet(f"background-color: transparent; font-size: 12px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        self.tree_section_label.setAlignment(Qt.AlignLeft)
        self.tree_section_label.setVisible(False)
        self.add_content(self.tree_section_label)
        
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
        
        self.add_content(self.tree_scroll)
        
        self.add_stretch()
    
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
