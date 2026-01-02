"""
Better logging formatter for Kometizarr

Clear, readable logs with progress tracking - unlike Kometa's messy output
"""

import logging
import sys
from datetime import datetime, timedelta


class ColoredFormatter(logging.Formatter):
    """Add colors to log levels for better readability"""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'

    def format(self, record):
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{self.BOLD}{levelname}{self.RESET}"

        # Format the message
        result = super().format(record)

        # Reset levelname for next use
        record.levelname = levelname

        return result


class ProgressTracker:
    """Track progress and calculate ETAs"""

    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = datetime.now()
        self.success = 0
        self.failed = 0
        self.skipped = 0

    def update(self, success: bool = True, skipped: bool = False):
        """Update progress"""
        self.current += 1
        if skipped:
            self.skipped += 1
        elif success:
            self.success += 1
        else:
            self.failed += 1

    def get_progress_str(self) -> str:
        """Get formatted progress string with percentage and ETA"""
        percentage = (self.current / self.total * 100) if self.total > 0 else 0

        # Calculate ETA
        elapsed = (datetime.now() - self.start_time).total_seconds()
        if self.current > 0:
            rate = elapsed / self.current
            remaining = (self.total - self.current) * rate
            eta = timedelta(seconds=int(remaining))
            eta_str = f"ETA: {eta}"
        else:
            eta_str = "ETA: calculating..."

        return f"[{self.current}/{self.total}] {percentage:.1f}% | {eta_str}"

    def get_stats_str(self) -> str:
        """Get statistics string"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        rate = self.current / elapsed if elapsed > 0 else 0

        return (
            f"✓ Success: {self.success} | "
            f"⏭  Skipped: {self.skipped} | "
            f"✗ Failed: {self.failed} | "
            f"Rate: {rate:.2f}/sec"
        )


def setup_logger(name: str = 'kometizarr', level: int = logging.INFO) -> logging.Logger:
    """
    Set up a clean, readable logger

    Args:
        name: Logger name
        level: Logging level

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers = []

    # Console handler with colored output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Clean format with timestamps
    formatter = ColoredFormatter(
        fmt='%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    return logger


def print_header(title: str):
    """Print a clear section header"""
    width = 70
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width + "\n")


def print_subheader(title: str):
    """Print a subsection header"""
    width = 70
    print("\n" + "-" * width)
    print(f"  {title}")
    print("-" * width)


def print_summary(stats: dict):
    """Print final summary with statistics"""
    width = 70
    print("\n" + "=" * width)
    print("  SUMMARY")
    print("=" * width)

    for key, value in stats.items():
        print(f"  {key:30s}: {value}")

    print("=" * width + "\n")
