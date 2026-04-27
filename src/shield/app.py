from __future__ import annotations

import argparse
from collections.abc import Sequence

from shield.core import Config, Orchestrator
from shield.db import EventStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Shield v0.1 scaffold")
    parser.add_argument(
        "--demo-trigger",
        action="store_true",
        help="emit a synthetic friction event and print its summary",
    )
    parser.add_argument(
        "--db-path",
        default=None,
        help="optional SQLite path for persisting the demo event",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = Config()
    db_path = args.db_path if args.db_path is not None else config.db_path

    with EventStore(db_path) as store:
        orchestrator = Orchestrator(config=config, event_store=store)
        if args.demo_trigger:
            event = orchestrator.trigger_demo()
            print("shield.demo_trigger=ok")
            print(f"session_id={event.session_id}")
            print(f"source={event.source.value}")
            print(f"score={event.score:.2f}")
            print(f"threshold={event.threshold_at_trigger:.2f}")
            print(f"reason={event.reason}")
            return 0

    build_parser().print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
