"""Bounded capsule client CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from servicefabric_contracts import CapsuleHostRequest


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="servicefabric-capsule")
    actions = root.add_subparsers(dest="action", required=True)
    open_session = actions.add_parser("open")
    open_session.add_argument("--request-file", required=True)
    dispatch = actions.add_parser("dispatch")
    dispatch.add_argument("--request-file", required=True)
    dispatch.add_argument("--method", default="GET")
    dispatch.add_argument("--path", default="/")
    dispatch.add_argument("--head-only", action="store_true")
    return root


def execute(client, argv: list[str]) -> str:
    args = parser().parse_args(argv)
    request = CapsuleHostRequest.model_validate_json(Path(args.request_file).read_text(encoding="utf-8"))
    session = client.open_session(request)
    if args.action == "open":
        value = session.result.model_dump(mode="json", by_alias=True)
    else:
        response = client.dispatch(session, args.method, args.path, head_only=args.head_only)
        value = {"status": response.status, "headers": response.headers, "body": response.body.decode("utf-8", errors="replace")}
        client.close_session(session)
    return json.dumps(value, sort_keys=True)

