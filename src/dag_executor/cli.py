# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

import argparse
import json
import sys

from dag_executor.executor import DagExecutorRunner


def app() -> None:
    parser = argparse.ArgumentParser(
        prog="dag-executor",
        description="Execute a YAML DAG workflow",
    )
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="Run a workflow YAML")
    run_p.add_argument("yaml_path", help="Path to workflow YAML")
    run_p.add_argument("--goal", default="", help="Goal text (D1)")
    run_p.add_argument("--artifacts-dir", default=None)
    run_p.add_argument("--working-dir", default=".")

    args = parser.parse_args()

    if args.command == "run":
        runner = DagExecutorRunner(
            artifacts_dir=args.artifacts_dir,
            working_directory=args.working_dir,
        )
        result = runner.run_from_yaml(args.yaml_path, goal_text=args.goal)
        sys.stdout.write(json.dumps(result, indent=2) + "\n")
        sys.exit(0 if result["status"] == "succeeded" else 1)
    else:
        parser.print_help()
        sys.exit(1)
