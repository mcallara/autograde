from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse


def _looks_like_git_url(repo_url: str) -> bool:
    """Best-effort validation for common git URL styles."""
    parsed = urlparse(repo_url)
    if parsed.scheme in {"http", "https", "ssh", "git", "file"} and parsed.path:
        return True
    # Accept local filesystem paths (useful for local/bare repositories).
    if Path(repo_url).exists():
        return True
    # Support SCP-like syntax, e.g. git@github.com:owner/repo.git
    return "@" in repo_url and ":" in repo_url


def _run_git(*args: str, check: bool = False, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=check,
        capture_output=True,
        text=True,
    )


def _remote_has_branch(repo_url: str, branch_name: str) -> bool:
    result = _run_git("ls-remote", "--heads", repo_url, branch_name)
    return result.returncode == 0 and bool(result.stdout.strip())


def _main_contains_file(repo_url: str, file_name: str) -> bool:
    temp_dir = Path(tempfile.mkdtemp(prefix="autograde-main-check-"))
    try:
        clone_result = _run_git(
            "clone",
            "--depth",
            "1",
            "--single-branch",
            "--branch",
            "main",
            repo_url,
            str(temp_dir),
        )
        if clone_result.returncode != 0:
            return False
        return (temp_dir / file_name).is_file()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def evaluate_repository(repo_url: str) -> dict[str, object]:
    result: dict[str, object] = {
        "repository": repo_url,
        "is_valid_url": _looks_like_git_url(repo_url),
        "is_git_repository": False,
        "has_main_branch": False,
        "has_feature_branch": False,
        "main_has_file1_txt": False,
        "meets_all_conditions": False,
    }

    if not result["is_valid_url"]:
        return result

    git_probe = _run_git("ls-remote", repo_url)
    if git_probe.returncode != 0:
        return result

    result["is_git_repository"] = True
    result["has_main_branch"] = _remote_has_branch(repo_url, "main")
    result["has_feature_branch"] = _remote_has_branch(repo_url, "feature")

    if result["has_main_branch"]:
        result["main_has_file1_txt"] = _main_contains_file(repo_url, "file1.txt")

    result["meets_all_conditions"] = all(
        [
            result["is_git_repository"],
            result["has_main_branch"],
            result["has_feature_branch"],
            result["main_has_file1_txt"],
        ]
    )
    return result


def _format_human_output(checks: dict[str, object]) -> str:
    def marker(ok: bool) -> str:
        return "PASS" if ok else "FAIL"

    lines = [
        f"Repository: {checks['repository']}",
        f"- Valid URL: {marker(bool(checks['is_valid_url']))}",
        f"- Is git repository: {marker(bool(checks['is_git_repository']))}",
        f"- Has main branch: {marker(bool(checks['has_main_branch']))}",
        f"- Has feature branch: {marker(bool(checks['has_feature_branch']))}",
        f"- main contains file1.txt: {marker(bool(checks['main_has_file1_txt']))}",
        f"Overall: {marker(bool(checks['meets_all_conditions']))}",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate repository requirements for autograding.")
    parser.add_argument("repository_url", help="Repository URL to validate")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    checks = evaluate_repository(args.repository_url)
    if args.json:
        print(json.dumps(checks, indent=2))
    else:
        print(_format_human_output(checks))

    return 0 if checks["meets_all_conditions"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
