# src/open_swarm_mcp/utils/logger.py

import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_logger(name: str = __name__) -> logging.Logger:
    """
    Set up a logger with both console and file handlers.

    Args:
        name (str): The name of the logger. Defaults to the module's name.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Set the minimum logging level for the logger
        logger.setLevel(logging.DEBUG)

        # Create formatter for log messages
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Console handler for outputting logs to stdout
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)  # Set console handler level
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Rotating file handler for logging to a file with rotation
        file_handler = RotatingFileHandler(
            filename="open_swarm_mcp.log",
            maxBytes=5*1024*1024,  # 5 MB per log file
            backupCount=5,         # Keep up to 5 backup log files
            encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)  # Set file handler level
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Prevent log messages from being propagated to the root logger
        logger.propagate = False

    return logger
