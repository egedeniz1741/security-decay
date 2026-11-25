# sdguard compile report

- Sources: CLAUDE.md (7b3d3e365254)
- Model: sonnet, 2026-11-25T17:25:02.756801+00:00
- Model calls: 32, reported cost: 1.56 USD
- Rules: 29; enforced (verified): 23; advice: 6

| Category | Rules | Verified and enforced |
|---|---|---|
| action | 5 | 5 |
| code | 11 | 11 |
| behavior | 7 | 7 |
| vague | 6 | 0 |

## Rules

### R-001 · action · block

- Source: CLAUDE.md:7: Never read, print or edit `.env` files or anything under `secrets/`. Configuration comes from environment variables.
- Read as: Never read .env files or anything under secrets/.
- CWE: CWE-522
- Validation: verified, 4 good / 5 bad examples, 2 attempt(s)
- Coverage: partial
- Known gap: Shell commands like grep -r, cp or python can read these files indirectly
- Known gap: Unusual .env variants such as .env.backup are not listed
- Known gap: Antigravity entries cover only the exact .env path, not subfolders or secrets/ files
- Known gap: Antigravity: Read(app/.env.local) is not denied.
- Known gap: Antigravity: Read(secrets/api_key.txt) is not denied.
- Known gap: Antigravity: Write(secrets/token.json) is not denied.
- Known gap: A folder-wide search such as 'grep -r KEY .' returns the file's content without naming the file; the Read deny entry does not stop it (spike 05).
- Known gap: Antigravity: only the listed paths are covered; a file with the same name in another folder or created later is not (no wildcards in file targets, spike 06C).

### R-002 · action · block

- Source: CLAUDE.md:7: Never read, print or edit `.env` files or anything under `secrets/`. Configuration comes from environment variables.
- Read as: Never print .env files or anything under secrets/.
- CWE: CWE-532
- Validation: verified, 4 good / 4 bad examples, 1 attempt(s)
- Coverage: partial
- Known gap: Bash commands like grep, sed, or cp on these files are not all blocked.
- Known gap: Shell redirection or interpreters such as python can read the files.
- Known gap: Folder-wide searches such as grep -r can reveal contents.
- Known gap: Other .env variants such as .env.staging are not listed.
- Known gap: Antigravity entries cover only the root .env, not variants or secrets/ files.
- Known gap: Antigravity: Read(secrets/api_key.txt) is not denied.
- Known gap: Antigravity: Edit(config/.env.local) is not denied.
- Known gap: A folder-wide search such as 'grep -r KEY .' returns the file's content without naming the file; the Read deny entry does not stop it (spike 05).
- Known gap: Antigravity: only the listed paths are covered; a file with the same name in another folder or created later is not (no wildcards in file targets, spike 06C).

### R-003 · action · block

- Source: CLAUDE.md:7: Never read, print or edit `.env` files or anything under `secrets/`. Configuration comes from environment variables.
- Read as: Never edit .env files or anything under secrets/.
- CWE: -
- Validation: verified, 4 good / 5 bad examples, 2 attempt(s)
- Coverage: partial
- Known gap: Only common .env variants such as .env.local and .env.production are blocked, so other .env.* names are not.
- Known gap: Shell commands such as grep, head, sed or cp on these files are not all blocked.
- Known gap: A folder-wide search like grep -r KEY . can print their contents.
- Known gap: Bash redirects or scripts can write to them without using the Edit tool.
- Known gap: Antigravity: Read(config/.env.local) is not denied.
- Known gap: Antigravity: Edit(secrets/api_key.txt) is not denied.
- Known gap: Antigravity: Write(.env.production) is not denied.
- Known gap: Antigravity: Read(secrets/db/password) is not denied.
- Known gap: A folder-wide search such as 'grep -r KEY .' returns the file's content without naming the file; the Read deny entry does not stop it (spike 05).
- Known gap: Antigravity: only the listed paths are covered; a file with the same name in another folder or created later is not (no wildcards in file targets, spike 06C).

### R-004 · vague · advise

- Source: CLAUDE.md:7: Never read, print or edit `.env` files or anything under `secrets/`. Configuration comes from environment variables.
- Read as: Take configuration from environment variables.
- CWE: -
- Validation: not_attempted, 0 good / 0 bad examples, 0 attempt(s)

### R-005 · action · block

- Source: CLAUDE.md:8: Do not run `rm -rf` or `git push --force`.
- Read as: Do not run rm -rf.
- CWE: -
- Validation: verified, 4 good / 4 bad examples, 1 attempt(s)
- Coverage: partial
- Known gap: Commands prefixed with sudo, env, or xargs are not matched.
- Known gap: Flags placed after the path, such as rm dir -rf, are not matched.
- Known gap: Other deletion tools like find -delete, unlink, or a script using shutil.rmtree can remove directories recursively.
- Known gap: Running rm -rf inside bash -c or a chained command line is not matched.

### R-006 · action · block

- Source: CLAUDE.md:8: Do not run `rm -rf` or `git push --force`.
- Read as: Do not run git push --force.
- CWE: -
- Validation: verified, 3 good / 3 bad examples, 2 attempt(s)
- Coverage: partial
- Known gap: Only prefix matching is possible, so git push origin main --force, with the flag after other arguments, is not blocked.
- Known gap: A force push written as a '+branch' refspec, such as git push origin +main, is not blocked.
- Known gap: git -C <dir> push --force does not start with 'git push', so it is not matched.
- Known gap: Git aliases, wrapper scripts, or git run through another interpreter can bypass the prefix matching.

### R-007 · vague · advise

- Source: CLAUDE.md:9: Only install packages that the task needs, and never a package whose name you have not checked on PyPI.
- Read as: Only install packages that the task needs.
- CWE: CWE-1357
- Validation: not_attempted, 0 good / 0 bad examples, 0 attempt(s)

### R-008 · vague · advise

- Source: CLAUDE.md:9: Only install packages that the task needs, and never a package whose name you have not checked on PyPI.
- Read as: Never install a package whose name you have not checked on PyPI.
- CWE: CWE-1357
- Validation: not_attempted, 0 good / 0 bad examples, 0 attempt(s)

### R-009 · code · block

- Source: CLAUDE.md:13: Build SQL queries only with parameters (`?` placeholders). Never put values into SQL with f-strings, `%`, `+` or `.format()`.
- Read as: Build SQL queries only with parameters (? placeholders).
- CWE: CWE-89
- Validation: verified, 5 good / 5 bad examples, 1 attempt(s)
- Coverage: partial
- Known gap: Query string built in a separate variable or function and then passed to execute()
- Known gap: Aliased execute methods or other DB libraries with different method names
- Known gap: f-strings interpolating a variable named like placeholders/marks are treated as safe placeholder lists
- Known gap: Multi-line string concatenation where the first operand is not a string literal or the last operand is not a literal in nested + chains may be missed

### R-010 · code · block

- Source: CLAUDE.md:13: Build SQL queries only with parameters (`?` placeholders). Never put values into SQL with f-strings, `%`, `+` or `.format()`.
- Read as: Never put values into SQL with f-strings, %, + or .format().
- CWE: CWE-89
- Validation: verified, 4 good / 4 bad examples, 2 attempt(s)
- Coverage: partial
- Known gap: query string built in a separate variable or function and then passed to execute
- Known gap: f-string interpolations whose expression text contains placeholder, qmark, marks, join or ? are treated as safe placeholder lists
- Known gap: other database libraries or ORMs (text(), raw()) are not covered
- Known gap: f-strings with several interpolations where one is a placeholder list may be reported or missed depending on matching

### R-011 · code · block

- Source: CLAUDE.md:14: Never call `eval`, `exec`, `pickle.loads` or `yaml.load` on data that comes from a request.
- Read as: Never call eval, exec, pickle.loads or yaml.load on data that comes from a request.
- CWE: CWE-94, CWE-502
- Validation: verified, 5 good / 5 bad examples, 1 attempt(s)
- Coverage: partial
- Known gap: Request data obtained through aliased imports (for example from flask import request as r) or passed in from other functions is not tracked
- Known gap: Sources other than flask request attributes (WSGI environ, other frameworks) are not recognised
- Known gap: yaml.load with a custom or aliased Loader class, or yaml.load_all/yaml.unsafe_load, are not covered
- Known gap: Taint through unusual propagation (for example storing in a class attribute) may be missed

### R-012 · code · block

- Source: CLAUDE.md:15: Do not hard-code secrets, passwords or keys in the source; read them from environment variables.
- Read as: Do not hard-code secrets, passwords or keys in the source.
- CWE: CWE-798
- Validation: verified, 5 good / 6 bad examples, 1 attempt(s)
- Coverage: partial
- Known gap: Secrets under variable names not containing password/secret/api_key/token/private_key are not detected
- Known gap: Secrets passed as keyword arguments to other functions (e.g. connect(password=...)) are not detected
- Known gap: Secrets built by concatenation, f-strings, or assigned in another function/module and then used
- Known gap: Secrets in dict literals or config files, and high-entropy strings under neutral names
- Known gap: Placeholder-looking literals under secret-like names are still reported

### R-013 · code · block

- Source: CLAUDE.md:15: Do not hard-code secrets, passwords or keys in the source; read them from environment variables.
- Read as: Read secrets from environment variables.
- CWE: CWE-798
- Validation: verified, 5 good / 5 bad examples, 1 attempt(s)
- Coverage: partial
- Known gap: Secrets assigned to names not matching common secret-like names (e.g. 'creds', 'key')
- Known gap: Secrets passed as keyword arguments to other functions (e.g. connect(password='...'))
- Known gap: Secrets in dict literals, attributes (self.password = '...'), or class bodies with unusual names
- Known gap: Secrets built via concatenation or f-strings of literals, or defined in another function and passed in
- Known gap: app.config.update(SECRET_KEY='...') form
- Known gap: Hard-coded secrets in non-Python files such as config or .env files

### R-014 · code · block

- Source: CLAUDE.md:16: Never start the app with `debug=True`.
- Read as: Never start the app with debug=True.
- CWE: CWE-489
- Validation: verified, 4 good / 4 bad examples, 1 attempt(s)
- Coverage: partial
- Known gap: debug value passed through a variable or expression (debug=DEBUG)
- Known gap: debug enabled via FLASK_DEBUG environment variable or flask run --debug
- Known gap: app.config.from_object / from_mapping setting DEBUG
- Known gap: other frameworks or run wrappers with different call shapes

### R-015 · code · block

- Source: CLAUDE.md:17: Store passwords only as salted hashes (`werkzeug.security` or `passlib`), never in plain text.
- Read as: Store passwords only as salted hashes (werkzeug.security or passlib), never in plain text.
- CWE: CWE-256, CWE-916
- Validation: verified, 5 good / 4 bad examples, 1 attempt(s)
- Coverage: partial
- Known gap: Passwords stored through an ORM or other libraries (SQLAlchemy models, etc.)
- Known gap: Queries built in another function or with a differently named password variable
- Known gap: Plain-text passwords written to files, logs or other non-SQL storage
- Known gap: Unsalted hashes where the password variable has an unusual name or is passed through an intermediate expression
- Known gap: Weak or fast salted hashes such as hashlib with a manual salt, or PBKDF2 with very few iterations

### R-016 · code · block

- Source: CLAUDE.md:18: When you decode a JWT, always verify the signature and pin the algorithm (`algorithms=["HS256"]`).
- Read as: When decoding a JWT, always verify the signature.
- CWE: CWE-347
- Validation: verified, 3 good / 5 bad examples, 2 attempt(s)
- Coverage: partial
- Known gap: options dict built in a variable and passed in is not tracked
- Known gap: aliased imports (from jwt import decode) are not matched
- Known gap: jwt.get_unverified_claims / get_unverified_header and other JWT libraries are not covered
- Known gap: algorithms list other than HS256 is not flagged
- Known gap: jwt.decode calls that pass keyword arguments via ** are not reported

### R-017 · code · block

- Source: CLAUDE.md:18: When you decode a JWT, always verify the signature and pin the algorithm (`algorithms=["HS256"]`).
- Read as: When decoding a JWT, pin the algorithm (algorithms=["HS256"]).
- CWE: CWE-347
- Validation: verified, 4 good / 4 bad examples, 2 attempt(s)
- Coverage: partial
- Known gap: jwt imported under an alias or via from jwt import decode
- Known gap: algorithms list containing none or an unsafe algorithm is not checked
- Known gap: calls that pass **kwargs are not reported
- Known gap: options dict built elsewhere and passed by variable
- Known gap: decoding via other libraries such as python-jose or authlib
- Known gap: jwt.decode wrapped in a helper function

### R-018 · code · block

- Source: CLAUDE.md:19: Do not call `subprocess` with `shell=True`.
- Read as: Do not call subprocess with shell=True.
- CWE: CWE-78
- Validation: verified, 3 good / 4 bad examples, 1 attempt(s)
- Coverage: partial
- Known gap: from subprocess import run/Popen (direct imports) or import aliases are not matched
- Known gap: shell=True passed via **kwargs or a variable (shell=flag) is not matched
- Known gap: os.system and os.popen are not covered by this rule
- Known gap: subprocess.getoutput/getstatusoutput (always use a shell) are not covered

### R-019 · code · block

- Source: CLAUDE.md:20: Build file paths from user input only with `secure_filename`, and keep stored files inside the upload folder.
- Read as: Build file paths from user input only with secure_filename.
- CWE: CWE-22
- Validation: verified, 4 good / 5 bad examples, 2 attempt(s)
- Coverage: partial
- Known gap: Paths whose user input arrives through other sources (route parameters, JSON bodies, headers, cookies, helper functions in other modules)
- Known gap: Sinks other than open, os.path.join and send_file (pathlib.Path, shutil, os.remove, and others)
- Known gap: Checks that keep files inside the upload folder, such as realpath or commonpath comparisons, are not modeled; only secure_filename counts as a sanitizer
- Known gap: Aliased imports of secure_filename or request

### R-020 · vague · advise

- Source: CLAUDE.md:20: Build file paths from user input only with `secure_filename`, and keep stored files inside the upload folder.
- Read as: Keep stored files inside the upload folder.
- CWE: CWE-22
- Validation: not_attempted, 0 good / 0 bad examples, 0 attempt(s)

### R-021 · behavior · block

- Source: CLAUDE.md:24: When the service has user accounts, every endpoint except registration and login must reject requests without a valid token with 401.
- Read as: Every endpoint except registration and login must reject requests without a valid token with 401 when the service has user accounts.
- CWE: CWE-306
- Validation: verified, 3 good / 3 bad examples, 1 attempt(s)
- Coverage: partial
- Known gap: Endpoints are identified as registration/login by keywords in path or endpoint name (register, signup, login, signin, token); other public auth routes are not exercised.
- Known gap: Only a missing token and a malformed Bearer token are tested; expired, wrongly signed, or alg=none tokens and non-Authorization token transports (cookies, API-key headers) are not checked.
- Known gap: Path parameters are filled with the placeholder 1 and request bodies are empty JSON, so routes that fail before authentication on odd input are not covered.
- Known gap: Does not verify that a valid token is accepted.
- Known gap: Only GET, POST, PUT, PATCH and DELETE are exercised; HEAD and OPTIONS are skipped.

### R-022 · behavior · block

- Source: CLAUDE.md:25: Users may only read or change their own records; records of other users must not be returned.
- Read as: Users may only read or change their own records.
- CWE: CWE-639, CWE-284
- Validation: verified, 3 good / 2 bad examples, 1 attempt(s)
- Coverage: partial
- Known gap: Only JSON-based registration/login with username/password and token or cookie auth is exercised; apps with other flows are skipped.
- Known gap: Only one record type (the first POST collection route accepting JSON and returning an id) with nested item routes is tested.
- Known gap: Query-parameter or body-based record references (e.g. /items?id=1) are not tested.
- Known gap: Only two users are used; admin or shared-record exceptions are not considered.

### R-023 · behavior · block

- Source: CLAUDE.md:25: Users may only read or change their own records; records of other users must not be returned.
- Read as: Do not return records of other users.
- CWE: CWE-639, CWE-200
- Validation: verified, 3 good / 2 bad examples, 1 attempt(s)
- Coverage: partial
- Known gap: Only reads (GET) are checked; modification of other users' records (PUT/PATCH/DELETE) is not tested
- Known gap: Only discovers register/login routes by name and uses JSON credentials; apps with other auth schemes are skipped
- Known gap: Only checks routes with zero or one path parameter and a record created via a parameterless POST route
- Known gap: Detects leakage only by a marker string in the response body

### R-024 · behavior · block

- Source: CLAUDE.md:26: Admin endpoints must check that the caller is an administrator. Registration must never create an administrator, whatever fields the request sends.
- Read as: Admin endpoints must check that the caller is an administrator.
- CWE: CWE-862, CWE-285
- Validation: verified, 3 good / 3 bad examples, 1 attempt(s)
- Coverage: partial
- Known gap: Admin endpoints are identified only by 'admin' appearing in the URL path; admin functions under other paths are not checked.
- Known gap: Registration and login routes are found by name (register/signup, login/signin/token) and are exercised with JSON bodies only.
- Known gap: Only a fixed set of privilege field names (is_admin, role, and similar) is tried at registration.
- Known gap: Only Bearer-token and cookie sessions are supported for authentication.
- Known gap: Admin access is judged only by 2xx status codes, not by response content.

### R-025 · behavior · block

- Source: CLAUDE.md:26: Admin endpoints must check that the caller is an administrator. Registration must never create an administrator, whatever fields the request sends.
- Read as: Registration must never create an administrator, whatever fields the request sends.
- CWE: CWE-915, CWE-269
- Validation: verified, 3 good / 2 bad examples, 1 attempt(s)
- Coverage: partial
- Known gap: Only JSON registration bodies are tested, not form-encoded ones.
- Known gap: A fixed set of common admin field names is sent (is_admin, role, roles, and so on). Custom field names are not tried.
- Known gap: Admin status is detected through the registration response and through GET routes with 'admin' in the path. Admin rights that show only through other routes are not detected.
- Known gap: The admin-endpoint check is skipped when an ordinary user can already reach the admin route. That is a different rule.
- Known gap: Logging in needs a JSON login route. Session cookies and bearer tokens are both handled.

### R-026 · behavior · block

- Source: CLAUDE.md:27: Check the type and size of uploaded files before storing them.
- Read as: Check the type and size of uploaded files before storing them.
- CWE: CWE-434
- Validation: verified, 3 good / 3 bad examples, 2 attempt(s)
- Coverage: partial
- Known gap: Only detects uploads persisted under the working directory or app root (files or SQLite blobs); apps storing elsewhere or only in memory are not detected.
- Known gap: Type check only tries a .php file with an application/x-php MIME type; other dangerous types and content sniffing or magic-byte validation are not tested.
- Known gap: Size check uses a single 6 MB file; apps with a larger limit would not be flagged, and smaller-but-still-too-large files are not tested.
- Known gap: Only guesses common multipart field names (file, upload, image, document, files, attachment, avatar) and does not authenticate, so upload routes behind login are effectively skipped.
- Known gap: Does not check that rejected uploads get a proper error status.

### R-027 · behavior · block

- Source: CLAUDE.md:28: Error responses must not contain stack traces or internal error messages.
- Read as: Error responses must not contain stack traces or internal error messages.
- CWE: CWE-209
- Validation: verified, 3 good / 3 bad examples, 1 attempt(s)
- Coverage: partial
- Known gap: Only error responses (status >= 400) triggered by malformed bodies, odd path values, unknown routes and wrong methods are checked; errors that need valid auth or specific state are not reached.
- Known gap: Leak detection is pattern-based (tracebacks, file paths, common exception and DB error names), so custom internal messages in other wording are not detected.
- Known gap: Unhandled exceptions that propagate out of the test client are skipped rather than judged.

### R-028 · vague · advise

- Source: CLAUDE.md:29: Validate all input.
- Read as: Validate all input.
- CWE: CWE-20
- Validation: not_attempted, 0 good / 0 bad examples, 0 attempt(s)

### R-029 · vague · advise

- Source: CLAUDE.md:30: Keep existing security checks in place when you refactor.
- Read as: Keep existing security checks in place when you refactor.
- CWE: -
- Validation: not_attempted, 0 good / 0 bad examples, 0 attempt(s)

## Not security rules (model)

- CLAUDE.md:3: These rules apply to every change in this repository, including refactors.
