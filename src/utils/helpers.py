"""Utility helper functions for MountLLM project."""

import os
from pathlib import Path
from typing import Optional, Tuple

from dotenv import load_dotenv
from loguru import logger


def setup_logging(level: str = "INFO") -> None:
    """Set up Loguru logging configuration."""
    # Remove default handler
    logger.remove()

    # Add console handler with custom format
    logger.add(
        sink=lambda msg: print(msg, end=""),
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level,
        colorize=True,
    )

    # Add file handler
    logger.add(
        "mountllm.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=level,
        rotation="10 MB",
        retention="7 days",
    )


def load_config() -> dict:
    """Load configuration from environment variables and .env file."""
    # Load .env file if it exists
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)

    config = {
        "api_base_url": os.getenv(
            "CAMPTOCAMP_API_BASE_URL", "https://api.camptocamp.org"
        ),
        "user_agent": os.getenv("CAMPTOCAMP_USER_AGENT", "MountLLM-DataCollector/1.0"),
        "rate_limit": int(os.getenv("CAMPTOCAMP_RATE_LIMIT", "100")),
        "max_items_per_category": int(os.getenv("MAX_ITEMS_PER_CATEGORY", "1000")),
        "output_dir": os.getenv("OUTPUT_DIR", "./data"),
        "bbox": parse_bbox(os.getenv("CAMPTOCAMP_BBOX")),
    }

    return config


def parse_bbox(bbox_str: Optional[str]) -> Optional[Tuple[float, float, float, float]]:
    """Parse bounding box string into tuple of coordinates.

    Expected format: "min_lon,min_lat,max_lon,max_lat"
    """
    if not bbox_str:
        return None

    try:
        coords = [float(x.strip()) for x in bbox_str.split(",")]
        if len(coords) != 4:
            raise ValueError("Bounding box must have exactly 4 coordinates")
        return tuple(coords)
    except ValueError as e:
        logger.warning(f"Invalid bounding box format: {bbox_str}. Error: {e}")
        return None


def validate_config(config: dict) -> bool:
    """Validate configuration values."""
    errors = []

    # Validate rate limit
    if config["rate_limit"] <= 0 or config["rate_limit"] > 1000:
        errors.append("Rate limit must be between 1 and 1000")

    # Validate max items
    if (
        config["max_items_per_category"] <= 0
        or config["max_items_per_category"] > 100_000
    ):
        errors.append("Max items per category must be between 1 and 100000")

    # Validate output directory
    output_path = Path(config["output_dir"])
    if not output_path.parent.exists():
        errors.append(f"Output directory parent does not exist: {output_path.parent}")

    # Validate bounding box if provided
    if config["bbox"]:
        min_lon, min_lat, max_lon, max_lat = config["bbox"]
        if min_lon >= max_lon or min_lat >= max_lat:
            errors.append(
                "Invalid bounding box: min coordinates must be less than max coordinates"
            )
        if not (-180 <= min_lon <= 180 and -180 <= max_lon <= 180):
            errors.append("Longitude must be between -180 and 180")
        if not (-90 <= min_lat <= 90 and -90 <= max_lat <= 90):
            errors.append("Latitude must be between -90 and 90")

    if errors:
        for error in errors:
            logger.error(f"Configuration error: {error}")
        return False

    return True


def create_sample_env_file() -> None:
    """Create a sample .env file with default configuration."""
    env_content = """# Camptocamp API settings
CAMPTOCAMP_API_BASE_URL=https://api.camptocamp.org
CAMPTOCAMP_USER_AGENT=MountLLM-DataCollector/1.0
CAMPTOCAMP_RATE_LIMIT=100

# Data collection settings
MAX_ITEMS_PER_CATEGORY=1000
OUTPUT_DIR=./data

# Optional: Geographic bounding box (min_lon,min_lat,max_lon,max_lat)
# Example for French Alps: CAMPTOCAMP_BBOX=5.0,44.0,7.0,46.0
# CAMPTOCAMP_BBOX=
"""

    env_path = Path(".env")
    if env_path.exists():
        logger.info(".env file already exists, skipping creation")
        return

    with open(env_path, "w") as f:
        f.write(env_content)

    logger.info(f"Created sample .env file at {env_path}")
    logger.info("Please review and modify the configuration as needed")


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def ensure_directories(*dir_paths: str) -> None:
    """Ensure that the specified directories exist."""
    for dir_path in dir_paths:
        Path(dir_path).mkdir(parents=True, exist_ok=True)


def format_file_size(file_path: Path) -> str:
    """Format file size in human-readable format."""
    size_bytes = file_path.stat().st_size

    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0

    return f"{size_bytes:.1f} TB"
