from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal


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

        # Top bar with back button
        top_bar = QWidget()
        top_bar.setStyleSheet("background-color: #1e1e1e;")
        top_bar.setFixedHeight(60)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 0, 20, 0)

        back_button = QPushButton("← Back")
        back_button.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
            QPushButton:pressed {
                background-color: #1d1d1d;
            }
        """)
        back_button.setCursor(Qt.PointingHandCursor)
        back_button.clicked.connect(self.back_pressed.emit)
        back_button.setFixedWidth(100)

        top_layout.addWidget(back_button)
        top_layout.addStretch()

        main_layout.addWidget(top_bar)

        # Content area
        self.content_widget = QWidget()
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


class BlueScreen(BaseScreen):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #e3f2fd;")
        
        # Add content
        title = QLabel("Fix #1")
        title.setStyleSheet("font-size: 32px; font-weight: bold; color: #0d47a1;")
        title.setAlignment(Qt.AlignCenter)
        self.add_content(title)
        
        description = QLabel("This is the blue screen for Fix #1\nYour implementation goes here")
        description.setStyleSheet("font-size: 14px; color: #424242; text-align: center;")
        description.setAlignment(Qt.AlignCenter)
        self.add_content(description)
        
        self.add_stretch()


class RedScreen(BaseScreen):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #ffebee;")
        
        # Add content
        title = QLabel("Fix #2")
        title.setStyleSheet("font-size: 32px; font-weight: bold; color: #b71c1c;")
        title.setAlignment(Qt.AlignCenter)
        self.add_content(title)
        
        description = QLabel("This is the red screen for Fix #2\nYour implementation goes here")
        description.setStyleSheet("font-size: 14px; color: #424242; text-align: center;")
        description.setAlignment(Qt.AlignCenter)
        self.add_content(description)
        
        self.add_stretch()


class GreenScreen(BaseScreen):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #e8f5e9;")
        
        # Add content
        title = QLabel("Fix #3")
        title.setStyleSheet("font-size: 32px; font-weight: bold; color: #1b5e20;")
        title.setAlignment(Qt.AlignCenter)
        self.add_content(title)
        
        description = QLabel("This is the green screen for Fix #3\nYour implementation goes here")
        description.setStyleSheet("font-size: 14px; color: #424242; text-align: center;")
        description.setAlignment(Qt.AlignCenter)
        self.add_content(description)
        
        self.add_stretch()


class GitHubScreen(BaseScreen):
    repo_linked = Signal(str)
    repo_unlinked = Signal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f5f5f5;")
        
        # Title
        title = QLabel("Link GitHub Repository")
        title.setStyleSheet("font-size: 32px; font-weight: bold; color: #1a1a1a;")
        title.setAlignment(Qt.AlignCenter)
        self.add_content(title)
        
        # Description
        description = QLabel("Enter your GitHub repository URL to link it to this project")
        description.setStyleSheet("font-size: 14px; color: #666666;")
        description.setAlignment(Qt.AlignCenter)
        self.add_content(description)
        
        self.add_content(QLabel())  # Spacer
        
        # Input container
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setSpacing(10)
        
        # Text input for GitHub URL
        from PySide6.QtWidgets import QLineEdit
        self.repo_input = QLineEdit()
        self.repo_input.setPlaceholderText("https://github.com/username/repository")
        self.repo_input.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                color: #1a1a1a;
                border: 2px solid #cccccc;
                border-radius: 5px;
                padding: 10px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 2px solid #0d47a1;
            }
        """)
        self.repo_input.setMinimumHeight(40)
        input_layout.addWidget(self.repo_input)
        
        # Link button
        self.link_button = QPushButton("Link Repository")
        self.link_button.setStyleSheet("""
            QPushButton {
                background-color: #0d47a1;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
        """)
        self.link_button.setCursor(Qt.PointingHandCursor)
        self.link_button.setFixedWidth(150)
        self.link_button.clicked.connect(self.on_link_clicked)
        input_layout.addWidget(self.link_button)
        
        self.add_content(input_container)
        
        # Status label
        self.status_label = QLabel()
        self.status_label.setStyleSheet("font-size: 12px; color: #666666;")
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
        self.status_label.setStyleSheet("font-size: 12px; color: #1b5e20;")
        self.repo_input.setEnabled(False)
        self.link_button.setEnabled(False)
    
    def set_unlinked_status(self):
        """Update UI to show no linked repository."""
        self.status_label.setText("")
        self.repo_input.setEnabled(True)
        self.link_button.setEnabled(True)
        self.repo_input.clear()
