from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.plant import router as plant_router


app = FastAPI()


# --------------------------------------------------
# CORS CONFIGURATION
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# PLANT API
# --------------------------------------------------

app.include_router(
    plant_router,
    prefix="/api"
)


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.get("/")
def home():

    return {
        "message": "Plant Guard AI Backend is Running 🌱"
    }