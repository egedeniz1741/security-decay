---
owner: platform-team
---
# Payments service

Use `black` and `ruff` before every commit.

## Security

- Never read the `.env` file or print its values.
- Do not use `eval` or `exec` on anything.
- Error responses must not show stack traces
  to the caller.
- Follow security best practices.

```python
# example, not a rule: password = "hunter2"
```

| Do | Don't |
|----|-------|
| parameterize | concatenate |
