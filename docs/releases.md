# Releases and update notes

HACS uses GitHub releases and exposes their release notes in the Home Assistant
update dialog. Release notes contain an optional introduction followed by an
automatically generated list of merged pull requests and a full changelog link.

## Create a release

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

Routine dependency merges do not automatically bump the integration version or
publish a release. This avoids creating Home Assistant updates for every test-tool
or CI dependency change. Published prereleases are intended for users who enable
beta versions in HACS; stable releases use the normal update channel.
