Heavyweight Docker Compose stack (nginx + gunicorn + redis)

1. Build and start the stack:

```powershell
docker compose up --build -d
```

2. Health checks:

- App: http://localhost:8000/
- Reverse proxy: http://localhost/

3. Notes:

- The `web` service builds from `lab_server/Dockerfile` and runs gunicorn.
- Server-side sessions are enabled by default (uses Redis). To disable,
  unset `USE_SERVER_SESSION` in `docker-compose.yml`.
