# Security rules

These rules apply to every change in this repository, including refactors.

## Working in the repository

- Never read, print or edit `.env` files or anything under `secrets/`. Configuration comes from environment variables.
- Do not run `rm -rf` or `git push --force`.
- Only install packages that the task needs, and never a package whose name you have not checked on PyPI.

## Code

- Build SQL queries only with parameters (`?` placeholders). Never put values into SQL with f-strings, `%`, `+` or `.format()`.
- Never call `eval`, `exec`, `pickle.loads` or `yaml.load` on data that comes from a request.
- Do not hard-code secrets, passwords or keys in the source; read them from environment variables.
- Never start the app with `debug=True`.
- Store passwords only as salted hashes (`werkzeug.security` or `passlib`), never in plain text.
- When you decode a JWT, always verify the signature and pin the algorithm (`algorithms=["HS256"]`).
- Do not call `subprocess` with `shell=True`.
- Build file paths from user input only with `secure_filename`, and keep stored files inside the upload folder.

## Behavior of the service

- When the service has user accounts, every endpoint except registration and login must reject requests without a valid token with 401.
- Users may only read or change their own records; records of other users must not be returned.
- Admin endpoints must check that the caller is an administrator. Registration must never create an administrator, whatever fields the request sends.
- Check the type and size of uploaded files before storing them.
- Error responses must not contain stack traces or internal error messages.
- Validate all input.
- Keep existing security checks in place when you refactor.
