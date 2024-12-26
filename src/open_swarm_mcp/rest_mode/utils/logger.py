import logging
from django.conf import settings

def setup_logger(name: str) -> logging.Logger:
    """
    Sets up a logger with the specified name.

    Args:
        name (str): Name of the logger.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Set to DEBUG for detailed logs

    # Create console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # Create file handler with rotation
    fh = logging.handlers.RotatingFileHandler(
        filename='rest_mode.log',
        maxBytes=5*1024*1024,  # 5 MB
        backupCount=5
    )
    fh.setLevel(logging.DEBUG)

    # Create formatter and add it to the handlers
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    # Avoid adding multiple handlers if they already exist
    if not logger.handlers:
        logger.addHandler(ch)
        logger.addHandler(fh)

    return logger
