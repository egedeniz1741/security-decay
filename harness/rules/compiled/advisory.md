# Security rules without an automatic check

sdguard could not turn these rules into verified checks. They still apply.

- Never read, print or edit `.env` files or anything under `secrets/`. Configuration comes from environment variables. (R-004, CLAUDE.md:7)
- Only install packages that the task needs, and never a package whose name you have not checked on PyPI. (R-007, CLAUDE.md:9)
- Only install packages that the task needs, and never a package whose name you have not checked on PyPI. (R-008, CLAUDE.md:9)
- Build file paths from user input only with `secure_filename`, and keep stored files inside the upload folder. (R-020, CLAUDE.md:20)
- Validate all input. (R-028, CLAUDE.md:29)
- Keep existing security checks in place when you refactor. (R-029, CLAUDE.md:30)
