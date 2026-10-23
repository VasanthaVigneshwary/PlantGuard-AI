from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pydantic import BaseModel, Field
import logging
import re
import io
import tempfile
from pathlib import Path
from PIL import Image
from ml.predict import predict_disease
from services.database_service import (
    get_disease_details_by_prediction,
    get_disease_details,
    get_disease_by_name,
    get_notifications as get_notification_records,
    save_prediction,
    get_prediction_history,
)


router = APIRouter()
logger = logging.getLogger(__name__)


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
    "Preview": "முன்னோட்டம்",
    "Selected plant leaf": "தேர்ந்தெடுக்கப்பட்ட தாவர இலை",
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
    "Source": "ஆதாரம்",
    "Source: TNAU Agritech Portal. Verify current product label and local approval before use.": "ஆதாரம்: TNAU Agritech Portal. பயன்பாட்டுக்கு முன் தற்போதைய தயாரிப்பு லேபிள் மற்றும் உள்ளூர் ஒப்புதலைச் சரிபார்க்கவும்.",
    "Plant image analyzed successfully 🌱": "தாவர படம் வெற்றிகரமாக பகுப்பாய்வு செய்யப்பட்டது 🌱",
    "Uncalibrated model score": "அளவுத்திருத்தம் செய்யப்படாத மாதிரி மதிப்பெண்",
    "This model score is not a calibrated probability, and unsupported images may still receive a class prediction. Treat the result as a candidate and verify it using plant symptoms or qualified agricultural guidance.": "இந்த மாதிரி மதிப்பெண் அளவுத்திருத்தம் செய்யப்பட்ட நிகழ்தகவு அல்ல; ஆதரிக்கப்படாத படங்களுக்கும் ஒரு வகுப்பு கணிப்பை வழங்கலாம். இந்த முடிவை சாத்தியமான குறியீடாகக் கருதி, தாவர அறிகுறிகள் அல்லது தகுதியான விவசாய வழிகாட்டுதலின் மூலம் சரிபார்க்கவும்.",
    "The image has little visual contrast or leaf detail. Please provide a clear, well-lit photo of a plant leaf. The model score is not calibrated.": "படத்தில் தெளிவான நிற வேறுபாடோ இலை விவரமோ போதவில்லை. நல்ல வெளிச்சத்தில் எடுக்கப்பட்ட தெளிவான இலைப் படத்தை வழங்கவும். மாதிரி மதிப்பெண் அளவுத்திருத்தம் செய்யப்படவில்லை.",
    "The image was analyzed, but prediction history could not be saved.": "படம் பகுப்பாய்வு செய்யப்பட்டது; ஆனால் கணிப்பு வரலாற்றைச் சேமிக்க முடியவில்லை.",
    "No major disease symptoms were detected by the model.": "மாடல் எந்த முக்கிய நோய் அறிகுறிகளையும் கண்டறியவில்லை.",
    "Continue monitoring the plant regularly.": "தாவரத்தை தொடர்ந்து கண்காணிக்கவும்.",
    "No disease treatment is currently required based on this prediction.": "இந்த கணிப்பின் அடிப்படையில் தற்போது நோய் சிகிச்சை தேவையில்லை.",
    "Continue regular plant care and monitoring.": "வழக்கமான தாவர பராமரிப்பு மற்றும் கண்காணிப்பை தொடரவும்.",
    "The AI model detected a possible plant disease. This result should be treated as an AI-based indication rather than a confirmed diagnosis.": "AI மாடல் சாத்தியமான தாவர நோயைக் கண்டறிந்துள்ளது. இது உறுதிப்படுத்தப்பட்ட நோய் கண்டறிதல் அல்ல; AI அடிப்படையிலான குறிகாட்டியாகவே பார்க்கப்பட வேண்டும்.",
    "Dark leaf lesions": "இலைகளில் கருமையான புள்ளிகள்",
    "Fruit lesions": "பழங்களில் புண்கள்",
    "Fruit rot": "பழ அழுகல்",
    "High humidity": "அதிக ஈரப்பதம்",
    "Excess leaf wetness": "இலைகளின் அதிக ஈரப்புத்தன்மை",
    "Poor air circulation": "மோசமான காற்றோட்டம்",
    "Favorable temperature": "சிறந்த வெப்பநிலை",
    "Late Blight Management": "லேட் ப்ளைட் மேலாண்மை",
    "Late Blight Management (Disease management)": "லேட் ப்ளைட் மேலாண்மை (நோய் மேலாண்மை)",
    "Disease management": "நோய் மேலாண்மை",
    "Integrated management of tomato late blight": "தக்காளி லேட் ப்ளைட்டை ஒருங்கிணைந்த முறையில் மேலாண்மை செய்தல்",
    "Foliar spray": "இலைத் தெளிப்பு",
    "Good air circulation": "சிறந்த காற்றோட்டம்",
    "Improve air circulation": "காற்றோட்டத்தை மேம்படுத்தவும்",
    "Avoid prolonged leaf wetness": "இலைகளில் நீண்ட நேரம் ஈரப்பதம் இருக்காமல் தவிர்க்கவும்",
    "Remove infected plant material": "பாதிக்கப்பட்ட தாவரப் பொருட்களை அகற்றவும்",
    "Use healthy planting material": "ஆரோக்கியமான நாற்று/விதை பொருளைப் பயன்படுத்தவும்",
    "Monitor crops regularly": "பயிர்களை தொடர்ந்து கண்காணிக்கவும்",
    "Apply as needed": "தேவைக்கேற்பப் பயன்படுத்தவும்",
    "Apply as directed": "வழிமுறைகள்: வழிமுறைகளின்படி பயன்படுத்தவும்",
    "Use as directed": "வழிமுறைகள்: வழிமுறைகளின்படி பயன்படுத்தவும்",
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
    "Basis": "அடிப்படை",
    "per acre": "ஒரு ஏக்கருக்கு",
    "per unit": "ஒரு அலகுக்கு",
    "per plant": "ஒரு செடியுக்கு",
    "Application rate": "பயன்பாட்டு வீதம்",
    "Application method": "பயன்பாட்டு முறை",
    "Treatment group": "சிகிச்சை குழு",
    "No treatment information is available.": "சிகிச்சை தகவல் தற்போது கிடைக்கவில்லை.",
    "Enter a valid affected area greater than zero.": "சரியான பாதிக்கப்பட்ட பரப்பளவை (பூஜ்ஜியத்தை விட அதிகமாக) உள்ளிடவும்.",
    "Enter the area of the crop that needs treatment.": "சிகிச்சை தேவைப்படும் பயிரின் பரப்பளவைக் குறிப்பிடவும்.",
    "Treatment": "சிகிச்சை",
    "Prevention": "தடுப்பு",
    "Symptoms": "அறிகுறிகள்",
    "Causes": "காரணங்கள்",
}

DISPLAY_NAME_TRANSLATIONS = {
    "Tomato": "தக்காளி",
    "Tomato Late Blight": "தக்காளி லேட் ப்ளைட்",
    "Tomato Early Blight": "தக்காளி ஆரம்பகால ப்ளைட்",
    "Tomato Leaf Mold": "தக்காளி இலை பூஞ்சை",
    "Tomato Septoria Leaf Spot": "தக்காளி செப்டோரியா இலைப்புள்ளி",
    "Tomato Spider Mites": "தக்காளி சிலந்தி பேன் தாக்குதல்",
    "Tomato Target Spot": "தக்காளி டார்கெட் புள்ளி",
    "Tomato Yellow Leaf Curl Virus": "தக்காளி மஞ்சள் இலை சுருள் வைரஸ்",
    "Tomato Mosaic Virus": "தக்காளி மொசைக் வைரஸ்",
    "Tomato Healthy": "தக்காளி ஆரோக்கியமானது",
    "Potato": "உருளைக்கிழங்கு",
    "Potato Late Blight": "உருளைக்கிழங்கு லேட் ப்ளைட்",
    "Potato Early Blight": "உருளைக்கிழங்கு ஆரம்பகால ப்ளைட்",
    "Potato Healthy": "உருளைக்கிழங்கு ஆரோக்கியமானது",
    "Apple": "ஆப்பிள்",
    "Apple Scab": "ஆப்பிள் ஸ்கேப் புள்ளி",
    "Apple Black Rot": "ஆப்பிள் பிளாக் ராட் அழுகல்",
    "Cedar Apple Rust": "சிடார் ஆப்பிள் துரு நோய்",
    "Apple Healthy": "ஆப்பிள் ஆரோக்கியமானது",
    "Blueberry": "புளூபெர்ரி",
    "Blueberry Healthy": "புளூபெர்ரி ஆரோக்கியமானது",
    "Cherry": "செர்ரி",
    "Cherry Powdery Mildew": "செர்ரி பவுடரி மில்டெவ்",
    "Cherry Healthy": "செர்ரி ஆரோக்கியமானது",
    "Corn": "சோளம்",
    "Corn Gray Leaf Spot": "சோளம் சாம்பல் இலைப்புள்ளி",
    "Corn Common Rust": "சோளம் பொதுவான துரு நோய்",
    "Corn Northern Leaf Blight": "சோளம் வடக்கு இலை கருகல்",
    "Corn Healthy": "சோளம் ஆரோக்கியமானது",
    "Grape": "திராட்சை",
    "Grape Black Rot": "திராட்சை கருப்பு அழுகல்",
    "Grape Esca (Black Measles)": "திராட்சை எஸ்கா தண்டு நோய்",
    "Grape Leaf Blight": "திராட்சை இலை கருகல்",
    "Grape Healthy": "திராட்சை ஆரோக்கியமானது",
    "Orange": "ஆரஞ்சு",
    "Citrus Greening (Huanglongbing)": "சிட்ரஸ் கிரீனிங் நோய்",
    "Peach": "பீச்",
    "Peach Bacterial Spot": "பீச் பாக்டீரியா புள்ளி",
    "Peach Healthy": "பீச் ஆரோக்கியமானது",
    "Pepper, Bell": "குடைமிளகாய்",
    "Pepper Bell Bacterial Spot": "குடைமிளகாய் பாக்டீரியா புள்ளி",
    "Pepper Bell Healthy": "குடைமிளகாய் ஆரோக்கியமானது",
    "Raspberry": "ராஸ்பெர்ரி",
    "Raspberry Healthy": "ராஸ்பெர்ரி ஆரோக்கியமானது",
    "Soybean": "சோயாபீன்",
    "Soybean Healthy": "சோயாபீன் ஆரோக்கியமானது",
    "Squash": "பூசணி",
    "Squash Powdery Mildew": "பூசணி சாம்பல் நோய்",
    "Strawberry": "ஸ்ட்ராபெர்ரி",
    "Strawberry Leaf Scorch": "ஸ்ட்ராபெர்ரி இலை கருகல்",
    "Strawberry Healthy": "ஸ்ட்ராபெர்ரி ஆரோக்கியமானது",
    "Rice": "நெல்",
    "Rice Blast": "நெல் குலை நோய்",
    "Rice Brown Spot": "நெல் பழுப்பு புள்ளி",
    "Cotton": "பருத்தி",
    "Cotton Leaf Curl Disease": "பருத்தி இலை சுருள் நோய்",
    "Cotton Bacterial Blight": "பருத்தி பாக்டீரியா கருகல்",
    "Chilli": "மிளகாய்",
    "Chilli Anthracnose": "மிளகாய் ஆந்த்ராக்னோஸ்",
    "Chilli Leaf Curl Disease": "மிளகாய் இலை சுருள் நோய்",
    "Late blight": "லேட் ப்ளைட்",
    "Early blight": "ஆரம்பகால ப்ளைட்",
    "Powdery mildew": "பவுடரி மில்டெவ்",
    "Bacterial spot": "பாக்டீரியா ஸ்பாட்",
    "Leaf spot": "இலை புள்ளி",
    "Apple scab": "ஆப்பிள் ஸ்கேப்",
    "Black rot": "கருப்பு அழுகல்",
    "Healthy": "ஆரோக்கியமானது",
}


def localize_display_name(value, language):
    if language != "ta" or not isinstance(value, str):
        return value

    normalized = value.strip()
    for english_text, tamil_text in sorted(DISPLAY_NAME_TRANSLATIONS.items(), key=lambda item: len(item[0]), reverse=True):
        if normalized.lower() == english_text.lower():
            return tamil_text

    for english_text, tamil_text in sorted(DISPLAY_NAME_TRANSLATIONS.items(), key=lambda item: len(item[0]), reverse=True):
        if english_text.lower() in normalized.lower():
            return normalized.replace(english_text, tamil_text)

    return normalized


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
    localized["status"] = localize_text_for_language(payload.get("status"), language)
    localized["uncertainty_warning"] = localize_text_for_language(payload.get("uncertainty_warning"), language)
    localized["history_warning"] = localize_text_for_language(payload.get("history_warning"), language)

    disease = localized.get("disease", {})
    if isinstance(disease, dict):
        disease["name"] = localize_display_name(disease.get("name"), language)
        disease["crop_name"] = localize_display_name(disease.get("crop_name"), language)
        disease["description"] = localize_text_for_language(disease.get("description"), language)

    symptoms = localized.get("symptoms", [])
    for symptom in symptoms:
        symptom["name"] = localize_display_name(localize_text_for_language(symptom.get("name"), language), language)
        symptom["description"] = localize_text_for_language(symptom.get("description"), language)

    causes = localized.get("causes", [])
    for cause in causes:
        cause["name"] = localize_display_name(localize_text_for_language(cause.get("name"), language), language)
        cause["description"] = localize_text_for_language(cause.get("description"), language)

    treatments = localized.get("treatments", [])
    for treatment in treatments:
        treatment["name"] = localize_display_name(localize_text_for_language(treatment.get("name"), language), language)
        treatment["type"] = localize_display_name(localize_text_for_language(treatment.get("type"), language), language)
        treatment["description"] = localize_text_for_language(treatment.get("description"), language)
        treatment["instructions"] = localize_text_for_language(treatment.get("instructions"), language)
        treatment["precautions"] = localize_text_for_language(treatment.get("precautions"), language)

        for rate in treatment.get("application_rates", []):
            rate["application_method"] = localize_display_name(localize_text_for_language(rate.get("application_method"), language), language)
            rate["measurement_unit"] = localize_display_name(localize_text_for_language(rate.get("measurement_unit"), language), language)
            rate["basis"] = localize_display_name(localize_text_for_language(rate.get("basis"), language), language)
            rate["notes"] = localize_text_for_language(rate.get("notes"), language)

    prevention = localized.get("prevention", [])
    for item in prevention:
        item["title"] = localize_display_name(localize_text_for_language(item.get("title"), language), language)
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


@router.get("/history")
def get_history_endpoint(limit: int = 20):
    """Retrieve recent plant diagnosis history from PostgreSQL."""
    history = get_prediction_history(limit=limit)

    return {
        "count": len(history),
        "history": history,
    }


# --------------------------------------------------
# PLANT IMAGE UPLOAD + AI PREDICTION
# --------------------------------------------------

@router.post("/upload")
async def upload_plant_image(
    file: UploadFile = File(...),
    language: str | None = Form("en"),
):
    # Read at most the limit plus one byte so a large request is not loaded whole.
    max_upload_bytes = 10 * 1024 * 1024
    contents = await file.read(max_upload_bytes + 1)
    if not contents:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty. Please select a valid plant leaf image."
        )

    if len(contents) > max_upload_bytes:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds the 10MB limit. Please upload a smaller image."
        )

    # Validate actual image content; do not trust the filename or MIME header.
    try:
        image_stream = io.BytesIO(contents)
        with Image.open(image_stream) as img:
            img_format = (img.format or "").upper()
            if img_format not in {"JPEG", "JPG", "PNG", "WEBP"}:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported image format ({img_format}). Only JPG, JPEG, PNG, and WEBP images are allowed."
                )
            width, height = img.size
            if width < 32 or height < 32:
                raise HTTPException(
                    status_code=400,
                    detail="Image resolution is too low for reliable leaf disease diagnosis."
                )
            if width * height > 40_000_000:
                raise HTTPException(
                    status_code=400,
                    detail="Image dimensions are too large. Please upload a smaller image."
                )
            img.verify()
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is not a valid, readable image. Please choose a JPG, PNG, or WEBP photo."
        )

    # 2. Use a generated temporary name and always remove the upload after inference.
    upload_folder = Path(__file__).resolve().parents[1] / "uploads"
    upload_folder.mkdir(parents=True, exist_ok=True)
    file_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix="upload_", suffix=".img", dir=upload_folder, delete=False
        ) as buffer:
            file_path = Path(buffer.name)
            buffer.write(contents)

        result = predict_disease(file_path)
    except Exception as exc:
        logger.exception("Plant image inference failed")
        raise HTTPException(
            status_code=500,
            detail="The model could not analyze this image. Please try another clear leaf photo."
        ) from exc
    finally:
        if file_path is not None:
            try:
                file_path.unlink(missing_ok=True)
            except OSError:
                logger.warning("Could not remove temporary plant image")

    # 4. Lookup database record for the predicted class
    try:
        disease_data = get_disease_details_by_prediction(result["disease"])
    except Exception as exc:
        logger.exception("Plant disease knowledge lookup failed")
        raise HTTPException(
            status_code=503,
            detail="The plant knowledge database is unavailable. Please try again later."
        ) from exc

    if disease_data is not None:
        disease = disease_data["disease"]
        disease_id = disease[0]
        disease_name = disease[1]
        crop_name = disease[2]
        description = disease[3]

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

        symptoms_list = [
            {"id": s[0], "name": s[1], "description": s[2]}
            for s in disease_data["symptoms"]
        ]
        causes_list = [
            {"id": c[0], "name": c[1], "description": c[2]}
            for c in disease_data["causes"]
        ]
        prevention_list = [
            {"id": p[0], "title": p[1], "description": p[2]}
            for p in disease_data["prevention"]
        ]
    else:
        # Honest fallback if a class is not yet monograph-seeded
        disease_id = None
        disease_name = result["condition"]
        crop_name = result["crop"]
        description = None
        treatments = {}
        symptoms_list = []
        causes_list = []
        prevention_list = []

    # 5. Persist prediction history to PostgreSQL
    prediction_id = None
    history_warning = None
    try:
        prediction_id = save_prediction(
            crop_id=None,
            crop_name=crop_name,
            disease_id=disease_id,
            confidence=result["confidence"],
            image_url=None,
            model_version="efficientnet_v2_s"
        )
    except Exception:
        logger.exception("Prediction history could not be saved")
        history_warning = "The image was analyzed, but prediction history could not be saved."

    normalized_language = normalize_language(language)
    response = {
        "message": "Plant image analyzed successfully 🌱",
        "filename": re.split(r"[/\\]", file.filename or "")[-1],
        "prediction": result["disease"],
        "confidence": result["confidence"],
        "status": result["status"],
        "uncertainty_warning": result.get("uncertainty_warning"),
        "is_healthy": result.get("is_healthy", False),
        "prediction_id": prediction_id,
        "history_saved": prediction_id is not None,
        "history_warning": history_warning,
        "top_predictions": result.get("top_predictions", []),
        "disease": {
            "id": disease_id,
            "name": disease_name,
            "crop_name": crop_name,
            "description": description
        },
        "symptoms": symptoms_list,
        "causes": causes_list,
        "treatments": list(treatments.values()),
        "prevention": prevention_list
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
        "symptom", "symptoms", "signs", "identify", "look for", "how do i know",
        "அறிகுறி", "அறிகுறிகள்", "அடையாளம்", "என்ன அறிகுறிகள்", "அறிகுறிகள் என்ன", "எந்த அறிகுறிகள்", "எப்படி அறிகுறிகள்", "அறிகுறிகள் எப்படி",
    ]
    cause_keywords = [
        "cause", "causes", "why did this happen", "what caused", "what causes this", "why is this happening", "how did this happen",
        "காரணம்", "காரணங்கள்", "காரணம் என்ன", "என்ன காரணம்", "ஏன்", "ஏன் ஏற்பட்டது", "எப்படி ஏற்பட்டது", "என்ன காரணங்கள்",
    ]
    treatment_keywords = [
        "treat", "treatment", "cure", "medicine", "medication", "control this disease", "how can i manage", "how to cure", "how to treat", "what should i do",
        "சிகிச்சை", "சிகிச்சை என்ன", "எப்படி சிகிச்சை", "சிகிச்சை எப்படி", "குணப்படுத்த", "மருந்து", "மருந்து எப்படி", "கட்டுப்படுத்த", "என்ன செய்ய வேண்டும்", "எப்படி நடத்துவது", "எப்படி செய்வது",
    ]
    prevention_keywords = [
        "prevent", "prevention", "precaution", "avoid", "stop it from spreading", "keep it from spreading",
        "தடுப்பு", "தடுக்க", "தவிர்க்க", "தடுப்பது", "தடுப்பு எப்படி", "எப்படி தடுப்பது", "எப்படி பரவாமல்", "பரவாமல்", "பரவாமல் தடுக்க", "பரவாமல் இருப்பது", "தடுக்க எப்படி",
    ]
    acreage_keywords = [
        "acre", "acres", "quantity", "amount", "how much", "how many", "application rate", "dosage", "how much treatment", "how much should i apply", "per acre",
        "ஏக்கர்", "ஏக்கர்களில்", "ஏக்கருக்கு", "அளவு", "எவ்வளவு", "தேவை", "மருந்து அளவு", "எவ்வளவு மருந்து", "மருந்து எவ்வளவு", "எவ்வளவு மருந்து வேண்டும்",
    ]
    disease_keywords = [
        "what disease", "detected disease", "what is the disease", "what disease is this", "what disease does my plant have", "what is this disease", "what disease is this plant",
        "என்ன நோய்", "நோய் என்ன", "இந்த நோய்", "இது என்ன நோய்", "என்ன நோய் இது", "நோய் எது", "இந்த நோய் என்ன", "எது நோய்",
    ]
    reliability_keywords = [
        "reliable", "trust", "accurate", "confidence", "sure",
        "நம்பகமான", "நம்பிக்கை", "உறுதி", "துல்லியம்", "நம்பகத்தன்மை", "நம்பகமானது",
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

    if any(keyword in lower_message for keyword in acreage_keywords):
        if disease_context is None:
            if language == "ta":
                response = "ஏக்கர் அடிப்படையில் சிகிச்சை அளவை கணக்கிடுவதற்கு தற்போதைய நோய் சூழல் தேவை. படத்தை பதிவேற்றவும் அல்லது நோயை குறிப்பிடவும்."
            else:
                response = "I need the current disease context to calculate acreage-based treatment requirements from the database. Please upload a plant image or specify the disease."
            return {"response": response, "context_used": False, "disease": None}

        acreage_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:acre|acres|ஏக்கர்|ஏக்கர்களில்|ஏக்கருக்கு)", lower_message)
        acreage = float(acreage_match.group(1)) if acreage_match else None

        if acreage is None:
            if language == "ta":
                response = "ஏக்கர் எண்ணை குறிப்பிடும்போது நான் சிகிச்சை அளவை கணக்கிட முடியும். உதாரணம்: '2 ஏக்கருக்கு எவ்வளவு மருந்து வேண்டும்?'"
            else:
                response = "I can calculate acreage-based treatment needs when you specify the affected area in acres. For example: 'How much treatment do I need for 2 acres?'."
            return {"response": response, "context_used": True, "disease": disease_name}

        area_rates = []
        for row in disease_context["treatments"]:
            if len(row) <= 6 or row[6] is None:
                continue
            rate_data = {
                "id": row[6],
                "application_method": row[7] if len(row) > 7 else None,
                "measurement_unit": row[8] if len(row) > 8 else None,
                "rate": float(row[9]) if len(row) > 9 and row[9] is not None else None,
                "basis": row[10] if len(row) > 10 else None,
                "notes": row[11] if len(row) > 11 else None,
            }
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
