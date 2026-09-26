"use client";

import { useEffect, useMemo, useState } from "react";

interface PredictionResult {
  message?: string;
  filename?: string;
  prediction: string;
  confidence: number;
  status?: string;
  disease: {
    id: number;
    name: string;
    crop_name: string;
    description: string;
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
      application_method: string;
      measurement_unit: string;
      rate: number | null;
      basis: string;
      notes: string;
    }[];
  }[];
  prevention: {
    id: number;
    title: string;
    description: string;
  }[];
}

interface LegacyDiseaseInfo {
  about: string;
  symptoms: string[];
  treatment: string[];
  prevention: string[];
}

interface DatabaseDiseaseInfo {
  about: string;
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

type TreatmentCalculationResult =
  | {
      error: string;
      quantity: null;
      totalRequired: null;
      basisLabel: string;
      unitLabel: string;
      rateDisplay: string;
      calculationText: string;
    }
  | {
      error: null;
      quantity: number;
      totalRequired: number;
      basisLabel: string;
      unitLabel: string;
      rateDisplay: string;
      calculationText: string;
    };

const translations: Record<Language, Record<string, string>> = {
  en: {
    navHome: "Home",
    navDetect: "Detect",
    navHow: "How It Works",
    navAbout: "About",
    notifications: "Notifications",
    notificationsSubtitle: "Plant health updates",
    notificationsLoading: "Loading notifications...",
    notificationsClose: "Close",
    notificationsEmpty: "No notifications right now. Check back later for plant-care reminders.",
    noNotifications: "No notifications right now.",
    assistantOnline: "Assistant online",
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
    confidence: "Confidence",
    guidance: "Guidance",
    detectedCondition: "Detected Condition",
    modelConfidence: "Model Confidence",
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
    confidenceScore: "Confidence Score",
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
    notifications: "அறிவிப்புகள்",
    notificationsSubtitle: "தாவர ஆரோக்கிய புதுப்பிப்புகள்",
    notificationsLoading: "அறிவிப்புகள் ஏற்றப்படுகின்றன...",
    notificationsClose: "மூடு",
    notificationsEmpty: "தற்சமயம் அறிவிப்புகள் இல்லை. சிறிது நேரம் கழித்து மீண்டும் பார்க்கவும்.",
    noNotifications: "தற்சமயம் அறிவிப்புகள் இல்லை.",
    assistantOnline: "செயல்பாட்டில் உள்ளது",
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
    confidence: "நம்பகத்தன்மை",
    guidance: "வழிகாட்டல்",
    detectedCondition: "கண்டறியப்பட்ட நிலை",
    modelConfidence: "மாதிரி நம்பகத்தன்மை",
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
    confidenceScore: "நம்பகத்தன்மை மதிப்பெண்",
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

function getDisplayUnit(measurementUnit: string) {
  if (!measurementUnit) {
    return "unit";
  }

  const cleanUnit = measurementUnit.trim();

  if (cleanUnit.includes("/")) {
    return cleanUnit.split("/")[0].trim() || "unit";
  }

  return cleanUnit || "unit";
}

function getProductDisplayName(
  treatmentName: string,
  notes: string
) {
  const cleanNotes = (notes || "").trim();

  if (!cleanNotes) {
    return treatmentName || "Unknown product";
  }

  const beforeSource = cleanNotes.split(/\s*Source:/i)[0].trim();

  if (beforeSource && beforeSource.length > 0) {
    return beforeSource.replace(/\.$/, "");
  }

  return treatmentName || "Unknown product";
}

function getRateBasisType(measurementUnit: string, basis: string) {
  const normalizedUnit = (measurementUnit || "").toLowerCase();
  const normalizedBasis = (basis || "").toLowerCase();

  if (
    normalizedBasis.includes("plant") ||
    normalizedUnit.includes("/plant") ||
    normalizedUnit.includes("plant")
  ) {
    return "plant";
  }

  if (
    normalizedBasis.includes("acre") ||
    normalizedUnit.includes("/acre") ||
    normalizedUnit.includes("acre")
  ) {
    return "area";
  }

  return "unknown";
}

function formatDiseaseName(prediction: string) {
  const parts = prediction.split("___");

  if (parts.length !== 2) {
    return {
      plant: "Unknown Plant",
      disease: prediction.replaceAll("_", " ").trim(),
    };
  }

  return {
    plant: parts[0].replaceAll("_", " ").trim(),
    disease: parts[1].replaceAll("_", " ").trim(),
  };
}

function getDiseaseInfo(disease: string): LegacyDiseaseInfo {
  const lower = disease.toLowerCase();

  if (lower.includes("late blight")) {
    return {
      about:
        "Late blight is a plant disease that can spread quickly, especially in cool and humid conditions.",
      symptoms: [
        "Dark or brown spots on leaves.",
        "Leaves may become weak and die.",
        "Disease may spread rapidly.",
      ],
      treatment: [
        "Remove severely affected leaves.",
        "Avoid watering directly over leaves.",
        "Improve air circulation.",
        "Follow the label instructions of suitable plant protection products.",
      ],
      prevention: [
        "Maintain proper spacing between plants.",
        "Keep leaves as dry as possible.",
        "Remove infected plant material.",
      ],
    };
  }

  if (lower.includes("early blight")) {
    return {
      about:
        "Early blight is a common fungal disease that can affect leaves and reduce plant growth.",
      symptoms: [
        "Small dark spots on older leaves.",
        "Spots may become larger.",
        "Leaves may turn yellow and fall.",
      ],
      treatment: [
        "Remove severely affected leaves.",
        "Keep the growing area clean.",
        "Avoid overhead watering.",
        "Use suitable treatment according to the product label.",
      ],
      prevention: [
        "Provide good plant spacing.",
        "Remove fallen infected leaves.",
        "Avoid prolonged leaf wetness.",
      ],
    };
  }

  if (lower.includes("powdery mildew")) {
    return {
      about:
        "Powdery mildew commonly appears as a white powder-like coating on plant leaves.",
      symptoms: [
        "White powder-like patches on leaves.",
        "Leaves may become distorted.",
        "Plant growth may become weaker.",
      ],
      treatment: [
        "Remove heavily infected leaves.",
        "Improve air circulation.",
        "Avoid excessive humidity.",
        "Use appropriate treatment according to the product label.",
      ],
      prevention: [
        "Give plants enough space.",
        "Avoid excessive watering.",
        "Keep the growing area clean.",
      ],
    };
  }

  if (lower.includes("bacterial spot")) {
    return {
      about:
        "Bacterial spot can cause dark or water-soaked spots on leaves and may reduce plant health.",
      symptoms: [
        "Small dark spots on leaves.",
        "Spots may enlarge.",
        "Affected leaves may become damaged.",
      ],
      treatment: [
        "Remove severely affected plant parts.",
        "Avoid handling plants when leaves are wet.",
        "Improve air circulation.",
        "Follow local agricultural guidance.",
      ],
      prevention: [
        "Use clean planting material.",
        "Avoid unnecessary leaf wetting.",
        "Remove infected plant debris.",
      ],
    };
  }

  if (lower.includes("apple scab")) {
    return {
      about:
        "Apple scab is a fungal disease that commonly affects apple leaves and fruit.",
      symptoms: [
        "Olive or dark spots on leaves.",
        "Leaves may become distorted.",
        "Fruit may develop rough or scabby areas.",
      ],
      treatment: [
        "Remove heavily infected leaves.",
        "Remove fallen infected plant material.",
        "Improve air circulation.",
        "Follow suitable agricultural treatment guidance.",
      ],
      prevention: [
        "Keep the growing area clean.",
        "Remove fallen leaves.",
        "Maintain good airflow around the plant.",
      ],
    };
  }

  if (lower.includes("black rot")) {
    return {
      about:
        "Black rot can cause dark lesions and deterioration of plant tissue.",
      symptoms: [
        "Dark lesions on leaves.",
        "Yellowing around affected areas.",
        "Plant tissue may gradually deteriorate.",
      ],
      treatment: [
        "Remove infected plant parts.",
        "Dispose of infected material safely.",
        "Improve air circulation.",
        "Follow appropriate agricultural guidance.",
      ],
      prevention: [
        "Keep plants healthy and well spaced.",
        "Remove infected debris.",
        "Avoid prolonged moisture on leaves.",
      ],
    };
  }

  if (lower.includes("healthy")) {
    return {
      about:
        "The AI model did not detect a known disease in the uploaded plant image.",
      symptoms: [
        "No major disease symptoms were detected by the model.",
        "Continue monitoring the plant regularly.",
      ],
      treatment: [
        "No disease treatment is currently required based on this prediction.",
        "Continue regular plant care and monitoring.",
      ],
      prevention: [
        "Provide sufficient water and nutrients.",
        "Maintain good air circulation.",
        "Regularly inspect leaves.",
      ],
    };
  }

  return {
    about:
      "The AI model detected a possible plant disease. This result should be treated as an AI-based indication rather than a confirmed diagnosis.",
    symptoms: [
      "Symptoms may vary depending on the plant and disease.",
      "Inspect affected leaves carefully.",
    ],
    treatment: [
      "Remove severely affected plant parts when appropriate.",
      "Maintain good air circulation.",
      "Avoid unnecessary leaf wetting.",
      "Follow product labels and local agricultural recommendations.",
    ],
    prevention: [
      "Keep the growing area clean.",
      "Monitor plants regularly.",
      "Remove infected plant material when appropriate.",
    ],
  };
}

function getExplanation(disease: string, language: Language) {
  const lower = disease.toLowerCase();

  if (lower.includes("healthy")) {
    return language === "ta"
      ? "AI மாடல் இந்த தாவரப் படத்தில் அறியப்பட்ட நோயைக் கண்டறியவில்லை."
      : "The AI model did not detect a known disease in this plant image.";
  }

  if (lower.includes("late blight")) {
    return language === "ta"
      ? "குளிர்ச்சியான மற்றும் அதிக ஈரப்பதம் கொண்ட சூழ்நிலைகளில் லேட் ப்ளைட் நோய் வேகமாகப் பரவக்கூடும். ஆரம்பத்திலேயே கவனித்து, சரியான தாவர பராமரிப்பை மேற்கொள்வது நோய் மேலும் பரவுவதை குறைக்க உதவும்."
      : "Late blight can spread quickly under cool and humid conditions. Early observation and proper plant care can help reduce further spread.";
  }

  if (lower.includes("early blight")) {
    return language === "ta"
      ? "ஆரம்பகால ப்ளைட் நோய் இலைகளில் கருமையான புள்ளிகளை உருவாக்கி, நிலைமை முன்னேறும்போது தாவர வளர்ச்சியைக் குறைக்கலாம்."
      : "Early blight can cause dark spots on leaves and may reduce plant growth if the condition progresses.";
  }

  if (lower.includes("powdery mildew")) {
    return language === "ta"
      ? "பவுடரி மில்டெவ் பொதுவாக இலைகளில் வெள்ளை தூள் போன்ற பூச்சாகத் தோன்றி, தாவர வளர்ச்சியை பாதிக்கலாம்."
      : "Powdery mildew commonly appears as a white powder-like coating on leaves and can affect plant growth.";
  }

  if (lower.includes("bacterial spot")) {
    return language === "ta"
      ? "பாக்டீரியா ஸ்பாட் நோய் இலைகளில் சிறிய கருமையான அல்லது நீர் நிறைந்த புள்ளிகளை ஏற்படுத்தி, தாவர திசுக்களைக் காயப்படுத்தலாம்."
      : "Bacterial spot can cause small dark or water-soaked spots on leaves and may damage plant tissue.";
  }

  if (lower.includes("leaf spot")) {
    return language === "ta"
      ? "இலை புள்ளி நோய்கள் இலைகளில் தெரியும் புள்ளிகள் அல்லது சேதத்தை உருவாக்கலாம்."
      : "Leaf spot diseases can create visible spots or damaged areas on plant leaves.";
  }

  return language === "ta"
    ? "AI மாடல் சாத்தியமான தாவர நோயைக் கண்டறிந்துள்ளது. மேலும் கவனிப்பு மற்றும் நிபுணர் சரிபார்ப்பு பயனுள்ளதாக இருக்கும்."
    : "The AI model detected a possible plant disease. Further observation and expert verification may be useful.";
}

export default function Home() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [calculatorQuantity, setCalculatorQuantity] = useState("");
  const [selectedRateId, setSelectedRateId] = useState<number | null>(null);

  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [notificationsLoading, setNotificationsLoading] = useState(false);
  const [notificationsError, setNotificationsError] = useState("");
  const [chatOpen, setChatOpen] = useState(false);
  const [chatMessage, setChatMessage] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [language, setLanguage] = useState<Language>("en");

  const t = translations[language];

  useEffect(() => {
    const savedLanguage = sessionStorage.getItem("plant-guard-language");
    if (savedLanguage === "en" || savedLanguage === "ta") {
      setLanguage(savedLanguage as Language);
    }
  }, []);

  useEffect(() => {
    sessionStorage.setItem("plant-guard-language", language);
  }, [language]);

  useEffect(() => {
    setMessages((current) => {
      const hasOnlyWelcomeMessage =
        current.length === 1 && current[0]?.sender === "bot";

      if (!hasOnlyWelcomeMessage) {
        return current;
      }

      return [{ sender: "bot", text: t.welcomeBot }];
    });
  }, [language, t.welcomeBot]);

  const [messages, setMessages] = useState<
    { sender: "bot" | "user"; text: string }[]
  >([
    {
      sender: "bot",
      text: translations.en.welcomeBot,
    },
  ]);

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
      const response = await fetch("http://127.0.0.1:8000/api/notifications", {
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
        "http://127.0.0.1:8000/api/upload",
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

      setTimeout(() => {
        scrollToSection("result");
      }, 200);
    } catch (err) {
      console.error(err);

      setError(
        "Unable to connect to Plant Guard AI backend. Make sure FastAPI is running."
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
    setSelectedRateId(null);
  };

  const calculatorOptions = useMemo(
    () =>
      result?.treatments.flatMap((treatment) =>
        treatment.application_rates
          .filter(
            (rate) =>
              rate.rate !== null &&
              Number.isFinite(Number(rate.rate)) &&
              Number(rate.rate) >= 0
          )
          .map((rate) => ({
            rateId: rate.id,
            treatmentId: treatment.id,
            treatmentName: treatment.name,
            treatmentType: treatment.type,
            productName: getProductDisplayName(
              treatment.name,
              rate.notes
            ),
            applicationMethod: rate.application_method,
            measurementUnit: rate.measurement_unit,
            rate: Number(rate.rate),
            basis: rate.basis,
            notes: rate.notes,
            basisType: getRateBasisType(
              rate.measurement_unit,
              rate.basis
            ),
          }))
      ) ?? [],
    [result]
  );

  const displayedOptions = useMemo(
    () => calculatorOptions.filter((option) => option.basisType === "area"),
    [calculatorOptions]
  );

  const selectedRate = useMemo(
    () =>
      displayedOptions.find((option) => option.rateId === selectedRateId) ??
      displayedOptions[0] ??
      null,
    [displayedOptions, selectedRateId]
  );

  const treatmentCalculation: TreatmentCalculationResult = useMemo(() => {
    if (!selectedRate) {
      return {
        error: "No area-based application-rate data is available for the selected product.",
        quantity: null,
        totalRequired: null,
        basisLabel: "",
        unitLabel: "",
        rateDisplay: "",
        calculationText: "",
      };
    }

    const quantity = Number(calculatorQuantity);

    if (
      calculatorQuantity.trim() === "" ||
      !Number.isFinite(quantity) ||
      quantity <= 0
    ) {
      return {
        error: "Enter a valid affected area greater than zero.",
        quantity: null,
        totalRequired: null,
        basisLabel: "",
        unitLabel: "",
        rateDisplay: "",
        calculationText: "",
      };
    }

    const totalRequired = quantity * selectedRate.rate;

    return {
      error: null,
      quantity,
      totalRequired,
      basisLabel:
        selectedRate.basis && selectedRate.basis.trim()
          ? selectedRate.basis
          : "per unit",
      unitLabel: getDisplayUnit(selectedRate.measurementUnit),
      rateDisplay: `${selectedRate.rate} ${selectedRate.measurementUnit}`,
      calculationText: `${quantity} acres × ${selectedRate.rate} ${selectedRate.measurementUnit} = ${totalRequired.toFixed(2)} ${getDisplayUnit(selectedRate.measurementUnit)}`,
    };
  }, [calculatorQuantity, selectedRate]);

  const hasValidCalculation =
    treatmentCalculation.error === null &&
    treatmentCalculation.totalRequired !== null;

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

    try {
      const response = await fetch("http://127.0.0.1:8000/api/chat", {
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

      if (!response.ok) {
        throw new Error(data.detail || "Unable to get a grounded response.");
      }

      setMessages((current) => {
        const updated = [...current];
        const botIndex = updated.findLastIndex(
          (item) => item.sender === "bot" && item.text === "Thinking..."
        );

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

      setMessages((current) => {
        const updated = [...current];
        const botIndex = updated.findLastIndex(
          (item) => item.sender === "bot" && item.text === "Thinking..."
        );

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
        plant: result.disease.crop_name,
        disease: result.disease.name,
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

          <div className="hidden items-center gap-7 md:flex">
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
          </div>

          <div className="flex items-center gap-3">
            <label className="hidden items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm sm:flex">
              <span className="text-xs uppercase tracking-wide text-slate-400">{t.languageLabel}</span>

              <select
                value={language}
                onChange={(event) => setLanguage(event.target.value as Language)}
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
                      Preview
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
                    alt="Selected plant leaf"
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
                      Analysis failed
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
                  {t.detectedCondition}
                </p>

                <h2 className="mt-2 text-4xl font-black md:text-5xl">
                  {diseaseData.disease}
                </h2>

                <p className="mt-4 text-lg text-green-50">
                  {language === "ta" ? "தாவர அடையாளம்:" : "Plant identified as"}{" "}
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

                    <div className="text-3xl">
                      {confidence >= 70
                        ? "🟢"
                        : confidence >= 40
                        ? "🟡"
                        : "🟠"}
                    </div>
                  </div>

                  <div className="mt-5 h-4 overflow-hidden rounded-full bg-slate-200">
                    <div
                      className="h-full rounded-full bg-green-600 transition-all duration-700"
                      style={{
                        width:
                          Math.min(confidence, 100) + "%",
                      }}
                    />
                  </div>

                  <p className="mt-3 text-sm text-slate-500">
                    {confidence >= 70
                      ? language === "ta"
                        ? "அதிக நம்பகத்தன்மை கொண்ட முடிவு."
                        : "High confidence result."
                      : confidence >= 40
                      ? language === "ta"
                        ? "மிதமான நம்பகத்தன்மை கொண்ட முடிவு. அறிகுறிகளைச் சரிபார்க்க பரிந்துரைக்கப்படுகிறது."
                        : "Moderate confidence result. Consider verifying the symptoms."
                      : language === "ta"
                        ? "குறைந்த நம்பகத்தன்மை கொண்ட முடிவு. கைமுறையாக சரிபார்ப்பது மிகவும் பரிந்துரைக்கப்படுகிறது."
                        : "Low confidence result. Manual verification is strongly recommended."}
                  </p>

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
                        {getExplanation(
                          diseaseData.disease,
                          language
                        )}
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
                  {diseaseInfo.about}
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
                  {diseaseInfo.symptoms.map(
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
                  )}
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
                  {diseaseInfo.causes.map((cause) => (
                    <li key={cause.id} className="flex gap-3 text-slate-600">
                      <span className="mt-1 text-purple-600">•</span>
                      <span>
                        <strong>{cause.name}</strong>
                        {cause.description
                          ? ` — ${cause.description}`
                          : ""}
                      </span>
                    </li>
                  ))}
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
                      No treatment information is available.
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
                  {diseaseInfo.prevention.map(
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
                  )}
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
                  Estimate the required treatment quantity using the disease-specific application rates from the agricultural knowledge base.
                </p>
              </div>

              {displayedOptions.length === 0 ? (
                <div className="mx-auto mt-8 max-w-2xl rounded-2xl border border-amber-200 bg-white/80 p-5 text-center text-sm text-slate-600">
                  No area-based application-rate data is available for this disease in the current knowledge base.
                </div>
              ) : (
                <>
                  <div className="mx-auto mt-8 max-w-4xl">
                    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                      <label className="mb-3 block text-sm font-bold text-slate-700">
                        {t.affectedArea}
                      </label>

                      <div className="flex flex-col gap-3 sm:flex-row">
                        <input
                          type="number"
                          min="0"
                          step="0.01"
                          value={calculatorQuantity}
                          onChange={(event) => setCalculatorQuantity(event.target.value)}
                          placeholder="Example: 0.16"
                          className="w-full rounded-2xl border border-slate-300 bg-white px-5 py-4 outline-none transition focus:border-green-500 focus:ring-4 focus:ring-green-100"
                        />

                        <div className="flex items-center justify-center rounded-2xl border border-slate-200 bg-slate-50 px-5 py-4 text-sm font-bold text-slate-700">
                          {t.acres}
                        </div>
                      </div>

                      <p className="mt-2 text-xs text-slate-500">
                        Enter the area of the crop that needs treatment.
                      </p>
                    </div>
                  </div>

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
                          <p className="font-bold text-slate-700">Basis</p>
                          <p className="mt-1 text-base font-black text-slate-900">
                            {selectedRate.basis || "per unit"}
                          </p>
                        </div>

                        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                          <p className="font-bold text-slate-700">{t.affectedArea}</p>
                          <p className="mt-1 text-base font-black text-slate-900">
                            {calculatorQuantity || "0"} acre
                          </p>
                        </div>

                        {selectedRate.treatmentName && (
                          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                            <p className="font-bold text-slate-700">Treatment group</p>
                            <p className="mt-1 text-base font-black text-slate-900">
                              {selectedRate.treatmentName}
                            </p>
                          </div>
                        )}
                      </div>

                      {selectedRate.notes && (
                        <p className="mt-4 text-sm text-slate-500">
                          <strong>{language === "ta" ? "குறிப்புகள்:" : "Notes:"}</strong> {selectedRate.notes}
                        </p>
                      )}

                      {treatmentCalculation.error ? (
                        <div className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
                          {treatmentCalculation.error}
                        </div>
                      ) : hasValidCalculation ? (
                        <>
                          <div className="mt-6 rounded-2xl border border-green-200 bg-green-50 p-5 text-center">
                            <p className="text-sm font-semibold text-slate-500">
                              {t.requiredQuantity}
                            </p>

                            <p className="mt-2 text-4xl font-black text-green-700">
                              {treatmentCalculation.totalRequired.toFixed(2)}
                            </p>

                            <p className="mt-1 text-xs font-medium uppercase tracking-wide text-slate-500">
                              {treatmentCalculation.unitLabel}
                            </p>
                          </div>

                          <div className="mt-4 text-sm leading-6 text-slate-600">
                            <strong>{language === "ta" ? "கணக்கீடு:" : "Calculation:"}</strong> {treatmentCalculation.calculationText}
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
                🔄 Analyze Another Plant
              </button>
            </div>

          </div>
        </section>
      )}

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
                    Assistant online
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
          <div className="flex-1 space-y-4 overflow-y-auto bg-slate-50 p-4">

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