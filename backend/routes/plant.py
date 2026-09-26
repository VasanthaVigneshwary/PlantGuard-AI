from fastapi import APIRouter, UploadFile, File, HTTPException, Form
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
    language: str | None = "en"


def normalize_language(value: str | None) -> str:
    if value is None:
        return "en"

    normalized = value.strip().lower()

    if normalized in {"en", "english"}:
        return "en"
    if normalized in {"ta", "tamil", "தமிழ்"}:
        return "ta"

    return "en"


TAMIL_TEXT_MAP = {
    "Plant identified as": "தாவர அடையாளம்: ",
    "Low confidence result. Manual verification is strongly recommended.": "குறைந்த நம்பகத்தன்மை கொண்ட முடிவு. கைமுறையாக சரிபார்ப்பது மிகவும் பரிந்துரைக்கப்படுகிறது.",
    "Moderate confidence result. Consider verifying the symptoms.": "மிதமான நம்பகத்தன்மை கொண்ட முடிவு. அறிகுறிகளைச் சரிபார்க்க பரிந்துரைக்கப்படுகிறது.",
    "High confidence result.": "அதிக நம்பகத்தன்மை கொண்ட முடிவு.",
    "Late blight can spread quickly under cool and humid conditions. Early observation and proper plant care can help reduce further spread.": "குளிர்ச்சியான மற்றும் அதிக ஈரப்பதம் கொண்ட சூழ்நிலைகளில் லேட் ப்ளைட் நோய் வேகமாகப் பரவக்கூடும். ஆரம்பத்திலேயே கவனித்து, சரியான தாவர பராமரிப்பை மேற்கொள்வது நோய் மேலும் பரவுவதை குறைக்க உதவும்.",
    "Early blight can cause dark spots on leaves and may reduce plant growth if the condition progresses.": "ஆரம்பகால ப்ளைட் நோய் இலைகளில் கருமையான புள்ளிகளை உருவாக்கி, நிலைமை முன்னேறும்போது தாவர வளர்ச்சியைக் குறைக்கலாம்.",
    "Powdery mildew commonly appears as a white powder-like coating on leaves and can affect plant growth.": "பவுடரி மில்டெவ் பொதுவாக இலைகளில் வெள்ளை தூள் போன்ற பூச்சாகத் தோன்றி, தாவர வளர்ச்சியை பாதிக்கலாம்.",
    "Bacterial spot can cause small dark or water-soaked spots on leaves and may damage plant tissue.": "பாக்டீரியா ஸ்பாட் நோய் இலைகளில் சிறிய கருமையான அல்லது நீர் நிறைந்த புள்ளிகளை ஏற்படுத்தி, தாவர திசுக்களைக் காயப்படுத்தலாம்.",
    "Leaf spot diseases can create visible spots or damaged areas on plant leaves.": "இலை புள்ளி நோய்கள் இலைகளில் தெரியும் புள்ளிகள் அல்லது சேதத்தை உருவாக்கலாம்.",
    "The AI model detected a possible plant disease. Further observation and expert verification may be useful.": "AI மாடல் சாத்தியமான தாவர நோயைக் கண்டறிந்துள்ளது. மேலும் கவனிப்பு மற்றும் நிபுணர் சரிபார்ப்பு பயனுள்ளதாக இருக்கும்.",
    "The AI model did not detect a known disease in this plant image.": "AI மாடல் இந்த தாவரப் படத்தில் அறியப்பட்ட நோயைக் கண்டறியவில்லை.",
    "This calculator is for estimation only. Always follow the product label and local agricultural recommendations for actual dosage.": "இந்த கால்குலேட்டர் தோராய மதிப்பீட்டிற்காக மட்டுமே. உண்மையான அளவுக்கு தயாரிப்பு லேபிள் மற்றும் உள்ளூர் விவசாய வழிமுறைகளைப் பின்பற்றவும்.",
    "Instructions:": "வழிமுறைகள்:",
    "Precautions:": "ஜாக்கிரதைகள்:",
    "Notes:": "குறிப்புகள்:",
    "Calculation:": "கணக்கீடு:",
    "Source: TNAU Agritech Portal. Verify current product label and local approval before use.": "மூலம்: TNAU Agritech Portal. பயன்பாட்டுக்கு முன் தற்போதைய தயாரிப்பு லேபிள் மற்றும் உள்ளூர் ஒப்புதலைச் சரிபார்க்கவும்.",
    "Plant image analyzed successfully 🌱": "தாவர படம் வெற்றிகரமாக பகுப்பாய்வு செய்யப்பட்டது 🌱",
    "No major disease symptoms were detected by the model.": "மாடல் எந்த முக்கிய நோய் அறிகுறிகளையும் கண்டறியவில்லை.",
    "Continue monitoring the plant regularly.": "தாவரத்தை தொடர்ந்து கண்காணிக்கவும்.",
    "No disease treatment is currently required based on this prediction.": "இந்த கணிப்பின் அடிப்படையில் தற்போது நோய் சிகிச்சை தேவையில்லை.",
    "Continue regular plant care and monitoring.": "வழக்கமான தாவர பராமரிப்பு மற்றும் கண்காணிப்பை தொடரவும்.",
    "The AI model detected a possible plant disease. This result should be treated as an AI-based indication rather than a confirmed diagnosis.": "AI மாடல் சாத்தியமான தாவர நோயைக் கண்டறிந்துள்ளது. இது உறுதிப்படுத்தப்பட்ட நோய் கண்டறிதல் அல்ல; AI அடிப்படையிலான குறிகாட்டியாகவே பார்க்கப்பட வேண்டும்.",
    "Dark leaf lesions": "இலைகளில் கருமையான புள்ளிகள்",
    "Fruit lesions": "பழங்களில் புண்கள்",
    "Fruit rot": "பழ அழுகல்",
    "High humidity": "அதிக ஈரப்பதம்",
    "Excess leaf wetness": "அதிகமான இலை ஈரப்புத்தன்மை",
    "Poor air circulation": "மோசமான காற்றோட்டம்",
    "Favorable temperature": "சிறந்த வெப்பநிலை",
    "Late Blight Management": "லேட் ப்ளைட் மேலாண்மை",
    "Integrated management of tomato late blight": "தக்காளி லேட் ப்ளைட்டை ஒருங்கிணைந்த முறையில் மேலாண்மை செய்தல்",
    "Foliar spray": "இலை தெளிப்பு",
    "Good air circulation": "சிறந்த காற்றோட்டம்",
    "Apply as needed": "தேவைக்கேற்பப் பயன்படுத்தவும்",
    "Apply as directed": "வழிமுறைகளின்படி பயன்படுத்தவும்",
    "Wear protective clothing": "பாதுகாப்பு ஆடைகளை அணியவும்",
    "Avoid overhead irrigation": "மேல் நீர்ப்பாசனத்தை தவிர்க்கவும்",
    "Remove infected debris": "பாதிக்கப்பட்ட கழிவுகளை அகற்றவும்",
    "Avoid prolonged moisture on leaves": "இலைகளில் நீண்ட நேரம் ஈரப்பதம் இருக்காமல் கவனிக்கவும்",
    "This result should be treated as an AI-based indication rather than a confirmed diagnosis.": "இது உறுதிப்படுத்தப்பட்ட நோய் கண்டறிதல் அல்ல; AI அடிப்படையிலான குறிகாட்டியாகவே பார்க்கப்பட வேண்டும்.",
    "Plant Guard AI provides an AI-based prediction and should not be considered a confirmed agricultural diagnosis. For serious crop problems, consult a qualified agricultural expert.": "Plant Guard AI ஆனது AI அடிப்படையிலான கணிப்பை வழங்குகிறது; இது உறுதிப்படுத்தப்பட்ட விவசாய நோய் கண்டறிதல் அல்ல. தீவிரமான பயிர் பிரச்சனைகளுக்கு தகுதி வாய்ந்த விவசாய நிபுணரை அணுகவும்.",
    "No area-based application-rate data is available for this disease in the current knowledge base.": "தற்போதைய அறிவுத் தரவுத்தளத்தில் இந்த நோய்க்கு பரப்பளவின்படி பயன்பாட்டு வீதத் தகவல் இல்லை.",
    "Enter a valid affected area greater than zero.": "சரியான பாதிக்கப்பட்ட பரப்பளவைக் (பூஜ்ஜியத்தை விட அதிகமான) உள்ளிடவும்.",
    "This calculator is for estimation only": "இந்த கால்குலேட்டர் தோராய மதிப்பீட்டிற்காக மட்டுமே",
    "Low confidence result": "குறைந்த நம்பகத்தன்மை கொண்ட முடிவு",
    "Moderate confidence result": "மிதமான நம்பகத்தன்மை கொண்ட முடிவு",
    "High confidence result": "அதிக நம்பகத்தன்மை கொண்ட முடிவு",
    "Plant identified as": "தாவர அடையாளம்:",
    "Continue regular plant care and monitoring": "வழக்கமான தாவர பராமரிப்பு மற்றும் கண்காணிப்பை தொடரவும்",
    "Results may vary": "முடிவுகள் மாறலாம்",
}


def localize_text_for_language(value, language):
    if language != "ta" or not isinstance(value, str):
        return value

    localized = value
    for english_text, tamil_text in TAMIL_TEXT_MAP.items():
        if english_text in localized:
            localized = localized.replace(english_text, tamil_text)

    return localized


def localize_disease_payload(payload, language):
    if language != "ta":
        return payload

    localized = payload.copy()
    localized["message"] = localize_text_for_language(payload.get("message"), language)

    disease = localized.get("disease", {})
    if isinstance(disease, dict):
        disease["description"] = localize_text_for_language(disease.get("description"), language)

    symptoms = localized.get("symptoms", [])
    for symptom in symptoms:
        symptom["name"] = localize_text_for_language(symptom.get("name"), language)
        symptom["description"] = localize_text_for_language(symptom.get("description"), language)

    causes = localized.get("causes", [])
    for cause in causes:
        cause["name"] = localize_text_for_language(cause.get("name"), language)
        cause["description"] = localize_text_for_language(cause.get("description"), language)

    treatments = localized.get("treatments", [])
    for treatment in treatments:
        treatment["name"] = localize_text_for_language(treatment.get("name"), language)
        treatment["type"] = localize_text_for_language(treatment.get("type"), language)
        treatment["description"] = localize_text_for_language(treatment.get("description"), language)
        treatment["instructions"] = localize_text_for_language(treatment.get("instructions"), language)
        treatment["precautions"] = localize_text_for_language(treatment.get("precautions"), language)

        for rate in treatment.get("application_rates", []):
            rate["application_method"] = localize_text_for_language(rate.get("application_method"), language)
            rate["measurement_unit"] = localize_text_for_language(rate.get("measurement_unit"), language)
            rate["basis"] = localize_text_for_language(rate.get("basis"), language)
            rate["notes"] = localize_text_for_language(rate.get("notes"), language)

    prevention = localized.get("prevention", [])
    for item in prevention:
        item["title"] = localize_text_for_language(item.get("title"), language)
        item["description"] = localize_text_for_language(item.get("description"), language)

    return localized


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
async def upload_plant_image(
    file: UploadFile = File(...),
    language: str | None = Form("en"),
):

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

        if len(row) > 6 and row[6] is not None:
            treatments[treatment_id]["application_rates"].append({
                "id": row[6],
                "application_method": row[7] if len(row) > 7 else None,
                "measurement_unit": row[8] if len(row) > 8 else None,
                "rate": float(row[9]) if len(row) > 9 and row[9] is not None else None,
                "basis": row[10] if len(row) > 10 else None,
                "notes": row[11] if len(row) > 11 else None
            })

    normalized_language = normalize_language(language)
    response = {
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

    return localize_disease_payload(response, normalized_language)


@router.post("/chat")
async def chat_with_plant_assistant(request: ChatRequest):
    message = request.message.strip()

    if not message:
        raise HTTPException(status_code=400, detail="Message is required.")

    language = normalize_language(request.language)
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

    symptom_keywords = [
        "symptom", "symptoms", "identify", "look for", "how do i know",
        "அறிகுறி", "அறிகுறிகள்", "என்ன அறிகுறிகள்", "அறிகுறிகள் என்ன",
    ]
    cause_keywords = [
        "cause", "causes", "why did this happen", "what caused",
        "காரணம்", "காரணங்கள்", "ஏன்", "ஏன் ஏற்பட்டது", "என்ன காரணம்",
    ]
    treatment_keywords = [
        "treat", "treatment", "control this disease", "how can i manage", "what should i do",
        "சிகிச்சை", "சிகிச்சை என்ன", "என்ன செய்ய வேண்டும்", "எப்படி நடத்துவது",
    ]
    prevention_keywords = [
        "prevent", "precaution", "stop it from spreading", "keep it from spreading",
        "தடுப்பு", "தடுப்பது", "பரவாமல்", "பரவாமல் தடுக்க",
    ]
    acreage_keywords = [
        "acre", "acres", "application rate", "dosage", "how much treatment", "how much should i apply", "per acre",
        "ஏக்கர்", "ஏக்கர்களில்", "மருந்து அளவு", "எவ்வளவு", "எவ்வளவு மருந்து",
    ]
    disease_keywords = [
        "what disease", "detected disease", "what is the disease", "what disease is this", "what disease does my plant have", "what is this disease", "what disease is this plant",
        "என்ன நோய்", "நோய் என்ன", "இந்த நோய்", "இது என்ன நோய்", "என்ன நோய் இது",
    ]
    reliability_keywords = [
        "reliable", "trust", "accurate", "confidence", "sure",
        "நம்பகமான", "நம்பிக்கை", "உறுதி", "துல்லியம்",
    ]

    def ta_response(text: str) -> str:
        return text if language == "ta" else text

    if any(keyword in lower_message for keyword in disease_keywords):
        if disease_context is not None:
            if language == "ta":
                response = (
                    f"தற்போதைய கண்டறியப்பட்ட நோய் {disease_name}. "
                    f"இது {crop_name} பயிருடன் தொடர்புடையது மற்றும் தற்போதைய படக் கண்டறிதல் சூழலில் அடிப்படையாகிறது."
                )
            else:
                response = (
                    f"The current detected disease is {disease_name}. "
                    f"This is associated with {crop_name} and is based on the current image prediction context."
                )
        else:
            if language == "ta":
                response = "தற்போது எந்த நோய் சூழலும் என்னிடம் இல்லை. ஒரு தாவரப் படத்தை பதிவேற்றி அல்லது நோயின் பெயரை குறிப்பிடவும், இதை Plant Guard அறிவு தளத்தில் தேடிப்பெற முடியும்."
            else:
                response = "I do not have a current detected disease in context. Please upload a plant image or specify the disease name so I can look it up in the Plant Guard knowledge base."
        return {"response": response, "context_used": context_used, "disease": disease_name}

    if any(keyword in lower_message for keyword in symptom_keywords):
        if disease_context is None:
            if language == "ta":
                response = "தற்போது எந்த நோய் சூழலும் இல்லை. படம் பதிவேற்றவும் அல்லது நோயை குறிப்பிடவும், அறிவு தளத்தில் அறிகுறிகளைத் தேடலாம்."
            else:
                response = "I do not have a current disease in context. Upload an image or specify the disease to look up the known symptoms in the database."
            return {"response": response, "context_used": False, "disease": None}

        symptoms = disease_context["symptoms"]
        if not symptoms:
            if language == "ta":
                response = f"{disease_name} நோய்க்கான அறிகுறி தரவு தற்போதைய அறிவு தளத்தில் கிடைக்கவில்லை."
            else:
                response = f"I could not find symptom data for {disease_name} in the current knowledge base."
        else:
            symptom_list = "; ".join(f"{item[1]}" for item in symptoms[:5])
            if language == "ta":
                response = f"{disease_name} நோயின் அறிகுறிகள்: {symptom_list}."
            else:
                response = f"For {disease_name}, the known symptoms include: {symptom_list}."
        return {"response": response, "context_used": True, "disease": disease_name}

    if any(keyword in lower_message for keyword in cause_keywords):
        if disease_context is None:
            if language == "ta":
                response = "தற்போது எந்த நோய் சூழலும் இல்லை. படம் பதிவேற்றவும் அல்லது நோயை குறிப்பிடவும், காரணங்களை சரிபார்க்கலாம்."
            else:
                response = "I do not have a current disease in context. Upload an image or specify the disease to check the known causes in the database."
            return {"response": response, "context_used": False, "disease": None}

        causes = disease_context["causes"]
        if not causes:
            if language == "ta":
                response = f"{disease_name} நோய்க்கான காரணத் தகவல் தற்போதைய அறிவு தளத்தில் இல்லை."
            else:
                response = f"I could not find cause information for {disease_name} in the current knowledge base."
        else:
            cause_list = "; ".join(f"{item[1]}" for item in causes[:5])
            if language == "ta":
                response = f"{disease_name} நோய்க்கான காரணங்கள்: {cause_list}."
            else:
                response = f"The known causes for {disease_name} include: {cause_list}."
        return {"response": response, "context_used": True, "disease": disease_name}

    if any(keyword in lower_message for keyword in treatment_keywords):
        if disease_context is None:
            if language == "ta":
                response = "தற்போது எந்த நோய் சூழலும் இல்லை. படம் பதிவேற்றவும் அல்லது நோயை குறிப்பிடவும், விவசாய அறிவு தளத்திலிருந்து சிகிச்சை வழிகாட்டலை பெறலாம்."
            else:
                response = "I do not have a current disease in context. Upload an image or specify the disease to get treatment guidance from the agricultural knowledge base."
            return {"response": response, "context_used": False, "disease": None}

        treatments = disease_context["treatments"]
        if not treatments:
            if language == "ta":
                response = f"{disease_name} நோய்க்கான சிகிச்சை வழிகாட்டல் தற்போதைய தரவுத்தளத்தில் கிடைக்கவில்லை."
            else:
                response = f"I could not find treatment guidance for {disease_name} in the current database."
        else:
            treatment_names = "; ".join(f"{item[1]}" for item in treatments[:5])
            if language == "ta":
                response = f"{disease_name} நோய்க்கான சிகிச்சை விருப்பங்கள்: {treatment_names}. தற்போதைய அறிவு தளத்தைப் பயன்படுத்தி பொருள் லேபிள் மற்றும் வழிகாட்டல்களைப் பின்பற்றவும்."
            else:
                response = f"Treatment options for {disease_name} include: {treatment_names}. Use the disease-specific treatment guidance and product label instructions from the current knowledge base."
        return {"response": response, "context_used": True, "disease": disease_name}

    if any(keyword in lower_message for keyword in prevention_keywords):
        if disease_context is None:
            if language == "ta":
                response = "தற்போது எந்த நோய் சூழலும் இல்லை. படம் பதிவேற்றவும் அல்லது நோயை குறிப்பிடவும், தடுப்பு வழிமுறைகளை தரவுத்தளத்தில் பார்க்கலாம்."
            else:
                response = "I do not have a current disease in context. Upload an image or specify the disease to look up prevention guidance from the database."
            return {"response": response, "context_used": False, "disease": None}

        prevention = disease_context["prevention"]
        if not prevention:
            if language == "ta":
                response = f"{disease_name} நோய்க்கான தடுப்பு வழிமுறைகள் தற்போதைய தரவுத்தளத்தில் கிடைக்கவில்லை."
            else:
                response = f"I could not find prevention guidance for {disease_name} in the current database."
        else:
            prevention_lines = "; ".join(f"{item[1]}" for item in prevention[:5])
            if language == "ta":
                response = f"{disease_name} நோய்க்கான தடுப்பு வழிமுறைகள்: {prevention_lines}."
            else:
                response = f"Prevention guidance for {disease_name} includes: {prevention_lines}."
        return {"response": response, "context_used": True, "disease": disease_name}

    if any(keyword in lower_message for keyword in acreage_keywords):
        if disease_context is None:
            if language == "ta":
                response = "ஏக்கர் அடிப்படையில் சிகிச்சை அளவை கணக்கிடுவதற்கு தற்போதைய நோய் சூழல் தேவை. படத்தை பதிவேற்றவும் அல்லது நோயை குறிப்பிடவும்."
            else:
                response = "I need the current disease context to calculate acreage-based treatment requirements from the database. Please upload a plant image or specify the disease."
            return {"response": response, "context_used": False, "disease": None}

        acreage_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:acre|acres)", lower_message)
        acreage = float(acreage_match.group(1)) if acreage_match else None

        if acreage is None:
            if language == "ta":
                response = "ஏக்கர் எண்ணை குறிப்பிடும்போது நான் சிகிச்சை அளவை கணக்கிட முடியும். உதாரணம்: '2 ஏக்கருக்கு எவ்வளவு மருந்து வேண்டும்?'"
            else:
                response = "I can calculate acreage-based treatment needs when you specify the affected area in acres. For example: 'How much treatment do I need for 2 acres?'."
            return {"response": response, "context_used": True, "disease": disease_name}

        area_rates = []
        for row in disease_context["treatments"]:
            if row[6] is None:
                continue
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
                        "product": row[1],
                        "rate": float(rate_data["rate"]),
                        "unit": unit,
                        "method": rate_data["application_method"],
                        "basis": rate_data["basis"],
                    })

        if not area_rates:
            if language == "ta":
                response = f"தற்போதைய அறிவு தளத்தில் {disease_name} நோய்க்கான ஏக்கர் அடிப்படையிலான பயன்பாட்டு வீதம் கிடைக்கவில்லை. நான் யூகிக்க மாட்டேன்; தற்போதைய தயாரிப்பு லேபிள் மற்றும் விவசாய வழிகாட்டல்களை சரிபார்க்கவும்."
            else:
                response = f"The current knowledge base does not include a usable acreage-based application rate for {disease_name}. I should not guess a rate. Please verify the current product label and applicable agricultural guidance."
            return {"response": response, "context_used": True, "disease": disease_name}

        selected = area_rates[0]
        total_required = acreage * float(selected["rate"])
        if language == "ta":
            response = (
                f"தற்போதைய தரவுத்தள வீதத்தின்படி {selected['product']} தயாரிப்புக்கு {selected['rate']} {selected['unit']} ஒரு ஏக்கருக்கு வீதம் உள்ளது. "
                f"{acreage} ஏக்கருக்கு மதிப்பிடப்பட்ட மொத்த அளவு {total_required:.2f} {selected['unit']}. "
                f"சிகிச்சையைப் பயன்படுத்துவதற்கு முன் தயாரிப்பு லேபிள் மற்றும் உள்ளூர் விவசாய வழிகாட்டல்களை எப்போதும் சரிபார்க்கவும்."
            )
        else:
            response = (
                f"Using the current database rate for {selected['product']}, the rate is {selected['rate']} {selected['unit']} per acre. "
                f"For {acreage} acres, the estimated total is {total_required:.2f} {selected['unit']}. "
                f"Always verify the current product label and local agricultural guidance before applying the treatment."
            )
        return {"response": response, "context_used": True, "disease": disease_name}

    if any(keyword in lower_message for keyword in reliability_keywords):
        confidence_value = request.confidence
        if confidence_value is not None:
            if language == "ta":
                response = (
                    f"தற்போதைய AI கணிப்பு நம்பகத்தன்மை {confidence_value:.2f}%. இது பட அடிப்படையிலான மாதிரி கணிப்பு; குறைந்த நம்பகத்தன்மை இருந்தால் அது உறுதியான நோய் கண்டறிதலாக எடுத்துக்கொள்ளப்படக்கூடாது. புல மதிப்பீடு மற்றும் நிபுணர் வழிகாட்டல் ஆகியவற்றுடன் இணைந்து இதைப் பயன்படுத்துவது சிறந்தது."
                )
            else:
                response = (
                    f"The current AI prediction confidence is {confidence_value:.2f}%. This is an image-based model prediction and should not be treated as a guaranteed diagnosis, especially when confidence is low. It is best used as a support tool alongside field observation and expert guidance."
                )
        else:
            if language == "ta":
                response = "AI கணிப்பு ஒரு பட அடிப்படையிலான மாதிரி மதிப்பீடு மட்டுமே; இது உறுதியான நோய் கண்டறிதல் அல்ல. புல அவதானிப்பு மற்றும் நிபுணர் வழிகாட்டலுடன் சேர்த்து பயன்படுத்துவது சிறந்தது."
            else:
                response = "The AI prediction is an image-based model estimate and should not be treated as a guaranteed diagnosis. It is best used as a support tool alongside field observation and expert guidance."
        return {"response": response, "context_used": context_used, "disease": disease_name}

    if disease_context is not None:
        base_context = (
            f"{disease_name} நோய் கண்டறியப்பட்டது. " if language == "ta" else f"The detected disease is {disease_name}. "
        )
        base_context += (
            "தற்போதைய அறிவு தளத்தில் அறிகுறிகள், காரணங்கள், சிகிச்சை மற்றும் தடுப்பு வழிமுறைகள் உள்ளன. " if language == "ta" else "The current knowledge base includes symptoms, causes, treatments, and prevention guidance for this condition. "
        )

        if "what are the symptoms" in lower_message or "symptoms" in lower_message or "அறிகுறி" in lower_message or "அறிகுறிகள்" in lower_message:
            symptoms = disease_context["symptoms"]
            symptom_list = "; ".join(f"{item[1]}" for item in symptoms[:5])
            response = f"{base_context} {'அறிகுறிகள்:' if language == 'ta' else 'Symptoms include:'} {symptom_list}."
        elif "cause" in lower_message or "why" in lower_message or "காரணம்" in lower_message or "ஏன்" in lower_message:
            causes = disease_context["causes"]
            cause_list = "; ".join(f"{item[1]}" for item in causes[:5])
            response = f"{base_context} {'சாத்தியமான காரணங்கள்:' if language == 'ta' else 'Common causes include:'} {cause_list}."
        elif "treat" in lower_message or "சிகிச்சை" in lower_message:
            treatments = disease_context["treatments"]
            treatment_names = "; ".join(f"{item[1]}" for item in treatments[:5])
            if language == "ta":
                response = f"{base_context}சிகிச்சை விருப்பங்கள்: {treatment_names}. பயன்படுத்துவதற்கு முன் தயாரிப்பு லேபிள் மற்றும் உள்ளூர் விவசாய வழிகாட்டல்களைப் பின்பற்றவும்."
            else:
                response = f"{base_context}Treatment options include: {treatment_names}. Use the product label and local agricultural guidance when applying them."
        elif "prevent" in lower_message or "தடுப்பு" in lower_message:
            prevention = disease_context["prevention"]
            prevention_lines = "; ".join(f"{item[1]}" for item in prevention[:5])
            if language == "ta":
                response = f"{base_context}தடுப்பு வழிமுறைகள்: {prevention_lines}."
            else:
                response = f"{base_context}Prevention guidance includes: {prevention_lines}."
        else:
            if language == "ta":
                response = f"{base_context}அறிகுறிகள், காரணங்கள், சிகிச்சை, தடுப்பு மற்றும் ஏக்கர் அடிப்படையிலான சிகிச்சை பற்றிய கேள்விகளுக்கு நான் உதவ முடியும்."
            else:
                response = f"{base_context}I can help with symptoms, causes, treatments, prevention, and acreage-based treatment questions for the current disease."
        return {"response": response, "context_used": True, "disease": disease_name}

    if language == "ta":
        response = "நான் தற்போது Plant Guard AI விவசாய அறிவு தளத்தில் கவனம் செலுத்துகிறேன். ஒரு தாவரப் படத்தை பதிவேற்றவும் அல்லது பயிர் மற்றும் நோயின் பெயரை சொல்லவும், தரவுத்தளத்திலிருந்து அடிப்படையான பதிலை நான் வழங்குவேன்."
    else:
        response = "I currently focus on the Plant Guard AI agriculture knowledge base. Please upload a plant image or tell me the crop and disease name so I can provide a grounded answer from the database."
    return {"response": response, "context_used": False, "disease": None}
