# Infrastructure & Operations

[Back to TRD Index](index.md)

---

## Overview

LPxGP runs on Railway with GitHub Actions CI/CD, Supabase for database/auth, and Langfuse for agent monitoring.

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DEPLOYMENT ARCHITECTURE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                          ┌─────────────────────┐                            │
│                          │     GitHub Repo     │                            │
│                          │                     │                            │
│                          │  main branch        │                            │
│                          └──────────┬──────────┘                            │
│                                     │                                        │
│                                     │ push                                   │
│                                     ▼                                        │
│                          ┌─────────────────────┐                            │
│                          │   GitHub Actions    │                            │
│                          │                     │                            │
│                          │  • Run tests        │                            │
│                          │  • Lint (ruff)      │                            │
│                          │  • Type check       │                            │
│                          └──────────┬──────────┘                            │
│                                     │                                        │
│                                     │ on success                             │
│                                     ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                           RAILWAY                                      │  │
│  │                                                                        │  │
│  │   ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐ │  │
│  │   │   Web Service   │     │  Cron Workers   │     │  Langfuse       │ │  │
│  │   │                 │     │                 │     │  (self-hosted)  │ │  │
│  │   │  FastAPI App    │     │  2 AM: Nightly  │     │                 │ │  │
│  │   │  Jinja2 + HTMX  │     │  4h: Incremental│     │  Agent traces   │ │  │
│  │   │                 │     │                 │     │  Prompt mgmt    │ │  │
│  │   └────────┬────────┘     └────────┬────────┘     └────────┬────────┘ │  │
│  │            │                       │                       │          │  │
│  └────────────┼───────────────────────┼───────────────────────┼──────────┘  │
│               │                       │                       │             │
│               └───────────────────────┼───────────────────────┘             │
│                                       │                                      │
│                                       ▼                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         SUPABASE CLOUD                                 │  │
│  │                                                                        │  │
│  │   ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐ │  │
│  │   │   PostgreSQL    │     │   Supabase Auth │     │   Storage       │ │  │
│  │   │   + pgvector    │     │   (JWT)         │     │   (Decks)       │ │  │
│  │   └─────────────────┘     └─────────────────┘     └─────────────────┘ │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        EXTERNAL SERVICES                               │  │
│  │                                                                        │  │
│  │   ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐ │  │
│  │   │   OpenRouter    │     │   Voyage AI     │     │   Calendar/     │ │  │
│  │   │   (LLMs)        │     │   (Embeddings)  │     │   Email APIs    │ │  │
│  │   └─────────────────┘     └─────────────────┘     └─────────────────┘ │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Railway Configuration

### Service Configuration

```toml
# railway.toml

[service]
name = "lpxgp"

[build]
builder = "nixpacks"
buildCommand = "uv sync --frozen"

[deploy]
startCommand = "uv run uvicorn src.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 30
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3

# Environment variable groups
[variables]
NODE_ENV = "production"
PYTHON_VERSION = "3.11"

# Cron jobs
[[cron]]
schedule = "0 2 * * *"  # 2 AM UTC daily
command = "uv run python -m src.agents.batch.run_nightly"

[[cron]]
schedule = "0 */4 * * *"  # Every 4 hours
command = "uv run python -m src.agents.batch.run_incremental"

[[cron]]
schedule = "0 3 1 * *"  # 1st of month at 3 AM
command = "uv run python -m src.agents.batch.monthly_retrain"
```

### Environment Variables

```bash
# Railway Environment Variables (set in dashboard)

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJhbG...
SUPABASE_SERVICE_ROLE_KEY=eyJhbG...  # For background jobs

# AI Services
OPENROUTER_API_KEY=sk-or-...
VOYAGE_API_KEY=pa-...

# Langfuse
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://langfuse-lpxgp.up.railway.app  # Self-hosted

# Security
TOKEN_ENCRYPTION_KEY=...  # For OAuth token encryption
SESSION_SECRET=...

# Feature flags
ENABLE_EMAIL_SYNC=false  # Disabled until M3
ENABLE_CALENDAR_SYNC=false
```

---

## GitHub Actions CI/CD

### Main Workflow

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install dependencies
        run: uv sync --frozen

      - name: Run linter
        run: uv run ruff check .

      - name: Run type checker
        run: uv run mypy src/

      - name: Run tests
        run: uv run pytest --cov=src --cov-report=xml
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL_TEST }}
          SUPABASE_ANON_KEY: ${{ secrets.SUPABASE_ANON_KEY_TEST }}

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Railway
        uses: railwayapp/github-deploy-action@v1.1.0
        with:
          railway_token: ${{ secrets.RAILWAY_TOKEN }}
          service: lpxgp
```

### Database Migration Workflow

```yaml
# .github/workflows/migrate.yml
name: Database Migrations

on:
  push:
    branches: [main]
    paths:
      - 'supabase/migrations/**'

jobs:
  migrate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Supabase CLI
        uses: supabase/setup-cli@v1
        with:
          version: latest

      - name: Run migrations
        run: |
          supabase link --project-ref ${{ secrets.SUPABASE_PROJECT_REF }}
          supabase db push
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}
```

---

## Monitoring & Observability

### Monitoring Stack

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       MONITORING ARCHITECTURE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  APPLICATION METRICS                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  Railway Dashboard:                                                  │   │
│  │  • CPU/Memory usage                                                 │   │
│  │  • Request count/latency                                            │   │
│  │  • Error rates                                                       │   │
│  │  • Deploy history                                                    │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  AGENT MONITORING (Langfuse)                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  • Full debate traces                                               │   │
│  │  • Token usage per agent                                            │   │
│  │  • Cost tracking                                                     │   │
│  │  • Latency breakdown                                                │   │
│  │  • Prompt version performance                                       │   │
│  │  • A/B test results                                                 │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  DATABASE MONITORING (Supabase)                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  • Query performance                                                │   │
│  │  • Connection pool                                                   │   │
│  │  • Storage usage                                                     │   │
│  │  • Slow query log                                                    │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ALERTING                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  Critical (PagerDuty/Slack):                                        │   │
│  │  • Error rate > 5%                                                  │   │
│  │  • API latency p95 > 5s                                             │   │
│  │  • Database connection failures                                      │   │
│  │  • Agent batch job failures                                         │   │
│  │                                                                      │   │
│  │  Warning (Slack only):                                              │   │
│  │  • Agent cost > $100/day                                            │   │
│  │  • Low cache hit rate                                               │   │
│  │  • High escalation rate                                             │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Health Check Endpoint

```python
# src/routes/health.py
from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check for Railway."""
    checks = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }

    # Database check
    try:
        await supabase.table("users").select("id").limit(1).execute()
        checks["checks"]["database"] = "ok"
    except Exception as e:
        checks["checks"]["database"] = f"error: {e}"
        checks["status"] = "degraded"

    # OpenRouter check
    try:
        # Light ping
        checks["checks"]["openrouter"] = "ok"
    except Exception as e:
        checks["checks"]["openrouter"] = f"error: {e}"
        checks["status"] = "degraded"

    return checks

@router.get("/health/detailed")
async def detailed_health():
    """Detailed health for debugging (admin only)."""
    return {
        "database": await check_database_health(),
        "cache": await check_cache_stats(),
        "agents": await check_agent_health(),
        "integrations": await check_integration_health(),
    }
```

### Custom Metrics

```python
# src/monitoring/metrics.py
from datetime import datetime, timedelta

async def get_platform_metrics(days: int = 7) -> dict:
    """Get platform-wide metrics."""
    cutoff = datetime.now() - timedelta(days=days)

    # User activity
    active_users = await supabase.table("users").select(
        "id", count="exact"
    ).gte("last_login", cutoff.isoformat()).execute()

    # Match metrics
    matches = await supabase.table("matches").select(
        "id", count="exact"
    ).gte("created_at", cutoff.isoformat()).execute()

    # Pitch metrics
    pitches = await supabase.table("pitches").select(
        "id", count="exact"
    ).gte("created_at", cutoff.isoformat()).execute()

    # Agent metrics (from Langfuse)
    agent_metrics = await get_agent_metrics(days)

    return {
        "period_days": days,
        "active_users": active_users.count,
        "matches_generated": matches.count,
        "pitches_generated": pitches.count,
        "agent_debates": agent_metrics["total_debates"],
        "agent_cost_usd": agent_metrics["total_cost"],
        "avg_latency_ms": agent_metrics["avg_latency"],
    }
```

---

## Security Configuration

### CORS Configuration

```python
# src/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://lpxgp.com",
        "https://www.lpxgp.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)
```

### Security Headers

```python
# src/middleware/security.py
from fastapi import Request

async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' cdn.tailwindcss.com unpkg.com; "
        "style-src 'self' 'unsafe-inline' cdn.tailwindcss.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://*.supabase.co"
    )

    return response
```

### Rate Limiting

```python
# src/middleware/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Apply to routes
@app.get("/api/v1/lps")
@limiter.limit("100/minute")
async def list_lps():
    ...

# AI endpoints - stricter limits
@app.post("/api/v1/matches/generate")
@limiter.limit("10/minute")
async def generate_matches():
    ...

@app.post("/api/v1/pitches")
@limiter.limit("20/hour", key_func=lambda r: r.state.company_id)
async def generate_pitch():
    ...
```

---

## Backup & Recovery

### Database Backups

Supabase handles automatic backups:

| Plan | Backup Frequency | Retention |
|------|-----------------|-----------|
| Free | Daily | 7 days |
| Pro | Daily | 14 days |
| Team | Daily + PITR | 30 days |

### Manual Backup Commands

```bash
# Export database (for migration or local dev)
supabase db dump -f backup.sql

# Import to new instance
supabase db push < backup.sql

# Export specific tables
supabase db dump -f lps_backup.sql --schema public --table lp_profiles
```

### Recovery Procedures

```markdown
## Disaster Recovery Runbook

### Scenario 1: Database Corruption
1. Identify last known good backup
2. Create new Supabase project
3. Restore from backup
4. Update Railway env vars
5. Verify data integrity
6. Redirect DNS

### Scenario 2: Accidental Data Deletion
1. Use Supabase PITR (Point-in-Time Recovery)
2. Recover to specific timestamp
3. Merge recovered data

### Scenario 3: Service Outage
1. Check Railway status
2. If Railway down: Enable maintenance mode
3. Notify users via status page
4. Monitor for resolution
```

---

## Environment Management

### Environment Separation

| Environment | Purpose | Database | URL |
|-------------|---------|----------|-----|
| Production | Live users | Supabase Prod | lpxgp.com |
| Staging | Pre-release testing | Supabase Staging | staging.lpxgp.com |
| Development | Local dev | Supabase Dev | localhost:8000 |

### Local Development

```bash
# Start local development
uv run uvicorn src.main:app --reload

# Use local .env file
cp .env.example .env

# Required env vars for local dev
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
OPENROUTER_API_KEY=sk-or-...
```

### Staging Deployment

```yaml
# .github/workflows/staging.yml
name: Deploy to Staging

on:
  push:
    branches: [develop]

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Railway Staging
        uses: railwayapp/github-deploy-action@v1.1.0
        with:
          railway_token: ${{ secrets.RAILWAY_TOKEN }}
          service: lpxgp-staging
```

---

## Logging

### Structured Logging

```python
# src/logging_config.py
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
)

# Usage
log = structlog.get_logger()

log.info("match_generated",
    fund_id=fund_id,
    lp_id=lp_id,
    score=score,
    latency_ms=latency
)
```

### Log Levels

| Level | Use Case |
|-------|----------|
| DEBUG | Development only, verbose |
| INFO | Normal operations, requests |
| WARNING | Recoverable issues |
| ERROR | Failures requiring attention |
| CRITICAL | System failures |

---

## Cost Management

### Cost Breakdown

| Service | Estimated Monthly Cost |
|---------|----------------------|
| Railway (Web + Cron) | $20-50 |
| Supabase Pro | $25 |
| OpenRouter (AI) | $100-500 |
| Voyage AI (Embeddings) | $50-100 |
| Langfuse (self-hosted) | $0 (on Railway) |

### Cost Monitoring

```python
# src/monitoring/cost.py
async def get_monthly_cost_breakdown() -> dict:
    """Get cost breakdown for current month."""
    # OpenRouter costs (from API)
    openrouter_cost = await get_openrouter_usage()

    # Voyage costs (estimated from token count)
    voyage_cost = await estimate_voyage_cost()

    # Railway (from dashboard API)
    railway_cost = await get_railway_usage()

    return {
        "openrouter": openrouter_cost,
        "voyage": voyage_cost,
        "railway": railway_cost,
        "supabase": 25.00,  # Fixed
        "total": sum([openrouter_cost, voyage_cost, railway_cost, 25.00])
    }

# Alert if costs spike
async def check_cost_alerts():
    costs = await get_monthly_cost_breakdown()
    if costs["total"] > 800:  # $800 threshold
        await send_slack_alert(f"Monthly costs at ${costs['total']}")
```

---

## Related Documents

- [Architecture](architecture.md) - System design
- [Agents](agents.md) - Agent batch processing
- [Integrations](integrations.md) - External service connections
