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
        layout.setSpacing(10)

        # Title
        title = QLabel("ProjectTimeSaver")
        title.setStyleSheet(f"background-color: transparent; font-size: 48px; font-weight: bold; color: {COLOR_ACCENT_BLUE}; letter-spacing: 2px;")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Courier New", 32, QFont.Bold))
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Link a repository to get started")
        subtitle.setStyleSheet(f"background-color: transparent; font-size: 14px; color: {COLOR_TEXT_SECONDARY}; letter-spacing: 0.5px;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        layout.addSpacing(20)
        # Note: main navigation buttons moved to a collapsible sidebar in MainWindow.
        info = QLabel("Use the sidebar to navigate the main sections.")
        info.setStyleSheet(f"background-color: transparent; font-size: 12px; color: {COLOR_TEXT_SECONDARY};")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)
        
        # GitHub button with unlink option
        github_container = QWidget()
        github_container.setStyleSheet("background-color: transparent;")
        github_layout = QHBoxLayout(github_container)
        github_layout.setSpacing(10)
        github_layout.setContentsMargins(0, 0, 0, 0)
        
        self.github_button = QPushButton("Link GitHub Repository")
        self.github_button.setMinimumHeight(48)
        self.github_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_SURFACE};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_SURFACE_LIGHT};
                border-radius: 0px;
                font-size: 13px;
                font-weight: 500;
                padding: 10px 20px;
                font-family: 'Courier New', monospace;
            }}
            QPushButton:hover {{
                background-color: {COLOR_ACCENT_DARK_BLUE};
                border: 1px solid {COLOR_ACCENT_BLUE};
                color: {COLOR_ACCENT_BLUE};
            }}
            QPushButton:pressed {{
                background-color: {COLOR_ACCENT_BLUE};
                color: #0f1419;
            }}
        """)
        self.github_button.setCursor(Qt.PointingHandCursor)
        self.github_button.clicked.connect(lambda: self.navigate(3))
        github_layout.addWidget(self.github_button)
        
        self.unlink_button = QPushButton("✕")
        self.unlink_button.setFixedSize(48, 48)
        self.unlink_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_SURFACE};
                color: {COLOR_ERROR};
                border: 1px solid {COLOR_SURFACE_LIGHT};
                border-radius: 0px;
                font-size: 18px;
                font-weight: bold;
                padding: 0px;
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
        self.unlink_button.setCursor(Qt.PointingHandCursor)
        self.unlink_button.clicked.connect(self.unlink_repo)
        self.unlink_button.setEnabled(False)
        github_layout.addWidget(self.unlink_button)
        
        layout.addWidget(github_container)
        
        layout.addStretch()
        # hide main-screen github controls since they are moved to the sidebar
        self.github_button.setVisible(False)
        self.unlink_button.setVisible(False)
    
    def set_repo_linked(self, is_linked):
        """Update the GitHub button state to show if a repo is linked."""
        self.unlink_button.setEnabled(is_linked)
        if is_linked:
            self.github_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLOR_SUCCESS};
                    color: #0f1419;
                    border: 1px solid {COLOR_SUCCESS};
                    border-radius: 0px;
                    font-size: 13px;
                    font-weight: 500;
                    padding: 10px 20px;
                    font-family: 'Courier New', monospace;
                }}
                QPushButton:hover {{
                    background-color: {COLOR_SURFACE};
                    border: 1px solid {COLOR_SUCCESS};
                    color: {COLOR_SUCCESS};
                }}
                QPushButton:pressed {{
                    background-color: {COLOR_SUCCESS};
                    border: 1px solid {COLOR_SUCCESS};
                }}
            """)
        else:
            self.github_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLOR_SURFACE};
                    color: {COLOR_TEXT_PRIMARY};
                    border: 1px solid {COLOR_SURFACE_LIGHT};
                    border-radius: 0px;
                    font-size: 13px;
                    font-weight: 500;
                    padding: 10px 20px;
                    font-family: 'Courier New', monospace;
                }}
                QPushButton:hover {{
                    background-color: {COLOR_ACCENT_DARK_BLUE};
                    border: 1px solid {COLOR_ACCENT_BLUE};
                    color: {COLOR_ACCENT_BLUE};
                }}
                QPushButton:pressed {{
                    background-color: {COLOR_ACCENT_BLUE};
                    border: 1px solid {COLOR_ACCENT_BLUE};
                }}
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

        # Create a main container with a collapsible sidebar on the left
        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setStyleSheet(f"#sidebar {{ background-color: {COLOR_SURFACE}; border-right: 1px solid {COLOR_SURFACE_LIGHT}; }}")
        self.sidebar.setFixedWidth(260)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        sidebar_layout.setSpacing(12)

        # Sidebar toggle (collapse/expand)
        self.sidebar_toggle = QPushButton("☰")
        self.sidebar_toggle.setFixedSize(36, 36)
        self.sidebar_toggle.setStyleSheet(f"background-color: transparent; color: {COLOR_ACCENT_BLUE}; font-size: 18px; border: none; font-weight: bold;")
        self.sidebar_toggle.setCursor(Qt.PointingHandCursor)
        self.sidebar_toggle.clicked.connect(self.toggle_sidebar)
        top_row = QWidget()
        top_row_layout = QHBoxLayout(top_row)
        top_row_layout.setContentsMargins(0, 0, 0, 0)
        top_row_layout.addWidget(self.sidebar_toggle)
        top_row_layout.addStretch()
        sidebar_layout.addWidget(top_row)

        # Navigation buttons in sidebar
        self.sidebar_buttons = []
        buttons_data = [
            ("Repo Overview", 0, COLOR_ACCENT_DARK_BLUE),
            ("FIX #2", 1, "#c41c3b"),
            ("FIX #3", 2, COLOR_SUCCESS),
        ]
        for label, index, accent_color in buttons_data:
            btn = QPushButton(label)
            btn.setMinimumHeight(70)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {COLOR_TEXT_PRIMARY};
                    border: 1px solid {COLOR_SURFACE_LIGHT};
                    border-radius: 0px;
                    font-family: 'Courier New', monospace;
                    font-size: 12px;
                    font-weight: 600;
                    padding: 10px;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background-color: {COLOR_SURFACE_LIGHT};
                    color: {accent_color};
                    border: 1px solid {accent_color};
                }}
                QPushButton:pressed {{
                    background-color: {accent_color};
                    color: #0f1419;
                    border: 1px solid {accent_color};
                }}
            """)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, idx=index: self.navigate_to_screen(idx))
            sidebar_layout.addWidget(btn)
            self.sidebar_buttons.append(btn)

        sidebar_layout.addStretch()
        # GitHub link + unlink controls in sidebar
        github_row = QWidget()
        github_row.setStyleSheet("background-color: transparent;")
        github_row_layout = QHBoxLayout(github_row)
        github_row_layout.setContentsMargins(0, 0, 0, 0)
        github_row_layout.setSpacing(8)

        self.sidebar_github_button = QPushButton("Link GitHub Repository")
        self.sidebar_github_button.setMinimumHeight(48)
        self.sidebar_github_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_SURFACE_LIGHT};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_SURFACE_LIGHT};
                border-radius: 0px;
                font-size: 11px;
                font-weight: 500;
                padding: 10px;
                font-family: 'Courier New', monospace;
            }}
            QPushButton:hover {{
                background-color: {COLOR_ACCENT_DARK_BLUE};
                border: 1px solid {COLOR_ACCENT_BLUE};
                color: {COLOR_ACCENT_BLUE};
            }}
            QPushButton:pressed {{
                background-color: {COLOR_ACCENT_BLUE};
                color: #0f1419;
            }}
        """)
        self.sidebar_github_button.setCursor(Qt.PointingHandCursor)
        self.sidebar_github_button.clicked.connect(lambda: self.navigate_to_screen(3))

        self.sidebar_unlink_button = QPushButton("✕")
        self.sidebar_unlink_button.setFixedSize(40, 40)
        self.sidebar_unlink_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_SURFACE_LIGHT};
                color: {COLOR_ERROR};
                border: 1px solid {COLOR_SURFACE_LIGHT};
                border-radius: 0px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLOR_ERROR};
                border: 1px solid {COLOR_ERROR};
                color: #0f1419;
            }}
        """)
        self.sidebar_unlink_button.setCursor(Qt.PointingHandCursor)
        self.sidebar_unlink_button.clicked.connect(self.unlink_repo)
        self.sidebar_unlink_button.setEnabled(False)

        github_row_layout.addWidget(self.sidebar_github_button)
        github_row_layout.addWidget(self.sidebar_unlink_button)
        sidebar_layout.addWidget(github_row)

        # Main container (sidebar + stacked content)
        main_container = QWidget()
        main_layout = QHBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stacked)

        self.setCentralWidget(main_container)
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
                    # Update sidebar controls
                    self.update_sidebar_repo_state(True, self.current_repo_url)
                    
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
            # Update sidebar to show unlinked state
            try:
                self.update_sidebar_repo_state(False)
            except Exception:
                pass
    
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
                    # Update sidebar controls as linked
                    try:
                        self.update_sidebar_repo_state(True, repo_url)
                    except Exception:
                        pass
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
            try:
                self.update_sidebar_repo_state(False)
            except Exception:
                pass
            
            # If we're on the GitHub screen, go back to main screen after unlinking
            if self.stacked.currentIndex() == 3:
                self.stacked.setCurrentIndex(0)
            
            self.logger.info("Repository unlinked successfully")
        except Exception as e:
            error_msg = f"Error unlinking repository: {str(e)}"
            print(error_msg)
            self.logger.error(error_msg)

    def toggle_sidebar(self):
        """Collapse or expand the sidebar."""
        try:
            collapsed_width = 56
            expanded_width = 260
            current = self.sidebar.width()
            if current > collapsed_width:
                self.sidebar.setFixedWidth(collapsed_width)
                # hide everything except the sidebar toggle button
                try:
                    for b in getattr(self, 'sidebar_buttons', []):
                        b.setVisible(False)
                except Exception:
                    pass
                try:
                    if hasattr(self, 'sidebar_github_button'):
                        self.sidebar_github_button.setVisible(False)
                    if hasattr(self, 'sidebar_unlink_button'):
                        self.sidebar_unlink_button.setVisible(False)
                except Exception:
                    pass
            else:
                self.sidebar.setFixedWidth(expanded_width)
                # show the sidebar contents again
                try:
                    for b in getattr(self, 'sidebar_buttons', []):
                        b.setVisible(True)
                except Exception:
                    pass
                try:
                    if hasattr(self, 'sidebar_github_button'):
                        self.sidebar_github_button.setVisible(True)
                    if hasattr(self, 'sidebar_unlink_button'):
                        self.sidebar_unlink_button.setVisible(True)
                except Exception:
                    pass
        except Exception as e:
            self.logger.error(f"Error toggling sidebar: {str(e)}")

    def update_sidebar_repo_state(self, is_linked, repo_url=None):
        """Update the sidebar GitHub button and unlink button state."""
        try:
            if is_linked and repo_url:
                repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
                text = f"✓ {repo_name}"
                # set green linked style
                self.sidebar_github_button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLOR_SUCCESS};
                        color: #0f1419;
                        border: 1px solid {COLOR_SUCCESS};
                        border-radius: 0px;
                        font-size: 11px;
                        font-weight: 600;
                        padding: 10px;
                        font-family: 'Courier New', monospace;
                    }}
                    QPushButton:hover {{
                        background-color: {COLOR_SURFACE};
                        border: 1px solid {COLOR_SUCCESS};
                        color: {COLOR_SUCCESS};
                    }}
                    QPushButton:pressed {{
                        background-color: {COLOR_SUCCESS};
                        color: #0f1419;
                    }}
                """)
                self.sidebar_github_button.setText(text)
                self.sidebar_unlink_button.setEnabled(True)
            else:
                # default unlinked style
                self.sidebar_github_button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLOR_SURFACE_LIGHT};
                        color: {COLOR_TEXT_PRIMARY};
                        border: 1px solid {COLOR_SURFACE_LIGHT};
                        border-radius: 0px;
                        font-size: 11px;
                        font-weight: 500;
                        padding: 10px;
                        font-family: 'Courier New', monospace;
                    }}
                    QPushButton:hover {{
                        background-color: {COLOR_ACCENT_DARK_BLUE};
                        border: 1px solid {COLOR_ACCENT_BLUE};
                        color: {COLOR_ACCENT_BLUE};
                    }}
                    QPushButton:pressed {{
                        background-color: {COLOR_ACCENT_BLUE};
                        color: #0f1419;
                    }}
                """)
                self.sidebar_github_button.setText("Link GitHub Repository")
                self.sidebar_unlink_button.setEnabled(False)
        except Exception as e:
            try:
                self.logger.error(f"Error updating sidebar repo state: {str(e)}")
            except Exception:
                pass


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # APPLICATION FONT
    base_dir = os.path.dirname(os.path.abspath(__file__))

    title_font = os.path.join(base_dir, "fonts", "Redhawk.otf")
    regular_font = os.path.join(base_dir, "fonts", "Inter-Regular.otf")
    bold_font = os.path.join(base_dir, "fonts", "Inter-Bold.otf")

    QFontDatabase.addApplicationFont(regular_font)
    QFontDatabase.addApplicationFont(bold_font)
    QFontDatabase.addApplicationFont(title_font)

    app.setFont(QFont("Inter", 10))

    window = MainWindow()
    window.toggle_sidebar()  # Start with sidebar collapsed
    window.show()
    sys.exit(app.exec())
