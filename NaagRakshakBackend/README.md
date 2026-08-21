# NaagRakshak — Production Backend System API Engine

High-throughput, production-grade Python FastAPI backend engine for **NaagRakshak** (AI-Powered Snake Identification & Safety Platform), servicing the React SPA frontend with zero-bloat deterministic safety enforcement.

---

## ⚡ Quick Start (Local Setup)

### 1. Activate Virtual Environment & Install Dependencies
```powershell
# From workspace root
..\Naag_ml\.venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r requirements.txt
```

### 2. Run Database Seeder & Verification Test Suite
```powershell
python test_backend.py
```

### 3. Launch Local Backend Server
```powershell
python run.py
```
Or with Uvicorn CLI:
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📡 API Endpoints Summary

- **Swagger Interactive API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Health check (Model warm-state & PostgreSQL DB connection) |
| `POST` | `/api/v1/predict` | Main AI Inference & Deterministic Safety Engine endpoint |
| `GET` | `/api/v1/species` | Paginated Indian snake taxonomy catalog |
| `GET` | `/api/v1/species/{id}` | Detailed species profile with regional language names |
| `GET` | `/api/v1/species/{id}/distribution` | Regional GBIF & ZSI occurrence frequencies |
| `GET` | `/api/v1/medical-facilities` | ASV government hospitals & ICU availability |
| `GET` | `/api/v1/rescue` | Forest department wildlife emergency dispatch helplines |

---

## 🔒 Configuration (`.env`)

- **PostgreSQL Database**: `postgresql+asyncpg://postgres:7044@localhost:5432/naagrakshak`
- **OpenAI API Key**: Enabled for constrained LLM natural language safety synthesis
- **Google Search API Key**: Enabled
