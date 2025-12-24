# Threat Model - LPxGP

[← Back to Security Findings](SECURITY-FINDINGS.md)

---

## 1. System Overview

LPxGP is a B2B SaaS platform for GP-LP matching. It processes:
- Institutional investor data (LP profiles, contact info)
- Fund information (strategies, target sizes)
- Relationship tracking (touchpoints, tasks)
- AI-generated content (pitches, match explanations)

---

## 2. Assets

### High Value Assets
| Asset | Sensitivity | Impact if Compromised |
|-------|-------------|----------------------|
| LP profiles | High | Competitive advantage, privacy violation |
| Contact information | High | Spam, phishing, regulatory issues |
| Fund strategies | High | Competitive intelligence |
| Match algorithms | Medium | Business logic exposure |
| User credentials | High | Account takeover |

### Data Classification
| Classification | Examples | Storage |
|----------------|----------|---------|
| **Confidential** | LP allocations, fund sizes | Encrypted, RLS protected |
| **Internal** | User emails, org names | RLS protected |
| **Public** | Published fund names | No special protection |

---

## 3. Threat Actors

### External Threats
| Actor | Motivation | Capability | Likelihood |
|-------|------------|------------|------------|
| **Competitor** | Data scraping, competitive intel | Medium-High | High |
| **Spammer** | Email harvesting | Low | Medium |
| **Cybercriminal** | Credential theft, ransomware | Medium | Medium |
| **Nation State** | Economic espionage | Very High | Low |

### Internal Threats
| Actor | Motivation | Capability | Likelihood |
|-------|------------|------------|------------|
| **Disgruntled employee** | Data exfiltration | High | Low |
| **Careless user** | Accidental exposure | Low | Medium |
| **Malicious insider** | Fraud, sabotage | High | Very Low |

---

## 4. Attack Surface

### Entry Points

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ATTACK SURFACE                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  EXTERNAL                                                                    │
│  ┌─────────────────┐                                                        │
│  │  Web App (HTMX) │────▶ FastAPI ────▶ Supabase                           │
│  └─────────────────┘        │                                                │
│                             │                                                │
│  ┌─────────────────┐        │                                                │
│  │  API Clients    │────────┘                                                │
│  └─────────────────┘                                                         │
│                                                                              │
│  INTERNAL                                                                    │
│  ┌─────────────────┐                                                        │
│  │  Background Jobs│────▶ OpenRouter ────▶ LLM APIs                         │
│  └─────────────────┘        │                                                │
│                             │                                                │
│  ┌─────────────────┐        │                                                │
│  │  Langfuse       │◀───────┘                                                │
│  └─────────────────┘                                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Endpoint Categories

| Category | Endpoints | Risk Level | Key Controls |
|----------|-----------|------------|--------------|
| **Authentication** | `/auth/*` | High | Rate limiting, lockout, CSRF |
| **Data Read** | `/lps/*`, `/funds/*` | Medium | RLS, audit logging |
| **Data Write** | `POST/PATCH` endpoints | High | RLS, input validation |
| **AI Generation** | `/matches/generate`, `/pitches` | Medium | Rate limiting, prompt safety |
| **File Upload** | `/funds/{id}/upload-deck` | High | Size limit, type validation |
| **Admin** | `/admin/*` | Very High | Role check, audit logging |

---

## 5. Threat Scenarios

### T1: Data Scraping by Competitor
**Attack**: Competitor creates account, systematically scrapes LP database
**Likelihood**: High | **Impact**: High

**Mitigations**:
- [x] Rate limiting on LP search (100/min)
- [x] Audit logging for LP profile access
- [ ] Behavioral analysis for scraping patterns (Future)
- [ ] CAPTCHA on search after threshold (Future)

### T2: Credential Stuffing
**Attack**: Automated login attempts with leaked credential lists
**Likelihood**: Medium | **Impact**: High

**Mitigations**:
- [x] Account lockout after 5 failed attempts
- [x] Rate limiting on login (5/min per IP)
- [ ] Require MFA for admin roles (M2)
- [ ] Monitor for leaked credentials (Future)

### T3: RLS Bypass
**Attack**: Attacker finds flaw in RLS policies to access other orgs' data
**Likelihood**: Low | **Impact**: Very High

**Mitigations**:
- [x] Restrictive RLS model (default deny)
- [x] Helper functions in SECURITY DEFINER mode
- [x] Single employment enforcement
- [ ] Automated RLS testing in CI (Phase 8)

### T4: SQL Injection
**Attack**: Malicious input in search/filter parameters
**Likelihood**: Low | **Impact**: High

**Mitigations**:
- [x] Supabase client uses parameterized queries
- [x] Pydantic input validation
- [x] No raw SQL in application code
- [ ] sqlmap testing in security audit (Future)

### T5: XSS in Generated Content
**Attack**: LLM generates malicious script in pitch/summary
**Likelihood**: Low | **Impact**: Medium

**Mitigations**:
- [x] Jinja2 auto-escaping enabled
- [x] Human review before using AI content
- [ ] Content sanitization layer (Future)
- [ ] CSP headers (Future)

### T6: CSRF on Destructive Actions
**Attack**: Trick user into deleting data via malicious link
**Likelihood**: Medium | **Impact**: Medium

**Mitigations**:
- [x] CSRF token required for state changes
- [x] SameSite=Strict cookies
- [x] Double-submit cookie pattern

### T7: Information Disclosure via Errors
**Attack**: Trigger errors to expose internal details
**Likelihood**: Medium | **Impact**: Low-Medium

**Mitigations**:
- [x] Error sanitization middleware
- [x] Generic error messages to client
- [x] Sensitive pattern detection
- [x] Request ID for internal correlation

### T8: API Key Exposure
**Attack**: Attacker finds API keys in logs, errors, or client code
**Likelihood**: Medium | **Impact**: High

**Mitigations**:
- [x] Structured logging with field redaction
- [x] No keys in error messages
- [x] Keys stored in environment variables
- [ ] Key rotation policy (Future)

---

## 6. Security Controls Matrix

| Control | Implementation | Status |
|---------|----------------|--------|
| **Authentication** | Supabase Auth + invitation-only | ✅ |
| **Authorization** | RLS + role-based access | ✅ |
| **Input Validation** | Pydantic models | ✅ |
| **Rate Limiting** | slowapi with scoped limits | ✅ |
| **CSRF Protection** | Double-submit cookies | ✅ |
| **Account Lockout** | 5 attempts / 30 min | ✅ |
| **Audit Logging** | Sensitive table access | ✅ |
| **Error Sanitization** | Middleware filter | ✅ |
| **Log Redaction** | structlog processor | ✅ |
| **MFA** | For admin roles | 🔜 M2 |
| **Penetration Testing** | Annual external audit | 🔜 M5 |

---

## 7. Residual Risks

| Risk | Residual Level | Acceptance Rationale |
|------|----------------|---------------------|
| Insider data theft | Medium | Audit logging provides deterrence and forensics |
| Sophisticated scraping | Low-Medium | Rate limits + audit make it detectable |
| Zero-day in dependencies | Low | Regular updates + pip-audit scanning |
| LLM prompt injection | Low | Human-in-the-loop for all AI content |

---

## 8. Security Roadmap

### M1 (Launch)
- [x] RLS hardening
- [x] Input validation
- [x] Rate limiting
- [x] CSRF protection
- [x] Account lockout
- [x] Audit logging

### M2
- [ ] MFA for admin roles
- [ ] Session management UI
- [ ] Security event notifications

### M5 (Production)
- [ ] External penetration test
- [ ] SOC 2 Type I preparation
- [ ] Security monitoring dashboard
- [ ] Incident response playbook

---

## 9. Related Documents

- [Security Findings](SECURITY-FINDINGS.md) - 72 issues from Red/Blue team
- [NFR](../prd/nfr.md) - Security requirements
- [Architecture](../trd/architecture.md) - RLS philosophy
