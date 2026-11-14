"""CLI for mem20portalz."""

from __future__ import annotations

import argparse
import json
import os
import sys
from getpass import getpass
from pathlib import Path

from .app import main_run
from .auth import hash_password
from .config import (
    ConfigError,
    default_config_path,
    get_user,
    list_users,
    load_config,
    new_config,
    save_config,
    upsert_user,
)


def _eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def cmd_init_config(args) -> int:
    path = args.config or default_config_path()
    p = Path(path).expanduser()
    if p.exists() and not args.force:
        _eprint(f"config already exists: {p} (use --force to overwrite)")
        return 1
    cfg = new_config()
    saved = save_config(cfg, path)
    print(f"initialized portal config: {saved}")
    if not cfg.get("session_secret"):
        _eprint("warning: session_secret is empty; login will be unavailable")
    return 0


def _resolve_password(args) -> str:
    if getattr(args, "password", None):
        return args.password
    if getattr(args, "password_stdin", False):
        pw = sys.stdin.read().rstrip("\n")
        if not pw:
            raise ConfigError("password from stdin is empty")
        return pw
    pw1 = getpass("Password: ")
    pw2 = getpass("Confirm password: ")
    if pw1 != pw2:
        raise ConfigError("passwords do not match")
    if not pw1:
        raise ConfigError("password must not be empty")
    return pw1


def cmd_add_user(args) -> int:
    path = args.config or default_config_path()
    try:
        cfg = load_config(path)
    except ConfigError as e:
        _eprint(f"error: {e}")
        return 2
    try:
        pw = _resolve_password(args)
        upsert_user(
            cfg,
            args.username,
            password_hash=hash_password(pw),
            store_path=args.store,
            display_name=args.display_name or args.username,
            enabled=True,
        )
        save_config(cfg, path)
    except ConfigError as e:
        _eprint(f"error: {e}")
        return 2
    print(f"user added/updated: {args.username}")
    return 0


def cmd_set_password(args) -> int:
    path = args.config or default_config_path()
    try:
        cfg = load_config(path)
        if not get_user(cfg, args.username):
            raise ConfigError(f"user not found: {args.username}")
        pw = _resolve_password(args)
        upsert_user(cfg, args.username, password_hash=hash_password(pw))
        save_config(cfg, path)
    except ConfigError as e:
        _eprint(f"error: {e}")
        return 2
    print(f"password updated: {args.username}")
    return 0


def _cmd_set_enabled(args, enabled: bool) -> int:
    path = args.config or default_config_path()
    try:
        cfg = load_config(path)
        if not get_user(cfg, args.username):
            raise ConfigError(f"user not found: {args.username}")
        upsert_user(cfg, args.username, enabled=enabled)
        save_config(cfg, path)
    except ConfigError as e:
        _eprint(f"error: {e}")
        return 2
    print(f"user {'enabled' if enabled else 'disabled'}: {args.username}")
    return 0


def cmd_enable_user(args) -> int:
    return _cmd_set_enabled(args, True)


def cmd_disable_user(args) -> int:
    return _cmd_set_enabled(args, False)


def cmd_list_users(args) -> int:
    path = args.config or default_config_path()
    try:
        cfg = load_config(path)
        users = list_users(cfg)
    except ConfigError as e:
        _eprint(f"error: {e}")
        return 2
    if args.json:
        out = [
            {
                "username": u.username,
                "display_name": u.display_name,
                "store_path": u.resolved_store_path,
                "enabled": u.enabled,
                "created_at": u.created_at,
            }
            for u in users
        ]
        print(json.dumps(out, indent=2))
        return 0
    if not users:
        print("no users configured")
        return 0
    for u in users:
        state = "enabled" if u.enabled else "disabled"
        print(f"{u.username}\t{state}\t{u.display_name}\t{u.resolved_store_path}")
    return 0


def cmd_check(args) -> int:
    path = args.config or default_config_path()
    try:
        cfg = load_config(path)
    except ConfigError as e:
        _eprint(f"error: {e}")
        return 2
    ok = True
    if not cfg.get("session_secret"):
        _eprint("warning: session_secret is not configured (login will fail)")
        ok = False
    users = list_users(cfg)
    if not users:
        _eprint("warning: no users configured")
    for u in users:
        if args.username and u.username != args.username:
            continue
        sp = Path(u.resolved_store_path)
        if not sp.exists():
            _eprint(f"warning: store path does not exist for {u.username}: {sp}")
            ok = False
    print(f"config: {Path(path).expanduser()}")
    print(f"users: {len(users)}")
    print(f"session_secret: {'set' if cfg.get('session_secret') else 'missing'}")
    return 0 if ok else 1


def cmd_serve(args) -> int:
    path = args.config or default_config_path()
    try:
        # validate early for clearer failure
        load_config(path)
    except ConfigError as e:
        _eprint(f"error: {e}")
        return 2
    host = args.host
    port = int(args.port)
    print(f"mem20 portal serving on http://{host}:{port} (config: {Path(path).expanduser()})", flush=True)
    try:
        main_run(path, host, port)
    except KeyboardInterrupt:
        pass
    except OSError as e:
        _eprint(f"error: cannot bind {host}:{port}: {e}")
        return 2
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mem20portalz", description="Customer-facing mem20 memories portal")
    config_help = f"config file path (default: $MEM20_PORTAL_CONFIG or {default_config_path()})"
    p.add_argument("--config", default=None, help=config_help)
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_config_arg(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--config", dest="config", default=argparse.SUPPRESS, help=config_help)

    s = sub.add_parser("init-config", help="create a new portal config with a generated session secret")
    add_config_arg(s)
    s.add_argument("--force", action="store_true", help="overwrite existing config")
    s.set_defaults(func=cmd_init_config)

    s = sub.add_parser("add-user", help="add or update a user account")
    add_config_arg(s)
    s.add_argument("--username", required=True)
    s.add_argument("--store", required=True, help="absolute path to the user's mem20 store")
    s.add_argument("--display-name", default=None)
    s.add_argument("--password", default=None, help="password (prefer prompt or --password-stdin)")
    s.add_argument("--password-stdin", action="store_true", help="read password from stdin")
    s.set_defaults(func=cmd_add_user)

    s = sub.add_parser("set-password", help="set a user's password")
    add_config_arg(s)
    s.add_argument("--username", required=True)
    s.add_argument("--password", default=None)
    s.add_argument("--password-stdin", action="store_true")
    s.set_defaults(func=cmd_set_password)

    s = sub.add_parser("enable-user", help="enable a user account")
    add_config_arg(s)
    s.add_argument("--username", required=True)
    s.set_defaults(func=cmd_enable_user)

    s = sub.add_parser("disable-user", help="disable a user account")
    add_config_arg(s)
    s.add_argument("--username", required=True)
    s.set_defaults(func=cmd_disable_user)

    s = sub.add_parser("list-users", help="list configured users")
    add_config_arg(s)
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_list_users)

    s = sub.add_parser("check", help="validate config and store paths")
    add_config_arg(s)
    s.add_argument("--username", default=None)
    s.set_defaults(func=cmd_check)

    s = sub.add_parser("serve", help="run the portal web server")
    add_config_arg(s)
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8095)
    s.set_defaults(func=cmd_serve)

    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args) or 0)
    except ConfigError as e:
        _eprint(f"error: {e}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
