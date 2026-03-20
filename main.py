import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QLabel
from PySide6.QtCore import Qt
from screens import BlueScreen, RedScreen, GreenScreen


class MainScreen(QWidget):
    """Main screen with navigation buttons."""
    def __init__(self, navigate_callback):
        super().__init__()
        self.navigate = navigate_callback
        self.setStyleSheet("background-color: #f5f5f5;")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        # Title
        title = QLabel("ProjectTimeSaver")
        title.setStyleSheet("font-size: 36px; font-weight: bold; color: #1a1a1a;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Select a fix to apply")
        subtitle.setStyleSheet("font-size: 14px; color: #666666;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        # Button container
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.setSpacing(15)

        buttons_data = [
            ("FIX #1", 0, "#e3f2fd", "#0d47a1"),
            ("FIX #2", 1, "#ffebee", "#b71c1c"),
            ("FIX #3", 2, "#e8f5e9", "#1b5e20"),
        ]

        for label, index, bg_color, text_color in buttons_data:
            btn = QPushButton(label)
            btn.setMinimumHeight(80)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg_color};
                    color: {text_color};
                    border: 2px solid {text_color};
                    border-radius: 8px;
                    font-size: 16px;
                    font-weight: bold;
                    padding: 10px;
                }}
                QPushButton:hover {{
                    background-color: {text_color};
                    color: white;
                    border: 2px solid {text_color};
                }}
                QPushButton:pressed {{
                    background-color: {text_color};
                    color: white;
                    border: 2px solid {text_color};
                }}
            """)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, idx=index: self.navigate(idx))
            button_layout.addWidget(btn)

        layout.addWidget(button_container)
        layout.addStretch()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ProjectTimeSaver - AI Bot UI")
        self.resize(1000, 700)
        self.setStyleSheet("background-color: #ffffff;")

        # Create stacked widget for screen management
        self.stacked = QStackedWidget()

        # Create main screen
        self.main_screen = MainScreen(self.navigate_to_screen)
        self.stacked.addWidget(self.main_screen)

        # Create detail screens
        self.blue_screen = BlueScreen()
        self.red_screen = RedScreen()
        self.green_screen = GreenScreen()

        self.stacked.addWidget(self.blue_screen)
        self.stacked.addWidget(self.red_screen)
        self.stacked.addWidget(self.green_screen)

        # Connect back signals
        self.blue_screen.back_pressed.connect(self.back_to_main)
        self.red_screen.back_pressed.connect(self.back_to_main)
        self.green_screen.back_pressed.connect(self.back_to_main)

        self.setCentralWidget(self.stacked)
        self.stacked.setCurrentIndex(0)

    def navigate_to_screen(self, index):
        """Navigate to a specific screen (1, 2, or 3 for detail screens)."""
        self.stacked.setCurrentIndex(index + 1)

    def back_to_main(self):
        """Return to the main screen."""
        self.stacked.setCurrentIndex(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
