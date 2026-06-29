from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import uuid
import time

EMAIL = "24f1000023@ds.study.iitm.ac.in"

ALLOWED_ORIGIN = "https://app-8hq25w.example.com"

LIMIT = 11
WINDOW = 10

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        ALLOWED_ORIGIN,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

clients = {}

@app.middleware("http")
async def middleware(request: Request, call_next):

    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    # Store it BEFORE calling the endpoint
    request.state.request_id = request_id

    client = request.headers.get("X-Client-Id", "anonymous")

    now = time.time()

    if client not in clients:
        clients[client] = []

    clients[client] = [t for t in clients[client] if now - t < WINDOW]

    if len(clients[client]) >= LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too Many Requests"},
        )

    clients[client].append(now)

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response

@app.get("/ping")
def ping(request: Request):

    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }