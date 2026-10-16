# Security Policy

## Reporting a vulnerability

If you discover a security vulnerability, please **do not open a public issue**.
Report it privately:

- GitHub: use the **"Report a vulnerability"** button on the Security tab, or
- Email the repository owner.

We will acknowledge within 48 hours and aim to resolve confirmed issues promptly.

## Supported versions

This is a personal prototype. Only the latest `main` branch is supported.

## Security model

This project follows these practices:

- **Secrets in Key Vault**, accessed via Managed Identity — never in code, `.env`
  (gitignored), or Terraform state.
- **CI/CD uses OIDC** — GitHub Actions authenticates to Azure with federated
  credentials (no long-lived client secrets).
- **Synthetic data only** — no real PII is processed or stored.
- **PII masking** — names and document numbers are masked before storage.
- **Parameterized SQL** — all queries use bound parameters (no SQL injection).
- **XSS-safe front-end** — all server-rendered strings are HTML-escaped.

## Known limitations

- Branch protection rules and GitHub Advanced Security (code/secret scanning)
  require a paid GitHub plan for private repositories.
- As a free-tier alternative, a `gitleaks` secret-scan workflow runs on every
  push and pull request (`.github/workflows/security-scan.yml`).

## See also

- `docs/security.md` — detailed security design (secrets, auth, PII, hardening).
