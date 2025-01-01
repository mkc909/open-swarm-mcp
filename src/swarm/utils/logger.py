# src/swarm/utils/logger.py

import logging
import sys

def setup_logger(name: str) -> logging.Logger:
    """
    Sets up and returns a logger with the specified name.
    Configures the logger to output to stdout with a specific format.

    Args:
        name (str): Name of the logger.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Set to DEBUG for detailed logs

    if not logger.handlers:
        # Create console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)

        # Create formatter and add it to the handler
        formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
        ch.setFormatter(formatter)

        # Add handler to the logger
        logger.addHandler(ch)

    return logger
