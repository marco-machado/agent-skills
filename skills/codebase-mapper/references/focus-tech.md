# Focus: tech

## Goal

Analyze the technology stack and external integrations.

## Documents to write

- `docs/generated/STACK.md`
- `docs/generated/INTEGRATIONS.md`

## Exploration commands

```bash
# Package manifests
ls package.json requirements.txt Cargo.toml go.mod pyproject.toml 2>/dev/null
cat package.json 2>/dev/null | head -100

# Config files (list only — never read .env contents)
ls -la *.config.* tsconfig.json .nvmrc .python-version 2>/dev/null
ls .env* 2>/dev/null  # note existence only

# SDK / API imports
grep -r "import.*stripe\|import.*supabase\|import.*aws\|import.*@" \
  src/ --include="*.ts" --include="*.tsx" 2>/dev/null | head -50
```

Read the manifests and any framework / build configs identified. Look
for `Dockerfile`, `docker-compose.yml`, `.github/workflows/*` to surface
runtime + CI/CD context.

## Template — `STACK.md`

Replace `[YYYY-MM-DD]` with today's date from session context. Use
"Not detected" or "Not applicable" when something isn't found.

```markdown
# Technology Stack

**Analysis Date:** [YYYY-MM-DD]

## Languages

**Primary:**
- [Language] [Version] — [Where used]

**Secondary:**
- [Language] [Version] — [Where used]

## Runtime

**Environment:**
- [Runtime] [Version]

**Package Manager:**
- [Manager] [Version]
- Lockfile: [present/missing]

## Frameworks

**Core:**
- [Framework] [Version] — [Purpose]

**Testing:**
- [Framework] [Version] — [Purpose]

**Build/Dev:**
- [Tool] [Version] — [Purpose]

## Key Dependencies

**Critical:**
- [Package] [Version] — [Why it matters]

**Infrastructure:**
- [Package] [Version] — [Purpose]

## Configuration

**Environment:**
- [How configured]
- [Key configs required]

**Build:**
- [Build config files]

## Platform Requirements

**Development:**
- [Requirements]

**Production:**
- [Deployment target]

---

*Stack analysis: [date]*
```

## Template — `INTEGRATIONS.md`

```markdown
# External Integrations

**Analysis Date:** [YYYY-MM-DD]

## APIs & External Services

**[Category]:**
- [Service] — [What it's used for]
  - SDK/Client: [package]
  - Auth: [env var name]

## Data Storage

**Databases:**
- [Type/Provider]
  - Connection: [env var]
  - Client: [ORM/client]

**File Storage:**
- [Service or "Local filesystem only"]

**Caching:**
- [Service or "None"]

## Authentication & Identity

**Auth Provider:**
- [Service or "Custom"]
  - Implementation: [approach]

## Monitoring & Observability

**Error Tracking:**
- [Service or "None"]

**Logs:**
- [Approach]

## CI/CD & Deployment

**Hosting:**
- [Platform]

**CI Pipeline:**
- [Service or "None"]

## Environment Configuration

**Required env vars:**
- [List critical vars]

**Secrets location:**
- [Where secrets are stored]

## Webhooks & Callbacks

**Incoming:**
- [Endpoints or "None"]

**Outgoing:**
- [Endpoints or "None"]

---

*Integration audit: [date]*
```
