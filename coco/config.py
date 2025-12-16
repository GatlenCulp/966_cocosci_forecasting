"""Project configuration and path management.

Defines project-wide constants, directory structures, and logging setup.
Automatically loads environment variables from .env if present.
"""

from pathlib import Path

from loguru import logger

# try:
#     from dotenv import load_dotenv

#     load_dotenv()
# except ImportError:
#     # dotenv not available - skip loading .env file
#     pass

# try:
#     from loguru import logger
# except ImportError:
#     # Fallback to standard logging if loguru not available
#     import logging

#     logger = logging.getLogger(__name__)
#     logging.basicConfig(level=logging.INFO)

# Paths
PROJ_ROOT = Path(__file__).resolve().parents[1]


DATA_DIR = PROJ_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

MODELS_DIR = PROJ_ROOT / "models"

REPORTS_DIR = PROJ_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

SRC_DIR = PROJ_ROOT / "coco"


# def _configure_logger(format: Literal["short", "long"] = "short"):
# Configure loguru with concise format for research notebooks
short_format = "<green>{time:HH:mm:ss}</green> | <level>{message:<100}</level> - <cyan>{name}</cyan>:<cyan>{line}</cyan>"

logger.remove(0)  # Remove default handler

# Simple format: just level, message, and optional exception
logger.add(
    lambda msg: print(msg, end=""),
    format=short_format,
    colorize=True,
)

# If tqdm is installed, use tqdm.write instead of print
# https://github.com/Delgan/loguru/issues/135
try:
    from tqdm import tqdm

    logger.remove()  # Remove the print handler
    logger.add(
        lambda msg: tqdm.write(msg, end=""),
        format=short_format,
        colorize=True,
    )
except ModuleNotFoundError:
    pass


# logger = _configure_logger("short")

# logger.info(f"PROJ_ROOT path is: {PROJ_ROOT}")
