from fastapi import FastAPI
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from cosmos_client import get_container
from azure.cosmos.exceptions import CosmosResourceNotFoundError
import uuid
import os
from keyvault_client import get_secret
from azure.cosmos import CosmosClient
from openai_client import get_openai_client, DEPLOYMENT
from typing import List


SYSTEM_PROMPT = SYSTEM_PROMPT = """You are Scarlet, a friendly and professional AI
assistant for Mayo Clinic in Karachi, Pakistan.

YOUR ROLE:
- Help patients with general health information.
- Answer questions about clinic services and hours.
- Assist with appointment scheduling queries.
- Provide guidance on when to seek urgent care.

CLINIC INFORMATION:
- Hours: Monday-Saturday, 9am-8pm PKT
- Emergency: Direct to nearest hospital or call 911
- Languages: English

STRICT RULES:
- Never diagnose a condition.
- Never recommend specific medications or dosages.
- For urgent symptoms (chest pain, difficulty breathing,
  severe bleeding), immediately advise calling 911 or
  going to the nearest emergency room.
- If unsure, say 'I recommend speaking with our doctor'

TONE: Warm, clear, professional. Respond in the same
language the patient uses English."""

class Message(BaseModel):
    role: str     # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[Message] = []   # conversation history from client
    session_id: Optional[str] = None

# class ChatRequest(BaseModel):
#     message: str
#     session_id: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    model: str
    tokens_used: int


# class SecretRequest(BaseModel):
#     secret_name: str


class Item(BaseModel):
    name: str
    category: str

app = FastAPI(title="Clinic API", version="1.0.0")


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    client = get_openai_client()



    ### Chat Completions API
    # Build the messages array:
    # 1. System prompt always comes first
    # 2. Last 5 history messages (to control token cost)
    # 3. Current user message last
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    recent_history = request.history[-5:]  # keep last 5 exchanges
    for msg in recent_history:
        messages.append({"role": msg.role, "content": msg.content})

    messages.append({"role": "user", "content": request.message})


    response = client.chat.completions.create(
        model=DEPLOYMENT,
        messages=messages,
        max_tokens=500,      # hard cap to control costs
        temperature=0.7,     # 0=deterministic, 1=creative
    )


    return ChatResponse(
        reply=response.choices[0].message.content,
        model=response.model,
        tokens_used=response.usage.total_tokens
    )


### Responses API
    # response = client.responses.create(
    #     instructions=SYSTEM_PROMPT,
    #     input=request.message,
    #     model=DEPLOYMENT
    # )

    # return ChatResponse(
    #     reply=response.output_text,
    #     model=response.model,
    #     tokens_used=response.usage.total_tokens
    # )

# It should be removed
# @app.post("/fetch-secret")
# def fetch_secret(req: SecretRequest):
#     try:
#         value = get_secret(req.secret_name)
#         return {
#             "secret_name": req.secret_name,
#             "retrieved": True,
#             "length": len(value),
#             "preview": value[:4] + "***" + value[-4:]  # never expose full value
#         }
#     except Exception as e:
#         return {"error": str(e), "retrieved": False}

# On startup: fetch secret from Key Vault using Managed Identity
# Falls back to env var for local development
def get_cosmos_client():
    try:
        conn_str = get_secret("CosmosConnectionString")
    except Exception:
        # Local dev fallback — use .env file
        conn_str = os.environ.get("COSMOS_CONNECTION_STRING", "")
    return CosmosClient.from_connection_string(conn_str)

@app.get("/health")
def health():
    return {"status": "healthy", "secret_source": "Key Vault"}

@app.get("/secret-demo")
def secret_demo():
    # Shows the concept — in real apps never expose secret values!
    db_password = get_secret("MyDatabasePassword")
    return {
        "message": "Secret fetched successfully from Key Vault",
        "secret_length": len(db_password),
        "first_char": db_password[0] + "***"
    }


@app.get("/")
def root():
    return {"message": "Clinic API is running", "status": "ok"}




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