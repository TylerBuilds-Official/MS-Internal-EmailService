# Email Service

A small, reusable internal email service for Microsoft 365 tenants. It sends mail
through the [Microsoft Graph API](https://learn.microsoft.com/graph/api/user-sendmail)
using app-only authentication, and **restricts recipients to users in your tenant's
directory** so internal apps can't accidentally email the outside world.

Point it at any tenant with a handful of environment variables — no code changes
required.

## Features

- App-only auth via Microsoft Entra ID (MSAL client credentials flow)
- Sends mail as a dedicated service mailbox
- Recipient allow-listing: every `to` / `cc` / `bcc` address is checked against the
  tenant directory before sending
- `cc`, `bcc`, and file attachments
- Clear, typed exceptions for configuration, auth, Graph, and send failures
- Use it as a Python library **or** run the bundled FastAPI service (API-key-protected `POST /send`, public `/health`)

## Prerequisites

An Entra ID **app registration** with these *application* (not delegated) Microsoft
Graph permissions, admin-consented:

| Permission      | Why                                            |
| --------------- | ---------------------------------------------- |
| `Mail.Send`     | Send mail as the service mailbox               |
| `User.Read.All` | Read the directory to validate recipients      |

You will need the app's **client ID**, the **tenant ID**, a **client secret**, and the
**object ID** of the mailbox mail is sent from.

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` and fill in your tenant's values:

```bash
cp .env.example .env
```

| Variable          | Description                                                        |
| ----------------- | ------------------------------------------------------------------ |
| `CLIENT_ID`       | Application (client) ID of the app registration                    |
| `TENANT_ID`       | Directory (tenant) ID                                              |
| `CLIENT_SECRET`   | A client secret for the app registration                           |
| `SERVICE_USER_ID` | Object ID of the mailbox mail is sent *from* (use a service account) |
| `COMPANY_NAME`    | Org display name, shown in recipient-rejection messages            |
| `API_KEY`         | Shared secret required in the `X-API-Key` header (HTTP API only)   |
| `CORS_ORIGINS`    | Comma-separated allowed CORS origins (HTTP API only; default `*`)  |

`.env` is gitignored — never commit real secrets.

## Usage (as a library)

The package root is `src/`, so add it to your `PYTHONPATH` (or import from within
`src/`).

```python
from email_service.email_service import EmailService

es = EmailService()

# Basic send
es.send_email(
    to="person@yourcompany.com",
    subject="Build finished",
    body="The nightly build completed successfully.",
)

# With cc, bcc, and attachments
es.send_email(
    to="person@yourcompany.com",
    subject="Report",
    body="See attached.",
    cc=["lead@yourcompany.com", "qa@yourcompany.com"],
    bcc="archive@yourcompany.com",
    attachments=["reports/summary.pdf"],
)

# HTML body
es.send_email(
    to="person@yourcompany.com",
    subject="Release notes",
    body="<h1>v2.0</h1><p>Shipped today.</p>",
    body_type="HTML",
)
```

`to`, `cc`, and `bcc` accept either a single address string or a list. `attachments`
accepts file paths (read and base64-encoded for you) or dicts already in Graph
attachment format. `body_type` defaults to `"Text"`; pass `"HTML"` to send an HTML
body.

## Recipient validation

Before sending, every recipient is checked against the tenant directory. If any
`to` / `cc` / `bcc` address isn't an internal user, the send is rejected with
`InvalidRecipientError` and no mail goes out.

## Error handling

All errors raised by the service subclass `EmailServiceError`, so callers can catch
everything from the library with a single `except`, or handle specific failures:

| Exception              | Raised when                                                    |
| ---------------------- | -------------------------------------------------------------- |
| `EmailServiceError`    | Base class for all errors below                                |
| `ConfigurationError`   | A required environment variable is missing or blank            |
| `AuthenticationError`  | An access token could not be acquired from Entra ID            |
| `GraphApiError`        | A Graph request returned a non-2xx response (`.status_code`, `.response_text`) |
| `EmailSendError`       | The `sendMail` request specifically was rejected (subclass of `GraphApiError`) |
| `InvalidRecipientError`| A recipient is not an internal directory user                  |

```python
from email_service.email_service import EmailService
from _errors import EmailServiceError, InvalidRecipientError

es = EmailService()
try:
    es.send_email(to="external@example.com", subject="Hi", body="...")
except InvalidRecipientError as e:
    print(f"Blocked: {e}")
except EmailServiceError as e:
    print(f"Send failed: {e}")
```

## HTTP API

The repo also ships a thin FastAPI service that wraps the library. The package root
is `src/`, so run it with `--app-dir src`:

```bash
uvicorn main:app --app-dir src --host 0.0.0.0 --port 8000
# add --reload for local development
```

| Method & path | Auth | Description |
| ------------- | ---- | ----------- |
| `GET /health` | none | Liveness probe → `{"status": "ok"}` |
| `POST /send`  | `X-API-Key` header | Send an internal email (`multipart/form-data`) |

`POST /send` takes `multipart/form-data`. Repeat `to` / `cc` / `bcc` to add multiple
recipients, and attach files as repeated `files` parts:

```bash
curl -X POST http://localhost:8000/send \
  -H "X-API-Key: $API_KEY" \
  -F "to=person@yourcompany.com" \
  -F "to=lead@yourcompany.com" \
  -F "subject=Nightly report" \
  -F "body=See attached." \
  -F "body_type=Text" \
  -F "files=@report.pdf"
```

Responses: `200` `{"status":"sent","recipients":[...]}` on success; `400` for a
non-internal recipient; `401` for a bad/missing API key; `422` for a malformed
request; `502` for an upstream Microsoft Graph / auth failure.

Interactive docs are at `/docs` once the server is running.

### Deploying

This endpoint can send mail as your whole org, so before exposing it:

- Set a **strong, random `API_KEY`** (`python -c "import secrets; print(secrets.token_urlsafe(32))"`).
- Set **`CORS_ORIGINS`** to your real front-end origins — the `*` default is wide open.
- Point **`SERVICE_USER_ID`** at a dedicated service mailbox, not a personal account.
- Terminate **TLS** at a reverse proxy in front of the app (uvicorn isn't your edge).
- Optionally disable the docs in production by passing `docs_url=None, redoc_url=None`
  to `FastAPI(...)` in `build_api.py`.

## License

Released under the [MIT License](LICENSE).
