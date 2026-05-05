import sys
import os
import shutil
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QLabel, QSplitter, QSizePolicy
from PySide6.QtCore import Qt, QThread, Signal, QObject, QTimer
from PySide6.QtGui import QFontDatabase, QFont # Used to change fonts (as long as they are downloaded)
from screens import BlueScreen, RedScreen, GreenScreen, SettingsScreen, GitHubScreen
import repo_puller
from overview import generate_repo_overview, generate_file_overview
from explain import collect_code_file_paths, generate_code_explanation, annotate_code_file, save_annotated_file
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
COLOR_ACCENT_RED = "#c41c3b"


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
        self._install_exception_hook()
        self.logger.info("Application started")
        self.ensure_repos_folder()

        screen = QApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            self.device_width = available.width()
            self.device_height = available.height()
        else:
            self.device_width = 1920
            self.device_height = 1080

        self.window_initial_width = max(900, min(int(self.device_width * 0.9), 1400))
        self.window_initial_height = max(680, min(int(self.device_height * 0.82), 1000))
        self.setMinimumSize(max(760, int(self.device_width * 0.55)), max(600, int(self.device_height * 0.55)))
        self.resize(self.window_initial_width, self.window_initial_height)

        self.sidebar_expanded_width = max(260, int(self.device_width * 0.16))
        self.sidebar_collapsed_width = max(56, int(self.device_width * 0.03))
        self.sidebar_allowed_max = max(400, int(self.device_width * 0.22))

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
        self.settings_screen = SettingsScreen()
        self.github_screen = GitHubScreen()

        self.blue_screen.repo_overview_requested.connect(self.on_generate_repo_overview)
        self.blue_screen.file_overview_requested.connect(self.on_generate_file_overview)
        self.red_screen.refresh_files_requested.connect(self.on_refresh_red_files)
        self.red_screen.code_explanation_requested.connect(self.on_generate_code_explanation)
        self.red_screen.annotate_file_requested.connect(self.on_annotate_file)
        self.red_screen.save_annotated_file_requested.connect(self.on_save_annotated_file)

        self.stacked.addWidget(self.blue_screen)
        self.stacked.addWidget(self.red_screen)
        self.stacked.addWidget(self.green_screen)
        self.stacked.addWidget(self.settings_screen)
        self.stacked.addWidget(self.github_screen)

        # Connect back signals
        self.blue_screen.back_pressed.connect(self.back_to_main)
        self.red_screen.back_pressed.connect(self.back_to_main)
        self.green_screen.back_pressed.connect(self.back_to_main)
        self.settings_screen.back_pressed.connect(self.back_to_main)
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
        self.sidebar.setMinimumWidth(self.sidebar_collapsed_width)
        self.sidebar.setMaximumWidth(self.sidebar_allowed_max)
        self.sidebar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
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
            ("Code Annotation", 1, COLOR_ACCENT_RED),
            ("Test Creator", 2, COLOR_SUCCESS),
            ("Settings", 3, COLOR_TEXT_SECONDARY),
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
        self.sidebar_github_button.clicked.connect(lambda: self.navigate_to_screen(4))

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
        self.stacked.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.addWidget(self.sidebar)
        self.main_splitter.addWidget(self.stacked)
        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)
        self.main_splitter.setCollapsible(0, False)

        self.setCentralWidget(self.main_splitter)
        self.stacked.setCurrentIndex(0)
        
        # Track current repo
        self.current_repo_url = None
        self.sidebar_collapsed = False
        self.set_sidebar_collapsed(True)
        
        # Check if repo is already linked
        self.check_and_update_repo_status()

    def _install_exception_hook(self):
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            error_message = f"Uncaught exception: {exc_value}"
            self.logger.exception(error_message)
            self.logger.exception("""Traceback:
""")
            import traceback
            traceback_text = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            self.logger.exception(traceback_text)
            sys.__excepthook__(exc_type, exc_value, exc_traceback)

        sys.excepthook = handle_exception

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
                    if os.path.isdir(repo_folder):
                        self.github_screen.show_file_tree(repo_folder)
                        self.blue_screen.set_repo_ready_state(True)
                    else:
                        self.logger.warning(f"Linked repo folder not found: {repo_folder}")
                        self.blue_screen.set_repo_ready_state(False)
                    
                    self.logger.info(f"Linked repo found: {self.current_repo_url}")
            except Exception as e:
                self.logger.error(f"Error reading repo_info.txt: {str(e)}")
        else:
            self.current_repo_url = None
            self.main_screen.set_repo_linked(False)
            self.blue_screen.set_repo_ready_state(False)
            # Update sidebar to show unlinked state
            try:
                self.update_sidebar_repo_state(False)
            except Exception:
                pass
    
    def _update_all_screens_repo_info(self):
        """Update all screens with current repo info."""
        repo_folder = self._get_repo_folder()
        self.blue_screen.set_repo_info(self.current_repo_url)
        self.red_screen.set_repo_info(self.current_repo_url)
        self.green_screen.set_repo_info(self.current_repo_url)
        self.settings_screen.set_repo_info(self.current_repo_url)
        self.github_screen.set_repo_info(self.current_repo_url)
        self.settings_screen.load_settings()
        repo_ready = bool(repo_folder and os.path.isdir(repo_folder))
        self.blue_screen.set_repo_ready_state(repo_ready)
        self.red_screen.set_repo_ready_state(repo_ready)
        if repo_ready:
            self.blue_screen.show_file_tree(repo_folder)
            self.red_screen.show_code_files(repo_folder)

    def _get_repo_folder(self):
        if not self.current_repo_url:
            return None
        repo_name = self.current_repo_url.rstrip('/').split('/')[-1].replace('.git', '')
        return os.path.join(self.repos_folder, repo_name)

    def navigate_to_screen(self, index):
        """Navigate to a specific screen (0-3 for detail screens, 4 for GitHub)."""
        self._update_all_screens_repo_info()
        if index == 3:
            self.settings_screen.load_settings()
        self.stacked.setCurrentIndex(index + 1)

    def back_to_main(self):
        """Return to the main screen."""
        self.stacked.setCurrentIndex(0)
        self.check_and_update_repo_status()

    def on_generate_repo_overview(self):
        repo_folder = self._get_repo_folder()
        self.logger.info("User requested repository overview generation")
        if not repo_folder or not os.path.isdir(repo_folder):
            self.blue_screen.set_overview_text("No linked repository folder is available. Please link a repository first.")
            self.logger.warning("Repository overview requested but no linked folder was available")
            return

        self.blue_screen.set_overview_text("Generating repository overview. This may take a moment...")

        class OverviewWorker(QObject):
            finished = Signal(str, bool)

            def __init__(self, folder_path, repo_url, logger_ref):
                super().__init__()
                self.folder_path = folder_path
                self.repo_url = repo_url
                self.logger = logger_ref

            def run(self):
                try:
                    self.logger.info(f"Overview worker started for folder: {self.folder_path}")
                    summary = generate_repo_overview(self.folder_path, self.repo_url)
                    self.logger.info("Overview worker completed generation")
                    self.finished.emit(summary, True)
                except Exception as exc:
                    self.logger.error(f"Overview generation failed: {str(exc)}")
                    self.finished.emit(f"Overview generation failed: {str(exc)}", False)

        self.overview_worker = OverviewWorker(repo_folder, self.current_repo_url, self.logger)
        self.overview_thread = QThread()
        self.overview_worker.moveToThread(self.overview_thread)

        self.overview_worker.finished.connect(self._apply_overview_result, Qt.QueuedConnection)
        self.overview_worker.finished.connect(self.overview_worker.deleteLater, Qt.QueuedConnection)
        self.overview_thread.finished.connect(self.overview_thread.deleteLater)
        self.overview_thread.started.connect(self.overview_worker.run)
        self.overview_thread.start()

    def _apply_overview_result(self, text, success):
        """Slot always called on the main thread via QueuedConnection."""
        try:
            self.blue_screen.set_overview_text(text)
        except Exception as exc:
            self.logger.error(f"Failed to update overview text in main thread: {exc}")
        finally:
            if hasattr(self, 'overview_thread') and self.overview_thread:
                self.overview_thread.quit()
            if success:
                self.logger.info("Repository overview generation completed successfully")
            else:
                self.logger.warning("Repository overview generation failed")

    def on_generate_file_overview(self, file_path):
        if not file_path or not os.path.isfile(file_path):
            self.blue_screen.set_overview_text("Selected file not found. Please select a valid file.")
            self.logger.warning("File overview requested but selected file was missing")
            return

        self.logger.info(f"User requested file overview generation for: {file_path}")
        self.blue_screen.set_overview_text("Generating file overview. This may take a moment...")

        class FileOverviewWorker(QObject):
            finished = Signal(str, bool)

            def __init__(self, file_path, logger_ref):
                super().__init__()
                self.file_path = file_path
                self.logger = logger_ref

            def run(self):
                try:
                    self.logger.info(f"File overview worker started for file: {self.file_path}")
                    summary = generate_file_overview(self.file_path)
                    self.logger.info("File overview worker completed generation")
                    self.finished.emit(summary, True)
                except Exception as exc:
                    self.logger.error(f"File overview generation failed: {str(exc)}")
                    self.finished.emit(f"File overview generation failed: {str(exc)}", False)

        self.file_overview_worker = FileOverviewWorker(file_path, self.logger)
        self.file_overview_thread = QThread()
        self.file_overview_worker.moveToThread(self.file_overview_thread)

        self.file_overview_worker.finished.connect(self._handle_file_overview_result, Qt.QueuedConnection)
        self.file_overview_worker.finished.connect(self.file_overview_worker.deleteLater, Qt.QueuedConnection)
        self.file_overview_thread.finished.connect(self.file_overview_thread.deleteLater)
        self.file_overview_thread.started.connect(self.file_overview_worker.run)
        self.file_overview_thread.start()

    def _handle_file_overview_result(self, text, success):
        """Slot always called on the main thread via QueuedConnection."""
        try:
            self.blue_screen.set_overview_text(text)
        except Exception as exc:
            self.logger.error(f"Failed to update file overview text in main thread: {exc}")
        finally:
            if hasattr(self, 'file_overview_thread') and self.file_overview_thread:
                self.file_overview_thread.quit()
            if success:
                self.logger.info("File overview generation completed successfully")
            else:
                self.logger.warning("File overview generation failed")

    def on_refresh_red_files(self):
        repo_folder = self._get_repo_folder()
        self.logger.info("Refreshing code file list for Red screen")
        if not repo_folder or not os.path.isdir(repo_folder):
            self.red_screen.set_repo_ready_state(False)
            return
        self.red_screen.show_code_files(repo_folder)

    def on_generate_code_explanation(self, file_path):
        if not file_path or not os.path.isfile(file_path):
            self.red_screen.set_status_text("Selected file not found. Please select a valid code file.")
            self.logger.warning("Code explanation requested but selected file was missing")
            return

        self.logger.info(f"User requested code explanation for: {file_path}")
        self.red_screen.set_status_text("Generating code explanation. This may take a moment...")
        self.red_screen.set_explanation_text("")

        class CodeExplanationWorker(QObject):
            finished = Signal(str, bool)

            def __init__(self, file_path, repo_root, logger_ref):
                super().__init__()
                self.file_path = file_path
                self.repo_root = repo_root
                self.logger = logger_ref

            def run(self):
                try:
                    self.logger.info(f"Code explanation worker started for: {self.file_path}")
                    summary = generate_code_explanation(self.file_path, self.repo_root)
                    self.logger.info("Code explanation worker completed generation")
                    self.finished.emit(summary, True)
                except Exception as exc:
                    self.logger.error(f"Code explanation generation failed: {str(exc)}")
                    self.finished.emit(f"Code explanation generation failed: {str(exc)}", False)

        repo_folder = self._get_repo_folder()
        self.code_explanation_worker = CodeExplanationWorker(file_path, repo_folder, self.logger)
        self.code_explanation_thread = QThread()
        self.code_explanation_worker.moveToThread(self.code_explanation_thread)
        self.code_explanation_worker.finished.connect(self._handle_code_explanation_result, Qt.QueuedConnection)
        self.code_explanation_worker.finished.connect(self.code_explanation_worker.deleteLater, Qt.QueuedConnection)
        self.code_explanation_thread.finished.connect(self.code_explanation_thread.deleteLater)
        self.code_explanation_thread.started.connect(self.code_explanation_worker.run)
        self.code_explanation_thread.start()

    def _handle_code_explanation_result(self, text, success):
        try:
            self.red_screen.set_explanation_text(text)
            self.red_screen.set_status_text("Explanation generation completed." if success else "Explanation generation failed.")
        except Exception as exc:
            self.logger.error(f"Failed to update Red screen explanation text: {exc}")
        finally:
            if hasattr(self, "code_explanation_thread") and self.code_explanation_thread:
                self.code_explanation_thread.quit()
            if success:
                self.logger.info("Code explanation generation completed successfully")
            else:
                self.logger.warning("Code explanation generation failed")

    def on_annotate_file(self, file_path):
        if not file_path or not os.path.isfile(file_path):
            self.red_screen.set_status_text("Selected file not found. Please select a valid code file.")
            self.logger.warning("Annotate requested but selected file was missing")
            return

        self.logger.info(f"User requested file annotation for: {file_path}")
        self.red_screen.set_status_text("Generating annotated version. This may take a moment...")
        self.red_screen.set_explanation_text("")

        class AnnotateWorker(QObject):
            finished = Signal(str, bool)

            def __init__(self, file_path, repo_root, logger_ref):
                super().__init__()
                self.file_path = file_path
                self.repo_root = repo_root
                self.logger = logger_ref

            def run(self):
                try:
                    self.logger.info(f"Annotate worker started for: {self.file_path}")
                    annotated = annotate_code_file(self.file_path, self.repo_root)
                    self.logger.info("Annotate worker completed")
                    self.finished.emit(annotated, True)
                except Exception as exc:
                    self.logger.error(f"Annotation failed: {str(exc)}")
                    self.finished.emit(f"Annotation failed: {str(exc)}", False)

        repo_folder = self._get_repo_folder()
        self.annotate_worker = AnnotateWorker(file_path, repo_folder, self.logger)
        self.annotate_thread = QThread()
        self.annotate_worker.moveToThread(self.annotate_thread)
        self.annotate_worker.finished.connect(self._handle_annotate_result, Qt.QueuedConnection)
        self.annotate_worker.finished.connect(self.annotate_worker.deleteLater, Qt.QueuedConnection)
        self.annotate_thread.finished.connect(self.annotate_thread.deleteLater)
        self.annotate_thread.started.connect(self.annotate_worker.run)
        self.annotate_thread.start()

    def _handle_annotate_result(self, text, success):
        try:
            self.red_screen.set_annotated_text(text)
            self.red_screen.set_status_text("Annotated version generated." if success else "Annotation failed.")
            self.red_screen.set_save_enabled(success)
        except Exception as exc:
            self.logger.error(f"Failed to update Red screen annotated text: {exc}")
        finally:
            if hasattr(self, "annotate_thread") and self.annotate_thread:
                self.annotate_thread.quit()
            if success:
                self.logger.info("File annotation completed successfully")
            else:
                self.logger.warning("File annotation failed")

    def on_save_annotated_file(self, file_path, annotated_content):
        if not file_path or not annotated_content:
            self.red_screen.set_status_text("No annotated content is available to save.")
            self.logger.warning("Save annotated file requested without content")
            return

        self.logger.info(f"Saving annotated file for: {file_path}")
        success, saved_path = save_annotated_file(file_path, annotated_content)
        if success:
            self.red_screen.set_status_text(f"Annotated file saved to: {saved_path}")
            self.logger.info(f"Annotated file saved: {saved_path}")
        else:
            self.red_screen.set_status_text(f"Failed to save annotated file: {saved_path}")
            self.logger.warning(f"Saving annotated file failed: {saved_path}")

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

    def set_sidebar_collapsed(self, collapsed: bool):
        """Set the sidebar collapsed or expanded state."""
        try:
            self.sidebar_collapsed = collapsed
            collapsed_width = self.sidebar_collapsed_width
            expanded_width = self.sidebar_expanded_width
            if collapsed:
                self.sidebar.setFixedWidth(collapsed_width)
                try:
                    for b in getattr(self, 'sidebar_buttons', []):
                        b.setVisible(False)
                except Exception:
                    pass
                try:
                    if hasattr(self, 'sidebar_github_button'):
                        self.sidebar_github_button.setVisible(False)
                        self.sidebar_github_button.setMaximumWidth(48)
                        self.sidebar_github_button.setText("Repo" if self.current_repo_url else "Link")
                        self.sidebar_github_button.setMinimumWidth(48)
                    if hasattr(self, 'sidebar_unlink_button'):
                        self.sidebar_unlink_button.setVisible(False)
                except Exception:
                    pass
            else:
                self.sidebar.setFixedWidth(expanded_width)
                try:
                    for b in getattr(self, 'sidebar_buttons', []):
                        b.setVisible(True)
                except Exception:
                    pass
                try:
                    if hasattr(self, 'sidebar_github_button'):
                        self.sidebar_github_button.setVisible(not collapsed)
                        self.sidebar_github_button.setMaximumWidth(16777215)
                        self.sidebar_github_button.setMinimumWidth(0)
                    if hasattr(self, 'sidebar_unlink_button'):
                        self.sidebar_unlink_button.setVisible(self.current_repo_url is not None)
                except Exception:
                    pass
                if self.current_repo_url:
                    self.update_sidebar_repo_state(True, self.current_repo_url)
                else:
                    self.update_sidebar_repo_state(False)
        except Exception as e:
            self.logger.error(f"Error setting sidebar collapsed state: {str(e)}")

    def toggle_sidebar(self):
        """Collapse or expand the sidebar."""
        self.set_sidebar_collapsed(not getattr(self, 'sidebar_collapsed', False))

    def update_sidebar_repo_state(self, is_linked, repo_url=None):
        """Update the sidebar GitHub button and unlink button state."""
        try:
            collapsed = getattr(self, 'sidebar_collapsed', False)
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
                self.sidebar_github_button.setText("GH" if collapsed else text)
                self.sidebar_github_button.setMaximumWidth(48 if collapsed else 16777215)
                self.sidebar_github_button.setVisible(True)
                self.sidebar_unlink_button.setEnabled(True)
            else:
                self.sidebar_github_button.setVisible(not collapsed)
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
                self.sidebar_github_button.setText("Link" if collapsed else "Link GitHub Repository")
                self.sidebar_github_button.setMaximumWidth(48 if collapsed else 16777215)
                self.sidebar_unlink_button.setEnabled(False)
            if collapsed:
                self.sidebar_unlink_button.setVisible(False)
            else:
                self.sidebar_unlink_button.setVisible(is_linked)
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
    window.show()
    sys.exit(app.exec())
