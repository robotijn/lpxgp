---
description: Review code quality for Python/FastAPI standards
allowed-tools: Read, Grep, Glob, Bash
---

Review the code in: $ARGUMENTS (file path or directory)

## Review Checklist

### Python Standards
- [ ] Type hints on all public functions
- [ ] Google-style docstrings where needed
- [ ] Using `pathlib.Path` over `os.path`
- [ ] Async/await for I/O operations
- [ ] Pydantic models for request/response

### Security
- [ ] No hardcoded secrets or credentials
- [ ] Input validation on user data
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention in templates
- [ ] No command injection vulnerabilities

### FastAPI Patterns
- [ ] Proper HTTP status codes
- [ ] Dependency injection where appropriate
- [ ] Error handling with HTTPException
- [ ] Request/response models documented

### Code Quality
- [ ] Functions under 50 lines
- [ ] Clear variable naming
- [ ] No duplicate code
- [ ] Proper error handling

## Actions

1. Run `uv run ruff check <path>` for linting
2. Check imports and dependencies
3. Look for TODO/FIXME comments
4. Identify potential improvements

## Output

Provide:
1. Issues found (categorized by severity)
2. Suggested fixes with code examples
3. Overall assessment (Good/Needs Work/Critical Issues)

If no path provided, review recent changes with `git diff`.
