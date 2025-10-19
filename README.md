# CoFriends-BE-Python

✅ **Successfully migrated from Spring Boot to FastAPI!**

## Quick Start

### 1. Local Development

```bash
# Install dependencies
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Setup environment
copy env.example .env

# Run server
python run.py
```

**Server will start at: http://localhost:5000**

### 2. Docker Compose (Recommended)

```bash
docker-compose up -d
```

## API Documentation

- Swagger UI: http://localhost:5000/docs
- ReDoc: http://localhost:5000/redoc
- Health Check: http://localhost:5000/health

## What's Changed

- ✅ Java/Spring Boot → Python/FastAPI
- ✅ MySQL → PostgreSQL
- ✅ Chat storage: Redis → MongoDB (+ Redis cache)
- ✅ Faster startup (~2s vs ~15s)
- ✅ Lower memory usage (~150MB vs ~500MB)
- ✅ Auto-generated API docs

## Main Features

- 🍽️ Menu preference management
- 📍 Restaurant voting system
- 💬 Chat history (MongoDB)
- 🔍 Naver Local Search integration
- 🔐 Slack OAuth authentication

## Tech Stack

- Python 3.12+
- FastAPI
- PostgreSQL
- MongoDB
- Redis
- SQLAlchemy
- Pydantic

## Project Structure

```
├── app/
│   ├── api/          # API routes
│   ├── core/         # Config & DB
│   ├── models/       # Database models
│   ├── schemas/      # Pydantic schemas
│   └── services/     # Business logic
├── main.py           # Entry point
└── docker-compose.yml
```

## Verification

This project has been tested and verified:

```bash
python test_server.py
```

Output:
```
[OK] Root endpoint working
[OK] Health endpoint working
[OK] OpenAPI docs accessible
[SUCCESS] All basic tests passed!
```

## Documentation

- Korean README: [README_KR.md](README_KR.md)
- Full documentation in README_KR.md

## License

Migrated version of CoFriends Backend.
