from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
import os
import shutil
import re

from ml.predict import predict_disease
from services.database_service import (
    get_disease_details_by_prediction,
    get_disease_details,
    get_disease_by_name,
    get_notifications as get_notification_records,
)


router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    crop: str | None = None
    disease: str | None = None
    confidence: float | None = None
    disease_id: int | None = None


# --------------------------------------------------
# TEST API
# --------------------------------------------------

@router.get("/test")
def test_plant_api():

    return {
        "message": "Plant API is working 🌱"
    }


@router.get("/notifications")
def get_notifications_endpoint():
    notifications = get_notification_records()

    return {
        "count": len(notifications),
        "notifications": notifications,
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


@router.post("/chat")
async def chat_with_plant_assistant(request: ChatRequest):
    message = request.message.strip()

    if not message:
        raise HTTPException(status_code=400, detail="Message is required.")

    lower_message = message.lower()

    disease_context = None
    context_used = False
    disease_name = None
    crop_name = request.crop.strip() if request.crop else None

    if request.disease_id is not None:
        disease_context = get_disease_details(request.disease_id)
    elif request.disease:
        disease_context = get_disease_by_name(request.disease, crop_name)

    if disease_context is not None:
        context_used = True
        disease_name = disease_context["disease"][1]
        crop_name = disease_context["disease"][2]

    def clean_label(value):
        return value.strip() if value else "Unknown"

    if any(keyword in lower_message for keyword in ["what disease", "detected disease", "what is the disease", "what disease is this", "what disease does my plant have", "what is this disease", "what disease is this plant"]):
        if disease_context is not None:
            response = (
                f"The current detected disease is {disease_name}. "
                f"This is associated with {crop_name} and is based on the current image prediction context."
            )
        else:
            response = "I do not have a current detected disease in context. Please upload a plant image or specify the disease name so I can look it up in the Plant Guard knowledge base."
        return {"response": response, "context_used": context_used, "disease": disease_name}

    if any(keyword in lower_message for keyword in ["symptom", "symptoms", "identify", "look for", "how do i know"]):
        if disease_context is None:
            return {
                "response": "I do not have a current disease in context. Upload an image or specify the disease to look up the known symptoms in the database.",
                "context_used": False,
                "disease": None,
            }

        symptoms = disease_context["symptoms"]
        if not symptoms:
            response = f"I could not find symptom data for {disease_name} in the current knowledge base."
        else:
            symptom_list = "; ".join(f"{item[1]}" for item in symptoms[:5])
            response = f"For {disease_name}, the known symptoms include: {symptom_list}."
        return {"response": response, "context_used": True, "disease": disease_name}

    if any(keyword in lower_message for keyword in ["cause", "causes", "why did this happen", "what caused"]):
        if disease_context is None:
            return {
                "response": "I do not have a current disease in context. Upload an image or specify the disease to check the known causes in the database.",
                "context_used": False,
                "disease": None,
            }

        causes = disease_context["causes"]
        if not causes:
            response = f"I could not find cause information for {disease_name} in the current knowledge base."
        else:
            cause_list = "; ".join(f"{item[1]}" for item in causes[:5])
            response = f"The known causes for {disease_name} include: {cause_list}."
        return {"response": response, "context_used": True, "disease": disease_name}

    if any(keyword in lower_message for keyword in ["treat", "treatment", "control this disease", "how can i manage", "what should i do"]):
        if disease_context is None:
            return {
                "response": "I do not have a current disease in context. Upload an image or specify the disease to get treatment guidance from the agricultural knowledge base.",
                "context_used": False,
                "disease": None,
            }

        treatments = disease_context["treatments"]
        if not treatments:
            response = f"I could not find treatment guidance for {disease_name} in the current database."
        else:
            treatment_names = "; ".join(f"{item[1]}" for item in treatments[:5])
            response = f"Treatment options for {disease_name} include: {treatment_names}. Use the disease-specific treatment guidance and product label instructions from the current knowledge base."
        return {"response": response, "context_used": True, "disease": disease_name}

    if any(keyword in lower_message for keyword in ["prevent", "precaution", "stop it from spreading", "keep it from spreading"]):
        if disease_context is None:
            return {
                "response": "I do not have a current disease in context. Upload an image or specify the disease to look up prevention guidance from the database.",
                "context_used": False,
                "disease": None,
            }

        prevention = disease_context["prevention"]
        if not prevention:
            response = f"I could not find prevention guidance for {disease_name} in the current database."
        else:
            prevention_lines = "; ".join(f"{item[1]}" for item in prevention[:5])
            response = f"Prevention guidance for {disease_name} includes: {prevention_lines}."
        return {"response": response, "context_used": True, "disease": disease_name}

    if any(keyword in lower_message for keyword in ["acre", "acres", "application rate", "dosage", "how much treatment", "how much should i apply", "per acre"]):
        if disease_context is None:
            return {
                "response": "I need the current disease context to calculate acreage-based treatment requirements from the database. Please upload a plant image or specify the disease.",
                "context_used": False,
                "disease": None,
            }

        acreage_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:acre|acres)", lower_message)
        acreage = float(acreage_match.group(1)) if acreage_match else None

        if acreage is None:
            return {
                "response": "I can calculate acreage-based treatment needs when you specify the affected area in acres. For example: 'How much treatment do I need for 2 acres?'.",
                "context_used": True,
                "disease": disease_name,
            }

        area_rates = []
        for treatment in disease_context["treatments"]:
            for rate in treatment[6] if isinstance(treatment, tuple) else []:
                pass

        for treatment in disease_context["treatments"]:
            for row in treatment[6] if isinstance(treatment, tuple) else []:
                pass

        # Get treatment rows in normalized DB format
        area_rates = []
        for row in disease_context["treatments"]:
            treatment_id = row[0]
            treatment_name = row[1]
            treatment_type = row[2]
            treatment_description = row[3]
            instructions = row[4]
            precautions = row[5]
            application_rates = []

            if row[6] is not None:
                application_rates = [{
                    "id": row[6],
                    "application_method": row[7],
                    "measurement_unit": row[8],
                    "rate": float(row[9]) if row[9] is not None else None,
                    "basis": row[10],
                    "notes": row[11],
                }]

            for rate_data in application_rates:
                if rate_data["rate"] is None:
                    continue

                unit = (rate_data["measurement_unit"] or "").strip()
                basis = (rate_data["basis"] or "").lower()
                unit_lower = unit.lower()
                if "acre" in basis or "/acre" in unit_lower or " per acre" in unit_lower or "acre" in unit_lower:
                    area_rates.append({
                        "product": treatment_name,
                        "rate": float(rate_data["rate"]),
                        "unit": unit,
                        "method": rate_data["application_method"],
                        "basis": rate_data["basis"],
                    })

        if not area_rates:
            response = f"The current knowledge base does not include a usable acreage-based application rate for {disease_name}. I should not guess a rate. Please verify the current product label and applicable agricultural guidance."
            return {"response": response, "context_used": True, "disease": disease_name}

        selected = area_rates[0]
        total_required = acreage * float(selected["rate"])
        response = (
            f"Using the current database rate for {selected['product']}, the rate is {selected['rate']} {selected['unit']} per acre. "
            f"For {acreage} acres, the estimated total is {total_required:.2f} {selected['unit']}. "
            f"Always verify the current product label and local agricultural guidance before applying the treatment."
        )
        return {"response": response, "context_used": True, "disease": disease_name}

    if any(keyword in lower_message for keyword in ["reliable", "trust", "accurate", "confidence", "sure"]):
        confidence_value = request.confidence
        if confidence_value is not None:
            response = (
                f"The current AI prediction confidence is {confidence_value:.2f}%. This is an image-based model prediction and should not be treated as a guaranteed diagnosis, especially when confidence is low. It is best used as a support tool alongside field observation and expert guidance."
            )
        else:
            response = "The AI prediction is an image-based model estimate and should not be treated as a guaranteed diagnosis. It is best used as a support tool alongside field observation and expert guidance."
        return {"response": response, "context_used": context_used, "disease": disease_name}

    if disease_context is not None:
        base_context = (
            f"The detected disease is {disease_name}. "
            f"The current knowledge base includes symptoms, causes, treatments, and prevention guidance for this condition. "
        )

        if "what are the symptoms" in lower_message or "symptoms" in lower_message:
            symptoms = disease_context["symptoms"]
            symptom_list = "; ".join(f"{item[1]}" for item in symptoms[:5])
            response = f"{base_context}Symptoms include: {symptom_list}."
        elif "cause" in lower_message or "why" in lower_message:
            causes = disease_context["causes"]
            cause_list = "; ".join(f"{item[1]}" for item in causes[:5])
            response = f"{base_context}Common causes include: {cause_list}."
        elif "treat" in lower_message:
            treatments = disease_context["treatments"]
            treatment_names = "; ".join(f"{item[1]}" for item in treatments[:5])
            response = f"{base_context}Treatment options include: {treatment_names}. Use the product label and local agricultural guidance when applying them."
        elif "prevent" in lower_message:
            prevention = disease_context["prevention"]
            prevention_lines = "; ".join(f"{item[1]}" for item in prevention[:5])
            response = f"{base_context}Prevention guidance includes: {prevention_lines}."
        else:
            response = (
                f"{base_context}I can help with symptoms, causes, treatments, prevention, and acreage-based treatment questions for the current disease."
            )
        return {"response": response, "context_used": True, "disease": disease_name}

    response = "I currently focus on the Plant Guard AI agriculture knowledge base. Please upload a plant image or tell me the crop and disease name so I can provide a grounded answer from the database."
    return {"response": response, "context_used": False, "disease": None}
