import sys
import os
import shutil
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QLabel
from PySide6.QtCore import Qt
from screens import BlueScreen, RedScreen, GreenScreen, GitHubScreen

# Global gradient stylesheet
GRADIENT_BACKGROUND = """
QWidget {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                stop:0 #1f2937, 
                                stop:1 #111827);
}
"""


class MainScreen(QWidget):
    """Main screen with navigation buttons."""
    def __init__(self, navigate_callback, unlink_callback):
        super().__init__()
        self.navigate = navigate_callback
        self.unlink_repo = unlink_callback
        self.setStyleSheet(GRADIENT_BACKGROUND)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        # Title
        title = QLabel("ProjectTimeSaver")
        title.setStyleSheet("background-color: transparent; font-family: 'Segoe UI', 'Inter', sans-serif; font-size: 36px; font-weight: bold; color: #f0f9ff;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Select a fix to apply")
        subtitle.setStyleSheet("background-color: transparent; font-family: 'Segoe UI', 'Inter', sans-serif; font-size: 14px; color: #cbd5e1;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        # Button container
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.setSpacing(15)

        buttons_data = [
            ("FIX #1", 0, "#1e40af", "#60a5fa"),
            ("FIX #2", 1, "#991b1b", "#f87171"),
            ("FIX #3", 2, "#15803d", "#4ade80"),
        ]

        for label, index, bg_color, text_color in buttons_data:
            btn = QPushButton(label)
            btn.setMinimumHeight(80)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg_color};
                    color: {text_color};
                    border: 3px solid transparent;
                    border-radius: 8px;
                    font-family: 'Segoe UI', 'Inter', sans-serif;
                    font-size: 16px;
                    font-weight: bold;
                    padding: 10px;
                }}
                QPushButton:hover {{
                    background-color: {bg_color};
                    color: {text_color};
                    border: 3px solid #ff8c00;
                }}
                QPushButton:pressed {{
                    background-color: {bg_color};
                    color: {text_color};
                    border: 3px solid #ff8c00;
                }}
            """)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, idx=index: self.navigate(idx))
            button_layout.addWidget(btn)

        layout.addWidget(button_container)
        
        # GitHub button with unlink option
        github_container = QWidget()
        github_layout = QHBoxLayout(github_container)
        github_layout.setSpacing(10)
        github_layout.setContentsMargins(0, 0, 0, 0)
        
        self.github_button = QPushButton("Link GitHub Repository")
        self.github_button.setMinimumHeight(50)
        self.github_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(30, 41, 59, 0.8);
                color: #e2e8f0;
                border: 3px solid transparent;
                border-radius: 8px;
                font-family: 'Segoe UI', 'Inter', sans-serif;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: rgba(30, 41, 59, 0.8);
                border: 3px solid #ff8c00;
                color: #f0f9ff;
            }
            QPushButton:pressed {
                background-color: rgba(30, 41, 59, 0.9);
                border: 3px solid #ff8c00;
            }
        """)
        self.github_button.setCursor(Qt.PointingHandCursor)
        self.github_button.clicked.connect(lambda: self.navigate(3))
        github_layout.addWidget(self.github_button)
        
        self.unlink_button = QPushButton("✕")
        self.unlink_button.setFixedSize(50, 50)
        self.unlink_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(127, 29, 29, 0.8);
                color: #ffffff;
                border: 3px solid transparent;
                border-radius: 5px;
                font-size: 18px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: rgba(127, 29, 29, 0.8);
                border: 3px solid #ff8c00;
                color: white;
            }
            QPushButton:pressed {
                background-color: rgba(127, 29, 29, 1);
                border: 3px solid #ff8c00;
                color: white;
            }
        """)
        self.unlink_button.setCursor(Qt.PointingHandCursor)
        self.unlink_button.clicked.connect(self.unlink_repo)
        self.unlink_button.setEnabled(False)
        github_layout.addWidget(self.unlink_button)
        
        layout.addWidget(github_container)
        
        layout.addStretch()
    
    def set_repo_linked(self, is_linked):
        """Update the GitHub button state to show if a repo is linked."""
        self.unlink_button.setEnabled(is_linked)
        if is_linked:
            self.github_button.setStyleSheet("""
                QPushButton {
                    background-color: #15803d;
                    color: #e2e8f0;
                    border: 3px solid transparent;
                    border-radius: 8px;
                    font-family: 'Segoe UI', 'Inter', sans-serif;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 10px;
                }
                QPushButton:hover {
                    background-color: #15803d;
                    border: 3px solid #ff8c00;
                    color: #f0f9ff;
                }
                QPushButton:pressed {
                    background-color: #166534;
                    border: 3px solid #ff8c00;
                }
            """)
        else:
            self.github_button.setStyleSheet("""
                QPushButton {
                    background-color: rgba(30, 41, 59, 0.8);
                    color: #e2e8f0;
                    border: 3px solid transparent;
                    border-radius: 8px;
                    font-family: 'Segoe UI', 'Inter', sans-serif;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 10px;
                }
                QPushButton:hover {
                    background-color: rgba(30, 41, 59, 0.8);
                    border: 3px solid #ff8c00;
                    color: #f0f9ff;
                }
                QPushButton:pressed {
                    background-color: rgba(30, 41, 59, 0.9);
                    border: 3px solid #ff8c00;
                }
            """)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ProjectTimeSaver - AI Bot UI")
        self.resize(1000, 700)
        self.setStyleSheet(GRADIENT_BACKGROUND)

        # Set up repos subfolder
        self.repos_folder = os.path.join(os.path.dirname(__file__), "repos")
        self.ensure_repos_folder()

        # Create stacked widget for screen management
        self.stacked = QStackedWidget()

        # Create main screen
        self.main_screen = MainScreen(self.navigate_to_screen, self.unlink_repo)
        self.stacked.addWidget(self.main_screen)

        # Create detail screens
        self.blue_screen = BlueScreen()
        self.red_screen = RedScreen()
        self.green_screen = GreenScreen()
        self.github_screen = GitHubScreen()

        self.stacked.addWidget(self.blue_screen)
        self.stacked.addWidget(self.red_screen)
        self.stacked.addWidget(self.green_screen)
        self.stacked.addWidget(self.github_screen)

        # Connect back signals
        self.blue_screen.back_pressed.connect(self.back_to_main)
        self.red_screen.back_pressed.connect(self.back_to_main)
        self.green_screen.back_pressed.connect(self.back_to_main)
        self.github_screen.back_pressed.connect(self.back_to_main)

        # Connect GitHub linking signals
        self.github_screen.repo_linked.connect(self.on_repo_linked)
        self.github_screen.repo_unlinked.connect(self.on_repo_unlinked)

        self.setCentralWidget(self.stacked)
        self.stacked.setCurrentIndex(0)
        
        # Track current repo
        self.current_repo_url = None
        
        # Check if repo is already linked
        self.check_and_update_repo_status()

    def ensure_repos_folder(self):
        """Ensure the repos subfolder exists."""
        if not os.path.exists(self.repos_folder):
            os.makedirs(self.repos_folder)

    def check_and_update_repo_status(self):
        """Check if a repo is already linked and update UI."""
        repo_info_file = os.path.join(self.repos_folder, "repo_info.txt")
        if os.path.exists(repo_info_file):
            try:
                with open(repo_info_file, "r") as f:
                    self.current_repo_url = f.read().strip()
                    self.main_screen.set_repo_linked(True)
                    self._update_all_screens_repo_info()
            except Exception:
                pass
        else:
            self.current_repo_url = None
            self.main_screen.set_repo_linked(False)
    
    def _update_all_screens_repo_info(self):
        """Update all screens with current repo info."""
        self.blue_screen.set_repo_info(self.current_repo_url)
        self.red_screen.set_repo_info(self.current_repo_url)
        self.green_screen.set_repo_info(self.current_repo_url)
        self.github_screen.set_repo_info(self.current_repo_url)

    def navigate_to_screen(self, index):
        """Navigate to a specific screen (0-2 for detail screens, 3 for github)."""
        self._update_all_screens_repo_info()
        self.stacked.setCurrentIndex(index + 1)

    def back_to_main(self):
        """Return to the main screen."""
        self.stacked.setCurrentIndex(0)
        self.check_and_update_repo_status()

    def on_repo_linked(self, repo_url):
        """Handle repository linking."""
        try:
            # Store the repo URL in a file for reference
            repo_info_file = os.path.join(self.repos_folder, "repo_info.txt")
            with open(repo_info_file, "w") as f:
                f.write(repo_url)
            
            self.current_repo_url = repo_url
            self.github_screen.set_linked_status(repo_url)
            self.main_screen.set_repo_linked(True)
            self._update_all_screens_repo_info()
        except Exception as e:
            self.github_screen.status_label.setText(f"Error linking repository: {str(e)}")
            self.github_screen.status_label.setStyleSheet("font-size: 12px; color: #fca5a5;")

    def on_repo_unlinked(self):
        """Handle repository unlinking."""
        self.github_screen.repo_unlinked.emit()

    def unlink_repo(self):
        """Remove linked repository and clear repos folder."""
        try:
            if os.path.exists(self.repos_folder):
                shutil.rmtree(self.repos_folder)
            self.ensure_repos_folder()
            
            self.current_repo_url = None
            self.github_screen.set_unlinked_status()
            self.main_screen.set_repo_linked(False)
            self._update_all_screens_repo_info()
        except Exception as e:
            print(f"Error unlinking repository: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
