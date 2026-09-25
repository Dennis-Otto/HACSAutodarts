"""Exercise release eligibility, protected merges and recovery without GitHub writes."""

import importlib.util
import re
import subprocess
from copy import deepcopy
from pathlib import Path
from unittest.mock import Mock, call

import pytest
import yaml

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


@pytest.mark.parametrize(
    "filename,test_only",
    [
        ("requirements-test.txt", True),
        ("tests/e2e/compose.yaml", True),
        ("custom_components/autodarts/manifest.json", False),
    ],
)
def test_publish_uses_workflow_and_checks_tag_manifest(filename, test_only):
    github = Mock()
    github.items.side_effect = lambda path: (
        [{"filename": filename}]
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
    assert ("Testabhängigkeiten" in inputs["introduction"]) is test_only
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
    pr.update(
        state="open", merged_at=None, body=release.MARKER, mergeable_state="clean"
    )
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
    start = Mock(return_value={42: 1})
    ready = Mock(return_value=True)
    monkeypatch.setattr(release, "start_pr_checks", start)
    monkeypatch.setattr(release, "pr_checks_ready", ready)
    assert release.validate_and_merge(github, pr, "0.4.3") == "merged"
    start.assert_called_once_with(github, 4, "head")
    ready.assert_called_once_with(github, {42: 1})
    github.dispatch.assert_not_called()
    assert github.api.call_args == call(
        "pulls/4/merge",
        method="PUT",
        data={
            "sha": "head",
            "merge_method": "squash",
            "commit_title": "chore(release): prepare v0.4.3 (#4)",
        },
        release_write=True,
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


def workflow_runs():
    return [
        {
            "id": index,
            "path": f".github/workflows/{workflow}",
            "event": "pull_request",
            "head_sha": "head",
            "pull_requests": [{"number": 4}],
            "conclusion": "action_required",
            "status": "completed",
            "run_attempt": 1,
            "check_suite_id": index,
        }
        for index, workflow in enumerate(release.WORKFLOWS, start=1)
    ]


def test_dispatch_checks_cannot_replace_pr_associated_checks():
    runs = workflow_runs()
    assert release.pr_workflow_runs(runs, 4, "head")
    assert (
        release.pr_workflow_runs(
            [dict(r, event="workflow_dispatch") for r in runs], 4, "head"
        )
        is None
    )
    assert release.pr_workflow_runs(runs, 99, "head") is None
    assert release.pr_workflow_runs(runs, 4, "other-head") is None
    assert release.pr_workflow_runs(runs[:-1], 4, "head") is None


def test_gated_pr_runs_fail_without_approving_or_substituting_checks():
    github = Mock()
    runs = workflow_runs()
    github.items.return_value = runs
    github.api.return_value = runs[0]
    with pytest.raises(RuntimeError, match="PR checks require approval"):
        release.start_pr_checks(github, 4, "head")
    assert all(
        kwargs.get("method") != "POST" for _, kwargs in github.api.call_args_list
    )
    github.dispatch.assert_not_called()


def test_app_triggered_pr_checks_run_without_workflow_approval():
    github = Mock()
    runs = [dict(r, conclusion=None, status="in_progress") for r in workflow_runs()]
    github.items.return_value = runs
    github.api.side_effect = lambda path, **kwargs: runs[
        int(path.rsplit("/", 1)[1]) - 1
    ]
    assert release.start_pr_checks(github, 4, "head") == {r["id"]: 1 for r in runs}
    assert all(
        kwargs.get("method") != "POST" for _, kwargs in github.api.call_args_list
    )
    github.dispatch.assert_not_called()


@pytest.fixture
def registration_clock(monkeypatch):
    clock = Mock(elapsed=0)
    clock.monotonic.side_effect = lambda: clock.elapsed

    def advance(seconds):
        clock.elapsed += seconds

    clock.sleep.side_effect = advance
    monkeypatch.setattr(release, "time", clock)
    return clock


@pytest.mark.parametrize("registration_delay", [215, 570, 1725])
def test_delayed_pr_registration_waits_for_all_real_runs(
    registration_clock, registration_delay
):
    # GitHub registered the v0.4.4 PR workflows 215 seconds after PR creation.
    # Earlier push checks and partial PR registration must not satisfy the gate.
    github = Mock()
    runs = [dict(r, conclusion=None, status="queued") for r in workflow_runs()]
    noise = [dict(r, event="push") for r in runs]
    noise += [dict(r, head_sha="previous-head") for r in runs]
    noise += [dict(r, pull_requests=[{"number": 99}]) for r in runs]
    github.items.side_effect = lambda *args: noise + (
        runs if registration_clock.elapsed >= registration_delay else runs[:-1]
    )
    github.api.side_effect = lambda path, **kwargs: runs[
        int(path.rsplit("/", 1)[1]) - 1
    ]

    assert release.start_pr_checks(github, 4, "head") == {r["id"]: 1 for r in runs}
    assert registration_delay <= registration_clock.elapsed < registration_delay + 15
    assert all(
        kwargs.get("method") != "POST" for _, kwargs in github.api.call_args_list
    )
    github.dispatch.assert_not_called()


def test_missing_pr_workflow_still_times_out_without_merging(registration_clock):
    github = Mock()
    github.items.return_value = workflow_runs()[:-1]

    with pytest.raises(TimeoutError, match="PR workflow registration"):
        release.start_pr_checks(github, 4, "head")

    assert registration_clock.elapsed == 1800
    github.api.assert_not_called()
    github.dispatch.assert_not_called()


def test_pr_check_wait_does_not_use_branch_dispatch_success():
    github = Mock()
    github.api.return_value = dict(workflow_runs()[0], conclusion="action_required")
    assert not release.pr_checks_ready(github, {1: 1})
    github.items.assert_not_called()
    github.api.return_value = dict(workflow_runs()[0], conclusion="success")
    github.items.return_value = [check(name) for name in release.CHECKS]
    assert release.pr_checks_ready(github, {1: 1})
    github.items.assert_called_once_with(
        "check-suites/1/check-runs?per_page=100&filter=latest", "check_runs"
    )


def test_only_release_writes_use_app_token(monkeypatch):
    monkeypatch.setenv("GH_TOKEN", "workflow-test-token")
    monkeypatch.setenv("GH_RELEASE_TOKEN", "release-test-token")
    execute = Mock(return_value=subprocess.CompletedProcess([], 0, stdout="{}"))
    monkeypatch.setattr(release.subprocess, "run", execute)
    github = release.GitHub(REPOSITORY)
    github.api("git/ref/heads/main")
    assert execute.call_args.kwargs["env"]["GH_TOKEN"] == "workflow-test-token"
    assert "GH_RELEASE_TOKEN" not in execute.call_args.kwargs["env"]
    github.api("pulls", method="POST", release_write=True)
    assert execute.call_args.kwargs["env"]["GH_TOKEN"] == "release-test-token"
    assert "release-test-token" not in execute.call_args.args[0]


def test_missing_app_token_stops_before_release_write(monkeypatch):
    monkeypatch.delenv("GH_RELEASE_TOKEN", raising=False)
    execute = Mock()
    monkeypatch.setattr(release.subprocess, "run", execute)
    with pytest.raises(RuntimeError, match="Configure the release GitHub App"):
        release.GitHub(REPOSITORY).api("pulls", method="POST", release_write=True)
    execute.assert_not_called()


def test_only_configured_app_or_legacy_bot_can_own_release_pr(monkeypatch):
    monkeypatch.setenv("GH_RELEASE_APP_SLUG", "renamed-release-app")
    pr = pull(author="renamed-release-app[bot]")
    pr["body"] = release.MARKER
    branch = pr["head"]["ref"] = "automation/dependency-release-v0.4.3"
    assert release.owned_release_pr(pr, branch, REPOSITORY)
    pr["user"]["login"] = "untrusted-app[bot]"
    assert not release.owned_release_pr(pr, branch, REPOSITORY)
    pr["user"]["login"] = "github-actions[bot]"
    assert release.owned_release_pr(pr, branch, REPOSITORY)


@pytest.mark.parametrize("state", ["blocked", "unstable", "unknown", None])
def test_parallel_checks_and_pending_protection_calculation_delay_merge(state):
    github = Mock()
    github.api.side_effect = [
        {"head": {"sha": "candidate"}, "state": "open", "mergeable_state": state},
        {"object": {"sha": "base"}},
    ]
    assert not release.merge_ready(github, 4, "candidate", "base")


def test_new_main_exits_wait_so_candidate_is_revalidated():
    github = Mock()
    github.api.side_effect = [
        {"head": {"sha": "candidate"}, "state": "open", "mergeable_state": "behind"},
        {"object": {"sha": "new-base"}},
    ]
    assert release.merge_ready(github, 4, "candidate", "base")


def test_candidate_changes_during_merge_wait_are_rejected():
    github = Mock()
    github.api.return_value = {"head": {"sha": "unexpected"}, "state": "open"}
    with pytest.raises(RuntimeError, match="candidate changed"):
        release.merge_ready(github, 4, "candidate", "base")


def test_ci_runs_cannot_cancel_other_commits_or_release_callers():
    workflows = Path(__file__).parents[1] / ".github/workflows"
    release_name = yaml.safe_load((workflows / "release.yml").read_text())["name"]
    for filename in release.WORKFLOWS:
        workflow = yaml.safe_load((workflows / filename).read_text())
        policies = [workflow.get("concurrency")] + [
            job.get("concurrency") for job in workflow["jobs"].values()
        ]
        for policy in filter(None, policies):
            expression = policy["group"] if isinstance(policy, dict) else policy
            groups = []
            # Consecutive commits and a release reusing CI on the same branch
            # must never compete in GitHub's cancellation/limited pending queue.
            for run_id, caller in enumerate(
                [workflow["name"], workflow["name"], release_name]
            ):
                context = {
                    "github.workflow": caller,
                    "github.ref": "refs/heads/main",
                    "github.run_id": str(run_id),
                }
                groups.append(
                    re.sub(
                        r"\$\{\{\s*(.*?)\s*\}\}",
                        lambda match: context[match[1]],
                        expression,
                    )
                )
            assert len(set(groups)) == len(groups), (
                f"{filename}: overlapping CI runs share {groups}"
            )


def main_runs(sha="release-commit"):
    return [
        dict(run, event="push", head_branch="main", head_sha=sha, conclusion="success")
        for run in workflow_runs()
        if not run["path"].endswith("dependency-review.yml")
    ]


def main_check_repository(runs=None):
    github = Mock()
    github.items.side_effect = lambda path, key: (
        (main_runs() if runs is None else runs)
        if path.startswith("actions/runs?")
        else [check(name) for name in release.CHECKS]
    )
    return github


def test_release_gate_requires_all_main_workflows_on_exact_commit():
    assert release.main_checks_ready(main_check_repository(), "release-commit")
    for changes in (
        {"event": "workflow_dispatch"},
        {"head_branch": "feature"},
        {"head_sha": "previous-commit"},
    ):
        github = main_check_repository([dict(run, **changes) for run in main_runs()])
        assert not release.main_checks_ready(github, "release-commit")
    assert not release.main_checks_ready(
        main_check_repository(main_runs()[:-1]), "release-commit"
    )


@pytest.mark.parametrize("conclusion", ["failure", "cancelled", "skipped", "timed_out"])
def test_failed_or_cancelled_main_checks_prevent_publication(conclusion):
    runs = main_runs()
    runs[-1]["conclusion"] = conclusion
    with pytest.raises(RuntimeError, match="Main workflow"):
        release.main_checks_ready(main_check_repository(runs), "release-commit")


def test_running_main_checks_delay_publication():
    runs = [dict(run, status="in_progress", conclusion=None) for run in main_runs()]
    assert not release.main_checks_ready(main_check_repository(runs), "release-commit")


@pytest.mark.parametrize(
    "invalid_checks",
    [[], [check("test", app=999)], [check("test", status="in_progress")]],
)
def test_successful_workflow_still_requires_its_expected_checks(invalid_checks):
    github = Mock()
    github.items.side_effect = lambda path, key: (
        main_runs() if path.startswith("actions/runs?") else invalid_checks
    )
    assert not release.main_checks_ready(github, "release-commit")


def test_failed_job_cannot_hide_behind_successful_workflow():
    github = Mock()
    github.items.side_effect = lambda path, key: (
        main_runs()
        if path.startswith("actions/runs?")
        else [check("test", conclusion="failure")]
    )
    with pytest.raises(RuntimeError, match="Main check test"):
        release.main_checks_ready(github, "release-commit")


def test_latest_main_run_failure_cannot_be_hidden_by_older_success():
    runs = main_runs()
    runs.append(dict(runs[-1], id=99, conclusion="failure"))
    with pytest.raises(RuntimeError, match="Main workflow"):
        release.main_checks_ready(main_check_repository(runs), "release-commit")


def test_release_job_requires_main_commit_gate():
    path = Path(__file__).parents[1] / ".github/workflows/release.yml"
    workflow = yaml.safe_load(path.read_text())
    assert "commit-checks" in workflow["jobs"]["release"]["needs"]
    gate = workflow["jobs"]["commit-checks"]
    assert any(
        '--verify-commit "$GITHUB_SHA"' in step.get("run", "") for step in gate["steps"]
    )
