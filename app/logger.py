import logging
from logging.handlers import RotatingFileHandler
import os

LOG_DIR = "logs"
LOG_FILE = "logs/app.log"

os.makedirs(LOG_DIR, exist_ok=True)
 
logger = logging.getLogger("bg_remover")
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

file_handler = RotatingFileHandler(
    LOG_FILE, maxBytes=5*1024*1024, backupCount=3
)  # 5 MB per file, keep 5 backups

file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.info("Logger initialized.")
