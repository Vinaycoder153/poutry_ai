# Backend (FastAPI)

## Run
From repo root:

```bash
python -m venv .venv-backend
.venv-backend\\Scripts\\activate
pip install -r app/requirements.txt
uvicorn app.main:app --reload --port 8000
```

Health:
- GET http://localhost:8000/api/health

Predict:
- POST http://localhost:8000/api/predict (multipart/form-data with field `file`)

