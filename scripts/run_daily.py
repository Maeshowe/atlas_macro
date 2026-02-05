#!/usr/bin/env python3
"""
ATLAS MACRO daily diagnostic.

Usage:
    python scripts/run_daily.py
    python scripts/run_daily.py --date 2026-02-05
    python scripts/run_daily.py --json
    python scripts/run_daily.py -v
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Ensure atlas_macro is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from atlas_macro.pipeline.daily import DailyPipeline


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run ATLAS MACRO daily stress diagnostic",
    )
    parser.add_argument(
        "--date", "-d", type=str, default=None, help="Date (YYYY-MM-DD), default: today"
    )
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON only")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    trade_date = None
    if args.date:
        try:
            trade_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print(f"Error: Invalid date format '{args.date}'. Use YYYY-MM-DD.")
            return 1

    pipeline = DailyPipeline()
    result = asyncio.run(pipeline.run(trade_date))

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print()
        print("=" * 60)
        print("ATLAS MACRO DIAGNOSTIC")
        print("=" * 60)
        print(f"Date:       {result.date}")
        print(f"State:      {result.macro_state.value}")
        print(f"Confidence: {result.confidence.value}")
        print("-" * 60)
        print("Drivers:")
        for d in result.drivers:
            print(f"  - {d}")
        print("-" * 60)
        print(f"Data Quality: {result.signals.data_quality:.0%}")
        print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
