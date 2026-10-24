"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  calculateTreatmentQuantity,
  getCalculableAreaRates,
  validateAreaInput,
} from "../lib/treatment-calculator.mjs";

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

interface PredictionResult {
  message?: string;
  filename?: string;
  prediction: string;
  confidence: number;
  status?: string;
  uncertainty_warning?: string | null;
  is_healthy?: boolean;
  history_saved?: boolean;
  history_warning?: string | null;
  disease: {
    id: number | null;
    name: string;
    crop_name: string;
    description: string | null;
  };
  symptoms: {
    id: number;
    name: string;
    description: string;
  }[];
  causes: {
    id: number;
    name: string;
    description: string;
  }[];
  treatments: {
    id: number;
    name: string;
    type: string;
    description: string;
    instructions: string;
    precautions: string;
    application_rates: {
      id: number;
      application_method: string | null;
      measurement_unit: string;
      rate: number | null;
      basis: string;
      notes: string;
      verified: boolean;
      product_formulation: string;
      source_url: string;
      disease_id: number;
    }[];
  }[];
  prevention: {
    id: number;
    title: string;
    description: string;
  }[];
}

interface HistoryItem {
  id: number;
  confidence: number | null;
  created_at: string | null;
  crop_name: string;
  disease_name: string;
  disease_id: number | null;
  model_version: string | null;
}

interface DatabaseDiseaseInfo {
  about: string | null;
  symptoms: PredictionResult["symptoms"];
  causes: PredictionResult["causes"];
  treatment: PredictionResult["treatments"];
  prevention: PredictionResult["prevention"];
}

interface NotificationItem {
  id: number;
  user_id: number | null;
  prediction_id: number | null;
  title: string;
  message: string;
  notification_type: string | null;
  scheduled_at: string | null;
  is_read: boolean;
  created_at: string | null;
}

type Language = "en" | "ta";

const translations: Record<Language, Record<string, string>> = {
  en: {
    navHome: "Home",
    navDetect: "Detect",
    navHow: "How It Works",
    navAbout: "About",
    navHistory: "History",
    historyTitle: "Prediction History",
    historySubtitle: "Saved model results from PostgreSQL. Uploaded images are not retained.",
    historyLoading: "Loading prediction history...",
    historyEmpty: "No saved predictions yet.",
    historyError: "Unable to load prediction history.",
    retry: "Retry",
    notifications: "Notifications",
    notificationsSubtitle: "Plant health updates",
    notificationsLoading: "Loading notifications...",
    notificationsClose: "Close",
    notificationsEmpty: "No notifications right now. Check back later for plant-care reminders.",
    noNotifications: "No notifications right now.",
    assistantOnline: "Assistant online",
    analyzeAnotherPlant: "Analyze Another Plant",
    welcomeBot: "Hi! 🌱 I'm Plant Guard AI. Ask me about plant diseases, symptoms, prevention, or how to use the disease detector.",
    heroBadge: "AI-powered plant health detection",
    heroCTA: "🔍 Detect Disease",
    heroSecondary: "How It Works →",
    heroMain: "Protect your plants with intelligent AI.",
    heroSubtitle: "Upload a plant leaf image and Plant Guard AI uses deep learning to identify possible diseases and provide useful plant-care guidance.",
    uploadLabel: "Upload leaf image",
    chooseImage: "Choose Image",
    analyzePlant: "Analyze Plant",
    chooseAnother: "Choose Another",
    readyToAnalyze: "Ready to analyze",
    plantHealthScanner: "Plant Health Scanner",
    aiAnalysis: "AI Analysis",
    aiModel: "AI Model",
    confidence: "Model Score",
    guidance: "Guidance",
    detectedCondition: "Detected Condition",
    candidateCondition: "Model's Candidate Classification",
    candidateCrop: "Candidate crop class:",
    modelConfidence: "Raw Model Score (Not Calibrated)",
    whatDoesThisMean: "What does this result mean?",
    aboutCondition: "About This Condition",
    commonSymptoms: "Common Symptoms",
    possibleCauses: "Possible Causes",
    treatment: "Treatment",
    applicationRates: "Application Rates",
    preventionTips: "Prevention Tips",
    treatmentCalculator: "Treatment Calculator",
    affectedArea: "Affected area",
    acres: "Acres",
    areaHelp: "Enter the affected area in acres. Calculation uses exact per-acre units only.",
    areaEmpty: "Enter the affected area.",
    areaInvalid: "Enter a valid number using digits and a decimal point only.",
    areaPositive: "Affected area must be greater than zero.",
    rateUnavailable: "Calculation is unavailable because no verified rate matches this disease, product/formulation, and supported area unit. Your area is not used to estimate a dose.",
    sourceReference: "Verified source",
    selectedProduct: "Selected Product",
    applicationMethod: "Application Method",
    rate: "Rate",
    requiredQuantity: "Required Quantity",
    buildProcess: "Simple Process",
    howWorks: "How Plant Guard AI works",
    upload: "Upload",
    getGuidance: "Get Guidance",
    keyFeatures: "Key Features",
    aiDetection: "AI Detection",
    confidenceScore: "Raw Model Score",
    plantGuidance: "Plant Guidance",
    aiAssistant: "AI Assistant",
    aboutProject: "About The Project",
    startAnalysis: "Start Analysis",
    importantDisclaimer: "Important Disclaimer",
    chatPlaceholder: "Ask about plant health...",
    chatThinking: "Thinking...",
    chatbotTitle: "Plant Guard AI",
    plantHealthAssistant: "AI Plant Health Assistant",
    chatInline: "Assistant online",
    diseaseDetection: "Disease Detection",
    analyzePlantTitle: "Analyze your plant",
    analyzePlantSubtitle: "Upload a clear image of a plant leaf and let the AI model analyze it.",
    selectFilePrompt: "Choose a clear photo showing the plant leaf. Better images can help the model produce a more useful prediction.",
    supportedFormats: "Supported image formats: JPG, JPEG, PNG, WEBP",
    selectedImage: "Selected image",
    plantImagePreview: "Your plant image",
    ready: "Ready",
    modelLabel: "AI Result",
    plantAnalysisComplete: "Plant analysis complete",
    predictionSummary: "Here is the prediction generated by Plant Guard AI.",
    aboutProjectText: "About The Project",
    quickNavigation: "Quick Navigation",
    projectLabel: "Project",
    languageLabel: "Language",
    english: "English",
    tamil: "தமிழ்",
    deepLearning: "Deep Learning",
    imageAnalysis: "Image Analysis",
    plantCare: "Plant Care",
    detectionSystem: "Detection system",
    poweredDetection: "Powered Detection",
    modelClasses: "Model Classes",
    digitalAssistance: "Digital Assistance",
    simpleProcess: "Simple Process",
    howItWorksIntro: "From image upload to useful plant health guidance in three simple steps.",
    step01: "STEP 01",
    step02: "STEP 02",
    step03: "STEP 03",
    howUploadDescription: "Upload a clear image of a plant leaf using the Plant Guard AI disease detector.",
    howProcessingDescription: "The image is processed by the FastAPI backend and analyzed using a trained deep learning model.",
    howGuidanceDescription: "View the predicted disease, confidence score, symptoms, recommended action and prevention tips.",
    featureRecognition: "Deep learning based plant disease prediction.",
    featureConfidence: "Understand how confident the model is in its prediction.",
    featureGuidance: "View symptoms, treatment actions and prevention tips.",
    featureAssistant: "Ask basic questions about plant health using the assistant.",
    healthierPlants: "Technology for healthier plants",
    projectIntro: "Plant Guard AI is a student mini-project that demonstrates how artificial intelligence and deep learning can assist with plant disease identification.",
    projectSystem: "The system combines a modern Next.js frontend with a FastAPI backend and a trained EfficientNet-based image classification model.",
    tryDiseaseDetection: "Try Disease Detection",
    platformDescription: "An AI-assisted plant health platform designed to make disease identification easier and more accessible.",
    featureDiseaseDetection: "AI-Powered Disease Detection",
    featureDiseaseDetectionText: "Identifies possible plant diseases from uploaded leaf images.",
    featureConfidenceResults: "Confidence-Based Results",
    featureConfidenceResultsText: "Displays the AI prediction along with its confidence score.",
    featureInfoSymptoms: "Disease Information and Symptoms",
    featureInfoSymptomsText: "Provides useful information about detected conditions and symptoms.",
    featureTreatmentPrevention: "Treatment and Prevention Guidance",
    featureTreatmentPreventionText: "Suggests practical plant-care actions and prevention measures.",
    featureTreatmentCalculator: "Treatment Calculator",
    featureTreatmentCalculatorText: "Estimates treatment quantity based on affected area and the agricultural application rate.",
    readyCheckPlant: "Ready to check your plant?",
    ctaDescription: "Upload a plant leaf image and explore what Plant Guard AI can detect.",
    footerSummary: "AI-powered plant disease detection and plant-care assistance.",
    quickNav: "Quick Navigation",
    homeLink: "Home",
    diseaseDetectionLink: "Disease Detection",
    howItWorksLink: "How It Works",
    aboutLink: "About",
    projectLink: "Project",
    miniProject: "Mini Project",
    footerCopyright: "© 2026 Plant Guard AI. Built as an academic mini-project.",
    techFooterText: "AI Plant Health Assistant",
    statusLabel: "Detection system",
  },
  ta: {
    navHome: "முகப்பு",
    navDetect: "கண்டறிதல்",
    navHow: "இது எப்படி வேலை செய்கிறது",
    navAbout: "பற்றி",
    navHistory: "வரலாறு",
    historyTitle: "கணிப்பு வரலாறு",
    historySubtitle: "PostgreSQL-இல் சேமிக்கப்பட்ட மாதிரி முடிவுகள். பதிவேற்றிய படங்கள் சேமிக்கப்படுவதில்லை.",
    historyLoading: "கணிப்பு வரலாறு ஏற்றப்படுகிறது...",
    historyEmpty: "சேமிக்கப்பட்ட கணிப்புகள் எதுவும் இல்லை.",
    historyError: "கணிப்பு வரலாற்றை ஏற்ற முடியவில்லை.",
    retry: "மீண்டும் முயற்சி",
    notifications: "அறிவிப்புகள்",
    notificationsSubtitle: "தாவர ஆரோக்கிய புதுப்பிப்புகள்",
    notificationsLoading: "அறிவிப்புகள் ஏற்றப்படுகின்றன...",
    notificationsClose: "மூடு",
    notificationsEmpty: "தற்சமயம் அறிவிப்புகள் இல்லை. சிறிது நேரம் கழித்து மீண்டும் பார்க்கவும்.",
    noNotifications: "தற்சமயம் அறிவிப்புகள் இல்லை.",
    assistantOnline: "செயல்பாட்டில் உள்ளது",
    analyzeAnotherPlant: "மற்றொரு தாவரத்தை பகுப்பாய்வு செய்யுங்கள்",
    welcomeBot: "வணக்கம்! 🌱 நான் Plant Guard AI. தாவர நோய்கள், அறிகுறிகள், தடுப்பு அல்லது நோய் கண்டறிதல் பற்றி கேளுங்கள்.",
    heroBadge: "AI-ஆல் இயக்கப்படும் தாவர ஆரோக்கிய கண்டறிதல்",
    heroCTA: "🔍 நோயைக் கண்டறி",
    heroSecondary: "இது எப்படி வேலை செய்கிறது →",
    heroMain: "நுண்ணறிவுள்ள AI-வுடன் உங்கள் தாவரங்களை பாதுகாக்கவும்.",
    heroSubtitle: "ஒரு தாவர இலைப் படத்தை பதிவேற்றி, Plant Guard AI சாத்தியமான நோய்களைக் கண்டறிந்து பயனுள்ள பராமரிப்புக் குறிப்புகளை வழங்குகிறது.",
    uploadLabel: "இலைப் படத்தை பதிவேற்றுக",
    chooseImage: "படத்தை தேர்ந்தெடு",
    analyzePlant: "தாவரத்தை பகுப்பாய்வு செய்",
    chooseAnother: "மற்றொரு படத்தை தேர்ந்தெடு",
    readyToAnalyze: "பகுப்பாய்வு தயாராக உள்ளது",
    plantHealthScanner: "தாவர ஆரோக்கிய ஸ்கேனர்",
    aiAnalysis: "AI பகுப்பாய்வு",
    aiModel: "AI மாதிரி",
    confidence: "மாதிரி மதிப்பெண்",
    guidance: "வழிகாட்டல்",
    detectedCondition: "கண்டறியப்பட்ட நிலை",
    candidateCondition: "மாதிரியின் சாத்தியமான வகைப்பாடு",
    candidateCrop: "சாத்தியமான பயிர் வகுப்பு:",
    modelConfidence: "மாதிரியின் மூல மதிப்பெண் (அளவுத்திருத்தம் செய்யப்படவில்லை)",
    whatDoesThisMean: "இந்த முடிவு அர்த்தப்படுத்துவது எது?",
    aboutCondition: "இந்த நிலை பற்றிய தகவல்",
    commonSymptoms: "பொதுவான அறிகுறிகள்",
    possibleCauses: "சாத்தியமான காரணங்கள்",
    treatment: "சிகிச்சை",
    applicationRates: "பயன்பாட்டு வீதங்கள்",
    preventionTips: "தடுப்பு குறிப்புகள்",
    treatmentCalculator: "சிகிச்சை கால்குலேட்டர்",
    affectedArea: "பாதிக்கப்பட்ட பகுதி",
    acres: "ஏக்கர்",
    areaHelp: "பாதிக்கப்பட்ட பரப்பை ஏக்கரில் உள்ளிடவும். கணக்கீடு ஏக்கருக்கான பொருந்தும் அலகுகளை மட்டுமே பயன்படுத்தும்.",
    areaEmpty: "பாதிக்கப்பட்ட பரப்பை உள்ளிடவும்.",
    areaInvalid: "எண்கள் மற்றும் தசமப் புள்ளியை மட்டும் பயன்படுத்தி சரியான எண்ணை உள்ளிடவும்.",
    areaPositive: "பாதிக்கப்பட்ட பரப்பு பூஜ்ஜியத்தை விட அதிகமாக இருக்க வேண்டும்.",
    rateUnavailable: "இந்த நோய், தயாரிப்பு/கலவை மற்றும் ஆதரிக்கப்படும் பரப்பளவு அலகுக்கு சரிபார்க்கப்பட்ட வீதம் இல்லை; கணக்கீடு கிடைக்காது. உங்கள் பரப்பளவை மருந்தளவை ஊகிக்கப் பயன்படுத்தமாட்டோம்.",
    sourceReference: "சரிபார்க்கப்பட்ட ஆதாரம்",
    selectedProduct: "தேர்ந்தெடுக்கப்பட்ட தயாரிப்பு",
    applicationMethod: "பயன்பாட்டு முறை",
    rate: "வீதம்",
    requiredQuantity: "தேவையான அளவு",
    buildProcess: "எளிய செயல்முறை",
    howWorks: "Plant Guard AI எப்படி வேலை செய்கிறது",
    upload: "பதிவேற்றம்",
    getGuidance: "வழிகாட்டலைப் பெறுக",
    keyFeatures: "முக்கிய அம்சங்கள்",
    aiDetection: "AI கண்டறிதல்",
    confidenceScore: "மாதிரியின் மூல மதிப்பெண்",
    plantGuidance: "தாவர வழிகாட்டல்",
    aiAssistant: "AI உதவியாளர்",
    aboutProject: "திட்டம் பற்றி",
    startAnalysis: "பகுப்பாய்வை தொடங்கு",
    importantDisclaimer: "முக்கிய அறிவிப்பு",
    chatPlaceholder: "தாவர ஆரோக்கியம் பற்றி கேளுங்கள்...",
    chatThinking: "சிந்திக்கிறது...",
    chatbotTitle: "Plant Guard AI",
    plantHealthAssistant: "AI தாவர ஆரோக்கிய உதவியாளர்",
    chatInline: "உதவியாளர் ஆன்லைன்",
    diseaseDetection: "நோய் கண்டறிதல்",
    analyzePlantTitle: "உங்கள் தாவரத்தை பகுப்பாய்வு செய்க",
    analyzePlantSubtitle: "ஒரு தாவர இலைப் படத்தை பதிவேற்றவும், AI மாதிரி அதை பகுப்பாய்வு செய்யட்டும்.",
    selectFilePrompt: "தாவர இலைக் காட்டும் தெளிவான படத்தைத் தேர்ந்தெடுக்கவும். தெளிவான படங்கள் சிறந்த முடிவை வழங்கலாம்.",
    supportedFormats: "ஆதரிக்கப்படும் பட வடிவங்கள்: JPG, JPEG, PNG, WEBP",
    selectedImage: "தேர்ந்தெடுக்கப்பட்ட படம்",
    plantImagePreview: "உங்கள் தாவரப் படம்",
    ready: "தயார்",
    modelLabel: "AI முடிவு",
    plantAnalysisComplete: "தாவர பகுப்பாய்வு முடிந்தது",
    predictionSummary: "Plant Guard AI உருவாக்கிய கணிப்பை இங்கே பார்க்கலாம்.",
    quickNavigation: "விரைவு வழிசெலுத்தல்",
    projectLabel: "திட்டம்",
    languageLabel: "மொழி",
    english: "English",
    tamil: "தமிழ்",
    deepLearning: "ஆழ்ந்த கற்றல்",
    imageAnalysis: "பட பகுப்பாய்வு",
    plantCare: "தாவர பராமரிப்பு",
    detectionSystem: "கண்டறிதல் அமைப்பு",
    poweredDetection: "AI-இயக்கப்பட்ட கண்டறிதல்",
    modelClasses: "மாதிரி வகைகள்",
    digitalAssistance: "டிஜிட்டல் உதவி",
    simpleProcess: "எளிய செயல்முறை",
    howItWorksIntro: "படத்தைப் பதிவேற்றி, மூன்று எளிய படிகளில் பயனுள்ள தாவர ஆரோக்கிய வழிகாட்டலைப் பெறுங்கள்.",
    step01: "படி 01",
    step02: "படி 02",
    step03: "படி 03",
    howUploadDescription: "Plant Guard AI நோய் கண்டறிதல் கருவியைப் பயன்படுத்தி, தாவர இலைப் படத்தை தெளிவாக பதிவேற்றவும்.",
    howProcessingDescription: "இலை படம் FastAPI பின்தளத்தால் செயலாக்கப்பட்டு, பயிற்சி பெற்ற ஆழ்ந்த கற்றல் மாதிரியால் பகுப்பாய்வு செய்யப்படுகிறது.",
    howGuidanceDescription: "கணிக்கப்பட்ட நோய், நம்பகத்தன்மை மதிப்பெண், அறிகுறிகள், பரிந்துரைக்கப்பட்ட நடவடிக்கை மற்றும் தடுப்பு குறிப்புகளைப் பாருங்கள்.",
    featureRecognition: "ஆழ்ந்த கற்றல் அடிப்படையிலான தாவர நோய் கணிப்பு.",
    featureConfidence: "மாதிரி அதன் கணிப்பில் எவ்வளவு நம்பகமானது என்பதைப் புரிந்து கொள்ளுங்கள்.",
    featureGuidance: "அறிகுறிகள், சிகிச்சை நடவடிக்கைகள் மற்றும் தடுப்பு குறிப்புகளைப் பாருங்கள்.",
    featureAssistant: "உதவியாளரைப் பயன்படுத்தி தாவர ஆரோக்கியம் பற்றிய அடிப்படை கேள்விகளைக் கேளுங்கள்.",
    healthierPlants: "ஆரோக்கியமான தாவரங்களுக்கான தொழில்நுட்பம்",
    projectIntro: "Plant Guard AI என்பது தாவர நோய் கண்டறிதலில் AI மற்றும் ஆழ்ந்த கற்றல் எவ்வாறு உதவ முடியும் என்பதை விளக்கும் ஒரு மாணவர் சிறிய திட்டம்.",
    projectSystem: "இந்த அமைப்பு, Modern Next.js முன்பக்கத்தையும் FastAPI பின்தளத்தையும், பயிற்சி பெற்ற EfficientNet அடிப்படையிலான பட வகைப்பாடு மாதிரியையும் ஒருங்கிணைக்கிறது.",
    tryDiseaseDetection: "நோய் கண்டறிதலை முயற்சிக்கவும்",
    platformDescription: "தாவர நோய் கண்டறிதலை எளிதாகவும் அணுகக்கூடியதாகவும் மாற்றும் AI-உதவி தாவர ஆரோக்கிய தளம்.",
    featureDiseaseDetection: "AI-உதவி நோய் கண்டறிதல்",
    featureDiseaseDetectionText: "பதிவேற்றப்பட்ட இலைப் படங்களிலிருந்து சாத்தியமான தாவர நோய்களைக் கண்டறிகிறது.",
    featureConfidenceResults: "நம்பகத்தன்மை அடிப்படையிலான முடிவுகள்",
    featureConfidenceResultsText: "AI கணிப்பை அதன் நம்பகத்தன்மையுடன் 함께 காட்டுகிறது.",
    featureInfoSymptoms: "நோய் தகவல் மற்றும் அறிகுறிகள்",
    featureInfoSymptomsText: "கண்டறியப்பட்ட நிலைகள் மற்றும் அறிகுறிகள் குறித்த பயனுள்ள தகவல்களை வழங்குகிறது.",
    featureTreatmentPrevention: "சிகிச்சை மற்றும் தடுப்பு வழிகாட்டல்",
    featureTreatmentPreventionText: "தாவர பராமரிப்புக்கான நடைமுறை நடவடிக்கைகள் மற்றும் தடுப்பு நடவடிக்கைகளை பரிந்துரைக்கிறது.",
    featureTreatmentCalculator: "சிகிச்சை கால்குலேட்டர்",
    featureTreatmentCalculatorText: "பாதிக்கப்பட்ட பகுதி மற்றும் விவசாய பயன்பாட்டு வீதத்தின் அடிப்படையில் சிகிச்சை அளவை மதிப்பிடுகிறது.",
    readyCheckPlant: "உங்கள் தாவரத்தைச் சரிபார்க்க வேண்டுமா?",
    ctaDescription: "ஒரு தாவர இலைப் படத்தை பதிவேற்றி, Plant Guard AI என்ன கண்டறிய முடியும் என்பதை ஆராயுங்கள்.",
    footerSummary: "AI-இயக்கப்பட்ட தாவர நோய் கண்டறிதல் மற்றும் தாவர பராமரிப்பு உதவி.",
    quickNav: "விரைவு வழிசெலுத்தல்",
    homeLink: "முகப்பு",
    diseaseDetectionLink: "நோய் கண்டறிதல்",
    howItWorksLink: "இது எப்படி வேலை செய்கிறது",
    aboutLink: "பற்றி",
    projectLink: "திட்டம்",
    miniProject: "சிறிய திட்டம்",
    footerCopyright: "© 2026 Plant Guard AI. கல்வி சிறிய திட்டமாக உருவாக்கப்பட்டது.",
    techFooterText: "AI தாவர ஆரோக்கிய உதவியாளர்",
    statusLabel: "கண்டறிதல் அமைப்பு",
  },
};

function getLocalizedDisplayName(value: string | undefined, language: Language) {
  if (!value) {
    return value ?? "";
  }

  if (language !== "ta") {
    return value;
  }

  const translations: Record<string, string> = {
    Tomato: "தக்காளி",
    "Tomato Late Blight": "தக்காளி லேட் ப்ளைட்",
    "Late blight": "லேட் ப்ளைட்",
    "Early blight": "ஆரம்பகால ப்ளைட்",
    "Powdery mildew": "பவுடரி மில்டெவ்",
    "Bacterial spot": "பாக்டீரியா ஸ்பாட்",
    "Leaf spot": "இலை புள்ளி",
    "Apple scab": "ஆப்பிள் ஸ்கேப்",
    "Black rot": "பிளாக் ராட்",
    Healthy: "ஆரோக்கியமான",
  };

  const normalized = value.trim();

  for (const [english, tamil] of Object.entries(translations)) {
    if (normalized.toLowerCase() === english.toLowerCase()) {
      return tamil;
    }
  }

  for (const [english, tamil] of Object.entries(translations)) {
    if (normalized.toLowerCase().includes(english.toLowerCase())) {
      return normalized.replace(new RegExp(english, "gi"), tamil);
    }
  }

  return normalized;
}

export default function Home() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [calculatorQuantity, setCalculatorQuantity] = useState("");
  const [calculatorTouched, setCalculatorTouched] = useState(false);
  const [selectedRateId, setSelectedRateId] = useState<number | null>(null);

  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [notificationsLoading, setNotificationsLoading] = useState(false);
  const [notificationsError, setNotificationsError] = useState("");
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const [chatMessage, setChatMessage] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [language, setLanguage] = useState<Language>(() => {
    if (typeof window === "undefined") {
      return "en";
    }

    const savedLanguage = sessionStorage.getItem("plant-guard-language");
    return savedLanguage === "ta" ? "ta" : "en";
  });
  const [messages, setMessages] = useState<
    { sender: "bot" | "user"; text: string }[]
  >([
    {
      sender: "bot",
      text: translations.en.welcomeBot,
    },
  ]);
  const resultSectionRef = useRef<HTMLElement | null>(null);
  const previousResultKeyRef = useRef<string>("");
  const chatMessagesRef = useRef<HTMLDivElement | null>(null);

  const t = translations[language];

  const refreshHistory = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/history`);
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "History request failed");
      }
      setHistory(Array.isArray(data.history) ? data.history : []);
      setHistoryError(false);
    } catch {
      setHistory([]);
      setHistoryError(true);
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    fetch(`${API_BASE_URL}/api/history`)
      .then(async (response) => {
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || "History request failed");
        }
        return data;
      })
      .then((data) => {
        if (active) {
          setHistory(Array.isArray(data.history) ? data.history : []);
          setHistoryError(false);
        }
      })
      .catch(() => {
        if (active) {
          setHistory([]);
          setHistoryError(true);
        }
      })
      .finally(() => {
        if (active) {
          setHistoryLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    sessionStorage.setItem("plant-guard-language", language);
  }, [language]);

  useEffect(() => {
    if (!result || !resultSectionRef.current) {
      return;
    }

    const currentResultKey = `${result.disease?.id ?? "unknown"}-${result.confidence ?? "0"}-${result.disease?.name ?? ""}`;

    if (currentResultKey === previousResultKeyRef.current) {
      return;
    }

    previousResultKeyRef.current = currentResultKey;

    const scrollTarget = () => {
      if (!resultSectionRef.current) {
        return;
      }

      resultSectionRef.current.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    };

    requestAnimationFrame(scrollTarget);
  }, [result]);

  useEffect(() => {
    if (chatMessagesRef.current) {
      chatMessagesRef.current.scrollTo({
        top: chatMessagesRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [messages, chatOpen]);

  const handleLanguageChange = (nextLanguage: Language) => {
    setLanguage(nextLanguage);

    setMessages((current) => {
      const hasOnlyWelcomeMessage =
        current.length === 1 && current[0]?.sender === "bot";

      if (hasOnlyWelcomeMessage) {
        return [{ sender: "bot", text: translations[nextLanguage].welcomeBot }];
      }

      return current;
    });
  };

  const notificationCount = notifications.length;

  const getNotificationIcon = (notificationType?: string | null) => {
    switch ((notificationType || "").toLowerCase()) {
      case "monitoring":
        return "🌿";
      case "inspection":
        return "🔍";
      case "prevention":
        return "🛡️";
      case "treatment":
        return "💧";
      case "care":
        return "💡";
      default:
        return "🌱";
    }
  };

  const fetchNotifications = async () => {
    setNotificationsLoading(true);
    setNotificationsError("");

    try {
      const response = await fetch(`${API_BASE_URL}/api/notifications`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to load notifications.");
      }

      setNotifications(Array.isArray(data.notifications) ? data.notifications : []);
    } catch (err) {
      console.error(err);
      setNotifications([]);
      setNotificationsError("Unable to load notifications right now.");
    } finally {
      setNotificationsLoading(false);
    }
  };

  const scrollToSection = (sectionId: string) => {
    document.getElementById(sectionId)?.scrollIntoView({
      behavior: "smooth",
    });
  };

  const handleFileChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    setSelectedFile(file);
    setPreview(URL.createObjectURL(file));
    setResult(null);
    setError("");

    setTimeout(() => {
      scrollToSection("analyzer");
    }, 100);
  };

  const analyzePlant = async () => {
    if (!selectedFile) {
      return;
    }

    setLoading(true);
    setResult(null);
    setError("");

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("language", language);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/upload`,
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Unable to analyze image."
        );
      }

      setResult(data);
      setSelectedRateId(null);
      setCalculatorQuantity("");
      if (data.history_saved) {
        setHistoryLoading(true);
        void refreshHistory();
      }
    } catch (err) {
      console.error(err);
      setError(
        err instanceof Error && err.name === "Error"
          ? err.message
          : "Unable to connect to Plant Guard AI backend. Make sure FastAPI is running."
      );
    } finally {
      setLoading(false);
    }
  };

  const resetAnalysis = () => {
    setSelectedFile(null);
    setPreview(null);
    setResult(null);
    setError("");
    setCalculatorQuantity("");
    setCalculatorTouched(false);
    setSelectedRateId(null);
  };

  const displayedOptions = useMemo(
    () => getCalculableAreaRates(result?.treatments, result?.disease.id ?? null),
    [result]
  );

  const selectedRate = useMemo(
    () =>
      displayedOptions.find((option) => option.rateId === selectedRateId) ??
      displayedOptions[0] ??
      null,
    [displayedOptions, selectedRateId]
  );

  const areaValidation = validateAreaInput(calculatorQuantity);
  const treatmentCalculation = calculateTreatmentQuantity(calculatorQuantity, selectedRate);

  const hasValidCalculation =
    treatmentCalculation.error === null &&
    treatmentCalculation.total !== null;

  const findPendingBotMessageIndex = (
    currentMessages: { sender: "bot" | "user"; text: string }[],
    placeholderText: string
  ) => {
    const pendingPlaceholders = new Set([
      "Thinking...",
      "சிந்திக்கிறது...",
      placeholderText,
    ]);

    return currentMessages.findLastIndex(
      (item) => item.sender === "bot" && pendingPlaceholders.has(item.text)
    );
  };

  const sendChatMessage = async () => {
    const message = chatMessage.trim();

    if (!message || chatLoading) {
      return;
    }

    setMessages((current) => [
      ...current,
      {
        sender: "user",
        text: message,
      },
      {
        sender: "bot",
        text: t.chatThinking,
      },
    ]);

    setChatMessage("");
    setChatLoading(true);

    const startedAt = Date.now();
    if (language === "ta") {
      console.log("[chat:ta] request-start", {
        message: message.slice(0, 120),
        disease: result?.disease?.name || null,
        startedAt,
      });
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message,
          crop: result?.disease.crop_name || undefined,
          disease: result?.disease.name || undefined,
          confidence: result?.confidence ?? undefined,
          disease_id: result?.disease.id ?? undefined,
          language,
        }),
      });

      const data = await response.json();

      if (language === "ta") {
        console.log("[chat:ta] response", {
          status: response.status,
          elapsedMs: Date.now() - startedAt,
          responseLength: data?.response?.length || 0,
        });
      }

      if (!response.ok) {
        throw new Error(data.detail || "Unable to get a grounded response.");
      }

      setMessages((current) => {
        const updated = [...current];
        const botIndex = findPendingBotMessageIndex(updated, t.chatThinking);

        if (botIndex >= 0) {
          updated[botIndex] = {
            sender: "bot",
            text: data.response || "I could not return a response.",
          };
        }

        return updated;
      });
    } catch (err) {
      console.error(err);

      if (language === "ta") {
        console.log("[chat:ta] error", {
          elapsedMs: Date.now() - startedAt,
        });
      }

      setMessages((current) => {
        const updated = [...current];
        const botIndex = findPendingBotMessageIndex(updated, t.chatThinking);

        if (botIndex >= 0) {
          updated[botIndex] = {
            sender: "bot",
            text: "I could not reach the Plant Guard AI assistant right now. Please try again in a moment.",
          };
        }

        return updated;
      });
    } finally {
      setChatLoading(false);
    }
  };

  const diseaseData = result
    ? {
        plant: getLocalizedDisplayName(result.disease.crop_name, language),
        disease: getLocalizedDisplayName(result.disease.name, language),
      }
    : null;

  const diseaseInfo: DatabaseDiseaseInfo | null = result
    ? {
        about: result.disease.description,
        symptoms: result.symptoms,
        causes: result.causes,
        treatment: result.treatments,
        prevention: result.prevention,
      }
    : null;

  const noVerifiedGuidance = language === "ta"
    ? "இந்த மாதிரி வகைக்கு சரிபார்க்கப்பட்ட தகவல் அறிவுத் தரவுத்தளத்தில் இல்லை."
    : "No verified guidance for this model class is available in the knowledge base.";
  const diagnosisDisclaimer = language === "ta"
    ? "இது ஒரு AI மாதிரி கணிப்பு மட்டுமே; உறுதிப்படுத்தப்பட்ட நோய் கண்டறிதல் அல்ல."
    : "This is an AI model prediction, not a confirmed diagnosis.";

  const confidence = result
    ? Math.max(
        0,
        Math.min(Number(result.confidence), 100)
      )
    : 0;

  return (
    <main className="min-h-screen bg-slate-50 text-slate-800">

      {/* NAVBAR */}
      <nav className="sticky top-0 z-50 border-b border-slate-200 bg-white/95 shadow-sm backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 lg:px-8">

          <button
            onClick={() => scrollToSection("home")}
            className="flex items-center gap-3"
          >
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-green-100 text-2xl shadow-sm">
              🌱
            </div>

            <div className="text-left">
              <div className="text-lg font-extrabold tracking-tight text-green-800">
                Plant Guard
              </div>

              <div className="text-xs font-medium text-slate-500">
                {t.plantHealthAssistant}
              </div>
            </div>
          </button>

          <div className="hidden flex-wrap items-center gap-4 md:flex md:gap-7">
            <button
              onClick={() => scrollToSection("home")}
              className="text-sm font-semibold text-slate-600 transition hover:text-green-700"
            >
              {t.navHome}
            </button>

            <button
              onClick={() => scrollToSection("analyzer")}
              className="text-sm font-semibold text-slate-600 transition hover:text-green-700"
            >
              {t.navDetect}
            </button>

            <button
              onClick={() => scrollToSection("how-it-works")}
              className="text-sm font-semibold text-slate-600 transition hover:text-green-700"
            >
              {t.navHow}
            </button>

            <button
              onClick={() => scrollToSection("about")}
              className="text-sm font-semibold text-slate-600 transition hover:text-green-700"
            >
              {t.navAbout}
            </button>

            <button
              onClick={() => scrollToSection("history")}
              className="text-sm font-semibold text-slate-600 transition hover:text-green-700"
            >
              {t.navHistory}
            </button>
          </div>

          <div className="flex items-center gap-3">
            <label className="hidden items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm sm:flex">
              <span className="text-xs uppercase tracking-wide text-slate-400">{t.languageLabel}</span>

              <select
                value={language}
                onChange={(event) => handleLanguageChange(event.target.value as Language)}
                className="bg-transparent font-semibold text-slate-700 outline-none"
                aria-label="Select website language"
              >
                <option value="en">{t.english}</option>
                <option value="ta">{t.tamil}</option>
              </select>
            </label>

            <div className="relative">
              <button
                onClick={async () => {
                  const nextState = !notificationsOpen;
                  setNotificationsOpen(nextState);

                  if (nextState && notifications.length === 0 && !notificationsLoading) {
                    await fetchNotifications();
                  }
                }}
                className="relative flex h-11 w-11 items-center justify-center rounded-full border border-slate-200 bg-white text-xl shadow-sm transition hover:bg-green-50"
                aria-label={t.notifications}
              >
                🔔

                {notificationCount > 0 && (
                  <span className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white ring-2 ring-white">
                    {notificationCount}
                  </span>
                )}
              </button>

              {notificationsOpen && (
                <div className="absolute right-0 top-14 w-80 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl">

                  <div className="flex items-center justify-between border-b p-4">
                    <div>
                      <h3 className="font-bold text-slate-800">
                        {t.notifications}
                      </h3>

                      <p className="text-xs text-slate-500">
                        {t.notificationsSubtitle}
                      </p>
                    </div>

                    <span className="rounded-full bg-green-100 px-2 py-1 text-xs font-bold text-green-700">
                      {notificationCount}
                    </span>
                  </div>

                  <div className="max-h-80 overflow-y-auto p-2">
                    {notificationsLoading && (
                      <div className="rounded-xl bg-slate-50 p-3 text-sm text-slate-500">
                        {t.notificationsLoading}
                      </div>
                    )}

                    {!notificationsLoading && notificationsError && (
                      <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                        {notificationsError}
                      </div>
                    )}

                    {!notificationsLoading && !notificationsError && notifications.length === 0 && (
                      <div className="rounded-xl bg-slate-50 p-3 text-sm text-slate-500">
                        {t.notificationsEmpty}
                      </div>
                    )}

                    {!notificationsLoading && !notificationsError && notifications.length > 0 && notifications.map((notification) => (
                      <div
                        key={notification.id}
                        className="flex w-full gap-3 rounded-xl p-3 text-left transition hover:bg-green-50"
                      >
                        <span className="text-xl">{getNotificationIcon(notification.notification_type)}</span>

                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-semibold text-slate-800">
                            {notification.title}
                          </p>

                          <p className="text-xs text-slate-500">
                            {notification.message}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="border-t bg-slate-50 p-3 text-center">
                    <button
                      onClick={() => setNotificationsOpen(false)}
                      className="text-xs font-semibold text-green-700"
                    >
                      {t.notificationsClose}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </nav>

      <section
        id="home"
        className="relative overflow-hidden bg-gradient-to-br from-green-50 via-white to-emerald-50 px-5 py-20 lg:py-28"
      >

        <div className="absolute -right-20 -top-20 h-72 w-72 rounded-full bg-green-100 opacity-60 blur-3xl" />
        <div className="absolute -bottom-32 -left-20 h-80 w-80 rounded-full bg-emerald-100 opacity-50 blur-3xl" />

        <div className="relative mx-auto grid max-w-7xl items-center gap-14 lg:grid-cols-2">

          <div>

            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-green-200 bg-white px-4 py-2 text-sm font-semibold text-green-700 shadow-sm">
              <span className="h-2 w-2 rounded-full bg-green-500" />
              {t.heroBadge}
            </div>

            <h1 className="max-w-3xl text-5xl font-black leading-tight tracking-tight text-slate-900 md:text-6xl lg:text-7xl">
              {t.heroMain}
            </h1>

            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">
              {t.heroSubtitle}
            </p>

            <div className="mt-9 flex flex-wrap gap-4">

              <button
                onClick={() => scrollToSection("analyzer")}
                className="rounded-2xl bg-green-700 px-7 py-4 font-bold text-white shadow-lg shadow-green-700/20 transition hover:-translate-y-0.5 hover:bg-green-800"
              >
                {t.heroCTA}
              </button>

              <button
                onClick={() => scrollToSection("how-it-works")}
                className="rounded-2xl border border-slate-300 bg-white px-7 py-4 font-bold text-slate-700 shadow-sm transition hover:bg-slate-50"
              >
                {t.heroSecondary}
              </button>

            </div>

            <div className="mt-10 flex flex-wrap gap-6 text-sm text-slate-500">
              <div className="flex items-center gap-2">
                <span className="text-lg">🤖</span>
                {t.deepLearning}
              </div>

              <div className="flex items-center gap-2">
                <span className="text-lg">📷</span>
                {t.imageAnalysis}
              </div>

              <div className="flex items-center gap-2">
                <span className="text-lg">🌱</span>
                {t.plantCare}
              </div>
            </div>

          </div>

          {/* HERO CARD */}
          <div className="relative">

            <div className="rounded-[2rem] border border-white bg-white p-4 shadow-2xl shadow-green-900/10">

              <div className="rounded-[1.5rem] bg-gradient-to-br from-green-700 to-emerald-600 p-8 text-white">

                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm font-medium text-green-100">
                      {t.plantHealthScanner}
                    </p>

                    <h2 className="mt-2 text-3xl font-black">
                      {t.aiAnalysis}
                    </h2>
                  </div>

                  <div className="rounded-2xl bg-white/15 p-3 text-3xl backdrop-blur">
                    🌿
                  </div>
                </div>

                <div className="mt-8 rounded-2xl bg-white/10 p-5 backdrop-blur">

                  <div className="flex items-center gap-4">

                    <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white text-2xl">
                      📷
                    </div>

                    <div>
                      <p className="font-bold">
                        {t.uploadLabel}
                      </p>

                      <p className="text-sm text-green-100">
                        JPG, PNG or WEBP
                      </p>
                    </div>

                  </div>

                </div>

                <div className="mt-4 grid grid-cols-3 gap-3">

                  <div className="rounded-2xl bg-white/10 p-4 text-center">
                    <div className="text-xl">🔬</div>
                    <p className="mt-1 text-xs text-green-100">
                      {t.aiModel}
                    </p>
                  </div>

                  <div className="rounded-2xl bg-white/10 p-4 text-center">
                    <div className="text-xl">📊</div>
                    <p className="mt-1 text-xs text-green-100">
                      {t.confidence}
                    </p>
                  </div>

                  <div className="rounded-2xl bg-white/10 p-4 text-center">
                    <div className="text-xl">🩺</div>
                    <p className="mt-1 text-xs text-green-100">
                      {t.guidance}
                    </p>
                  </div>

                </div>

              </div>
            </div>

            <div className="absolute -bottom-5 -left-5 hidden rounded-2xl border bg-white p-4 shadow-xl sm:block">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-green-100">
                  ✅
                </div>

                <div>
                  <p className="text-xs text-slate-500">
                    {t.detectionSystem}
                  </p>

                  <p className="text-sm font-bold text-green-700">
                    {t.readyToAnalyze}
                  </p>
                </div>
              </div>
            </div>

          </div>

        </div>
      </section>

      {/* STATS */}
      <section className="border-y border-slate-200 bg-white px-5 py-7">
        <div className="mx-auto grid max-w-5xl gap-6 text-center sm:grid-cols-3">

          <div>
            <p className="text-3xl font-black text-green-700">
              AI
            </p>
            <p className="mt-1 text-sm text-slate-500">
              {t.poweredDetection}
            </p>
          </div>

          <div>
            <p className="text-3xl font-black text-green-700">
              38
            </p>
            <p className="mt-1 text-sm text-slate-500">
              {t.modelClasses}
            </p>
          </div>

          <div>
            <p className="text-3xl font-black text-green-700">
              24/7
            </p>
            <p className="mt-1 text-sm text-slate-500">
              {t.digitalAssistance}
            </p>
          </div>

        </div>
      </section>

      {/* ANALYZER */}
      <section
        id="analyzer"
        className="px-5 py-20 lg:py-24"
      >
        <div className="mx-auto max-w-6xl">

          <div className="mx-auto max-w-3xl text-center">
            <span className="text-sm font-bold uppercase tracking-widest text-green-700">
              {t.diseaseDetection}
            </span>

            <h2 className="mt-3 text-4xl font-black text-slate-900">
              {t.analyzePlantTitle}
            </h2>

            <p className="mt-4 text-lg text-slate-600">
              {t.analyzePlantSubtitle}
            </p>
          </div>

          <div className="mt-12 rounded-[2rem] border border-slate-200 bg-white p-5 shadow-xl md:p-8">

            {/* UPLOAD CARD */}
            <div className="rounded-[1.5rem] border-2 border-dashed border-green-200 bg-gradient-to-br from-green-50 to-emerald-50 p-8 text-center md:p-12">

              <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-3xl bg-white text-4xl shadow-md">
                📷
              </div>

              <h3 className="mt-6 text-2xl font-black text-slate-900">
                {t.uploadLabel}
              </h3>

              <p className="mx-auto mt-3 max-w-lg text-slate-500">
                {t.selectFilePrompt}
              </p>

              <label className="mt-7 inline-flex cursor-pointer items-center gap-2 rounded-2xl bg-green-700 px-7 py-4 font-bold text-white shadow-lg transition hover:-translate-y-0.5 hover:bg-green-800">
                📁 {t.chooseImage}

                <input
                  type="file"
                  accept="image/*"
                  onChange={handleFileChange}
                  className="hidden"
                />
              </label>

              <p className="mt-4 text-xs text-slate-400">
                {t.supportedFormats}
              </p>

              {selectedFile && (
                <div className="mx-auto mt-6 max-w-md rounded-2xl bg-white p-4 text-left shadow-sm">
                  <p className="text-xs font-medium text-slate-400">
                    {t.selectedImage}
                  </p>

                  <p className="mt-1 truncate font-semibold text-green-700">
                    {selectedFile.name}
                  </p>
                </div>
              )}

            </div>

            {/* PREVIEW */}
            {preview && (
              <div className="mt-10">

                <div className="mb-5 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-bold uppercase tracking-wide text-green-700">
                      {language === "ta" ? "முன்னோட்டம்" : "Preview"}
                    </p>

                    <h3 className="mt-1 text-2xl font-black">
                      {t.plantImagePreview}
                    </h3>
                  </div>

                  <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-bold text-green-700">
                    {t.ready}
                  </span>
                </div>

                <div className="overflow-hidden rounded-3xl border border-slate-200 bg-slate-50">
                  <img
                    src={preview}
                    alt={language === "ta" ? "தேர்ந்தெடுக்கப்பட்ட தாவர இலை" : "Selected plant leaf"}
                    className="mx-auto max-h-[500px] w-full object-contain"
                  />
                </div>

                <div className="mt-6 flex flex-wrap justify-center gap-3">

                  <button
                    onClick={analyzePlant}
                    disabled={loading}
                    className="rounded-2xl bg-green-700 px-8 py-4 font-bold text-white shadow-lg transition hover:bg-green-800 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {loading
                      ? "🔄 " + t.aiAnalysis
                      : "🔍 " + t.analyzePlant}
                  </button>

                  <button
                    onClick={resetAnalysis}
                    disabled={loading}
                    className="rounded-2xl border border-slate-300 bg-white px-7 py-4 font-bold text-slate-600 transition hover:bg-slate-50 disabled:opacity-50"
                  >
                    {t.chooseAnother}
                  </button>

                </div>

              </div>
            )}

            {/* ERROR */}
            {error && (
              <div className="mt-8 rounded-2xl border border-red-200 bg-red-50 p-5">
                <div className="flex gap-3">
                  <span className="text-xl">⚠️</span>

                  <div>
                    <h3 className="font-bold text-red-800">
                      {language === "ta" ? "பகுப்பாய்வு தோல்வியடைந்தது" : "Analysis failed"}
                    </h3>

                    <p className="mt-1 text-sm text-red-700">
                      {error}
                    </p>
                  </div>
                </div>
              </div>
            )}

          </div>
        </div>
      </section>

      {/* RESULT */}
      {result && diseaseData && diseaseInfo && (
        <section
          id="result"
          ref={resultSectionRef}
          className="scroll-mt-20 bg-slate-100 px-5 py-20"
        >
          <div className="mx-auto max-w-6xl">

            <div className="mx-auto max-w-3xl text-center">
              <span className="text-sm font-bold uppercase tracking-widest text-green-700">
                {t.modelLabel}
              </span>

              <h2 className="mt-3 text-4xl font-black text-slate-900">
                {t.plantAnalysisComplete}
              </h2>

              <p className="mt-3 text-slate-600">
                {t.predictionSummary}
              </p>
            </div>

            {/* MAIN RESULT */}
            <div className="mt-12 overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-xl">

              <div className="bg-gradient-to-br from-green-700 to-emerald-600 p-8 text-center text-white md:p-12">

                <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-3xl bg-white/15 text-4xl backdrop-blur">
                  🌿
                </div>

                <p className="mt-5 text-sm font-bold uppercase tracking-widest text-green-100">
                  {t.candidateCondition}
                </p>

                <h2 className="mt-2 text-4xl font-black md:text-5xl">
                  {diseaseData.disease}
                </h2>

                <p className="mt-4 text-lg text-green-50">
                  {t.candidateCrop}{" "}
                  <span className="font-bold">
                    {diseaseData.plant}
                  </span>
                </p>

              </div>

              <div className="p-6 md:p-10">

                {/* CONFIDENCE */}
                <div className="rounded-2xl bg-slate-50 p-6">

                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-bold text-slate-500">
                        {t.modelConfidence.toUpperCase()}
                      </p>

                      <p className="mt-1 text-3xl font-black text-slate-900">
                        {confidence.toFixed(2)}%
                      </p>
                    </div>

                    <div className="text-3xl" aria-hidden="true">ℹ️</div>
                  </div>

                  <div className="mt-5 h-4 overflow-hidden rounded-full bg-slate-200">
                    <div
                      className="h-full rounded-full bg-blue-600 transition-all duration-700"
                      style={{
                        width:
                          Math.min(confidence, 100) + "%",
                      }}
                    />
                  </div>

                  <p className="mt-3 text-sm text-slate-600">
                    {result.uncertainty_warning || (language === "ta"
                      ? "இந்த மதிப்பெண் அளவுத்திருத்தம் செய்யப்பட்ட நிகழ்தகவு அல்ல. முடிவை அறிகுறிகளுடன் ஒப்பிட்டு சரிபார்க்கவும்."
                      : "This score is not a calibrated probability. Check the result against visible symptoms.")}
                  </p>
                  {result.history_warning && (
                    <p className="mt-2 text-sm text-amber-700">{result.history_warning}</p>
                  )}

                </div>

                {/* EXPLANATION */}
                <div className="mt-6 rounded-2xl border border-green-100 bg-green-50 p-6">

                  <div className="flex gap-4">
                    <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-white text-2xl shadow-sm">
                      💡
                    </div>

                    <div>
                      <h3 className="text-xl font-black text-green-900">
                        {t.whatDoesThisMean}
                      </h3>

                      <p className="mt-2 leading-7 text-green-900/70">
                        {diagnosisDisclaimer}
                      </p>
                    </div>
                  </div>

                </div>

              </div>

            </div>

            {/* INFO CARDS */}
            <div className="mt-8 grid gap-6 md:grid-cols-2">

              <div className="rounded-3xl border border-slate-200 bg-white p-7 shadow-md">
                <div className="flex items-center gap-3">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-green-100 text-xl">
                    📖
                  </div>

                  <h3 className="text-xl font-black">
                    {t.aboutCondition}
                  </h3>
                </div>

                <p className="mt-5 leading-7 text-slate-600">
                  {diseaseInfo.about || noVerifiedGuidance}
                </p>
              </div>

              <div className="rounded-3xl border border-slate-200 bg-white p-7 shadow-md">
                <div className="flex items-center gap-3">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-100 text-xl">
                    🔎
                  </div>

                  <h3 className="text-xl font-black">
                    {t.commonSymptoms}
                  </h3>
                </div>

                <ul className="mt-5 space-y-3">
                  {diseaseInfo.symptoms.length > 0 ? diseaseInfo.symptoms.map(
                    (symptom, index) => (
                      <li
                        key={index}
                        className="flex gap-3 text-slate-600"
                      >
                        <span className="mt-1 text-green-600">
                          ✓
                        </span>

                        <span>
                          <strong>{symptom.name}</strong>
                          {symptom.description
                            ? ` — ${symptom.description}`
                            : ""}
                        </span>
                      </li>
                    )
                  ) : <li className="text-slate-500">{noVerifiedGuidance}</li>}
                </ul>
              </div>

              <div className="rounded-3xl border border-slate-200 bg-white p-7 shadow-md">
                <div className="flex items-center gap-3">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-purple-100 text-xl">
                    🧬
                  </div>

                  <h3 className="text-xl font-black">
                    {t.possibleCauses}
                  </h3>
                </div>

                <ul className="mt-5 space-y-3">
                  {diseaseInfo.causes.length > 0 ? diseaseInfo.causes.map((cause) => (
                    <li key={cause.id} className="flex gap-3 text-slate-600">
                      <span className="mt-1 text-purple-600">•</span>
                      <span>
                        <strong>{cause.name}</strong>
                        {cause.description
                          ? ` — ${cause.description}`
                          : ""}
                      </span>
                    </li>
                  )) : <li className="text-slate-500">{noVerifiedGuidance}</li>}
                </ul>
              </div>

              <div className="rounded-3xl border border-slate-200 bg-white p-7 shadow-md">
                <div className="flex items-center gap-3">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-orange-100 text-xl">
                    🩺
                  </div>

                  <h3 className="text-xl font-black">
                    {t.treatment}
                  </h3>
                </div>

                <div className="mt-5 space-y-5">
                  {diseaseInfo.treatment.map((treatment) => (
                    <div key={treatment.id} className="text-slate-600">
                      <p className="font-bold text-slate-800">
                        {treatment.name}
                        {treatment.type ? ` (${treatment.type})` : ""}
                      </p>

                      {treatment.description && (
                        <p className="mt-1">{treatment.description}</p>
                      )}

                      {treatment.instructions && (
                        <p className="mt-2 text-sm">
                          <strong>{language === "ta" ? "வழிமுறைகள்:" : "Instructions:"}</strong>{" "}
                          {treatment.instructions}
                        </p>
                      )}

                      {treatment.precautions && (
                        <p className="mt-1 text-sm">
                          <strong>{language === "ta" ? "ஜாக்கிரதைகள்:" : "Precautions:"}</strong>{" "}
                          {treatment.precautions}
                        </p>
                      )}

                      {treatment.application_rates.length > 0 && (
                        <div className="mt-3 rounded-xl bg-orange-50 p-3 text-sm">
                          <p className="font-bold text-orange-900">
                            {t.applicationRates}
                          </p>
                          <ul className="mt-2 space-y-2">
                            {treatment.application_rates.map((rate) => (
                              <li key={rate.id}>
                                <strong>{rate.application_method}:</strong>{" "}
                                {rate.rate ?? "Not specified"}{" "}
                                {rate.measurement_unit}
                                {rate.basis ? ` (${rate.basis})` : ""}
                                {rate.notes ? ` — ${rate.notes}` : ""}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}

                  {diseaseInfo.treatment.length === 0 && (
                    <p className="text-slate-500">
                      {language === "ta"
                        ? "சரிபார்க்கப்பட்ட சிகிச்சை தகவல் கிடைக்கவில்லை."
                        : "No verified treatment information is available."}
                    </p>
                  )}
                </div>
              </div>

              <div className="rounded-3xl border border-slate-200 bg-white p-7 shadow-md">
                <div className="flex items-center gap-3">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-100 text-xl">
                    🛡️
                  </div>

                  <h3 className="text-xl font-black">
                    {t.preventionTips}
                  </h3>
                </div>

                <ul className="mt-5 space-y-3">
                  {diseaseInfo.prevention.length > 0 ? diseaseInfo.prevention.map(
                    (item, index) => (
                      <li
                        key={index}
                        className="flex gap-3 text-slate-600"
                      >
                        <span className="mt-1 text-green-600">
                          ✓
                        </span>

                        <span>
                          <strong>{item.title}</strong>
                          {item.description
                            ? ` — ${item.description}`
                            : ""}
                        </span>
                      </li>
                    )
                  ) : <li className="text-slate-500">{noVerifiedGuidance}</li>}
                </ul>
              </div>

            </div>

            {/* CALCULATOR */}
            <div className="mt-8 rounded-3xl border border-green-200 bg-gradient-to-br from-green-50 to-emerald-50 p-7 shadow-md md:p-9">

              <div className="text-center">
                <div className="text-4xl">
                  🧮
                </div>

                <h3 className="mt-3 text-2xl font-black text-green-900">
                  {t.treatmentCalculator}
                </h3>

                <p className="mx-auto mt-2 max-w-2xl text-slate-600">
                  {language === "ta"
                    ? "இந்த நோய்க்கான விவசாய அறிவு தள பயன்பாட்டு வீதங்களைப் பயன்படுத்தி தேவையான சிகிச்சை அளவை மதிப்பிடுங்கள்."
                    : "Estimate the required treatment quantity using the disease-specific application rates from the agricultural knowledge base."}
                </p>
              </div>

              <div className="mx-auto mt-8 max-w-4xl">
                <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                  <label htmlFor="affected-area" className="mb-3 block text-sm font-bold text-slate-700">
                    {t.affectedArea}
                  </label>

                  <div className="flex flex-col gap-3 sm:flex-row">
                    <input
                      id="affected-area"
                      type="text"
                      inputMode="decimal"
                      autoComplete="off"
                      value={calculatorQuantity}
                      onChange={(event) => {
                        setCalculatorQuantity(event.target.value);
                        setCalculatorTouched(true);
                      }}
                      onBlur={() => setCalculatorTouched(true)}
                      placeholder="Example: 0.16"
                      aria-invalid={calculatorTouched && !areaValidation.valid}
                      aria-describedby="affected-area-help affected-area-error"
                      className="w-full rounded-2xl border border-slate-300 bg-white px-5 py-4 outline-none transition focus:border-green-500 focus:ring-4 focus:ring-green-100"
                    />

                    <div className="flex items-center justify-center rounded-2xl border border-slate-200 bg-slate-50 px-5 py-4 text-sm font-bold text-slate-700">
                      {t.acres}
                    </div>
                  </div>

                  <p id="affected-area-help" className="mt-2 text-xs text-slate-500">{t.areaHelp}</p>
                  {calculatorTouched && !areaValidation.valid && (
                    <p id="affected-area-error" role="alert" className="mt-2 text-sm font-semibold text-red-700">
                      {areaValidation.error === "empty"
                        ? t.areaEmpty
                        : areaValidation.error === "non_positive"
                          ? t.areaPositive
                          : t.areaInvalid}
                    </p>
                  )}
                </div>
              </div>

              {displayedOptions.length === 0 ? (
                <div className="mx-auto mt-6 max-w-4xl rounded-2xl border border-amber-200 bg-white/80 p-5 text-sm text-amber-950">
                  <p className="font-bold">{language === "ta" ? "கணக்கீடு கிடைக்கவில்லை" : "Calculation unavailable"}</p>
                  <p className="mt-1">{t.rateUnavailable}</p>
                </div>
              ) : (
                <>

                  <div className="mx-auto mt-8 max-w-4xl">
                    <p className="mb-3 text-sm font-bold uppercase tracking-wide text-slate-600">
                      {t.treatment} / {t.aiModel}
                    </p>

                    <div className="grid gap-3 md:grid-cols-2">
                      {displayedOptions.map((option) => (
                        <button
                          key={option.rateId}
                          type="button"
                          onClick={() => setSelectedRateId(option.rateId)}
                          className={`rounded-2xl border p-4 text-left transition ${
                            selectedRate?.rateId === option.rateId
                              ? "border-green-500 bg-green-50 shadow-md"
                              : "border-slate-200 bg-white hover:border-green-300 hover:bg-green-50/50"
                          }`}
                        >
                          <div className="text-base font-black text-slate-900">
                            {option.productName}
                          </div>

                          <div className="mt-2 text-sm font-semibold text-green-700">
                            {option.rate} {option.measurementUnit}
                          </div>

                          {option.treatmentName && option.productName !== option.treatmentName && (
                            <div className="mt-1 text-xs text-slate-500">
                              {option.treatmentName}
                            </div>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>

                  {selectedRate && (
                    <div className="mx-auto mt-8 max-w-4xl rounded-2xl bg-white p-6 shadow-md">
                      <div className="grid gap-4 text-sm text-slate-600 md:grid-cols-2 xl:grid-cols-3">
                        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                          <p className="font-bold text-slate-700">{t.selectedProduct}</p>
                          <p className="mt-1 text-base font-black text-slate-900">
                            {selectedRate.productName}
                          </p>
                        </div>

                        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                          <p className="font-bold text-slate-700">{t.applicationMethod}</p>
                          <p className="mt-1 text-base font-black text-slate-900">
                            {selectedRate.applicationMethod}
                          </p>
                        </div>

                        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                          <p className="font-bold text-slate-700">{t.rate}</p>
                          <p className="mt-1 text-base font-black text-slate-900">
                            {selectedRate.rate} {selectedRate.measurementUnit}
                          </p>
                        </div>

                        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                          <p className="font-bold text-slate-700">
                            {language === "ta" ? "அடிப்படை" : "Basis"}
                          </p>
                          <p className="mt-1 text-base font-black text-slate-900">
                            {language === "ta"
                              ? selectedRate.basis?.toLowerCase().includes("acre")
                                ? "ஒரு ஏக்கருக்கு"
                                : selectedRate.basis || "ஒரு அலகுக்கு"
                              : selectedRate.basis || "per unit"}
                          </p>
                        </div>

                        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                          <p className="font-bold text-slate-700">{t.affectedArea}</p>
                          <p className="mt-1 text-base font-black text-slate-900">
                            {calculatorQuantity || "0"} {language === "ta" ? "ஏக்கர்" : "acre"}
                          </p>
                        </div>

                        {selectedRate.treatmentName && (
                          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                            <p className="font-bold text-slate-700">
                              {language === "ta" ? "சிகிச்சை குழு" : "Treatment group"}
                            </p>
                            <p className="mt-1 text-base font-black text-slate-900">
                              {language === "ta" && selectedRate.treatmentName === "Late Blight Management"
                                ? "லேட் ப்ளைட் மேலாண்மை"
                                : selectedRate.treatmentName}
                            </p>
                          </div>
                        )}
                      </div>

                      <p className="mt-4 text-sm text-slate-600">
                        <strong>{t.sourceReference}:</strong>{" "}
                        <a
                          href={selectedRate.sourceUrl}
                          target="_blank"
                          rel="noreferrer"
                          className="break-all font-semibold text-blue-700 underline"
                        >
                          {selectedRate.sourceUrl}
                        </a>
                      </p>

                      {hasValidCalculation ? (
                        <>
                          <div className="mt-6 rounded-2xl border border-green-200 bg-green-50 p-5 text-center">
                            <p className="text-sm font-semibold text-slate-500">
                              {t.requiredQuantity}
                            </p>

                            <p className="mt-2 text-4xl font-black text-green-700">
                              {treatmentCalculation.total.toFixed(2)}
                            </p>

                            <p className="mt-1 text-xs font-medium uppercase tracking-wide text-slate-500">
                              {treatmentCalculation.unit}
                            </p>
                          </div>

                          <div className="mt-4 text-sm leading-6 text-slate-600">
                            <strong>{language === "ta" ? "கணக்கீடு:" : "Calculation:"}</strong>{" "}
                            {treatmentCalculation.area} acres × {selectedRate.rate} {selectedRate.measurementUnit} = {treatmentCalculation.total.toFixed(2)} {treatmentCalculation.unit}
                          </div>
                        </>
                      ) : null}
                    </div>
                  )}
                </>
              )}

              <p className="mx-auto mt-6 max-w-2xl text-center text-xs leading-5 text-slate-500">
                {language === "ta"
                  ? "இந்த கால்குலேட்டர் தோராய மதிப்பீட்டிற்காக மட்டுமே. உண்மையான அளவுக்கு தயாரிப்பு லேபிள் மற்றும் உள்ளூர் விவசாய வழிமுறைகளைப் பின்பற்றவும்."
                  : "This calculator is for estimation only. Always follow the product label and local agricultural recommendations for actual dosage."}
              </p>

            </div>

            {/* DISCLAIMER */}
            <div className="mt-8 rounded-2xl border border-yellow-200 bg-yellow-50 p-6">

              <div className="flex gap-3">
                <span className="text-xl">
                  ⚠️
                </span>

                <div>
                  <h3 className="font-black text-yellow-900">
                    {t.importantDisclaimer}
                  </h3>

                  <p className="mt-2 text-sm leading-6 text-yellow-800">
                    {language === "ta"
                      ? "Plant Guard AI ஆனது AI அடிப்படையிலான கணிப்பை வழங்குகிறது; இது உறுதிப்படுத்தப்பட்ட விவசாய நோய் கண்டறிதல் அல்ல. தீவிரமான பயிர் பிரச்சனைகளுக்கு தகுதி வாய்ந்த விவசாய நிபுணரை அணுகவும்."
                      : "Plant Guard AI provides an AI-based prediction and should not be considered a confirmed agricultural diagnosis. For serious crop problems, consult a qualified agricultural expert."}
                  </p>
                </div>
              </div>

            </div>

            <div className="mt-8 text-center">
              <button
                onClick={resetAnalysis}
                className="rounded-2xl border border-green-600 bg-white px-7 py-4 font-bold text-green-700 transition hover:bg-green-50"
              >
                🔄 {t.analyzeAnotherPlant}
              </button>
            </div>

          </div>
        </section>
      )}

      {/* SAVED PREDICTIONS */}
      <section id="history" className="bg-slate-50 px-5 py-20">
        <div className="mx-auto max-w-6xl">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-sm font-bold uppercase tracking-widest text-green-700">
                {t.navHistory}
              </p>
              <h2 className="mt-2 text-3xl font-black text-slate-900">
                {t.historyTitle}
              </h2>
              <p className="mt-2 text-slate-600">{t.historySubtitle}</p>
            </div>
            <button
              onClick={() => {
                setHistoryLoading(true);
                void refreshHistory();
              }}
              className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-bold text-slate-700 transition hover:bg-slate-100"
            >
              {t.retry}
            </button>
          </div>

          {historyLoading ? (
            <p className="mt-6 rounded-2xl bg-white p-6 text-slate-500">{t.historyLoading}</p>
          ) : historyError ? (
            <div className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-6 text-amber-900">
              {t.historyError}
            </div>
          ) : history.length === 0 ? (
            <p className="mt-6 rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-slate-500">
              {t.historyEmpty}
            </p>
          ) : (
            <ul className="mt-6 grid gap-4 md:grid-cols-2">
              {history.map((item) => (
                <li key={item.id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h3 className="text-lg font-bold text-slate-900">{item.disease_name}</h3>
                      <p className="mt-1 text-sm text-slate-600">{item.crop_name}</p>
                    </div>
                    <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-bold text-blue-800">
                      {t.modelConfidence}: {item.confidence === null ? "—" : `${item.confidence.toFixed(2)}%`}
                    </span>
                  </div>
                  <p className="mt-4 text-xs text-slate-500">
                    {item.created_at
                      ? new Date(item.created_at).toLocaleString(language === "ta" ? "ta-IN" : "en-US")
                      : "—"}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section
        id="how-it-works"
        className="bg-white px-5 py-24"
      >
        <div className="mx-auto max-w-6xl">

          <div className="mx-auto max-w-3xl text-center">
            <span className="text-sm font-bold uppercase tracking-widest text-green-700">
              {t.simpleProcess}
            </span>

            <h2 className="mt-3 text-4xl font-black text-slate-900">
              {t.howWorks}
            </h2>

            <p className="mt-4 text-lg text-slate-600">
              {t.howItWorksIntro}
            </p>
          </div>

          <div className="mt-14 grid gap-7 md:grid-cols-3">

            <div className="group rounded-3xl border border-slate-200 bg-slate-50 p-8 transition hover:-translate-y-1 hover:shadow-xl">

              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-green-100 text-3xl transition group-hover:scale-105">
                📷
              </div>

              <p className="mt-7 text-sm font-bold text-green-700">
                {t.step01}
              </p>

              <h3 className="mt-2 text-2xl font-black">
                {t.upload}
              </h3>

              <p className="mt-4 leading-7 text-slate-600">
                {t.howUploadDescription}
              </p>

            </div>

            <div className="group rounded-3xl border border-slate-200 bg-slate-50 p-8 transition hover:-translate-y-1 hover:shadow-xl">

              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-100 text-3xl transition group-hover:scale-105">
                🤖
              </div>

              <p className="mt-7 text-sm font-bold text-blue-700">
                {t.step02}
              </p>

              <h3 className="mt-2 text-2xl font-black">
                {t.aiAnalysis}
              </h3>

              <p className="mt-4 leading-7 text-slate-600">
                {t.howProcessingDescription}
              </p>

            </div>

            <div className="group rounded-3xl border border-slate-200 bg-slate-50 p-8 transition hover:-translate-y-1 hover:shadow-xl">

              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-orange-100 text-3xl transition group-hover:scale-105">
                🌱
              </div>

              <p className="mt-7 text-sm font-bold text-orange-700">
                {t.step03}
              </p>

              <h3 className="mt-2 text-2xl font-black">
                {t.getGuidance}
              </h3>

              <p className="mt-4 leading-7 text-slate-600">
                {t.howGuidanceDescription}
              </p>

            </div>

          </div>

        </div>
      </section>

      {/* FEATURES */}
      <section className="bg-slate-50 px-5 py-24">
        <div className="mx-auto max-w-6xl">

          <div className="text-center">
            <span className="text-sm font-bold uppercase tracking-widest text-green-700">
              {t.keyFeatures}
            </span>

            <h2 className="mt-3 text-4xl font-black">
              {t.keyFeatures}
            </h2>
          </div>

          <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">

            <div className="rounded-3xl bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-lg">
              <div className="text-3xl">🤖</div>
              <h3 className="mt-5 font-black">
                {t.aiDetection}
              </h3>
              <p className="mt-2 text-sm leading-6 text-slate-500">
                {t.featureRecognition}
              </p>
            </div>

            <div className="rounded-3xl bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-lg">
              <div className="text-3xl">📊</div>
              <h3 className="mt-5 font-black">
                {t.confidenceScore}
              </h3>
              <p className="mt-2 text-sm leading-6 text-slate-500">
                {t.featureConfidence}
              </p>
            </div>

            <div className="rounded-3xl bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-lg">
              <div className="text-3xl">🩺</div>
              <h3 className="mt-5 font-black">
                {t.plantGuidance}
              </h3>
              <p className="mt-2 text-sm leading-6 text-slate-500">
                {t.featureGuidance}
              </p>
            </div>

            <div className="rounded-3xl bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-lg">
              <div className="text-3xl">🤖</div>
              <h3 className="mt-5 font-black">
                {t.aiAssistant}
              </h3>
              <p className="mt-2 text-sm leading-6 text-slate-500">
                {t.featureAssistant}
              </p>
            </div>

          </div>

        </div>
      </section>

      {/* ABOUT */}
<section
  id="about"
  className="scroll-mt-20 bg-white px-5 py-24"
>
  <div className="mx-auto grid max-w-6xl gap-12 lg:grid-cols-2 lg:items-center">

    <div>
      <span className="text-sm font-bold uppercase tracking-widest text-green-700">
        {t.aboutProject}
      </span>

      <h2 className="mt-3 text-4xl font-black text-slate-900">
        {t.healthierPlants}
      </h2>

      <p className="mt-6 text-lg leading-8 text-slate-600">
        {t.projectIntro}
      </p>

      <p className="mt-5 leading-7 text-slate-600">
        {t.projectSystem}
      </p>

      <button
        onClick={() => scrollToSection("analyzer")}
        className="mt-7 rounded-2xl bg-green-700 px-6 py-3 font-bold text-white transition hover:bg-green-800"
      >
        {t.tryDiseaseDetection} →
      </button>
    </div>

    <div className="rounded-[2rem] bg-gradient-to-br from-green-700 to-emerald-600 p-8 text-white shadow-xl">

      <div className="text-5xl">
        🌱
      </div>

      <h3 className="mt-6 text-3xl font-black">
        Plant Guard AI
      </h3>

      <p className="mt-4 leading-7 text-green-50">
        {t.platformDescription}
      </p>

      <div className="mt-8 space-y-5">

        <div>
          <p className="font-bold">
            ✓ {t.featureDiseaseDetection}
          </p>
          <p className="mt-1 text-sm text-green-100">
            {t.featureDiseaseDetectionText}
          </p>
        </div>

        <div>
          <p className="font-bold">
            ✓ {t.featureConfidenceResults}
          </p>
          <p className="mt-1 text-sm text-green-100">
            {t.featureConfidenceResultsText}
          </p>
        </div>

        <div>
          <p className="font-bold">
            ✓ {t.featureInfoSymptoms}
          </p>
          <p className="mt-1 text-sm text-green-100">
            {t.featureInfoSymptomsText}
          </p>
        </div>

        <div>
          <p className="font-bold">
            ✓ {t.featureTreatmentPrevention}
          </p>
          <p className="mt-1 text-sm text-green-100">
            {t.featureTreatmentPreventionText}
          </p>
        </div>

        <div>
          <p className="font-bold">
            ✓ {t.featureTreatmentCalculator}
          </p>
          <p className="mt-1 text-sm text-green-100">
            {t.featureTreatmentCalculatorText}
          </p>
        </div>

      </div>
    </div>

  </div>
</section>

      {/* CTA */}
      <section className="px-5 py-20">
        <div className="mx-auto max-w-6xl overflow-hidden rounded-[2rem] bg-gradient-to-r from-green-700 to-emerald-600 p-8 text-center text-white shadow-xl md:p-14">

          <div className="text-5xl">
            🌿
          </div>

          <h2 className="mt-5 text-3xl font-black md:text-4xl">
            {t.readyCheckPlant}
          </h2>

          <p className="mx-auto mt-4 max-w-2xl text-green-50">
            {t.ctaDescription}
          </p>

          <button
            onClick={() => scrollToSection("analyzer")}
            className="mt-7 rounded-2xl bg-white px-7 py-4 font-black text-green-800 shadow-lg transition hover:-translate-y-0.5"
          >
            🔍 {t.startAnalysis}
          </button>

        </div>
      </section>

      {/* FOOTER */}
      <footer className="bg-slate-950 px-5 py-12 text-white">

        <div className="mx-auto grid max-w-6xl gap-10 md:grid-cols-3">

          <div>
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-green-700 text-2xl">
                🌱
              </div>

              <div>
                <h3 className="font-black">
                  Plant Guard AI
                </h3>

                <p className="text-xs text-slate-400">
                  {t.techFooterText}
                </p>
              </div>
            </div>

            <p className="mt-5 max-w-sm text-sm leading-6 text-slate-400">
              {t.footerSummary}
            </p>
          </div>

          <div>
            <h3 className="font-bold">
              {t.quickNav}
            </h3>

            <div className="mt-4 space-y-3 text-sm text-slate-400">

              <button
                onClick={() => scrollToSection("home")}
                className="block transition hover:text-white"
              >
                {t.homeLink}
              </button>

              <button
                onClick={() => scrollToSection("analyzer")}
                className="block transition hover:text-white"
              >
                {t.diseaseDetectionLink}
              </button>

              <button
                onClick={() => scrollToSection("history")}
                className="block transition hover:text-white"
              >
                {t.navHistory}
              </button>

              <button
                onClick={() =>
                  scrollToSection("how-it-works")
                }
                className="block transition hover:text-white"
              >
                {t.howItWorksLink}
              </button>

              <button
                onClick={() => scrollToSection("about")}
                className="block transition hover:text-white"
              >
                {t.aboutLink}
              </button>

            </div>
          </div>

          <div>
            <h3 className="font-bold">
              {t.projectLink}
            </h3>

            <p className="mt-4 text-sm leading-6 text-slate-400">
              B.Tech Artificial Intelligence & Data Science
            </p>

            <p className="mt-3 text-sm text-slate-500">
              {t.miniProject}
            </p>
          </div>

        </div>

        <div className="mx-auto mt-10 max-w-6xl border-t border-slate-800 pt-6 text-center text-xs text-slate-500">
          {t.footerCopyright}
        </div>

      </footer>

      {/* CHATBOT */}
      {chatOpen && (
        <div className="fixed bottom-24 right-5 z-[60] flex h-[520px] w-[350px] flex-col overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-2xl sm:right-7">

          {/* CHAT HEADER */}
          <div className="bg-gradient-to-r from-green-700 to-emerald-600 p-5 text-white">

            <div className="flex items-center justify-between">

              <div className="flex items-center gap-3">

                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/15 text-2xl">
                  🤖
                </div>

                <div>
                  <h3 className="font-black">
                    {t.chatbotTitle}
                  </h3>

                  <div className="mt-0.5 flex items-center gap-1.5 text-xs text-green-100">
                    <span className="h-2 w-2 rounded-full bg-green-300" />
                    {t.chatInline}
                  </div>
                </div>

              </div>

              <button
                onClick={() => setChatOpen(false)}
                className="rounded-xl p-2 text-white transition hover:bg-white/10"
              >
                ✕
              </button>

            </div>

          </div>

          {/* MESSAGES */}
          <div
            ref={chatMessagesRef}
            className="flex-1 space-y-4 overflow-y-auto bg-slate-50 p-4"
          >

            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${
                  message.sender === "user"
                    ? "justify-end"
                    : "justify-start"
                }`}
              >

                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-6 ${
                    message.sender === "user"
                      ? "rounded-br-md bg-green-700 text-white"
                      : "rounded-bl-md bg-white text-slate-700 shadow-sm"
                  }`}
                >
                  {message.text}
                </div>

              </div>
            ))}

          </div>

          {/* CHAT INPUT */}
          <div className="border-t bg-white p-3">

            <div className="flex items-center gap-2">

              <input
                type="text"
                value={chatMessage}
                disabled={chatLoading}
                onChange={(event) =>
                  setChatMessage(event.target.value)
                }
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    sendChatMessage();
                  }
                }}
                placeholder={chatLoading ? t.chatThinking : t.chatPlaceholder}
                className="min-w-0 flex-1 rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-sm outline-none focus:border-green-500 focus:ring-2 focus:ring-green-100 disabled:cursor-not-allowed disabled:opacity-60"
              />

              <button
                onClick={sendChatMessage}
                disabled={chatLoading}
                className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-green-700 text-lg text-white transition hover:bg-green-800 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {chatLoading ? "…" : "➤"}
              </button>

            </div>

          </div>

        </div>
      )}

      {/* FLOATING CHAT BUTTON */}
      <button
        onClick={() => setChatOpen(!chatOpen)}
        className="fixed bottom-6 right-5 z-[60] flex h-16 w-16 items-center justify-center rounded-full bg-green-700 text-3xl text-white shadow-2xl shadow-green-900/30 transition hover:scale-105 hover:bg-green-800 sm:right-7"
        aria-label="Open Plant Guard AI chatbot"
      >
        {chatOpen ? "✕" : "🤖"}

        {!chatOpen && (
          <span className="absolute right-0 top-0 h-4 w-4 rounded-full bg-green-300 ring-2 ring-white" />
        )}
      </button>

    </main>
  );
}
