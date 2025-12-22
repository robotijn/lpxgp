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

- All data encrypted at rest (Supabase default)
- All traffic over HTTPS
- JWT tokens with 1 hour expiry
- Refresh tokens with 7 day expiry
- Row-level security enforced
- Input validation on all endpoints
- Rate limiting: 100 req/min per user
- Audit logging for sensitive actions
- No sensitive data in logs

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
