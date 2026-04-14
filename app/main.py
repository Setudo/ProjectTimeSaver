import sys
import os
import shutil
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QLabel
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QFontDatabase, QFont # Used to change fonts (as long as they are downloaded)
from screens import BlueScreen, RedScreen, GreenScreen, GitHubScreen
import repo_puller
import threading
from logger import AppLogger

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
        title.setStyleSheet("background-color: transparent;  font-size: 40px; font-weight: bold; color: #f0f9ff;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Select a fix to apply")
        subtitle.setStyleSheet("background-color: transparent;  font-size: 14px; color: #cbd5e1;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        # Button container
        button_container = QWidget()
        button_container.setStyleSheet("background-color: transparent;")
        button_layout = QVBoxLayout(button_container)
        button_layout.setSpacing(15)

        buttons_data = [
            ("FIX #1", 0, "#1e40af", "#333333"),
            ("FIX #2", 1, "#721414", "#333333"),
            ("FIX #3", 2, "#10582a", "#333333"),
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
        github_container.setStyleSheet("background-color: transparent;")
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

        # Set up repos subfolder and logger
        self.app_dir = os.path.dirname(__file__)
        self.repos_folder = os.path.join(self.app_dir, "repos")
        self.logger = AppLogger(self.app_dir)
        self.logger.info("Application started")
        self.ensure_repos_folder()

        # Track download worker/thread for cancellation
        self.download_thread = None
        self.download_worker = None
        self.should_cancel_download = False

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
        self.github_screen.cancel_download.connect(self.on_cancel_download)
        self.github_screen.unlink_repo_button.clicked.connect(self.unlink_repo)

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
            self.logger.debug(f"Created repos folder: {self.repos_folder}")

    def check_and_update_repo_status(self):
        """Check if a repo is already linked and update UI."""
        repo_info_file = os.path.join(self.repos_folder, "repo_info.txt")
        if os.path.exists(repo_info_file):
            try:
                with open(repo_info_file, "r") as f:
                    self.current_repo_url = f.read().strip()
                    self.main_screen.set_repo_linked(True)
                    self._update_all_screens_repo_info()
                    
                    # Also prepare the file tree for the GitHub screen
                    repo_name = self.current_repo_url.rstrip('/').split('/')[-1].replace('.git', '')
                    repo_folder = os.path.join(self.repos_folder, repo_name)
                    self.github_screen.show_file_tree(repo_folder)
                    
                    self.logger.info(f"Linked repo found: {self.current_repo_url}")
            except Exception as e:
                self.logger.error(f"Error reading repo_info.txt: {str(e)}")
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
        """Handle repository linking by downloading the repo in a background thread."""
        self.logger.info(f"User initiated download for: {repo_url}")
        self.github_screen.show_progress()
        self.github_screen.update_status("Downloading repository...", is_error=False)

        class RepoWorker(QObject):
            progress = Signal(int, int)  # bytes_downloaded, total_bytes
            finished = Signal(bool, str)

            def __init__(self, repo_url, dest_path, logger_ref):
                super().__init__()
                self.repo_url = repo_url
                self.dest_path = dest_path
                self.logger = logger_ref
                self.should_cancel = False

            def progress_callback(self, bytes_downloaded, total_bytes):
                """Called by repo_puller during download."""
                if not self.should_cancel:
                    self.progress.emit(bytes_downloaded, total_bytes)

            def run(self):
                try:
                    self.logger.debug(f"Starting download to: {self.dest_path}")
                    ok, message = repo_puller.download_repo(
                        self.repo_url, 
                        self.dest_path,
                        progress_callback=self.progress_callback
                    )
                    if ok:
                        self.logger.info(f"Download successful: {message}")
                    else:
                        self.logger.warning(f"Download failed: {message}")
                except Exception as e:
                    ok, message = False, f"Unexpected error: {str(e)}"
                    self.logger.error(f"Download exception: {str(e)}")
                self.finished.emit(ok, message)

        # derive a folder name from the repo url
        repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
        dest_path = os.path.join(self.repos_folder, repo_name)

        self.download_worker = RepoWorker(repo_url, dest_path, self.logger)
        self.download_thread = QThread()
        self.download_worker.moveToThread(self.download_thread)

        # Handle progress updates on main thread
        self.download_worker.progress.connect(self.github_screen.update_progress)

        # Handle completion on main thread
        def _on_finished(ok, message):
            self.github_screen.hide_progress()
            if ok:
                try:
                    repo_info_file = os.path.join(self.repos_folder, "repo_info.txt")
                    with open(repo_info_file, "w") as f:
                        f.write(repo_url)
                    self.current_repo_url = repo_url
                    self.github_screen.set_linked_status(repo_url)
                    
                    # Show the file tree for the linked repository
                    repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
                    repo_folder = os.path.join(self.repos_folder, repo_name)
                    self.github_screen.show_file_tree(repo_folder)
                    
                    self.main_screen.set_repo_linked(True)
                    self._update_all_screens_repo_info()
                    self.logger.info("Repository successfully linked and downloaded")
                except Exception as e:
                    error_msg = f"Error saving repo info: {str(e)}"
                    self.github_screen.update_status(error_msg, is_error=True)
                    self.logger.error(error_msg)
            else:
                error_msg = f"Download failed: {message}"
                self.github_screen.update_status(error_msg, is_error=True)
                self.logger.warning(error_msg)

        self.download_worker.finished.connect(_on_finished)
        self.download_worker.finished.connect(self.download_thread.quit)
        self.download_worker.finished.connect(self.download_worker.deleteLater)
        self.download_thread.finished.connect(self.download_thread.deleteLater)
        self.download_thread.started.connect(self.download_worker.run)
        self.download_thread.start()

    def on_cancel_download(self):
        """Cancel the current download."""
        if self.download_worker:
            self.logger.warning("User cancelled download")
            self.download_worker.should_cancel = True
            if self.download_thread:
                self.download_thread.quit()
                self.download_thread.wait()
            self.github_screen.hide_progress()
            self.github_screen.update_status("Download cancelled", is_error=True)

    def on_repo_unlinked(self):
        """Handle repository unlinking."""
        self.github_screen.repo_unlinked.emit()

    def unlink_repo(self):
        """Remove linked repository and clear repos folder."""
        try:
            # Delete the specific repo folder if it exists
            if self.current_repo_url:
                repo_name = self.current_repo_url.rstrip('/').split('/')[-1].replace('.git', '')
                repo_folder = os.path.join(self.repos_folder, repo_name)
                if os.path.exists(repo_folder):
                    import time
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            # Handle read-only files on Windows by changing permissions
                            for root, dirs, files in os.walk(repo_folder, topdown=False):
                                for f in files:
                                    try:
                                        os.chmod(os.path.join(root, f), 0o777)
                                    except Exception:
                                        pass
                                for d in dirs:
                                    try:
                                        os.chmod(os.path.join(root, d), 0o777)
                                    except Exception:
                                        pass
                            
                            shutil.rmtree(repo_folder)
                            self.logger.debug(f"Successfully deleted repo folder: {repo_folder}")
                            break  # Success, exit retry loop
                        except Exception as e:
                            if attempt < max_retries - 1:
                                self.logger.debug(f"Unlink attempt {attempt + 1} failed for {repo_folder}, retrying: {str(e)}")
                                time.sleep(0.5)  # Wait before retry
                            else:
                                # Try Windows-specific fallback
                                try:
                                    import platform
                                    if platform.system() == 'Windows':
                                        import subprocess
                                        # Use rd command with /s /q flags to force delete
                                        result = subprocess.run(['cmd', '/c', 'rd', '/s', '/q', repo_folder], 
                                                              capture_output=True, text=True, timeout=30)
                                        if result.returncode == 0:
                                            self.logger.debug(f"Successfully deleted repo folder using Windows rd command: {repo_folder}")
                                        else:
                                            self.logger.warning(f"Windows rd command failed for {repo_folder}: {result.stderr}")
                                    else:
                                        self.logger.warning(f"Failed to delete repo folder {repo_folder} after {max_retries} attempts: {str(e)}")
                                except Exception as fallback_e:
                                    self.logger.warning(f"Failed to delete repo folder {repo_folder} after {max_retries} attempts and fallback: {str(e)}, fallback error: {str(fallback_e)}")
                                # Continue anyway - the repo_info.txt will be deleted
            
            # Delete the repo info file
            repo_info_file = os.path.join(self.repos_folder, "repo_info.txt")
            if os.path.exists(repo_info_file):
                try:
                    os.remove(repo_info_file)
                    self.logger.debug("Successfully deleted repo_info.txt")
                except Exception as e:
                    self.logger.warning(f"Failed to delete repo_info.txt: {str(e)}")
            
            self.current_repo_url = None
            self.github_screen.set_unlinked_status()
            self.github_screen.update()  # Force UI update
            self.main_screen.set_repo_linked(False)
            self._update_all_screens_repo_info()
            
            # If we're on the GitHub screen, go back to main screen after unlinking
            if self.stacked.currentIndex() == 3:
                self.stacked.setCurrentIndex(0)
            
            self.logger.info("Repository unlinked successfully")
        except Exception as e:
            error_msg = f"Error unlinking repository: {str(e)}"
            print(error_msg)
            self.logger.error(error_msg)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # APPLICATION FONT
    base_dir = os.path.dirname(os.path.abspath(__file__))

    regular_font = os.path.join(base_dir, "fonts", "Inter-Regular.otf")
    bold_font = os.path.join(base_dir, "fonts", "Inter-Bold.otf")

    QFontDatabase.addApplicationFont(regular_font)
    QFontDatabase.addApplicationFont(bold_font)

    app.setFont(QFont("Inter", 10))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
