#!/usr/bin/env python3
"""Main entry point for MountLLM data collection."""

import asyncio
import sys
from pathlib import Path

from loguru import logger

from src.data.collector import DataCollector
from src.utils.helpers import (
    create_sample_env_file,
    load_config,
    setup_logging,
    validate_config,
)


async def main():
    """Main data collection function."""
    logger.info("🚀 Starting MountLLM Data Collection")
    logger.info("=" * 50)

    try:
        # Load and validate configuration
        logger.info("📋 Loading configuration...")
        config = load_config()

        if not validate_config(config):
            logger.error(
                "❌ Configuration validation failed. Please check your .env file."
            )
            return 1

        logger.info("✅ Configuration loaded successfully")
        logger.info(f"   API Base URL: {config['api_base_url']}")
        logger.info(f"   Rate Limit: {config['rate_limit']} requests/minute")
        logger.info(f"   Max Items per Category: {config['max_items_per_category']}")
        logger.info(f"   Output Directory: {config['output_dir']}")
        if config["bbox"]:
            logger.info(f"   Bounding Box: {config['bbox']}")
        else:
            logger.info("   Bounding Box: None (collecting worldwide)")

        # Create data collector
        collector = DataCollector(
            output_dir=config["output_dir"],
            max_items_per_category=config["max_items_per_category"],
            bbox=config["bbox"],
            api_base_url=config["api_base_url"],
            user_agent=config["user_agent"],
            rate_limit=config["rate_limit"],
        )

        # Run the collection pipeline
        logger.info("🔍 Starting data collection pipeline...")
        items, raw_path, processed_path, report_path = await collector.run_collection()

        # Final summary
        logger.info("=" * 50)
        logger.info("🎉 Data collection completed successfully!")
        logger.info(f"📊 Total items collected: {len(items)}")
        logger.info(f"📁 Raw data saved to: {raw_path}")
        logger.info(f"📁 Processed data saved to: {processed_path}")
        logger.info(f"📄 Collection report: {report_path}")
        logger.info("=" * 50)

        return 0

    except KeyboardInterrupt:
        logger.info("⚠️  Data collection interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Unexpected error during data collection: {e}")
        logger.exception("Full traceback:")
        return 1


def setup():
    """Set up the project environment."""
    logger.info("🔧 Setting up project environment...")

    # Create sample .env file if it doesn't exist
    create_sample_env_file()

    # Ensure data directories exist
    data_dirs = ["./data", "./data/raw", "./data/processed", "./data/final"]
    for dir_path in data_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Ensured directory exists: {dir_path}")


if __name__ == "__main__":
    logger.info("🐍 MountLLM starting up...")

    # Set up logging first
    setup_logging(level="INFO")

    # Set up project environment
    setup()

    # Run the main function
    try:
        logger.info("🔄 Running main data collection...")
        exit_code = asyncio.run(main())
        logger.info(f"✅ Data collection finished with exit code: {exit_code}")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.warning("⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        logger.exception("Full traceback:")
        sys.exit(1)
