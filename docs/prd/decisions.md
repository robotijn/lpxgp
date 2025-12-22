# Decisions Log

[← Back to Index](index.md)

---

| # | Decision | Options Considered | Rationale |
|---|----------|-------------------|-----------|
| 1 | Supabase Cloud | Self-hosted, Cloud | Faster setup, managed backups, reliable |
| 2 | Voyage AI for embeddings | OpenAI, Cohere, Open source | Best quality for financial domain |
| 3 | Priority A→B→C | Various orders | Search is foundation, then matching, then output |
| 4 | PDF supplement approach | Modify PDF, Generate new | Keep original intact, generate addendum |
| 5 | pgvector for vectors | Pinecone, Weaviate | Integrated with Supabase, no extra service |
| 6 | CDN for frontend, supabase-py for database | npm/bundler, SQLAlchemy | Minimize build tools and dependencies for faster iteration |

---

[Next: Appendix →](appendix.md)
