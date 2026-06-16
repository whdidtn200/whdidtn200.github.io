#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys


def applescript_literal(value: str) -> str:
    return json.dumps(value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--to", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--body", required=True)
    parser.add_argument("--account-address")
    parser.add_argument("--timeout-seconds", type=int, default=30)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def build_script(args: argparse.Namespace) -> str:
    script = [
        'tell application "Mail"',
        f"set targetRecipient to {applescript_literal(args.to)}",
        f"set messageSubject to {applescript_literal(args.subject)}",
        f"set messageBody to {applescript_literal(args.body)}",
        "set newMessage to make new outgoing message with properties {subject:messageSubject, content:messageBody & return & return, visible:false}",
        "tell newMessage",
    ]
    if args.account_address:
        script.extend(
            [
                f"set preferredAddress to {applescript_literal(args.account_address)}",
                "try",
                "set sender to preferredAddress",
                "end try",
            ]
        )
    script.extend(
        [
            "make new to recipient at end of to recipients with properties {address:targetRecipient}",
            "send",
            "end tell",
            "end tell",
        ]
    )
    return "\n".join(script)


def main() -> int:
    args = parse_args()
    script = build_script(args)
    wrapped_script = "\n".join(
        [
            f"with timeout of {args.timeout_seconds} seconds",
            script,
            "end timeout",
        ]
    )
    if args.dry_run:
        print(wrapped_script)
        return 0

    subprocess.run(
        ["osascript", "-e", wrapped_script],
        check=True,
        timeout=args.timeout_seconds + 5,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
