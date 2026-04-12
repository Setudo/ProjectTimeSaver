from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal

# Global gradient stylesheet
GRADIENT_BACKGROUND = """
QWidget {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                stop:0 #1f2937, 
                                stop:1 #111827);
}
"""


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
        top_bar.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f172a, stop:1 #030712);")
        top_bar.setFixedHeight(60)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 0, 20, 0)

        back_button = QPushButton("← Back")
        back_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(51, 65, 85, 0.5);
                color: #ffffff;
                border: 3px solid transparent;
                border-radius: 5px;
                padding: 10px 20px;
                font-family: 'Segoe UI', 'Inter', sans-serif;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(51, 65, 85, 0.7);
                border: 3px solid #ff8c00;
            }
            QPushButton:pressed {
                background-color: rgba(51, 65, 85, 0.4);
                border: 3px solid #ff8c00;
            }
        """)
        back_button.setCursor(Qt.PointingHandCursor)
        back_button.clicked.connect(self.back_pressed.emit)
        back_button.setFixedWidth(100)

        top_layout.addWidget(back_button)
        
        # Repo indicator (center)
        self.repo_indicator = QLabel()
        self.repo_indicator.setAlignment(Qt.AlignCenter)
        self.repo_indicator.setStyleSheet("""
            QLabel {
                background-color: rgba(30, 64, 175, 0.2);
                color: #93c5fd;
                border: 1px solid #3b82f6;
                border-radius: 5px;
                padding: 8px 16px;
                font-family: 'Segoe UI', 'Inter', sans-serif;
                font-size: 12px;
                font-weight: bold;
            }
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
    def __init__(self):
        super().__init__()
        self.setStyleSheet(GRADIENT_BACKGROUND)
        
        # Add content
        title = QLabel("Fix #1")
        title.setStyleSheet("background-color: transparent; font-family: 'Segoe UI', 'Inter', sans-serif; font-size: 32px; font-weight: bold; color: #93c5fd;")
        title.setAlignment(Qt.AlignCenter)
        self.add_content(title)
        
        description = QLabel("This is the blue screen for Fix #1\nYour implementation goes here")
        description.setStyleSheet("background-color: transparent; font-family: 'Segoe UI', 'Inter', sans-serif; font-size: 14px; color: #cbd5e1; text-align: center;")
        description.setAlignment(Qt.AlignCenter)
        self.add_content(description)
        
        self.add_stretch()


class RedScreen(BaseScreen):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(GRADIENT_BACKGROUND)
        
        # Add content
        title = QLabel("Fix #2")
        title.setStyleSheet("background-color: transparent; font-family: 'Segoe UI', 'Inter', sans-serif; font-size: 32px; font-weight: bold; color: #fca5a5;")
        title.setAlignment(Qt.AlignCenter)
        self.add_content(title)
        
        description = QLabel("This is the red screen for Fix #2\nYour implementation goes here")
        description.setStyleSheet("background-color: transparent; font-family: 'Segoe UI', 'Inter', sans-serif; font-size: 14px; color: #cbd5e1; text-align: center;")
        description.setAlignment(Qt.AlignCenter)
        self.add_content(description)
        
        self.add_stretch()


class GreenScreen(BaseScreen):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(GRADIENT_BACKGROUND)
        
        # Add content
        title = QLabel("Fix #3")
        title.setStyleSheet("background-color: transparent; font-family: 'Segoe UI', 'Inter', sans-serif; font-size: 32px; font-weight: bold; color: #86efac;")
        title.setAlignment(Qt.AlignCenter)
        self.add_content(title)
        
        description = QLabel("This is the green screen for Fix #3\nYour implementation goes here")
        description.setStyleSheet("background-color: transparent; font-family: 'Segoe UI', 'Inter', sans-serif; font-size: 14px; color: #cbd5e1; text-align: center;")
        description.setAlignment(Qt.AlignCenter)
        self.add_content(description)
        
        self.add_stretch()


class GitHubScreen(BaseScreen):
    repo_linked = Signal(str)
    repo_unlinked = Signal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet(GRADIENT_BACKGROUND)
        
        # Title
        title = QLabel("Link GitHub Repository")
        title.setStyleSheet("background-color: transparent; font-family: 'Segoe UI', 'Inter', sans-serif; font-size: 32px; font-weight: bold; color: #f0f9ff;")
        title.setAlignment(Qt.AlignCenter)
        self.add_content(title)
        
        # Description
        description = QLabel("Enter your GitHub repository URL to link it to this project")
        description.setStyleSheet("background-color: transparent; font-family: 'Segoe UI', 'Inter', sans-serif; font-size: 14px; color: #cbd5e1;")
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
        self.repo_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(55, 65, 81, 0.4);
                color: #f0f9ff;
                border: 2px solid rgba(107, 114, 128, 0.3);
                border-radius: 5px;
                padding: 10px;
                font-family: 'Segoe UI', 'Inter', sans-serif;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 2px solid #ff8c00;
                background-color: rgba(55, 65, 81, 0.6);
            }
            QLineEdit::placeholder {
                color: rgba(148, 163, 184, 0.6);
            }
        """)
        self.repo_input.setMinimumHeight(40)
        input_layout.addWidget(self.repo_input)
        
        # Link button
        self.link_button = QPushButton("Link Repository")
        self.link_button.setStyleSheet("""
            QPushButton {
                background-color: #1e40af;
                color: white;
                border: 3px solid transparent;
                border-radius: 5px;
                padding: 10px 20px;
                font-family: 'Segoe UI', 'Inter', sans-serif;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1e40af;
                border: 3px solid #ff8c00;
            }
            QPushButton:pressed {
                background-color: #1e3a8a;
                border: 3px solid #ff8c00;
            }
        """)
        self.link_button.setCursor(Qt.PointingHandCursor)
        self.link_button.setFixedWidth(150)
        self.link_button.clicked.connect(self.on_link_clicked)
        input_layout.addWidget(self.link_button)
        
        self.add_content(input_container)
        
        # Status label
        self.status_label = QLabel()
        self.status_label.setStyleSheet("background-color: transparent; font-family: 'Segoe UI', 'Inter', sans-serif; font-size: 12px; color: #cbd5e1;")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.add_content(self.status_label)
        
        self.add_stretch()
    
    def on_link_clicked(self):
        """Handle the link repository button click."""
        repo_url = self.repo_input.text().strip()
        if repo_url:
            self.repo_linked.emit(repo_url)
    
    def set_linked_status(self, repo_url):
        """Update UI to show a linked repository."""
        self.status_label.setText(f"✓ Linked to: {repo_url}")
        self.status_label.setStyleSheet("background-color: transparent; font-family: 'Segoe UI', 'Inter', sans-serif; font-size: 12px; color: #86efac;")
        self.repo_input.setEnabled(False)
        self.link_button.setEnabled(False)
    
    def set_unlinked_status(self):
        """Update UI to show no linked repository."""
        self.status_label.setText("")
        self.repo_input.setEnabled(True)
        self.link_button.setEnabled(True)
        self.repo_input.clear()
        self.set_repo_info(None)
