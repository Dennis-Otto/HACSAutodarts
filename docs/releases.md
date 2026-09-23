# Releases and update notes

HACS uses GitHub releases and exposes their release notes in the Home Assistant
update dialog. Release notes contain an optional introduction followed by an
automatically generated list of merged pull requests and a full changelog link.

## Automatic dependency releases

Merged Dependabot updates automatically produce a maintenance release. Patch and
minor dependency PRs merge after their required checks; major dependency PRs still
need a maintainer to merge them. Once merged, both follow the same release process:

1. **Release dependency updates** finds merged Dependabot PRs that are not included
   in the latest published release.
2. It creates a version-only PR, increasing the integration's patch version
   (for example, `0.4.2` → `0.4.3`). A library's major version change does not by
   itself imply a major integration version change.
3. The existing tests, Ruff, HACS, hassfest, workflow linting, CodeQL, dependency
   review and secret scan run against the release candidate. GitHub's normal
   branch protection remains in force; no required checks or approvals are bypassed.
4. After merging the checked version PR, the existing **Release integration**
   workflow validates the release and waits for every main-branch commit check
   (tests, HACS, hassfest, workflow lint, CodeQL and secret scan) to succeed on the
   exact commit being published. Missing, failed, cancelled or skipped checks
   prevent publication. It then publishes the generated changelog.

CI runs independently for every commit and caller. A new commit or release does
not cancel an earlier commit's tests, validation or security checks. Publication
remains serialized to prevent competing release writes.

The workflow starts after a Dependabot merge. A scheduled reconciliation runs at
minutes 13 and 43 of each hour to catch merges whose events GitHub suppresses for
`GITHUB_TOKEN`; GitHub may delay scheduled jobs. Already released changes do not
produce another release. Several pending updates can share one release. Other
changes already merged into `main` are included in the release and its changelog.

Reconciliation uses the protected `release` environment with `deployment: false`.
It retains access to the App key and the environment's branch restrictions without
creating deployment records for checks that find nothing to publish. Only the
publication job in **Release integration** records a deployment, linked to its
release page. Creating a draft does not create a deployment record. Workflow runs
remain visible in Actions, including checks that do not produce a release.

Test dependencies and GitHub Actions updates also produce releases. Their release
introduction explains that those dependency changes do not add integration features.
Version-only release PRs carry the `release` label and are omitted from the changelog.

Automatic releases inherit the latest published release's channel: while that is
a WIP prerelease, automatic maintenance releases remain WIP prereleases. After a
maintainer publishes a stable release, subsequent automatic maintenance releases
are stable as well. HACS users must enable the repository's
[prerelease switch](https://www.hacs.xyz/docs/use/entities/switch/) to receive WIP
updates. HACS offers releases when it refreshes repository data; publishing does
not automatically install an update or restart Home Assistant.

A GitHub App creates and updates the release branch and PR. Unlike
`GITHUB_TOKEN`-authored changes, these events start normal PR workflows without
GitHub's bot-PR approval gate. The workflow waits for checks associated with that
exact PR and commit; separately dispatched branch checks do not count. Only trusted
default-branch orchestration code receives the App token. Candidate code runs in
the normal CI workflows, and all branch protection rules remain in force.

GitHub may register PR workflows several minutes after the PR is created. The
release workflow allows up to thirty minutes for all five PR workflows to appear,
then waits for their checks to finish. Partial registration or successful checks
from another event, PR or commit never permit a merge. If a workflow stays missing,
the run fails without publishing; a later run reuses the existing version PR.
The overall job allows up to ninety minutes, including the subsequent checks,
protected merge and publication.

### One-time GitHub App setup

Use a private GitHub App owned by the maintainer with **Contents: Read and write**,
**Pull requests: Read and write** and mandatory **Metadata: Read-only**. No webhook,
account permissions, Administration, Actions or Workflows write permission is
needed. An existing release App with those permissions can be reused; add this
repository to its selected installation repositories.

Create a `release` Actions environment restricted to deployments from the `main`
branch. Store `RELEASE_AUTOMATION_PRIVATE_KEY` as a secret in that environment,
and set the repository Actions variable `RELEASE_AUTOMATION_CLIENT_ID` to the App's
Client ID. Never commit the key. The pinned official `actions/create-github-app-token`
action mints a short-lived token restricted to this repository and these two write
permissions, then revokes it when the job finishes. The App identity comes from
the action's output, so renaming the App does not require changing the workflow.
GitHub's built-in token is used for reading checks and dispatching the existing
release workflow. Removing the installation or key revokes future App access.

Until the Client ID variable is configured, scheduled/merge-triggered runs are
skipped. A manual run reports missing credentials. This GitHub App is separate
from the Autodarts cloud application's Client ID.

### Recovery and manual control

- To check for pending dependency updates immediately, run **Release dependency
  updates → Run workflow** on `main`.
- A failed run does not publish a release. Fix the reported check or API problem
  and rerun; an existing version PR is reused, including after a successful merge
  followed by a publishing failure.
- Closing a version PR without merging pauses that version. Reopen it to resume.
  Disable the workflow in GitHub Actions to pause the automation entirely.
- A version manually changed on `main` is never overwritten. Publish that version
  through the manual workflow first. Automatic version calculation supports
  numeric `x.y.z` tags; a suffix such as `-rc.1` needs a manual release strategy.

## Create a manual release

1. Update `custom_components/autodarts/manifest.json` to the intended version in a
   pull request and merge it after the required checks pass.
2. Open **Actions → Release integration → Run workflow** on `main`.
3. Enter the same version, without a `v` prefix, and optionally add your own
   introduction. Markdown is supported, including important migration notes.
4. Choose whether this is a prerelease and whether to save a draft. Both default
   to enabled while this integration is work in progress.
5. Run the workflow. It reruns the integration tests and HACS/hassfest checks,
   validates the version, generates the notes, and creates the release. With
   **draft** disabled, the release is published directly. Otherwise, review the
   draft under **Releases** and publish it when ready.

Your introduction appears first. Leaving it empty produces only the generated
notes, with no placeholder text. You can edit the introduction in a release draft
before publishing. The complete notes also appear in the workflow run summary.

## Keep generated notes useful

Use descriptive pull request titles that explain the user-visible change.
The configuration in `.github/release.yml` groups merged pull requests by label:

| Label | Release-note section |
| --- | --- |
| `breaking-change` | Wichtige Änderungen und Migration |
| `enhancement` | Neue Funktionen |
| `bug` | Fehlerbehebungen |
| `dependencies`, `maintenance` | Abhängigkeiten und Wartung |
| `documentation` | Dokumentation |
| Other or no label | Weitere Änderungen |

Dependabot changes are included in the maintenance section. GitHub generates
these notes from merged pull requests; it does not explain individual code changes
or translate pull request titles. Include migration instructions in your own text.

The optional introduction in the manual workflow remains available for release
highlights or migration instructions. Automatic dependency releases use a short
maintenance introduction followed by the same generated changelog.
