import os
from pathlib import Path

# Base Directory Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "tracker.db"

# Security Configuration
SECRET_KEY = os.getenv("APP_SECRET_KEY", "b3af829d1c02e4839102ca74ef82c91a")
ENCRYPTION_KEY = os.getenv("DATABASE_ENCRYPTION_KEY", "0123456789abcdef0123456789abcdef") 

# Core Tracker Control Rules
BACKGROUND_CHECK_INTERVAL_SECONDS = 300  # Poll platforms every 5 minutes
HTTP_REQUEST_TIMEOUT_SECONDS = 30       # Drop hanging network requests after 30s
MAX_CONCURRENT_WORKERS = 3              # Max concurrent browser tasks running

# Ensure necessary system subfolders exist natively on boot
os.makedirs(BASE_DIR / "database", exist_ok=True)
