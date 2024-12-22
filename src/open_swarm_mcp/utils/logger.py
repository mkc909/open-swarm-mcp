# src/open_swarm_mcp/utils/logger.py

import logging
from typing import Optional

def setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.DEBUG) -> logging.Logger:
    """
    Set up a logger with the specified name, log file, and level.

    Args:
        name (str): Name of the logger.
        log_file (Optional[str]): Path to the log file. If None, logs to console only.
        level (int): Logging level.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Avoid adding multiple handlers to the logger
    if not logger.handlers:
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # File handler
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setLevel(level)
            fh.setFormatter(formatter)
            logger.addHandler(fh)

    return logger
