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
   workflow validates the release and publishes its generated changelog.

The workflow starts after a Dependabot merge. A scheduled reconciliation runs at
minutes 13 and 43 of each hour to catch merges whose events GitHub suppresses for
`GITHUB_TOKEN`; GitHub may delay scheduled jobs. Already released changes do not
produce another release. Several pending updates can share one release. Other
changes already merged into `main` are included in the release and its changelog.

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

The workflow uses GitHub's short-lived token, with no personal access token. The
repository must allow Actions to create pull requests. Candidate checks are
explicitly dispatched so bot-created PRs do not depend on suppressed or
approval-gated PR events. Only trusted default-branch orchestration code runs with
write permissions; candidate code runs in the normal CI workflows.

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
