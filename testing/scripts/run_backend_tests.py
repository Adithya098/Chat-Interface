import argparse
import subprocess
import sys
from pathlib import Path


def _collect_test_ids(python_exe: str, repo_root: Path, targets: list[str], passthrough: list[str]) -> list[str]:
    collect_cmd = [
        python_exe,
        "-m",
        "pytest",
        "--collect-only",
        "-q",
        "--override-ini",
        "addopts=",
    ]
    collect_cmd.extend(targets)
    collect_cmd.extend(passthrough)
    proc = subprocess.run(
        collect_cmd,
        cwd=str(repo_root),
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return []
    return [line.strip() for line in proc.stdout.splitlines() if "::" in line]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run backend tests from testing/backend.")
    parser.add_argument("--api", action="store_true", help="Run API tests only.")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only.")
    args, passthrough = parser.parse_known_args()

    repo_root = Path(__file__).resolve().parents[2]
    backend_tests = repo_root / "testing" / "backend"

    test_targets: list[str] = []
    if args.api and not args.unit:
        test_targets.append(str(backend_tests / "api"))
    elif args.unit and not args.api:
        test_targets.append(str(backend_tests / "unit"))
    else:
        test_targets.append(str(backend_tests))

    passed_test_ids = _collect_test_ids(sys.executable, repo_root, test_targets, passthrough)

    cmd = [sys.executable, "-m", "pytest"]
    cmd.extend(test_targets)
    cmd.extend(passthrough)
    result = subprocess.run(cmd, cwd=str(repo_root), check=False).returncode

    if result == 0 and passed_test_ids:
        print("\nPassed tests:")
        for test_id in passed_test_ids:
            print(f"- {test_id}")

    return result


if __name__ == "__main__":
    raise SystemExit(main())
