from fastapi import FastAPI
from datetime import datetime

app = FastAPI(title="Clinic API", version="1.0.0")

@app.get("/")
def root():
    return {"message": "Clinic API is running", "status": "ok"}

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/items")
def get_items():
    return {
        "items": [
            {"id": 1, "name": "Panadol", "category": "medicine"},
            {"id": 2, "name": "Bandage", "category": "supplies"},
            {"id": 3, "name": "Syringe", "category": "equipment"},
        ]
    }