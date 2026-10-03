# WatchMe

A lightweight personal watchlist and discovery app. Search for movies and TV shows, pick the exact one you mean, save it, and receive interesting notifications to nudge you to finally watch it.

## Architecture

```
┌──────────────────────────────────────────────────────┐
│              Angular + Ionic + Capacitor              │
│         (Mobile / PWA Frontend)                      │
│                                                      │
│  • Watchlist Screen    • Search Screen               │
│  • Item Detail Screen  • Item Screen                 │
│  • Local SQLite        • Push notification listener  │
└──────────────────┬───────────────────────────────────┘
                   │ REST (HTTP/JSON)
                   ▼
┌──────────────────────────────────────────────────────┐
│                 FastAPI Backend                       │
│                                                      │
│  /api/search        /api/watchlist                   │
│  /api/devices       /api/notifications               │
│                                                      │
│  ┌──────────────┐  ┌────────────┐  ┌─────────────┐  │
│  │ Metadata     │  │ Notif.     │  │ Push        │  │
│  │ Provider     │  │ Generator  │  │ Provider    │  │
│  │ (TMDB)       │  │ (Groq/TPL) │  │ (FCM)       │  │
│  └──────┬───────┘  └─────┬──────┘  └──────┬──────┘  │
│         │               │                 │          │
│         ▼               ▼                 ▼          │
│       TMDB API       Groq API         Firebase      │
│  ┌──────────────────────────────────────────────┐   │
│  │              APScheduler                     │   │
│  │  (generates+sends notifications periodically) │   │
│  └──────────────────────────────────────────────┘   │
└──────────────────┬───────────────────────────────────┘
                   │ SQLAlchemy (asyncpg)
                   ▼
┌──────────────────────────────────────────────────────┐
│                   PostgreSQL                         │
│                                                      │
│  media_item        watchlist_item                    │
│  device            notification_event                │
└──────────────────────────────────────────────────────┘
```

## External Services

| Service | Purpose | Free Tier |
|---------|---------|-----------|
| **TMDB** | Movie/TV search & metadata | Free with attribution ([terms](https://www.themoviedb.org/api-terms-of-use)) |
| **Groq** | AI notification generation | Free tier: 6,000 tokens/min, 500K tokens/day on llama-3.3-70b |
| **Firebase FCM** | Push notifications (Android) | Free (Spark plan, no daily limit for FCM) |
| **PostgreSQL** | Structured data storage | Free self-hosted / Neon free tier (0.5 GB) |

> **Attribution**: This product uses the TMDB API but is not endorsed or certified by TMDB.

## Prerequisites

- **Python 3.12+** and [`uv`](https://docs.astral.sh/uv/) (backend)
- **Node.js 20+** and `npm` (frontend)
- **Docker** (for local PostgreSQL, or use any Postgres instance)
- A free [TMDB API key](https://www.themoviedb.org/settings/api)
- *(Optional)* A free [Groq API key](https://console.groq.com)
- *(Optional)* Firebase project + service account JSON (for push notifications)

## Quick Start

### 1. Start PostgreSQL

```bash
docker compose up -d db
```

Or use any local/cloud PostgreSQL instance and update `DATABASE_URL` in `.env`.

### 2. Backend Setup

```bash
cd backend

# Copy and edit environment file
cp .env.example .env
# → Set TMDB_API_KEY (required)
# → Set GROQ_API_KEY (optional, enables AI notifications)
# → Set FCM_CREDENTIALS_PATH (optional, enables push)

# Install dependencies with uv
uv sync

# Run database migrations
uv run alembic upgrade head

# Start the dev server
uv run uvicorn app.main:app --reload --port 8000
```

Backend runs at: http://localhost:8000  
API docs at: http://localhost:8000/docs

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run ionic:serve
```

Frontend runs at: http://localhost:8100

### 4. Run on Android

```bash
cd frontend
npm run build
npx cap sync android
npx cap open android
```

## Development Tips

### Test notifications immediately

```bash
# Generate a test notification for a device (requires DEBUG=true in .env)
curl -X POST http://localhost:8000/api/notifications/test \
  -H "Content-Type: application/json" \
  -d '{"device_id": "your-device-id"}'
```

### Speed up notification scheduler for testing

Set in `.env`:
```
DEBUG=true
NOTIFICATION_INTERVAL_SECONDS=60
```

### Mock mode (no API keys)

The app runs without TMDB/Groq/FCM keys:
- Without `TMDB_API_KEY`: search returns empty results (logs a warning)
- Without `GROQ_API_KEY`: falls back to deterministic template notifications
- Without `FCM_CREDENTIALS_PATH`: notifications are generated but not sent (logged only)

## Project Structure

```
WatchMe/
├── docker-compose.yml       # PostgreSQL only
├── README.md
├── backend/
│   ├── pyproject.toml       # uv/hatchling project config
│   ├── .env.example
│   ├── alembic.ini
│   ├── alembic/             # DB migrations
│   └── app/
│       ├── main.py          # FastAPI app + lifespan
│       ├── config.py        # Pydantic settings
│       ├── api/             # Route handlers
│       ├── models/          # SQLAlchemy ORM models
│       ├── schemas/         # Pydantic request/response schemas
│       ├── services/        # Business logic + provider abstractions
│       │   ├── metadata/    # MetadataProvider (TMDB)
│       │   ├── notifications/ # NotificationGenerator (Groq + template)
│       │   ├── push/        # PushNotificationProvider (FCM)
│       │   └── search/      # WebSearchService (DuckDuckGo)
│       ├── db/              # SQLAlchemy session
│       └── scheduler/       # APScheduler jobs
└── frontend/
    ├── package.json
    ├── capacitor.config.ts
    └── src/app/
        ├── core/
        │   ├── services/    # API, watchlist, device, notifications
        │   └── models/      # TypeScript interfaces
        ├── pages/
        │   ├── watchlist/   # Main watchlist screen
        │   ├── search/      # Search + results
        │   ├── item-detail/ # Search result detail + Add to Watchlist
        │   └── item/        # Watchlist item detail + notes
        └── shared/          # MediaCard component
```

## API Reference

### Search
```
GET /api/search?q={query}&type={movie|tv|all}
```
Returns 5–10 candidates. Never assumes which one the user means.

### Watchlist
```
GET    /api/watchlist?device_id={id}
POST   /api/watchlist              body: { provider, providerId, mediaType, deviceId }
DELETE /api/watchlist/{id}?device_id={id}
POST   /api/watchlist/{id}/watched?device_id={id}
POST   /api/watchlist/{id}/unwatched?device_id={id}
```

### Devices
```
POST /api/devices/register         body: { deviceId, platform, pushToken }
```

### Notifications
```
GET  /api/notifications?device_id={id}
POST /api/notifications/test       body: { device_id, watchlist_item_id? }
```

## Running Tests

### Backend
```bash
cd backend
uv run pytest -v
```

### Frontend
```bash
cd frontend
npm test
```

## V1 Scope — What's NOT included

The following are explicitly out of scope for V1:

- User accounts / authentication / OAuth
- Social features (friends, ratings, reviews, comments)
- Streaming availability / watch providers
- Release reminders / episode tracking
- ML recommendations / embeddings / vector DB
- Redis, Kafka, Celery, Elasticsearch
- Paid APIs or infrastructure

## License

MIT
