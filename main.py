from fastapi import FastAPI
from datetime import datetime
from pydantic import BaseModel
from cosmos_client import get_container
from azure.cosmos.exceptions import CosmosResourceNotFoundError
import uuid

class Item(BaseModel):
    name: str
    category: str

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

@app.post("/items")
def create_item(item: Item):
    return {
        "message": f"Item '{item.name}' received.",
        "data": item,
        "id": 99
    }


# GET all patients from Cosmos DB
@app.get("/patients")
def get_patients():
    container = get_container()
    query = "SELECT p.id, p.name, p.age, p.city, p.condition FROM patients p"
    items = list(container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))
    return {"patients": items, "count": len(items)}

# GET patients by city (efficient — uses partition key)
@app.get("/patients/city/{city}")
def get_patients_by_city(city: str):
    container = get_container()
    query = f"SELECT * FROM patients p WHERE p.city = '{city}'"
    items = list(container.query_items(
        query=query,
        partition_key=city
    ))
    return {"patients": items, "city": city}

# POST — create a new patient
@app.post("/patients")
def create_patient(patient: dict):
    container = get_container()
    if "id" not in patient:
        patient["id"] = str(uuid.uuid4())
    result = container.create_item(body=patient)
    return {"message": "Patient created", "id": result["id"]}

# GET single patient by id and city
@app.get("/patients/{city}/{patient_id}")
def get_patient(city: str, patient_id: str):
    container = get_container()
    try:
        item = container.read_item(
            item=patient_id,
            partition_key=city
        )
        return item
    except CosmosResourceNotFoundError:
        return {"error": "Patient not found"}, 404