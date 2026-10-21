# Backend

## Run locally

Set a private key for signing login cookies, then start the API from `BACKEND/`:

```bash
export JWT_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
uv run uvicorn main:app --reload --port 4020
```

The API creates the SQLite tables in `DATABASE/practice.db` when it starts. Local
HTTP uses a non-secure cookie by default. Set `COOKIE_SECURE=true` when serving
the API over HTTPS.

## User authentication

- `POST /api/users/register` accepts a username, email, and password.
- `POST /api/users/login` accepts an email, password, and `clientType` of `web` or `mobile`.
- Web login stores the JWT in an HTTP-only cookie.
- Mobile login returns the JWT as `accessToken` for Expo SecureStore.
- `POST /api/users/logout` clears the web login cookie.
- `GET /api/users/me` accepts the web cookie or a mobile Bearer token.

Passwords are stored as salted bcrypt hashes. Mobile clients send the saved JWT
as `Authorization: Bearer <accessToken>` when calling protected endpoints.

`clientType` selects how the token is returned; it does not prove that a request
came from a native app. Expo logs out locally with
`SecureStore.deleteItemAsync("accessToken")`. Clearing either the cookie or the
SecureStore item does not revoke the JWT, which remains valid until it expires.
