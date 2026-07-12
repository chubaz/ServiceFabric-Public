"""Bounded application and artifact CLI projection."""

from __future__ import annotations

import argparse
import json


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="servicefabric")
    resources = root.add_subparsers(dest="resource", required=True)
    app = resources.add_parser("app")
    app_actions = app.add_subparsers(dest="action", required=True)
    app_actions.add_parser("list")
    describe = app_actions.add_parser("describe")
    describe.add_argument("application_id")
    build = app_actions.add_parser("build")
    build.add_argument("application_id")
    build.add_argument("--revision", required=True)
    artifact = resources.add_parser("artifact")
    artifact_actions = artifact.add_subparsers(dest="action", required=True)
    artifact_describe = artifact_actions.add_parser("describe")
    artifact_describe.add_argument("digest")
    artifact_verify = artifact_actions.add_parser("verify")
    artifact_verify.add_argument("digest")
    return root


def execute(client, argv: list[str]) -> str:
    args = parser().parse_args(argv)
    if args.resource == "app" and args.action == "list":
        value = {"applications": list(client.list_applications())}
    elif args.resource == "app" and args.action == "describe":
        value = client.describe_application(args.application_id).model_dump(mode="json", by_alias=True)
    elif args.resource == "app" and args.action == "build":
        value = client.build_application(args.application_id, args.revision).model_dump(mode="json", by_alias=True)
    elif args.action == "describe":
        value = client.get_artifact_manifest(args.digest).model_dump(mode="json", by_alias=True)
    else:
        verification = client.verify_artifact(args.digest)
        value = {
            "artifact_digest": verification.artifact_digest,
            "valid": verification.valid,
            "verified_files": list(verification.verified_files),
            "errors": list(verification.errors),
        }
    return json.dumps(value, sort_keys=True)
