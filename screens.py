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
