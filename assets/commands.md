# Docker Compose Commands

Use these commands from the project root:

```bash
cd C:\Coding\Projects\AI_agent_app
```

---

## 1. Build And Run Everything

Run backend, Redis, Prometheus, Grafana, Streamlit, and React:

```bash
docker compose --profile streamlit --profile react up --build
```

Run the same full stack in the background:

```bash
docker compose --profile streamlit --profile react up -d --build
```

URLs:

```text
FastAPI:    http://127.0.0.1:8000
Streamlit:  http://127.0.0.1:8501
React:      http://127.0.0.1:5173
Prometheus: http://127.0.0.1:9090
Grafana:    http://127.0.0.1:3000
```

---

## 2. Run Default Backend Stack Only

This starts services without optional frontend profiles:

```bash
docker compose up --build
```

This normally starts:

```text
redis
backend
prometheus
grafana
```

Run it in the background:

```bash
docker compose up -d --build
```

---

## 3. Run With Streamlit Frontend

Build and run Redis, backend, observability, and Streamlit:

```bash
docker compose --profile streamlit up --build
```

Run in the background:

```bash
docker compose --profile streamlit up -d --build
```

After CSS-only Streamlit changes:

```bash
docker compose --profile streamlit build streamlit
docker compose --profile streamlit up -d --force-recreate streamlit
```

---

## 4. Run With React Frontend

Build and run Redis, backend, observability, and React:

```bash
docker compose --profile react up --build
```

Run in the background:

```bash
docker compose --profile react up -d --build
```

Recreate only React:

```bash
docker compose --profile react up -d --force-recreate react
```

---

## 5. Build Selected Services

Build only backend:

```bash
docker compose build backend
```

Build only Streamlit:

```bash
docker compose --profile streamlit build streamlit
```

Build only React:

```bash
docker compose --profile react build react
```

Build everything, including optional frontends:

```bash
docker compose --profile streamlit --profile react build
```

---

## 6. Restart Or Recreate Selected Containers

Restart backend after backend code changes:

```bash
docker compose up -d --force-recreate backend
```

Restart Streamlit after frontend Python or CSS changes:

```bash
docker compose --profile streamlit up -d --force-recreate streamlit
```

Restart React after frontend changes:

```bash
docker compose --profile react up -d --force-recreate react
```

Restart observability:

```bash
docker compose up -d --force-recreate prometheus grafana
```

---

## 7. Logs

View all logs:

```bash
docker compose logs -f
```

Backend logs:

```bash
docker compose logs -f backend
```

Streamlit logs:

```bash
docker compose --profile streamlit logs -f streamlit
```

React logs:

```bash
docker compose --profile react logs -f react
```

Prometheus and Grafana logs:

```bash
docker compose logs -f prometheus grafana
```

---

## 8. Container Status And Health Checks

List running Compose containers:

```bash
docker compose ps
```

Check backend health manually:

```bash
curl http://127.0.0.1:8000/metrics
```

Check Streamlit:

```bash
curl http://127.0.0.1:8501
```

Check React:

```bash
curl http://127.0.0.1:5173
```

---

## 9. Stop And Clean Up

Stop containers but keep volumes:

```bash
docker compose down
```

Stop containers for both frontend profiles:

```bash
docker compose --profile streamlit --profile react down
```

Stop and remove named volumes, including React `node_modules` volume:

```bash
docker compose --profile streamlit --profile react down -v
```

Remove stopped containers and unused images/layers:

```bash
docker system prune
```

---

## 10. Useful Rebuild Patterns

Backend code changed:

```bash
docker compose build backend
docker compose up -d --force-recreate backend
```

Streamlit CSS changed:

```bash
docker compose --profile streamlit build streamlit
docker compose --profile streamlit up -d --force-recreate streamlit
```

Both backend and Streamlit changed:

```bash
docker compose --profile streamlit build backend streamlit
docker compose --profile streamlit up -d --force-recreate backend streamlit
```

React package files changed:

```bash
docker compose --profile react build react
docker compose --profile react up -d --force-recreate react
```
