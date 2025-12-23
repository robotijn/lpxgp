---
description: Explore and navigate the LPxGP codebase
allowed-tools: Glob, Grep, Read, Bash
---

Explore the codebase for: $ARGUMENTS (topic, file pattern, or question)

## Exploration Modes

### By Topic
- "authentication" - Find auth-related code
- "matching" - LP-Fund matching algorithm
- "agents" - AI agent implementations
- "database" - Supabase/PostgreSQL code
- "templates" - Jinja2/HTMX frontend

### By Pattern
- "*.py" - All Python files
- "test_*" - Test files
- "migrations/*" - Database migrations

### By Question
- "how does X work?" - Trace code flow
- "where is X defined?" - Find definitions
- "what calls X?" - Find usages

## Project Structure Quick Reference

```
src/
  main.py          - FastAPI app + routes
  config.py        - Settings/env vars
  templates/       - Jinja2 templates
  static/          - Images

tests/
  test_main.py     - pytest tests

supabase/
  migrations/      - SQL migrations

docs/
  prd/             - Product requirements
  architecture/    - Technical specs
  product-doc/     - PDF generation
```

## Output

Provide:
1. Relevant files found
2. Key code snippets
3. How components connect
4. Suggested next steps for deeper exploration

If no argument, show project overview and recent changes.
