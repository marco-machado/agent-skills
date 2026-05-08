# Forbidden files (shared guardrail)

These rules apply in every focus phase. Read this once before the first
phase runs.

## NEVER read or quote contents from these files

- `.env`, `.env.*`, `*.env` — environment variables with secrets
- `credentials.*`, `secrets.*`, `*secret*`, `*credential*` — credential files
- `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.jks` — certificates and private keys
- `id_rsa*`, `id_ed25519*`, `id_dsa*` — SSH private keys
- `.npmrc`, `.pypirc`, `.netrc` — package manager auth tokens
- `config/secrets/*`, `.secrets/*`, `secrets/` — secret directories
- `*.keystore`, `*.truststore` — Java keystores
- `serviceAccountKey.json`, `*-credentials.json` — cloud service credentials
- `docker-compose*.yml` sections containing passwords — may include inline secrets
- Any `.gitignore`d file that appears to contain secrets

## If you encounter one of these files

- Note its **existence only**: `` `.env` file present — contains environment configuration ``
- **Never** quote its contents, even partially.
- **Never** include values like `API_KEY=...` or `sk-...` in any output document.

## Why this matters

Mapping output is committed to git. Leaked secrets become a security
incident. A post-write scan (`scripts/scan-secrets.py`) runs after all
focus phases complete, but the only reliable defense is not reading the
secrets in the first place.
