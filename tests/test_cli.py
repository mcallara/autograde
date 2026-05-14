from __future__ import annotations

import subprocess
from pathlib import Path

from autograde.cli import evaluate_repository


def _run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)


def _create_remote_with_branches(
    temp_path: Path,
    *,
    with_main: bool = True,
    with_feature: bool = True,
    with_file1: bool = True,
) -> str:
    remote = temp_path / "remote.git"
    work = temp_path / "work"

    _run(["git", "init", "--bare", str(remote)], cwd=temp_path)
    _run(["git", "init", str(work)], cwd=temp_path)
    _run(["git", "config", "user.name", "Test User"], cwd=work)
    _run(["git", "config", "user.email", "test@example.com"], cwd=work)

    main_branch_name = "main" if with_main else "master"
    _run(["git", "checkout", "-b", main_branch_name], cwd=work)

    if with_file1:
        (work / "file1.txt").write_text("hello\n", encoding="utf-8")
    else:
        (work / "another.txt").write_text("hello\n", encoding="utf-8")

    _run(["git", "add", "."], cwd=work)
    _run(["git", "commit", "-m", "initial"], cwd=work)
    _run(["git", "remote", "add", "origin", str(remote)], cwd=work)
    _run(["git", "push", "-u", "origin", main_branch_name], cwd=work)

    if with_feature:
        _run(["git", "checkout", "-b", "feature"], cwd=work)
        (work / "feature.txt").write_text("feature\n", encoding="utf-8")
        _run(["git", "add", "."], cwd=work)
        _run(["git", "commit", "-m", "feature"], cwd=work)
        _run(["git", "push", "-u", "origin", "feature"], cwd=work)

    return str(remote)


def test_all_conditions_met(tmp_path: Path) -> None:
    repo_url = _create_remote_with_branches(tmp_path)
    result = evaluate_repository(repo_url)

    assert result["is_git_repository"] is True
    assert result["has_main_branch"] is True
    assert result["has_feature_branch"] is True
    assert result["main_has_file1_txt"] is True
    assert result["meets_all_conditions"] is True


def test_missing_feature_branch(tmp_path: Path) -> None:
    repo_url = _create_remote_with_branches(tmp_path, with_feature=False)
    result = evaluate_repository(repo_url)

    assert result["is_git_repository"] is True
    assert result["has_main_branch"] is True
    assert result["has_feature_branch"] is False
    assert result["main_has_file1_txt"] is True
    assert result["meets_all_conditions"] is False


def test_missing_main_branch(tmp_path: Path) -> None:
    repo_url = _create_remote_with_branches(tmp_path, with_main=False)
    result = evaluate_repository(repo_url)

    assert result["is_git_repository"] is True
    assert result["has_main_branch"] is False
    assert result["has_feature_branch"] is True
    assert result["main_has_file1_txt"] is False
    assert result["meets_all_conditions"] is False


def test_missing_file1_in_main(tmp_path: Path) -> None:
    repo_url = _create_remote_with_branches(tmp_path, with_file1=False)
    result = evaluate_repository(repo_url)

    assert result["is_git_repository"] is True
    assert result["has_main_branch"] is True
    assert result["has_feature_branch"] is True
    assert result["main_has_file1_txt"] is False
    assert result["meets_all_conditions"] is False


def test_invalid_repository_url() -> None:
    result = evaluate_repository("not-a-valid-url")

    assert result["is_valid_url"] is False
    assert result["is_git_repository"] is False
    assert result["meets_all_conditions"] is False
