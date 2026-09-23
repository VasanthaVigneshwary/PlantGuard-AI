from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import shutil

from ml.predict import predict_disease
from services.database_service import get_disease_details_by_prediction


router = APIRouter()


# --------------------------------------------------
# TEST API
# --------------------------------------------------

@router.get("/test")
def test_plant_api():

    return {
        "message": "Plant API is working 🌱"
    }


# --------------------------------------------------
# PLANT IMAGE UPLOAD + AI PREDICTION
# --------------------------------------------------

@router.post("/upload")
async def upload_plant_image(file: UploadFile = File(...)):

    # Check file type
    allowed_extensions = [".jpg", ".jpeg", ".png", ".webp"]

    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension not in allowed_extensions:

        raise HTTPException(
            status_code=400,
            detail="Only JPG, JPEG, PNG and WEBP images are allowed."
        )


    # Create uploads folder if it doesn't exist
    upload_folder = "uploads"

    os.makedirs(upload_folder, exist_ok=True)


    # Create safe filename
    file_path = os.path.join(
        upload_folder,
        file.filename
    )


    # Save uploaded image
    with open(file_path, "wb") as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )


    # Run AI prediction
    try:
        result = predict_disease(file_path)

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"AI prediction failed: {str(e)}"
        )

    disease_data = get_disease_details_by_prediction(result["disease"])

    if disease_data is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "No knowledge-base disease record found for prediction: "
                f"{result['disease']}"
            )
        )

    disease = disease_data["disease"]
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
        "message": "Plant image analyzed successfully 🌱",
        "filename": file.filename,
        "prediction": result["disease"],
        "confidence": result["confidence"],
        "status": result["status"],
        "disease": {
            "id": disease[0],
            "name": disease[1],
            "crop_name": disease[2],
            "description": disease[3]
        },
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
        "treatments": list(treatments.values()),
        "prevention": [
            {
                "id": item[0],
                "title": item[1],
                "description": item[2]
            }
            for item in disease_data["prevention"]
        ]
    }