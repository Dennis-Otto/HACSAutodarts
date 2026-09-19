"""Exercise release eligibility, protected merges and recovery without GitHub writes."""

import importlib.util
from copy import deepcopy
from pathlib import Path
from unittest.mock import Mock, call

import pytest

SPEC = importlib.util.spec_from_file_location(
    "dependency_release",
    Path(__file__).parents[1] / ".github/scripts/dependency_release.py",
)
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)
REPOSITORY = "Dennis-Otto/HACSAutodarts"


def pull(number=2, author="dependabot[bot]", sha="dependency"):
    return {
        "number": number,
        "user": {"login": author},
        "merge_commit_sha": sha,
        "merged_at": "2026-09-19T19:11:38Z",
        "state": "closed",
        "base": {"ref": "main"},
        "head": {
            "ref": "dependabot/pip/python-major",
            "sha": "head",
            "repo": {"full_name": REPOSITORY},
        },
        "body": "Dependency update",
        "html_url": f"https://github.com/{REPOSITORY}/pull/{number}",
    }


def check(name, check_id=2, status="completed", conclusion="success", app=15368):
    return {
        "name": name,
        "id": check_id,
        "status": status,
        "conclusion": conclusion,
        "app": {"id": app},
    }


@pytest.mark.parametrize(
    ("previous", "expected"),
    [
        ("v0.4.2", "0.4.3"),
        ("1.9.99", "1.9.100"),
        ("0.0.0", "0.0.1"),
    ],
)
def test_next_patch_version(previous, expected):
    assert release.next_version(previous) == expected


@pytest.mark.parametrize(
    "version", ["v1.2", "v01.2.3", "v1.2.3-rc.1", "main", "1.2.3\n"]
)
def test_unsupported_versions_cannot_be_published_automatically(version):
    with pytest.raises(ValueError):
        release.next_version(version)


def test_only_merged_same_repository_dependabot_changes_are_eligible():
    valid = pull()
    variants = [deepcopy(valid) for _ in range(5)]
    variants[0]["merged_at"] = None
    variants[1]["merge_commit_sha"] = "already-released"
    variants[2]["user"]["login"] = "maintainer"
    variants[3]["head"]["repo"]["full_name"] = "outside/fork"
    variants[4]["base"]["ref"] = "development"
    assert release.dependency_prs([valid, *variants], {"dependency"}, REPOSITORY) == [
        valid
    ]


def test_deleted_fork_does_not_become_trusted():
    pr = pull()
    pr["head"]["repo"] = None
    assert release.dependency_prs([pr], {"dependency"}, REPOSITORY) == []


def test_fresh_successful_github_checks_are_required():
    previous = {name: check(name, 1) for name in release.CHECKS}
    current = [check(name) for name in release.CHECKS]
    assert release.checks_ready(current, previous)
    assert not release.checks_ready(current[:-1], previous)
    assert not release.checks_ready(list(previous.values()), previous)
    assert not release.checks_ready(
        [dict(c, app={"id": 999}) for c in current], previous
    )
    assert not release.checks_ready(
        [dict(c, status="in_progress") for c in current], previous
    )


@pytest.mark.parametrize(
    "conclusion", ["failure", "cancelled", "skipped", "neutral", "timed_out"]
)
def test_non_successful_checks_block_merge(conclusion):
    with pytest.raises(RuntimeError, match="Required check failed"):
        release.checks_ready(
            [check(name, conclusion=conclusion) for name in release.CHECKS], {}
        )


def test_latest_attempt_wins_over_old_success():
    checks = [check(name, 1) for name in release.CHECKS]
    checks.append(check("test", 2, conclusion="failure"))
    with pytest.raises(RuntimeError, match="test"):
        release.checks_ready(checks, {})


def test_candidate_may_only_change_manifest_version():
    base = {"domain": "autodarts", "version": "0.4.2", "requirements": []}
    candidate = dict(base, version="0.4.3")
    release.validate_version_only(base, candidate, "0.4.3", [release.MANIFEST])
    with pytest.raises(RuntimeError):
        release.validate_version_only(
            base,
            dict(candidate, requirements=["unexpected"]),
            "0.4.3",
            [release.MANIFEST],
        )
    with pytest.raises(RuntimeError):
        release.validate_version_only(
            base, candidate, "0.4.3", [release.MANIFEST, "extra.py"]
        )


def fake_repository():
    github = Mock(repository=REPOSITORY)
    published = {"tag_name": "v0.4.2", "draft": False, "prerelease": True}
    github.items.side_effect = lambda path, *args: (
        [published] if path.startswith("releases?") else [pull()]
    )
    github.api.side_effect = lambda path, **kwargs: (
        {"object": {"sha": "main"}}
        if path == "git/ref/heads/main"
        else [{"status": "ahead", "commits": [{"sha": "dependency"}]}]
    )
    github.manifest.return_value = ({"version": "0.4.2", "domain": "autodarts"}, "blob")
    return github


def test_no_initial_release_means_no_implicit_channel_choice():
    github = Mock()
    github.items.return_value = []
    release.run(github)
    github.api.assert_not_called()
    github.dispatch.assert_not_called()


def test_published_commit_does_not_create_duplicate_release():
    github = fake_repository()
    github.api.side_effect = lambda path, **kwargs: (
        {"object": {"sha": "main"}}
        if path == "git/ref/heads/main"
        else [{"status": "identical", "commits": []}]
    )
    release.run(github)
    github.dispatch.assert_not_called()
    github.manifest.assert_not_called()


def test_unrelated_changes_do_not_start_dependency_release():
    github = fake_repository()
    github.api.side_effect = lambda path, **kwargs: (
        {"object": {"sha": "main"}}
        if path == "git/ref/heads/main"
        else [{"status": "ahead", "commits": [{"sha": "unrelated"}]}]
    )
    release.run(github)
    github.dispatch.assert_not_called()
    github.manifest.assert_not_called()


def test_manual_version_is_never_overwritten():
    github = fake_repository()
    github.manifest.return_value = ({"version": "0.5.0"}, "blob")
    with pytest.raises(RuntimeError, match="manually changed"):
        release.run(github)
    github.dispatch.assert_not_called()


def test_failed_candidate_cannot_publish(monkeypatch):
    github = fake_repository()
    monkeypatch.setattr(release, "prepare_pr", Mock(return_value=pull()))
    monkeypatch.setattr(
        release, "validate_and_merge", Mock(side_effect=RuntimeError("failed checks"))
    )
    publisher = Mock()
    monkeypatch.setattr(release, "publish", publisher)
    with pytest.raises(RuntimeError, match="failed checks"):
        release.run(github)
    publisher.assert_not_called()


def test_release_inherits_channel_after_successful_protected_merge(monkeypatch):
    github = fake_repository()
    candidate = pull()
    prepare = Mock(return_value=candidate)
    merge = Mock(return_value="release-commit")
    publish = Mock()
    monkeypatch.setattr(release, "prepare_pr", prepare)
    monkeypatch.setattr(release, "validate_and_merge", merge)
    monkeypatch.setattr(release, "publish", publish)
    release.run(github)
    merge.assert_called_once_with(github, candidate, "0.4.3")
    publish.assert_called_once_with(github, "0.4.3", True, [pull()])


def test_publish_uses_workflow_and_checks_tag_manifest(monkeypatch):
    github = Mock()
    github.items.side_effect = lambda path: (
        [{"filename": "requirements-test.txt"}]
        if path.startswith("pulls/")
        else [
            {
                "tag_name": "v0.4.3",
                "draft": False,
                "prerelease": True,
                "html_url": "https://example.test/release",
            }
        ]
    )
    github.manifest.return_value = ({"version": "0.4.3"}, "blob")
    release.publish(github, "0.4.3", True, [pull()])
    workflow, ref, inputs = github.dispatch.call_args.args
    assert (workflow, ref) == ("release.yml", "main")
    assert inputs["version"] == "0.4.3"
    assert inputs["prerelease"] is True
    assert inputs["draft"] is False
    assert "Testabhängigkeiten" in inputs["introduction"]
    assert github.manifest.call_args == call("v0.4.3")


def test_closed_release_pr_is_not_silently_recreated():
    github = Mock(repository=REPOSITORY)
    pr = pull(author="github-actions[bot]")
    pr["head"]["ref"] = "automation/dependency-release-v0.4.3"
    pr["body"] = release.MARKER
    pr["merged_at"] = None
    with pytest.raises(RuntimeError, match="closed without merging"):
        release.prepare_pr(github, "0.4.3", "main", [pull()], [pr])
    github.api.assert_not_called()


def test_candidate_runs_real_checks_before_sha_guarded_merge(monkeypatch):
    github = Mock(repository=REPOSITORY)
    pr = pull(number=4, author="github-actions[bot]")
    pr.update(state="open", merged_at=None, body=release.MARKER)
    pr["head"]["ref"] = "automation/dependency-release-v0.4.3"
    base = {"domain": "autodarts", "version": "0.4.2"}
    github.manifest.side_effect = lambda ref: (
        (base if ref == "main" else dict(base, version="0.4.3")),
        "blob",
    )
    github.items.return_value = [{"filename": release.MANIFEST}]
    responses = {
        "pulls/4": pr,
        "git/ref/heads/main": {"object": {"sha": "main"}},
        "compare/main...head": {"status": "ahead"},
        "pulls/4/merge": {"merged": True, "sha": "merged"},
    }
    github.api.side_effect = lambda path, **kwargs: responses[path]
    monkeypatch.setattr(
        release,
        "get_checks",
        Mock(side_effect=[[], [check(name) for name in release.CHECKS]]),
    )
    assert release.validate_and_merge(github, pr, "0.4.3") == "merged"
    assert github.dispatch.call_count == len(release.WORKFLOWS)
    assert (
        call(
            "dependency-review.yml",
            pr["head"]["ref"],
            {"base_ref": "main", "head_ref": "head"},
        )
        in github.dispatch.call_args_list
    )
    assert github.api.call_args == call(
        "pulls/4/merge",
        method="PUT",
        data={
            "sha": "head",
            "merge_method": "squash",
            "commit_title": "chore(release): prepare v0.4.3 (#4)",
        },
    )


def test_retry_after_merged_version_pr_does_not_bump_again(monkeypatch):
    github = fake_repository()
    merged_pr = pull(number=4, author="github-actions[bot]", sha="version-commit")
    merged_pr["head"]["ref"] = "automation/dependency-release-v0.4.3"
    merged_pr["body"] = release.MARKER
    github.items.side_effect = lambda path, *args: (
        [{"tag_name": "v0.4.2", "draft": False, "prerelease": True}]
        if path.startswith("releases?")
        else [pull(), merged_pr]
    )
    github.api.side_effect = lambda path, **kwargs: (
        {"object": {"sha": "main"}}
        if path == "git/ref/heads/main"
        else [
            {
                "status": "ahead",
                "commits": [{"sha": "dependency"}, {"sha": "version-commit"}],
            }
        ]
    )
    github.manifest.return_value = ({"version": "0.4.3"}, "blob")
    monkeypatch.setattr(
        release, "validate_and_merge", Mock(return_value="version-commit")
    )
    publisher = Mock()
    monkeypatch.setattr(release, "publish", publisher)
    release.run(github)
    publisher.assert_called_once_with(github, "0.4.3", True, [pull()])
    assert all(
        kwargs.get("method") != "POST" for _, kwargs in github.api.call_args_list
    )
