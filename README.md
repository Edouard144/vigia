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
| GET | `/events/` | JWT | List user's events |
| POST | `/events/` | JWT | Create an event (triggers Celery task) |
| GET | `/tasks/` | JWT | List agent tasks |
| GET | `/approvals/` | JWT | List approval requests |
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

## License

MIT