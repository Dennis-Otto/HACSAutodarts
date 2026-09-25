# Security policy

## Supported versions

Security fixes are provided for the latest release of the Autodarts integration. Older versions receive no fixes; update through HACS to stay protected.

## Reporting a vulnerability

Please do not open a public issue for a suspected vulnerability. Use GitHub's private vulnerability reporting for this repository:

<https://github.com/Dennis-Otto/HACSAutodarts/security/advisories/new>

Include the affected version, Home Assistant version, Board Manager version, setup type (local or cloud), reproduction steps, and potential impact. Reports will be acknowledged as soon as practical. Confirmed vulnerabilities are fixed privately and disclosed in a GitHub security advisory and the release notes once a fixed release is available.

## Secrets

Autodarts access and refresh tokens, Board Manager API keys, Home Assistant access tokens, private network addresses, and logs or diagnostics containing those values must never be committed to this repository or posted in public issues.

The integration stores Autodarts tokens only in the Home Assistant config entry. The Board Manager API key returned by the local configuration endpoint is discarded before any value reaches Home Assistant entities. Diagnostics redact the board ID, addresses, client ID and tokens and contain no API keys; the Docker end-to-end test verifies this against a real Home Assistant instance. Every push and pull request is scanned with Gitleaks.
