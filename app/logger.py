"""Simple logging utility for the app. Logs to a file in the app directory."""

import os
from datetime import datetime
from pathlib import Path


class AppLogger:
    """Logs events to a file, resetting on each app start."""

    def __init__(self, log_dir: str):
        self.log_dir = Path(log_dir)
        self.log_file = self.log_dir / "logs.txt"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        # Reset log file on app start
        self._reset_log()

    def _reset_log(self):
        """Clear the log file."""
        with open(self.log_file, "w") as f:
            f.write(f"=== App Started at {datetime.now().isoformat()} ===\n")

    def log(self, message: str, level: str = "INFO"):
        """Write a log message with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        try:
            with open(self.log_file, "a") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Failed to write log: {e}")

    def info(self, message: str):
        """Log an info message."""
        self.log(message, "INFO")

    def error(self, message: str):
        """Log an error message."""
        self.log(message, "ERROR")

    def warning(self, message: str):
        """Log a warning message."""
        self.log(message, "WARNING")

    def debug(self, message: str):
        """Log a debug message."""
        self.log(message, "DEBUG")
