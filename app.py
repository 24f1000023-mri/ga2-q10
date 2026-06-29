from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import uuid
import time

EMAIL = "24f1000023@ds.study.iitm.ac.in"

ALLOWED_ORIGIN = "https://app-8hq25w.example.com"

LIMIT = 11
WINDOW = 10  # seconds

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.example\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store request timestamps per client
clients = {}


@app.middleware("http")
async def request_context_and_rate_limit(request: Request, call_next):
    # Request ID
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id

    # Client ID
    client_id = request.headers.get("X-Client-Id", "anonymous")

    now = time.time()

    if client_id not in clients:
        clients[client_id] = []

    # Remove timestamps older than 10 seconds
    clients[client_id] = [
        t for t in clients[client_id]
        if now - t < WINDOW
    ]

    # Rate limit
    if len(clients[client_id]) >= LIMIT:
        response = JSONResponse(
            status_code=429,
            content={"detail": "Too Many Requests"},
        )
        response.headers["Retry-After"] = str(WINDOW)
        response.headers["X-Request-ID"] = request_id
        return response

    clients[client_id].append(now)

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/ping")
def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }


@app.get("/")
def root():
    return {"status": "ok"}
