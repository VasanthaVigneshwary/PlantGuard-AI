from fastapi import FastAPI
from routes.plant import router as plant_router

app = FastAPI()

app.include_router(plant_router, prefix="/api")

@app.get("/")
def home():
    return {
        "message": "Plant Guard AI Backend is Running 🌱"
    }