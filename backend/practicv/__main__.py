from __future__ import annotations

import argparse
import json
import sys

from practicv.adapters.db.session import SessionLocal
from practicv.seed import seed_demo


def _seed(volume: int) -> int:
    with SessionLocal() as session:
        result = seed_demo(session, volume=volume)
        session.commit()
    sys.stdout.write(
        json.dumps(
            {
                "profile_id": str(result.profile_id),
                "offer_ids": [str(value) for value in result.offer_ids],
                "application_ids": [str(value) for value in result.application_ids],
                "offers_total": result.offers_total,
                "matches_total": result.matches_total,
                "applications_total": result.applications_total,
                "reminders_total": result.reminders_total,
            },
            ensure_ascii=False,
        )
        + "\n"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="practicv")
    subparsers = parser.add_subparsers(dest="command", required=True)

    seed_parser = subparsers.add_parser("seed", help="Seed synthetic data")
    seed_parser.add_argument("--demo", action="store_true", help="Create demo data")
    seed_parser.add_argument(
        "--volume",
        type=int,
        default=1000,
        help="Number of additional synthetic offers for volume testing",
    )

    args = parser.parse_args()
    if args.command == "seed":
        if not args.demo:
            parser.error("Use --demo to confirm synthetic seeding")
        return _seed(args.volume)
    parser.error("Unknown command")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
