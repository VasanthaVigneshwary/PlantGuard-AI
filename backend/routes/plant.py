from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import shutil

from ml.predict import predict_disease


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


    # Return result
    return {

        "message": "Plant image analyzed successfully 🌱",

        "filename": file.filename,

        "prediction": result["disease"],

        "confidence": result["confidence"],

        "status": result["status"]

    }