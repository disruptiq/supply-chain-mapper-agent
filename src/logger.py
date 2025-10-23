import logging
import sys
import os
from pathlib import Path
from typing import Optional
import colorama

class SupplyChainLogger:
    """Enhanced logging for the supply chain mapper"""

    def __init__(self, level: str = "INFO", log_file: Optional[str] = None, enable_colors: bool = True):
        colorama.init()  # Initialize colorama for cross-platform color support
        self.enable_colors = enable_colors and self._supports_color()

        # Create logger
        self.logger = logging.getLogger('supply_chain_mapper')
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))

        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self._get_formatter())
        self.logger.addHandler(console_handler)

        # File handler if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

        # Custom log levels for our use case
        self.SUCCESS_LEVEL = 25
        logging.addLevelName(self.SUCCESS_LEVEL, "SUCCESS")

        # Add success method to Logger class if not already present
        if not hasattr(logging.Logger, 'success'):
            def success(self, message, *args, **kwargs):
                if self.isEnabledFor(25):  # SUCCESS_LEVEL
                    self._log(25, message, args, **kwargs)
            logging.Logger.success = success

    def _supports_color(self) -> bool:
        """Check if terminal supports colors"""
        return (
            hasattr(sys.stdout, 'isatty') and
            sys.stdout.isatty() and
            sys.platform != 'win32' or
            'COLORTERM' in os.environ or
            os.environ.get('TERM_PROGRAM', '').startswith(('iTerm', 'Apple'))
        )

    def _get_formatter(self):
        """Get appropriate formatter based on color support"""
        if self.enable_colors:
            return ColoredFormatter()
        else:
            return logging.Formatter('%(levelname)s: %(message)s')

    def get_logger(self):
        """Get the configured logger"""
        return self.logger

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors using colorama"""

    COLORS = {
        'DEBUG': colorama.Fore.CYAN,
        'INFO': colorama.Fore.GREEN,
        'SUCCESS': colorama.Fore.LIGHTGREEN_EX,
        'WARNING': colorama.Fore.YELLOW,
        'ERROR': colorama.Fore.RED,
        'CRITICAL': colorama.Fore.LIGHTRED_EX,
        'RESET': colorama.Fore.RESET
    }

    def format(self, record):
        if record.levelname in self.COLORS:
            color = self.COLORS[record.levelname]
            reset = self.COLORS['RESET']
            record.levelname = f"{color}{record.levelname}{reset}"
            record.msg = f"{color}{record.msg}{reset}"

        return super().format(record)

# Global logger instance
_logger_instance = None

def get_logger(level: str = "INFO", log_file: Optional[str] = None, enable_colors: bool = True):
    """Get or create the global logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = SupplyChainLogger(level, log_file, enable_colors)
    return _logger_instance.get_logger()
