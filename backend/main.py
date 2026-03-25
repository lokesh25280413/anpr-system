from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
import models

from routes import user_routes, video_routes

# -----------------------------
# App Initialization
# -----------------------------

app = FastAPI(
    title="ANPR System API",
    description="Automatic Number Plate Recognition Backend",
    version="1.0.0"
)

# -----------------------------
# CORS (VERY IMPORTANT)
# -----------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change later for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Startup Event (Better Practice)
# -----------------------------

@app.on_event("startup")
def startup():
    print("🚀 Starting ANPR Backend...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database connected & tables created")

# -----------------------------
# Routes
# -----------------------------

app.include_router(user_routes.router)
app.include_router(video_routes.router)

# -----------------------------
# Root Endpoint
# -----------------------------

@app.get("/")
def home():
    return {
        "message": "ANPR Backend Running 🚀",
        "docs": "/docs"
    }