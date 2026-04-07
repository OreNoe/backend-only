# RendelIt Backend

Backend FastAPI separado para desplegar en Render.

## Estructura

- `backend/main.py`: API FastAPI
- `backend/requirements.txt`: dependencias Python
- `data/products.json`: catálogo inicial
- `render.yaml`: blueprint para Render

## Deploy en Render

1. Subí este repo a GitHub.
2. Creá un Web Service en Render desde ese repo.
3. Render va a usar `render.yaml`.
4. El backend queda disponible con:
   - Build: `pip install -r backend/requirements.txt`
   - Start: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

## Endpoints

- `GET /health`
- `GET /api/products`
- `GET /api/stores/pins`
- `POST /api/reports`
