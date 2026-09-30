# Vigia

AI-powered life assistant backend. Processes events from integrations (Gmail, Calendar, Slack) through an LLM agent, routes actions requiring approval, and exposes a REST API for the dashboard.

## Tech Stack

- **Backend**: Django 6.x + Django REST Framework + drf-spectacular
- **Auth**: JWT (SimpleJWT) + Social Auth (Google OAuth via django-allauth)
- **Async Tasks**: Celery + Redis (Upstash)
- **AI**: LangGraph + LangChain + Groq (Llama 3.1 8B)
- **Database**: PostgreSQL (production) / SQLite (dev)
- **Real-time**: Django Channels

## Project Structure

```
vigia/
├── core/                  # Project settings, WSGI/ASGI, Celery
├── agents/                # Event/Task/Approval models + LangGraph agent + Celery tasks
├── dashboard/             # REST API views, serializers, URL routing
├── integrations/          # Integration & OAuthConnection models
├── common/                # Shared base model + health check
└── manage.py
```

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt   # or use the venv already present

# 2. Copy environment variables
cp .env.example .env              # already present as .env

# 3. Run migrations
python manage.py makemigrations
python manage.py migrate

# 4. Start the server
python manage.py runserver
```

## API

Base URL: `http://localhost:8000/api/`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/token/` | No | Get JWT access + refresh token |
| POST | `/token/refresh/` | No | Refresh access token |
| GET | `/auth/user/` | JWT | Current user ("you are") |
| GET | `/events/` | JWT | List user's events (each with a denormalized `activity` record) |
| POST | `/events/` | JWT | Create an event (triggers Celery task) |
| GET | `/tasks/` | JWT | List agent tasks |
| GET | `/approvals/` | JWT | List approval requests (`?pending=true` to filter) |
| POST | `/approvals/{id}/respond/` | JWT | Approve or reject an action |
| GET | `/health/` | No | Health check |

### Authentication

```bash
# Get token
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"your-username","password":"your-password"}'

# Use token
curl -H "Authorization: Bearer <access-token>" \
  http://localhost:8000/api/events/
```

`POST /api/token/` returns `{"access": "...", "refresh": "..."}`. Send the access
token as `Authorization: Bearer <access>`. Access tokens live 30 minutes; refresh
tokens live 7 days and are rotated + blacklisted on use, so always send the
**latest** refresh token back to `/api/token/refresh/`.

### CORS

The API responds to CORS preflights (`OPTIONS`) on every `/api/*` path. The
frontend origin must be on the allowlist — set it in the environment:

| Variable | Description |
|----------|-------------|
| `FRONTEND_URL` | Primary frontend origin, e.g. `https://app.vigia.dev` |
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of extra allowed origins |

The response headers returned to the browser are:

```
Access-Control-Allow-Origin: https://app.vigia.dev
Access-Control-Allow-Methods: DELETE, GET, OPTIONS, PATCH, POST, PUT
Access-Control-Allow-Headers: accept, accept-encoding, authorization, content-type, dnt, origin, user-agent, x-csrftoken, x-requested-with
Access-Control-Allow-Credentials: true
Vary: Origin
Access-Control-Max-Age: 86400
```

Local dev origins (`localhost:5173`, `:8080`, `:8081`, `:3000`) are allowed by default.

### Approvals

`GET /api/approvals/` items carry everything the UI renders; all of it is
read-only except via `respond/`:

```json
{
  "id": "…",
  "title": "Pay January invoice",
  "intent": "Settle the January invoice before it goes to collections",
  "recipient": "billing@vendor.com",
  "channel": "banking",
  "risk": "high",
  "confidence": 0.87,
  "expires_in_minutes": 1440,
  "reasoning": ["Involves an outbound money transfer"],
  "draft": "Wire $420 to billing@vendor.com",
  "side_effects": ["Funds leave the account immediately"],
  "message": "…",
  "approved": null,
  "responded_at": null,
  "created_at": "…"
}
```

- `channel` is one of `gmail`, `calendar`, `slack`, `banking`, `contacts`.
- `risk` is one of `low`, `medium`, `high`.
- `approved` is `null` while pending, then `true`/`false`.
- `?pending=true` returns only undecided requests; `?pending=false` returns only
  decided ones. `?status=pending|approved|declined` also works.
- `?search=` matches title/intent/recipient/draft/message; `?ordering=` accepts
  `created_at`, `responded_at`, `risk`.

Deciding an approval:

```bash
curl -X POST http://localhost:8000/api/approvals/<id>/respond/ \
  -H "Authorization: Bearer <access>" \
  -H "Content-Type: application/json" \
  -d '{"approved": true, "message": "Looks good"}'
```

Responds `400` without `approved`, `409` if already decided, and returns the
updated approval object. An optional `message` is appended to `message` as a
decision note rather than overwriting the agent's summary.

### Activity

`GET /api/events/` exposes a denormalized `activity` object per event, derived
from its tasks and approvals — the feed the dashboard can render directly:

```json
{
  "id": "…",
  "time": "2026-01-08T10:00:00Z",
  "created_at": "2026-01-08T10:00:00Z",
  "channel": "banking",
  "outcome": "approved",
  "title": "Pay January invoice",
  "detail": "Wire $420 to billing@vendor.com"
}
```

`outcome` is one of `autonomous` (agent acted without approval), `approved`,
`declined`, or `observed` (noted but not yet acted on).

### Connections

No backend endpoint — connection state is currently static frontend config.


## Swagger Docs

Interactive API documentation at `/api/docs/`.

## Celery

```bash
# Start Celery worker
celery -A core.celery worker -l info

# Start Celery beat (for periodic tasks)
celery -A core.celery beat -l info
```

## Tests

```bash
python manage.py test
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Django secret key |
| `DEBUG` | Yes | Enable debug mode |
| `DB_NAME` | Yes | Database name |
| `DB_USER` | Yes | Database user |
| `DB_PASSWORD` | Yes | Database password |
| `DB_HOST` | Yes | Database host |
| `DB_PORT` | Yes | Database port |
| `CELERY_BROKER_URL` | Yes | Celery broker URL |
| `CELERY_RESULT_BACKEND` | Yes | Celery result backend |
| `GROQ_API_KEY` | Yes | Groq API key for LLM |
| `SENTRY_DSN` | No | Sentry DSN for error tracking |
| `GOOGLE_OAUTH_CLIENT_ID` | No | Google OAuth client ID |
| `GOOGLE_OAUTH_CLIENT_SECRET` | No | Google OAuth client secret |
| `FRONTEND_URL` | No | Primary frontend origin allowed by CORS |
| `CORS_ALLOWED_ORIGINS` | No | Comma-separated extra CORS origins |

## License

MIT