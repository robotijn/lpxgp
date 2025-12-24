# Security Findings - Red Team / Blue Team Audit

**Date:** 2024-12-23
**Status:** Tracking document for security remediation

---

## Summary

| Severity | Red Team | Blue Team | Total |
|----------|----------|-----------|-------|
| CRITICAL | 0 | 5 | 5 |
| HIGH | 6 | 22 | 28 |
| MEDIUM | 4 | 28 | 32 |
| LOW | 2 | 5 | 7 |
| **Total** | **12** | **60** | **72** |

---

## Critical Issues (Fix Before M1)

### C1: No Pydantic Request Models
- **Location:** API endpoints (not yet implemented)
- **Impact:** No input validation, injection risk
- **Fix:** Create Pydantic models for all POST/PATCH endpoints
- **Status:** [ ] Pending (M1 implementation)

### C2: Self-Match Prevention Missing
- **Location:** `fund_lp_matches` table
- **Impact:** GP could match own LP org
- **Fix:** Add CHECK constraint: `fund.org_id != lp_org_id`
- **Status:** [ ] Pending (add to migration)

### C3: Stack Traces Exposed in Errors
- **Location:** Health check endpoint
- **Impact:** Information disclosure
- **Fix:** Filter exceptions, return generic errors
- **Status:** [ ] Pending (M1 implementation)

### C4: GP/LP Data Leakage via RLS
- **Location:** `004_rls_policies.sql`
- **Impact:** Any user can read all LP contacts
- **Fix:** Restrict `people`, `employment` tables by org
- **Status:** [ ] Pending (refine RLS policies)

### C5: M1b Tables Not in Migrations
- **Location:** `docs/milestones/m1b-ir-core.md`
- **Impact:** Schema mismatch
- **Fix:** Create `006_ir_core_schema.sql`
- **Status:** [ ] Pending (M1b implementation)

---

## High Priority Issues

### RLS Policy Gaps (6 issues)

| ID | Table | Issue | Fix |
|----|-------|-------|-----|
| H1 | `employment` | All users can read all employment records | Restrict by org membership |
| H2 | `people` | All users can read all contacts | Restrict by org relationship |
| H3 | `invitations` | No DELETE policy | Add explicit DELETE policy |
| H4 | `outreach_events` | No DELETE/UPDATE policy | Add policies |
| H5 | `lp_profiles` | Globally readable | Add audit logging |
| H6 | `current_user_org_id()` | LIMIT 1 without ORDER BY | Add ORDER BY updated_at DESC |

### Business Logic Gaps (8 issues)

| ID | Issue | Fix |
|----|-------|-----|
| H7 | No fund name uniqueness per org | Add UNIQUE(org_id, name) |
| H8 | Financial amounts allow negative | Add CHECK >= 0 |
| H9 | Pipeline state transitions undocumented | Document state machine |
| H10 | File upload limits not enforced | Implement MAX_FILE_UPLOAD_MB |
| H11 | Export row limits not enforced | Implement MAX_EXPORT_ROWS |
| H12 | Rate limiting not documented | Add to nfr.md |
| H13 | No audit logging | Implement audit_logs table |
| H14 | Agent tables not in migrations | Create 005_agent_schema.sql |

---

## Medium Priority Issues

### Documentation Gaps
- [ ] Expand nfr.md security section
- [ ] Document error response format
- [ ] Document rate limiting matrix
- [ ] Create threat model document
- [ ] Document token generation algorithm

### Code Quality
- [ ] Pin dependency versions (use `==` not `>=`)
- [ ] Add security scanning (bandit, pip-audit)
- [ ] Implement CSRF protection
- [ ] Add account lockout policy
- [ ] Validate environment variables on startup

### Schema Consistency
- [x] M1b: `clients` → `organizations` (FIXED)
- [x] M1b: `users` → `people` (FIXED)
- [ ] Add CASCADE DELETE to foreign keys
- [ ] Document JSONB field structures

---

## Remediation Schedule

### Before M1 Launch
1. Create Pydantic models with validation
2. Add self-match prevention constraint
3. Filter stack traces from error responses
4. Review and refine RLS policies

### Before M2 Launch
5. Implement audit logging
6. Document rate limiting
7. Pin dependency versions
8. Add security test scenarios

### Before M3 Launch
9. Create agent schema migration
10. Implement CSRF protection
11. Create threat model document

---

## Positive Findings

- RLS enabled on all tables
- Invite-only platform design
- Human-in-the-loop for AI content
- Test specifications cover attack vectors
- Supabase provides encryption and backups

---

## References

- [TRD: Infrastructure](../trd/infrastructure.md) - Security configuration
- [TRD: Architecture](../trd/architecture.md) - RLS design
- [PRD: NFR](../prd/nfr.md) - Non-functional requirements
- [Milestones](../milestones/index.md) - Implementation schedule
