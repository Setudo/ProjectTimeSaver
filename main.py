import sys
import os
import shutil
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QLabel
from PySide6.QtCore import Qt
from screens import BlueScreen, RedScreen, GreenScreen, GitHubScreen


class MainScreen(QWidget):
    """Main screen with navigation buttons."""
    def __init__(self, navigate_callback, unlink_callback):
        super().__init__()
        self.navigate = navigate_callback
        self.unlink_repo = unlink_callback
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
        
        # GitHub button with unlink option
        github_container = QWidget()
        github_layout = QHBoxLayout(github_container)
        github_layout.setSpacing(10)
        github_layout.setContentsMargins(0, 0, 0, 0)
        
        self.github_button = QPushButton("Link GitHub Repository")
        self.github_button.setMinimumHeight(50)
        self.github_button.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f5;
                color: #333333;
                border: 2px dashed #999999;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #eeeeee;
                border: 2px dashed #666666;
            }
            QPushButton:pressed {
                background-color: #dddddd;
            }
        """)
        self.github_button.setCursor(Qt.PointingHandCursor)
        self.github_button.clicked.connect(lambda: self.navigate(3))
        github_layout.addWidget(self.github_button)
        
        self.unlink_button = QPushButton("✕")
        self.unlink_button.setFixedSize(50, 50)
        self.unlink_button.setStyleSheet("""
            QPushButton {
                background-color: #ffcdd2;
                color: #c62828;
                border: 2px solid #c62828;
                border-radius: 5px;
                font-size: 18px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #ef5350;
                color: white;
                border: 2px solid #ef5350;
            }
            QPushButton:pressed {
                background-color: #c62828;
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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ProjectTimeSaver - AI Bot UI")
        self.resize(1000, 700)
        self.setStyleSheet("background-color: #ffffff;")

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
        
        # Check if repo is already linked
        self.check_and_update_repo_status()

    def ensure_repos_folder(self):
        """Ensure the repos subfolder exists."""
        if not os.path.exists(self.repos_folder):
            os.makedirs(self.repos_folder)

    def check_and_update_repo_status(self):
        """Check if a repo is already linked and update UI."""
        # For now, we check if repos folder has any content
        if os.path.exists(self.repos_folder) and os.listdir(self.repos_folder):
            # Repo is linked
            self.main_screen.set_repo_linked(True)

    def navigate_to_screen(self, index):
        """Navigate to a specific screen (0-2 for detail screens, 3 for github)."""
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
            
            self.github_screen.set_linked_status(repo_url)
            self.main_screen.set_repo_linked(True)
        except Exception as e:
            self.github_screen.status_label.setText(f"Error linking repository: {str(e)}")
            self.github_screen.status_label.setStyleSheet("font-size: 12px; color: #c62828;")

    def on_repo_unlinked(self):
        """Handle repository unlinking."""
        self.github_screen.repo_unlinked.emit()

    def unlink_repo(self):
        """Remove linked repository and clear repos folder."""
        try:
            if os.path.exists(self.repos_folder):
                shutil.rmtree(self.repos_folder)
            self.ensure_repos_folder()
            
            self.github_screen.set_unlinked_status()
            self.main_screen.set_repo_linked(False)
        except Exception as e:
            print(f"Error unlinking repository: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
