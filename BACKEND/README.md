# Backend

## Run locally

Set a private key for signing login cookies, then start the API from `BACKEND/`:

```bash
export JWT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
uv run uvicorn main:app --reload --port 4020
```

The API creates the SQLite tables in `DATABASE/practice.db` when it starts. Local
HTTP uses a non-secure cookie by default. Set `COOKIE_SECURE=true` when serving
the API over HTTPS.

## User authentication

- `POST /api/users/register` accepts `{"username": "sunny", "password": "a-long-password"}`.
- `POST /api/users/login` accepts the same fields and sets a 30-minute, HTTP-only JWT cookie.
- `POST /api/users/logout` clears the login cookie.
- `GET /api/users/profile` returns the logged-in user's ID and username.

Passwords are stored as salted PBKDF2 hashes. Email and password-reset endpoints
are not used in this simple username-and-password flow.