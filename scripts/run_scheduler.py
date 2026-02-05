#!/usr/bin/env python3
"""
ATLAS MACRO scheduler.

Runs the daily pipeline at a specified time on trading days.

Usage:
    python scripts/run_scheduler.py                    # Default: 4:30 PM
    python scripts/run_scheduler.py --time 16:30
    python scripts/run_scheduler.py --time 09:30 -v
"""

import argparse
import asyncio
import logging
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from atlas_macro.pipeline.daily import DailyPipeline

logger = logging.getLogger("atlas_scheduler")


def is_trading_day(d: date) -> bool:
    """Check if date is a weekday (basic check, no holiday calendar)."""
    return d.weekday() < 5


def next_run_time(target_hour: int, target_minute: int) -> datetime:
    """Calculate the next run datetime, skipping weekends."""
    now = datetime.now()
    target = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    while target.weekday() >= 5:
        target += timedelta(days=1)
    return target


def run_scheduler(target_hour: int = 16, target_minute: int = 30) -> None:
    """Run the scheduler loop."""
    pipeline = DailyPipeline()
    logger.info(f"ATLAS MACRO scheduler started. Target time: {target_hour:02d}:{target_minute:02d}")

    while True:
        target = next_run_time(target_hour, target_minute)
        wait_seconds = (target - datetime.now()).total_seconds()
        logger.info(f"Next run: {target} (sleeping {wait_seconds:.0f}s)")
        time.sleep(max(0, wait_seconds))

        if is_trading_day(date.today()):
            try:
                result = asyncio.run(pipeline.run())
                logger.info(
                    f"Completed: {result.macro_state.value} [{result.confidence.value}]"
                )
            except Exception:
                logger.exception("Pipeline failed")
        else:
            logger.info(f"Skipping non-trading day: {date.today()}")


def main() -> int:
    parser = argparse.ArgumentParser(description="ATLAS MACRO scheduler")
    parser.add_argument(
        "--time", "-t", type=str, default="16:30", help="Run time HH:MM (default: 16:30)"
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    try:
        hour, minute = map(int, args.time.split(":"))
    except ValueError:
        print(f"Error: Invalid time format '{args.time}'. Use HH:MM.")
        return 1

    run_scheduler(hour, minute)
    return 0


if __name__ == "__main__":
    sys.exit(main())
