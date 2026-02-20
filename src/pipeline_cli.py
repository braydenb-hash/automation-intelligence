import argparse
import json
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Automation Intelligence daily scan pipeline"
    )
    parser.add_argument(
        "--days-back", type=int, default=7,
        help="How many days back to check for videos (default: 7)"
    )
    parser.add_argument(
        "--max-per-channel", type=int, default=3,
        help="Max videos to process per channel (default: 3)"
    )
    parser.add_argument(
        "--rebuild-curriculum-only", action="store_true",
        help="Skip monitoring, just rebuild curriculum from existing library"
    )

    args = parser.parse_args()

    if args.rebuild_curriculum_only:
        from .generators.curriculum_builder import rebuild_curriculum
        rebuild_curriculum()
        print("Curriculum rebuilt.")
        return

    from .pipeline import run_daily_scan

    summary = run_daily_scan(
        days_back=args.days_back,
        max_per_channel=args.max_per_channel,
    )

    print("\n=== DAILY SCAN SUMMARY ===")
    print(json.dumps(summary, indent=2))

    if summary.get("high_value"):
        print("\nHIGH-VALUE DISCOVERIES:")
        for item in summary["high_value"]:
            print("  [%d/10] %s" % (item["score"], item["title"]))
            print("          %s" % item["url"])


if __name__ == "__main__":
    main()
