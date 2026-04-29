from __future__ import annotations

import argparse
from collections.abc import Sequence
from datetime import datetime, timezone
import os
from pathlib import Path
import sys
import uuid

from shield.core import Config, FrictionEvent, Orchestrator, TriggerSource
from shield.db import EventStore
from shield.trigger import (
    ALLOW_DOMAINS_SETTING_KEY,
    DEFAULT_RISK_DOMAINS,
    RISK_DOMAINS_SETTING_KEY,
    extract_domain,
    load_allow_domains,
    load_risk_domains,
    match_allowlist,
    match_trigger,
    normalize_candidate,
    parse_allow_domains,
    parse_risk_domains,
)

APP_DATA_DIR_ENV_VAR = "NOFAPSHIELD_APP_DATA_DIR"


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
        help="launch the pause overlay after --demo-trigger or --trigger-url records its event",
    )
    parser.add_argument(
        "--trigger-url",
        default=None,
        help="classify a supplied URL/domain against the active local risk list",
    )
    parser.add_argument(
        "--list-risk-domains",
        action="store_true",
        help="print the active local risk domains used by --trigger-url",
    )
    parser.add_argument(
        "--set-risk-domains",
        default=None,
        help="store a comma- or newline-separated local risk domain list",
    )
    parser.add_argument(
        "--list-allow-domains",
        action="store_true",
        help="print the local domains that override --trigger-url risk matches",
    )
    parser.add_argument(
        "--set-allow-domains",
        default=None,
        help="store a comma- or newline-separated local allow domain list",
    )
    return parser


def _default_app_data_db_path() -> Path:
    base_override = os.environ.get(APP_DATA_DIR_ENV_VAR)
    if base_override:
        base_dir = Path(base_override)
    elif sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            base_dir = Path(local_app_data) / "NoFapShield"
        else:
            base_dir = Path.home() / "AppData" / "Local" / "NoFapShield"
    else:
        base_dir = Path.home() / ".local" / "share" / "nofapshield"

    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir / "shield.db"


def _resolve_db_path(cli_db_path: str | None, config: Config) -> str:
    if cli_db_path is not None:
        return cli_db_path
    if config.db_path != ":memory:":
        return config.db_path
    return str(_default_app_data_db_path())


def _run_overlay_screen(db_path: str | None = None) -> int:
    from shield.ui.blur_overlay import run_overlay

    return run_overlay(alternative_actions=_read_saved_alternative_actions(db_path))


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


def _read_saved_alternative_actions(db_path: str | None) -> list[str] | None:
    if db_path is None:
        return None
    try:
        with EventStore(db_path) as store:
            value = store.get_setting("alternative_actions", None)
    except Exception:
        return None

    from shield.ui.blur_overlay import normalize_alternative_actions

    actions = normalize_alternative_actions(value, fallback=())
    return actions or None


def _run_default_screen(db_path: str) -> int:
    if _is_onboarding_completed(db_path):
        return _run_dashboard_screen(db_path)
    return _run_onboarding_screen(db_path)


def _is_onboarding_completed(db_path: str) -> bool:
    try:
        with EventStore(db_path) as store:
            value = store.get_setting("onboarding_completed", False)
    except Exception:
        return False
    return _is_completed_setting(value)


def _is_completed_setting(value: object) -> bool:
    if value is True:
        return True
    if isinstance(value, int) and not isinstance(value, bool):
        return value == 1
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1"}
    return False


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
    return _run_overlay_screen(db_path)


def _print_trigger_invalid(candidate: str) -> None:
    print("shield.trigger_url=ok")
    print("trigger=invalid")
    print(f"candidate={candidate}")


def _print_trigger_no_match(candidate_domain: str) -> None:
    print("shield.trigger_url=ok")
    print("trigger=no_match")
    print(f"candidate={candidate_domain}")


def _print_trigger_match(event: FrictionEvent, event_id: int, match) -> None:
    print("shield.trigger_url=ok")
    print("trigger=matched")
    print(f"candidate={match.candidate_domain}")
    print(f"matched_domain={match.matched_domain}")
    print(f"event_id={event_id}")
    print(f"session_id={event.session_id}")
    print(f"source={event.source.value}")
    print(f"reason={event.reason}")


def _print_trigger_allowlisted(match) -> None:
    print("shield.trigger_url=ok")
    print("trigger=allowlisted")
    print(f"candidate={match.candidate_domain}")
    print(f"allowed_domain={match.matched_domain}")


def _load_risk_domains(db_path: str) -> tuple[str, ...]:
    try:
        with EventStore(db_path) as store:
            return load_risk_domains(store)
    except Exception:
        return DEFAULT_RISK_DOMAINS


def _load_allow_domains(db_path: str) -> tuple[str, ...]:
    try:
        with EventStore(db_path) as store:
            return load_allow_domains(store)
    except Exception:
        return ()


def _print_risk_domains(domains: Sequence[str]) -> None:
    print("shield.risk_domains=ok")
    print(f"domains={','.join(domains)}")
    print(f"count={len(domains)}")


def _run_list_risk_domains(db_path: str) -> int:
    _print_risk_domains(_load_risk_domains(db_path))
    return 0


def _print_allow_domains(domains: Sequence[str]) -> None:
    print("shield.allow_domains=ok")
    print(f"domains={','.join(domains)}")
    print(f"count={len(domains)}")


def _run_list_allow_domains(db_path: str) -> int:
    _print_allow_domains(_load_allow_domains(db_path))
    return 0


def _run_set_allow_domains(db_path: str, value: str) -> int:
    domains = parse_allow_domains(value)
    if not domains:
        print("shield.allow_domains=ok")
        print("action=set")
        print("status=no_valid_domains")
        return 0

    with EventStore(db_path) as store:
        store.set_setting(ALLOW_DOMAINS_SETTING_KEY, list(domains))

    print("shield.allow_domains=ok")
    print("action=set")
    print("status=saved")
    print(f"domains={','.join(domains)}")
    print(f"count={len(domains)}")
    return 0


def _run_set_risk_domains(db_path: str, value: str) -> int:
    domains = parse_risk_domains(value, fallback=())
    if not domains:
        print("shield.risk_domains=ok")
        print("action=set")
        print("status=no_valid_domains")
        return 0

    with EventStore(db_path) as store:
        store.set_setting(RISK_DOMAINS_SETTING_KEY, list(domains))

    print("shield.risk_domains=ok")
    print("action=set")
    print("status=saved")
    print(f"domains={','.join(domains)}")
    print(f"count={len(domains)}")
    return 0


def _run_url_trigger(
    config: Config,
    db_path: str,
    candidate: str,
    show_overlay: bool = False,
) -> int:
    normalized_candidate = normalize_candidate(candidate) or ""
    candidate_domain = extract_domain(candidate)
    if candidate_domain is None:
        _print_trigger_invalid(normalized_candidate)
        return 0

    allow_match = match_allowlist(candidate, _load_allow_domains(db_path))
    if allow_match is not None:
        _print_trigger_allowlisted(allow_match)
        return 0

    match = match_trigger(candidate, _load_risk_domains(db_path))
    if match is None:
        _print_trigger_no_match(candidate_domain)
        return 0

    event = FrictionEvent(
        source=TriggerSource.MANUAL_URL,
        triggered_at=datetime.now(timezone.utc),
        session_id=str(uuid.uuid4()),
        score=config.demo_score,
        threshold_at_trigger=config.trigger_threshold,
        reason=f"local URL/domain trigger matched {match.matched_domain}",
    )
    with EventStore(db_path) as store:
        event_id = store.record_event(event)

    _print_trigger_match(event, event_id, match)
    if not show_overlay:
        return 0

    print("overlay=launched")
    return _run_overlay_screen(db_path)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    has_risk_domain_command = args.list_risk_domains or args.set_risk_domains is not None
    has_allow_domain_command = args.list_allow_domains or args.set_allow_domains is not None
    has_domain_command = has_risk_domain_command or has_allow_domain_command
    if args.list_risk_domains and args.set_risk_domains is not None:
        parser.error("--list-risk-domains cannot be used with --set-risk-domains")
    if args.list_allow_domains and args.set_allow_domains is not None:
        parser.error("--list-allow-domains cannot be used with --set-allow-domains")
    if has_risk_domain_command and has_allow_domain_command:
        parser.error(
            "--list-risk-domains/--set-risk-domains cannot be combined with "
            "--list-allow-domains/--set-allow-domains"
        )
    if has_domain_command and (
        args.screen is not None
        or args.demo_trigger
        or args.trigger_url is not None
        or args.show_overlay
    ):
        parser.error(
            "--list-risk-domains/--set-risk-domains/--list-allow-domains/"
            "--set-allow-domains cannot be combined with --screen, "
            "--demo-trigger, --trigger-url, or --show-overlay"
        )
    if args.demo_trigger and args.trigger_url is not None:
        parser.error("--demo-trigger cannot be used with --trigger-url")
    if args.trigger_url is not None and args.screen is not None:
        parser.error("--trigger-url cannot be used with --screen")
    if args.show_overlay and not (args.demo_trigger or args.trigger_url is not None):
        parser.error("--show-overlay requires --demo-trigger or --trigger-url")
    if args.show_overlay and args.screen is not None:
        parser.error("--show-overlay cannot be used with --screen")

    config = Config()
    db_path = _resolve_db_path(args.db_path, config)
    if args.list_risk_domains:
        return _run_list_risk_domains(db_path)
    if args.set_risk_domains is not None:
        return _run_set_risk_domains(db_path, args.set_risk_domains)
    if args.list_allow_domains:
        return _run_list_allow_domains(db_path)
    if args.set_allow_domains is not None:
        return _run_set_allow_domains(db_path, args.set_allow_domains)

    if args.screen == "overlay":
        return _run_overlay_screen(db_path)
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
    if args.trigger_url is not None:
        return _run_url_trigger(
            config=config,
            db_path=db_path,
            candidate=args.trigger_url,
            show_overlay=args.show_overlay,
        )

    return _run_default_screen(db_path)


if __name__ == "__main__":
    raise SystemExit(main())
