# Non-Functional Requirements

[← Back to Index](index.md)

---

## 12.1 Performance

| Metric | Requirement |
|--------|-------------|
| Page load time | < 2 seconds (LCP) |
| Search response | < 500ms |
| Semantic search | < 2 seconds |
| Match generation | < 30 seconds for 100 matches |
| Pitch generation | < 10 seconds |
| Concurrent users | Support 100 simultaneous |
| Database queries | < 100ms for indexed queries |

---

## 12.2 Security

### Encryption & Transport
- All data encrypted at rest (Supabase default)
- All traffic over HTTPS (TLS 1.3)
- JWT tokens with 1 hour expiry
- Refresh tokens with 7 day expiry

### Access Control
- Row-level security enforced with 5-tier role model:
  - **Viewer**: Read-only access to own org data
  - **Member**: Read/write access to own org data
  - **Admin**: Full access to own org, user management
  - **Fund Admin (FA)**: Cross-org read access, privileged operations
  - **Super Admin**: Full system access
- Single current employment enforced (no multi-org users)
- Invitation-only registration (no public signups)

#### Fund Admin (FA) Role Specification

| Capability | FA | Super Admin |
|------------|:--:|:-----------:|
| Cross-org READ (all dashboards) | ✓ | ✓ |
| Impersonate GP/LP users (view-only) | ✓ | ✓ |
| Impersonate with write mode | ✗ | ✓ |
| Own FA Dashboard | ✓ | ✓ |
| Add manual recommendations | ✓ | ✓ |
| Onboard GP/LP | ✓ | ✓ |
| Full CRUD: GPs | ✓ | ✓ |
| Full CRUD: LPs | ✓ | ✓ |
| Full CRUD: People | ✓ | ✓ |
| Full CRUD: Users | ✓ | ✓ |
| Assign Viewer/Member roles | ✓ | ✓ |
| Assign Admin/FA roles | ✗ | ✓ |
| Set up org billing | ✓ | ✓ |
| System-wide settings | ✗ | ✓ |

**FA Role Restrictions:**
- FA CANNOT add, remove, or modify Admin or Fund Admin roles
- FA CAN only assign Viewer or Member roles to users
- Only Super Admin can promote users to Admin or Fund Admin
- FA impersonation is always view-only (cannot make changes)

#### Dashboard Access Model

**Shared-with-Ownership Model:**
- GP organizations: One dashboard per fund, shared by all org users
- LP organizations: One unified dashboard, shared by all org users
- All items show `created_by` attribution
- Activity feeds show team-wide activity with user attribution
- Can filter "my items" vs "all items"
- No private/personal item scoping within an org

### Input Validation
- Pydantic models for all API endpoints
- Email validation with `email-validator`
- Financial amounts: Decimal, >= 0, max 1,000,000 MM
- Percentages: 0-100 range with bounds checking
- Text fields: Max length enforcement
- File uploads: Max 50MB, PDF/PPTX only

### Rate Limiting

| Endpoint | Limit | Scope | Purpose |
|----------|-------|-------|---------|
| `POST /auth/login` | 5/min | per IP | Brute force prevention |
| `POST /matches/generate` | 10/min | per org | AI cost control |
| `POST /pitches` | 20/hour | per user | AI cost control |
| `GET /lp-search` | 100/min | per user | Data scraping prevention |
| `POST /data-imports` | 5/hour | per org | Resource protection |
| Default | 100/min | per user | General protection |

### Account Lockout
- **Threshold**: 5 failed login attempts
- **Duration**: 30 minute lockout
- **Scope**: Per email address
- **Tracking**: Stored in `login_attempts` table with 90-day retention

### CSRF Protection
- Double-submit cookie pattern
- `X-CSRF-Token` header required for state-changing requests
- SameSite=Strict cookies
- HTMX integration via `hx-headers`

### Logging & Audit
- Structured logging with sensitive field redaction
- Audit log for sensitive table access (LP profiles, matches)
- Request ID tracking for debugging
- No passwords, tokens, or API keys in logs

#### Impersonation Audit Requirements
- All impersonation sessions logged to `impersonation_logs` table
- Required fields: admin_user_id, target_user_id, started_at, ended_at, reason (optional)
- Actions during impersonation tagged with both user IDs in audit_logs
- Retention: 2 years minimum for compliance
- Access to logs: Super Admin only

#### Role Change Audit
- All role changes logged with: changed_by, old_role, new_role, timestamp
- Logged regardless of who makes the change (FA or Super Admin)

#### Entity Change Audit
- All GP/LP/People/User changes logged by FA
- Captures: entity_type, entity_id, operation, changed_by, timestamp

---

## 12.3 Reliability

- 99.9% uptime target (Supabase SLA)
- Daily automated backups (Supabase)
- Point-in-time recovery (7 days)
- Health check endpoints
- Graceful error handling
- Retry logic for external APIs

---

## 12.4 Scalability

- Stateless backend (horizontal scaling ready)
- Database connection pooling (Supabase)
- Async operations for AI calls
- Background jobs for enrichment
- Static assets served by FastAPI (Railway handles caching)

---

[Next: Decisions Log →](decisions.md)
