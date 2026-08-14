import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from contextvars import ContextVar

# ContextVar to store request-scoped identifiers (async-safe and thread-safe)
request_id_var: ContextVar[str] = ContextVar("request_id", default="system")

class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get()
        return True

# Load env variables or defaults
LOG_LEVEL_STR = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE", "kronx_app.log")
LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", "10485760"))  # 10MB default
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))

# Determine absolute path for log file
log_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log_path = os.path.join(log_dir, LOG_FILE)

# Setup logger
logger = logging.getLogger("kronx")
logger.setLevel(getattr(logging, LOG_LEVEL_STR, logging.INFO))

# Clear any existing handlers
logger.handlers = []

# Add request_id filter
req_id_filter = RequestIdFilter()
logger.addFilter(req_id_filter)

# Format including request ID
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - [req:%(request_id)s] - [%(filename)s:%(lineno)d] - %(message)s"
)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Rotating file handler
try:
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
except Exception as e:
    print(f"Could not initialize rotating file logger: {e}", file=sys.stderr)
