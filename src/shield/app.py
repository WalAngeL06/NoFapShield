from __future__ import annotations

import argparse
from collections.abc import Sequence

from shield.core import Config, FrictionEvent, Orchestrator
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
    parser.add_argument(
        "--screen",
        choices=("overlay", "checkin", "dashboard", "settings", "onboarding"),
        default=None,
        help="launch a specific UI screen",
    )
    parser.add_argument(
        "--show-overlay",
        action="store_true",
        help="launch the pause overlay after --demo-trigger records its event",
    )
    return parser


def _run_overlay_screen() -> int:
    from shield.ui.blur_overlay import run_overlay

    return run_overlay()


def _run_checkin_screen(db_path: str) -> int:
    from shield.ui.morning_checkin import run_checkin

    return run_checkin(db_path=db_path)


def _run_dashboard_screen(db_path: str | None = None) -> int:
    from shield.ui.dashboard import run_dashboard

    return run_dashboard(db_path=db_path)


def _run_settings_screen(db_path: str | None = None) -> int:
    from shield.ui.settings import run_settings

    return run_settings(db_path=db_path)


def _run_onboarding_screen(db_path: str | None = None) -> int:
    from shield.ui.onboarding import run_onboarding

    return run_onboarding(db_path=db_path)


def _print_demo_event(event: FrictionEvent) -> None:
    print("shield.demo_trigger=ok")
    print(f"session_id={event.session_id}")
    print(f"source={event.source.value}")
    print(f"score={event.score:.2f}")
    print(f"threshold={event.threshold_at_trigger:.2f}")
    print(f"reason={event.reason}")


def _run_demo_trigger(config: Config, db_path: str, show_overlay: bool = False) -> int:
    with EventStore(db_path) as store:
        orchestrator = Orchestrator(config=config, event_store=store)
        event = orchestrator.trigger_demo()

    _print_demo_event(event)
    if not show_overlay:
        return 0

    print("overlay=launched")
    # TODO: Pass saved alternative_actions once the overlay runner accepts custom cards.
    return _run_overlay_screen()


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.show_overlay and not args.demo_trigger:
        parser.error("--show-overlay requires --demo-trigger")
    if args.show_overlay and args.screen is not None:
        parser.error("--show-overlay cannot be used with --screen")

    if args.screen == "overlay":
        return _run_overlay_screen()

    config = Config()
    db_path = args.db_path if args.db_path is not None else config.db_path
    if args.screen == "dashboard":
        return _run_dashboard_screen(db_path)
    if args.screen == "settings":
        return _run_settings_screen(db_path)
    if args.screen == "onboarding":
        return _run_onboarding_screen(db_path)
    if args.screen == "checkin":
        return _run_checkin_screen(db_path)

    if args.demo_trigger:
        return _run_demo_trigger(config=config, db_path=db_path, show_overlay=args.show_overlay)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
