# ContextIQ Setup

## Recommended: Docker Compose

Prerequisites: Docker Desktop with Compose, Git, and a browser.

```bash
copy .env.example .env
```

Edit `.env` and set `POSTGRES_PASSWORD` and `SECRET_KEY` to local values. Do not commit `.env` or put provider keys in frontend variables.

```bash
docker compose config --quiet
docker compose up --build
```

The backend runs migrations before serving. Seed optional synthetic core data in a second terminal:

```bash
docker compose exec backend python /scripts/generate_synthetic_data.py --mode db --users 2
```

Open `http://localhost:3000`. API documentation is available at ports 8000 through 8004 under `/docs`.

## Manual Service Setup

Each Python service has its own `requirements.txt`. Create a virtual environment, install requirements, configure the service environment, and run Uvicorn from that service directory. The frontend uses Node.js 20+:

```bash
cd frontend
npm ci
npm run dev
```

The full command reference is [cmd.md](../cmd.md).

## Environment Safety

- `.env.example` contains placeholders only.
- `SECRET_KEY`, database passwords, and LLM keys are server-side values.
- `LLM_PROVIDER=mock` needs no API key.
- Production should use a secret manager, verified authentication, restricted CORS, `DEBUG=false`, and a managed database.
