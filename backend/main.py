from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from database import Base, engine
import models

from routes import user_routes, video_routes

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# create database tables
Base.metadata.create_all(bind=engine)

app.include_router(user_routes.router)
app.include_router(video_routes.router)

@app.get("/")
def home():
    return {"message": "ANPR Backend Running"}