import os
from pathlib import Path

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Directories
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
CONSULTAS_DIR = OUTPUT_DIR / "consultas"
EXPORTS_DIR = OUTPUT_DIR / "exports"
LOGS_DIR = OUTPUT_DIR / "logs"

DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
CHECKPOINT_DIR = DATA_DIR / "checkpoints"

DB_PATH = CHECKPOINT_DIR / "consultas.db"
PADRON_CACHE_DB = CACHE_DIR / "padron_reducido.db"
DEFAULT_EXCEL_OUTPUT = EXPORTS_DIR / "Consulta_RUC_SUNAT.xlsx"

# Settings
BATCH_SIZE = 1000
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0  # seconds
TIMEOUT = 10.0  # seconds
PAUSE_BETWEEN_BATCHES = 0.01  # seconds

LOG_LEVEL = "INFO"
LOG_FILE = LOGS_DIR / "app.log"

# Ensure directories exist
for directory in [INPUT_DIR, OUTPUT_DIR, CONSULTAS_DIR, EXPORTS_DIR, LOGS_DIR, DATA_DIR, CACHE_DIR, CHECKPOINT_DIR]:
    os.makedirs(directory, exist_ok=True)
