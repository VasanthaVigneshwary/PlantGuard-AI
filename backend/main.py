from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.plant import router as plant_router
from database import get_connection
from services.database_service import (
    get_all_crops,
    get_all_diseases,
    get_disease_details
)

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


# --------------------------------------------------
# DATABASE TEST
# --------------------------------------------------

@app.get("/api/db-test")
def database_test():

    connection = get_connection()

    cursor = connection.cursor()
    cursor.execute("SELECT current_database();")

    database_name = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    return {
        "message": "PostgreSQL connection successful! ✅",
        "database": database_name
    }
# --------------------------------------------------
# CROPS
# --------------------------------------------------

@app.get("/api/crops")
def get_crops():

    crops = get_all_crops()

    return {
        "count": len(crops),
        "crops": [
            {
                "id": crop[0],
                "name": crop[1],
                "scientific_name": crop[2],
                "description": crop[3]
            }
            for crop in crops
        ]
    }
@app.get("/api/diseases")
def get_diseases():

    diseases = get_all_diseases()

    return {
        "count": len(diseases),
        "diseases": [
            {
                "id": disease[0],
                "name": disease[1],
                "crop_name": disease[2],
                "description": disease[3]
            }
            for disease in diseases
        ]
    }
@app.get("/api/diseases/{disease_id}")
def get_disease(disease_id: int):

    disease_data = get_disease_details(disease_id)

    if disease_data is None:
        return {
            "error": "Disease not found"
        }

    disease = disease_data["disease"]

    # Group application rates under their treatment
    treatments = {}

    for row in disease_data["treatments"]:

        treatment_id = row[0]

        if treatment_id not in treatments:
            treatments[treatment_id] = {
                "id": row[0],
                "name": row[1],
                "type": row[2],
                "description": row[3],
                "instructions": row[4],
                "precautions": row[5],
                "application_rates": []
            }

        # Add application rate if one exists
        if row[6] is not None:
            treatments[treatment_id]["application_rates"].append({
                "id": row[6],
                "application_method": row[7],
                "measurement_unit": row[8],
                "rate": float(row[9]) if row[9] is not None else None,
                "basis": row[10],
                "notes": row[11]
            })

    return {
        "id": disease[0],
        "name": disease[1],
        "crop_name": disease[2],
        "description": disease[3],

        "symptoms": [
            {
                "id": symptom[0],
                "name": symptom[1],
                "description": symptom[2]
            }
            for symptom in disease_data["symptoms"]
        ],

        "causes": [
            {
                "id": cause[0],
                "name": cause[1],
                "description": cause[2]
            }
            for cause in disease_data["causes"]
        ],

        "prevention": [
            {
                "id": item[0],
                "title": item[1],
                "description": item[2]
            }
            for item in disease_data["prevention"]
        ],

        "treatments": list(treatments.values())
    }