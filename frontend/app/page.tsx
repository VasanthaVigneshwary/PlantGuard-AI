"use client";

import { useState } from "react";

interface PredictionResult {
  message?: string;
  filename?: string;
  prediction: string;
  confidence: number;
  status?: string;
}

interface DiseaseInfo {
  about: string;
  symptoms: string[];
  treatment: string[];
  prevention: string[];
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

function getDiseaseInfo(disease: string): DiseaseInfo {
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

function getExplanation(disease: string) {
  const lower = disease.toLowerCase();

  if (lower.includes("healthy")) {
    return "The AI model did not detect a known disease in this plant image.";
  }

  if (lower.includes("late blight")) {
    return "Late blight can spread quickly under cool and humid conditions. Early observation and proper plant care can help reduce further spread.";
  }

  if (lower.includes("early blight")) {
    return "Early blight can cause dark spots on leaves and may reduce plant growth if the condition progresses.";
  }

  if (lower.includes("powdery mildew")) {
    return "Powdery mildew commonly appears as a white powder-like coating on leaves and can affect plant growth.";
  }

  if (lower.includes("bacterial spot")) {
    return "Bacterial spot can cause small dark or water-soaked spots on leaves and may damage plant tissue.";
  }

  if (lower.includes("leaf spot")) {
    return "Leaf spot diseases can create visible spots or damaged areas on plant leaves.";
  }

  return "The AI model detected a possible plant disease. Further observation and expert verification may be useful.";
}

export default function Home() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [affectedPlants, setAffectedPlants] = useState("");
  const [ratePerPlant, setRatePerPlant] = useState("");

  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const [chatMessage, setChatMessage] = useState("");

  const [messages, setMessages] = useState<
    { sender: "bot" | "user"; text: string }[]
  >([
    {
      sender: "bot",
      text: "Hi! 🌱 I'm Plant Guard AI. Ask me about plant diseases, symptoms, prevention, or how to use the disease detector.",
    },
  ]);

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
    setAffectedPlants("");
    setRatePerPlant("");
  };

  const calculateTreatment = () => {
    const plants = Number(affectedPlants);
    const rate = Number(ratePerPlant);

    if (!plants || !rate || plants < 0 || rate < 0) {
      return null;
    }

    return plants * rate;
  };

  const sendChatMessage = () => {
    const message = chatMessage.trim();

    if (!message) {
      return;
    }

    setMessages((current) => [
      ...current,
      {
        sender: "user",
        text: message,
      },
    ]);

    setChatMessage("");

    const lower = message.toLowerCase();

    let response =
      "I can help with basic plant disease information. Try asking about late blight, symptoms, prevention, or how Plant Guard AI works. 🌱";

    if (
      lower.includes("late blight") ||
      lower.includes("lateblight")
    ) {
      response =
        "Late blight is a plant disease that can spread quickly in cool and humid conditions. Look for dark spots on leaves and remove severely affected plant parts when appropriate.";
    } else if (lower.includes("early blight")) {
      response =
        "Early blight commonly causes dark spots on older leaves. Good air circulation, clean growing areas, and avoiding prolonged leaf wetness can help manage the risk.";
    } else if (
      lower.includes("powdery mildew") ||
      lower.includes("mildew")
    ) {
      response =
        "Powdery mildew often appears as white powder-like patches on leaves. Improving air circulation and avoiding excessive humidity can help.";
    } else if (
      lower.includes("symptom") ||
      lower.includes("symptoms")
    ) {
      response =
        "Plant disease symptoms can include leaf spots, yellowing, wilting, white powder-like growth, or damaged plant tissue. Upload a clear leaf image to use the AI detector.";
    } else if (
      lower.includes("prevent") ||
      lower.includes("prevention")
    ) {
      response =
        "Good prevention includes regular plant inspection, proper spacing, good air circulation, clean growing areas, and avoiding unnecessary leaf wetting.";
    } else if (
      lower.includes("how") &&
      lower.includes("work")
    ) {
      response =
        "Plant Guard AI works by accepting a plant leaf image, sending it to the FastAPI backend, and using a trained deep learning model to predict a possible disease and confidence score.";
    } else if (
      lower.includes("hello") ||
      lower.includes("hi") ||
      lower.includes("hey")
    ) {
      response =
        "Hello! 🌿 I'm Plant Guard AI. How can I help you with your plant today?";
    }

    setTimeout(() => {
      setMessages((current) => [
        ...current,
        {
          sender: "bot",
          text: response,
        },
      ]);
    }, 500);
  };

  const treatmentAmount = calculateTreatment();

  const diseaseData = result
    ? formatDiseaseName(result.prediction)
    : null;

  const diseaseInfo = diseaseData
    ? getDiseaseInfo(diseaseData.disease)
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
                AI Plant Health Assistant
              </div>
            </div>
          </button>

          <div className="hidden items-center gap-7 md:flex">
            <button
              onClick={() => scrollToSection("home")}
              className="text-sm font-semibold text-slate-600 transition hover:text-green-700"
            >
              Home
            </button>

            <button
              onClick={() => scrollToSection("analyzer")}
              className="text-sm font-semibold text-slate-600 transition hover:text-green-700"
            >
              Detect
            </button>

            <button
              onClick={() => scrollToSection("how-it-works")}
              className="text-sm font-semibold text-slate-600 transition hover:text-green-700"
            >
              How It Works
            </button>

            <button
              onClick={() => scrollToSection("about")}
              className="text-sm font-semibold text-slate-600 transition hover:text-green-700"
            >
              About
            </button>
          </div>

          <div className="relative">
            <button
              onClick={() =>
                setNotificationsOpen(!notificationsOpen)
              }
              className="relative flex h-11 w-11 items-center justify-center rounded-full border border-slate-200 bg-white text-xl shadow-sm transition hover:bg-green-50"
              aria-label="Notifications"
            >
              🔔

              <span className="absolute right-2 top-2 h-2.5 w-2.5 rounded-full bg-red-500 ring-2 ring-white" />
            </button>

            {notificationsOpen && (
              <div className="absolute right-0 top-14 w-80 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl">

                <div className="flex items-center justify-between border-b p-4">
                  <div>
                    <h3 className="font-bold text-slate-800">
                      Notifications
                    </h3>

                    <p className="text-xs text-slate-500">
                      Plant health updates
                    </p>
                  </div>

                  <span className="rounded-full bg-green-100 px-2 py-1 text-xs font-bold text-green-700">
                    3
                  </span>
                </div>

                <div className="space-y-1 p-2">

                  <button className="flex w-full gap-3 rounded-xl p-3 text-left transition hover:bg-green-50">
                    <span className="text-xl">🌿</span>

                    <div>
                      <p className="text-sm font-semibold">
                        Plant health check
                      </p>

                      <p className="text-xs text-slate-500">
                        Upload a leaf image for AI analysis.
                      </p>
                    </div>
                  </button>

                  <button className="flex w-full gap-3 rounded-xl p-3 text-left transition hover:bg-green-50">
                    <span className="text-xl">🔍</span>

                    <div>
                      <p className="text-sm font-semibold">
                        Monitor your plants
                      </p>

                      <p className="text-xs text-slate-500">
                        Regular inspection can help identify issues early.
                      </p>
                    </div>
                  </button>

                  <button className="flex w-full gap-3 rounded-xl p-3 text-left transition hover:bg-green-50">
                    <span className="text-xl">💡</span>

                    <div>
                      <p className="text-sm font-semibold">
                        Plant care reminder
                      </p>

                      <p className="text-xs text-slate-500">
                        Maintain good spacing and airflow.
                      </p>
                    </div>
                  </button>

                </div>

                <div className="border-t bg-slate-50 p-3 text-center">
                  <button
                    onClick={() =>
                      setNotificationsOpen(false)
                    }
                    className="text-xs font-semibold text-green-700"
                  >
                    Close
                  </button>
                </div>
              </div>
            )}
          </div>

        </div>
      </nav>

      {/* HERO */}
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
              AI-powered plant health detection
            </div>

            <h1 className="max-w-3xl text-5xl font-black leading-tight tracking-tight text-slate-900 md:text-6xl lg:text-7xl">
              Protect your plants with{" "}
              <span className="text-green-700">
                intelligent AI.
              </span>
            </h1>

            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">
              Upload a plant leaf image and Plant Guard AI uses
              deep learning to identify possible diseases and
              provide useful plant-care guidance.
            </p>

            <div className="mt-9 flex flex-wrap gap-4">

              <button
                onClick={() => scrollToSection("analyzer")}
                className="rounded-2xl bg-green-700 px-7 py-4 font-bold text-white shadow-lg shadow-green-700/20 transition hover:-translate-y-0.5 hover:bg-green-800"
              >
                🔍 Detect Disease
              </button>

              <button
                onClick={() => scrollToSection("how-it-works")}
                className="rounded-2xl border border-slate-300 bg-white px-7 py-4 font-bold text-slate-700 shadow-sm transition hover:bg-slate-50"
              >
                How It Works →
              </button>

            </div>

            <div className="mt-10 flex flex-wrap gap-6 text-sm text-slate-500">
              <div className="flex items-center gap-2">
                <span className="text-lg">🤖</span>
                Deep Learning
              </div>

              <div className="flex items-center gap-2">
                <span className="text-lg">📷</span>
                Image Analysis
              </div>

              <div className="flex items-center gap-2">
                <span className="text-lg">🌱</span>
                Plant Care
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
                      Plant Health Scanner
                    </p>

                    <h2 className="mt-2 text-3xl font-black">
                      AI Analysis
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
                        Upload leaf image
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
                      AI Model
                    </p>
                  </div>

                  <div className="rounded-2xl bg-white/10 p-4 text-center">
                    <div className="text-xl">📊</div>
                    <p className="mt-1 text-xs text-green-100">
                      Confidence
                    </p>
                  </div>

                  <div className="rounded-2xl bg-white/10 p-4 text-center">
                    <div className="text-xl">🩺</div>
                    <p className="mt-1 text-xs text-green-100">
                      Guidance
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
                    Detection system
                  </p>

                  <p className="text-sm font-bold text-green-700">
                    Ready to analyze
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
              Powered Detection
            </p>
          </div>

          <div>
            <p className="text-3xl font-black text-green-700">
              38
            </p>
            <p className="mt-1 text-sm text-slate-500">
              Model Classes
            </p>
          </div>

          <div>
            <p className="text-3xl font-black text-green-700">
              24/7
            </p>
            <p className="mt-1 text-sm text-slate-500">
              Digital Assistance
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
              Disease Detection
            </span>

            <h2 className="mt-3 text-4xl font-black text-slate-900">
              Analyze your plant
            </h2>

            <p className="mt-4 text-lg text-slate-600">
              Upload a clear image of a plant leaf and let the
              AI model analyze it.
            </p>
          </div>

          <div className="mt-12 rounded-[2rem] border border-slate-200 bg-white p-5 shadow-xl md:p-8">

            {/* UPLOAD CARD */}
            <div className="rounded-[1.5rem] border-2 border-dashed border-green-200 bg-gradient-to-br from-green-50 to-emerald-50 p-8 text-center md:p-12">

              <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-3xl bg-white text-4xl shadow-md">
                📷
              </div>

              <h3 className="mt-6 text-2xl font-black text-slate-900">
                Upload a plant image
              </h3>

              <p className="mx-auto mt-3 max-w-lg text-slate-500">
                Choose a clear photo showing the plant leaf.
                Better images can help the model produce a more
                useful prediction.
              </p>

              <label className="mt-7 inline-flex cursor-pointer items-center gap-2 rounded-2xl bg-green-700 px-7 py-4 font-bold text-white shadow-lg transition hover:-translate-y-0.5 hover:bg-green-800">
                📁 Choose Image

                <input
                  type="file"
                  accept="image/*"
                  onChange={handleFileChange}
                  className="hidden"
                />
              </label>

              <p className="mt-4 text-xs text-slate-400">
                Supported image formats: JPG, JPEG, PNG, WEBP
              </p>

              {selectedFile && (
                <div className="mx-auto mt-6 max-w-md rounded-2xl bg-white p-4 text-left shadow-sm">
                  <p className="text-xs font-medium text-slate-400">
                    Selected image
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
                      Your plant image
                    </h3>
                  </div>

                  <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-bold text-green-700">
                    Ready
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
                      ? "🔄 AI is analyzing..."
                      : "🔍 Analyze Plant"}
                  </button>

                  <button
                    onClick={resetAnalysis}
                    disabled={loading}
                    className="rounded-2xl border border-slate-300 bg-white px-7 py-4 font-bold text-slate-600 transition hover:bg-slate-50 disabled:opacity-50"
                  >
                    Choose Another
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
                AI Result
              </span>

              <h2 className="mt-3 text-4xl font-black text-slate-900">
                Plant analysis complete
              </h2>

              <p className="mt-3 text-slate-600">
                Here is the prediction generated by Plant Guard AI.
              </p>
            </div>

            {/* MAIN RESULT */}
            <div className="mt-12 overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-xl">

              <div className="bg-gradient-to-br from-green-700 to-emerald-600 p-8 text-center text-white md:p-12">

                <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-3xl bg-white/15 text-4xl backdrop-blur">
                  🌿
                </div>

                <p className="mt-5 text-sm font-bold uppercase tracking-widest text-green-100">
                  Detected Condition
                </p>

                <h2 className="mt-2 text-4xl font-black md:text-5xl">
                  {diseaseData.disease}
                </h2>

                <p className="mt-4 text-lg text-green-50">
                  Plant identified as{" "}
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
                        MODEL CONFIDENCE
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
                      ? "High confidence result."
                      : confidence >= 40
                      ? "Moderate confidence result. Consider verifying the symptoms."
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
                        What does this result mean?
                      </h3>

                      <p className="mt-2 leading-7 text-green-900/70">
                        {getExplanation(
                          diseaseData.disease
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
                    About This Condition
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
                    Common Symptoms
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

                        <span>{symptom}</span>
                      </li>
                    )
                  )}
                </ul>
              </div>

              <div className="rounded-3xl border border-slate-200 bg-white p-7 shadow-md">
                <div className="flex items-center gap-3">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-orange-100 text-xl">
                    🩺
                  </div>

                  <h3 className="text-xl font-black">
                    Recommended Action
                  </h3>
                </div>

                <ul className="mt-5 space-y-3">
                  {diseaseInfo.treatment.map(
                    (item, index) => (
                      <li
                        key={index}
                        className="flex gap-3 text-slate-600"
                      >
                        <span className="mt-1 text-orange-500">
                          •
                        </span>

                        <span>{item}</span>
                      </li>
                    )
                  )}
                </ul>
              </div>

              <div className="rounded-3xl border border-slate-200 bg-white p-7 shadow-md">
                <div className="flex items-center gap-3">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-100 text-xl">
                    🛡️
                  </div>

                  <h3 className="text-xl font-black">
                    Prevention Tips
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

                        <span>{item}</span>
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
                  Treatment Calculator
                </h3>

                <p className="mx-auto mt-2 max-w-xl text-slate-600">
                  Estimate the total quantity based on the number
                  of affected plants and the treatment rate.
                </p>
              </div>

              <div className="mx-auto mt-8 grid max-w-3xl gap-5 md:grid-cols-2">

                <div>
                  <label className="mb-2 block text-sm font-bold text-slate-700">
                    Number of affected plants
                  </label>

                  <input
                    type="number"
                    min="0"
                    value={affectedPlants}
                    onChange={(event) =>
                      setAffectedPlants(
                        event.target.value
                      )
                    }
                    placeholder="Example: 10"
                    className="w-full rounded-2xl border border-slate-300 bg-white px-5 py-4 outline-none transition focus:border-green-500 focus:ring-4 focus:ring-green-100"
                  />
                </div>

                <div>
                  <label className="mb-2 block text-sm font-bold text-slate-700">
                    Treatment amount per plant
                  </label>

                  <input
                    type="number"
                    min="0"
                    value={ratePerPlant}
                    onChange={(event) =>
                      setRatePerPlant(
                        event.target.value
                      )
                    }
                    placeholder="Example: 5"
                    className="w-full rounded-2xl border border-slate-300 bg-white px-5 py-4 outline-none transition focus:border-green-500 focus:ring-4 focus:ring-green-100"
                  />
                </div>

              </div>

              {treatmentAmount !== null && (
                <div className="mx-auto mt-6 max-w-3xl rounded-2xl bg-white p-6 text-center shadow-md">

                  <p className="text-sm font-semibold text-slate-500">
                    Estimated total treatment quantity
                  </p>

                  <p className="mt-2 text-4xl font-black text-green-700">
                    {treatmentAmount}
                  </p>

                  <p className="mt-1 text-xs text-slate-400">
                    units
                  </p>

                </div>
              )}

              <p className="mx-auto mt-6 max-w-2xl text-center text-xs leading-5 text-slate-500">
                This calculator is for estimation only. Always
                follow the product label and local agricultural
                recommendations for actual dosage.
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
                    Important Disclaimer
                  </h3>

                  <p className="mt-2 text-sm leading-6 text-yellow-800">
                    Plant Guard AI provides an AI-based prediction
                    and should not be considered a confirmed
                    agricultural diagnosis. For serious crop
                    problems, consult a qualified agricultural
                    expert.
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
              Simple Process
            </span>

            <h2 className="mt-3 text-4xl font-black text-slate-900">
              How Plant Guard AI works
            </h2>

            <p className="mt-4 text-lg text-slate-600">
              From image upload to useful plant health guidance
              in three simple steps.
            </p>
          </div>

          <div className="mt-14 grid gap-7 md:grid-cols-3">

            <div className="group rounded-3xl border border-slate-200 bg-slate-50 p-8 transition hover:-translate-y-1 hover:shadow-xl">

              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-green-100 text-3xl transition group-hover:scale-105">
                📷
              </div>

              <p className="mt-7 text-sm font-bold text-green-700">
                STEP 01
              </p>

              <h3 className="mt-2 text-2xl font-black">
                Upload
              </h3>

              <p className="mt-4 leading-7 text-slate-600">
                Upload a clear image of a plant leaf using the
                Plant Guard AI disease detector.
              </p>

            </div>

            <div className="group rounded-3xl border border-slate-200 bg-slate-50 p-8 transition hover:-translate-y-1 hover:shadow-xl">

              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-100 text-3xl transition group-hover:scale-105">
                🤖
              </div>

              <p className="mt-7 text-sm font-bold text-blue-700">
                STEP 02
              </p>

              <h3 className="mt-2 text-2xl font-black">
                AI Analysis
              </h3>

              <p className="mt-4 leading-7 text-slate-600">
                The image is processed by the FastAPI backend and
                analyzed using a trained deep learning model.
              </p>

            </div>

            <div className="group rounded-3xl border border-slate-200 bg-slate-50 p-8 transition hover:-translate-y-1 hover:shadow-xl">

              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-orange-100 text-3xl transition group-hover:scale-105">
                🌱
              </div>

              <p className="mt-7 text-sm font-bold text-orange-700">
                STEP 03
              </p>

              <h3 className="mt-2 text-2xl font-black">
                Get Guidance
              </h3>

              <p className="mt-4 leading-7 text-slate-600">
                View the predicted disease, confidence score,
                symptoms, recommended action and prevention tips.
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
              Key Features
            </span>

            <h2 className="mt-3 text-4xl font-black">
              Built to assist plant care
            </h2>
          </div>

          <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">

            <div className="rounded-3xl bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-lg">
              <div className="text-3xl">🤖</div>
              <h3 className="mt-5 font-black">
                AI Detection
              </h3>
              <p className="mt-2 text-sm leading-6 text-slate-500">
                Deep learning based plant disease prediction.
              </p>
            </div>

            <div className="rounded-3xl bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-lg">
              <div className="text-3xl">📊</div>
              <h3 className="mt-5 font-black">
                Confidence Score
              </h3>
              <p className="mt-2 text-sm leading-6 text-slate-500">
                Understand how confident the model is in its prediction.
              </p>
            </div>

            <div className="rounded-3xl bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-lg">
              <div className="text-3xl">🩺</div>
              <h3 className="mt-5 font-black">
                Plant Guidance
              </h3>
              <p className="mt-2 text-sm leading-6 text-slate-500">
                View symptoms, treatment actions and prevention tips.
              </p>
            </div>

            <div className="rounded-3xl bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-lg">
              <div className="text-3xl">🤖</div>
              <h3 className="mt-5 font-black">
                AI Assistant
              </h3>
              <p className="mt-2 text-sm leading-6 text-slate-500">
                Ask basic questions about plant health using the assistant.
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
              About The Project
            </span>

            <h2 className="mt-3 text-4xl font-black text-slate-900">
              Technology for healthier plants
            </h2>

            <p className="mt-6 text-lg leading-8 text-slate-600">
              Plant Guard AI is a student mini-project that
              demonstrates how artificial intelligence and deep
              learning can assist with plant disease identification.
            </p>

            <p className="mt-5 leading-7 text-slate-600">
              The system combines a modern Next.js frontend with
              a FastAPI backend and a trained EfficientNet-based
              image classification model.
            </p>

            <button
              onClick={() => scrollToSection("analyzer")}
              className="mt-7 rounded-2xl bg-green-700 px-6 py-3 font-bold text-white transition hover:bg-green-800"
            >
              Try Disease Detection →
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
              An AI-assisted plant health platform designed to
              make disease identification easier and more accessible.
            </p>

            <div className="mt-8 space-y-4">

              <div className="flex items-center gap-3">
                <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/15">
                  ✓
                </span>
                <span>Next.js frontend</span>
              </div>

              <div className="flex items-center gap-3">
                <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/15">
                  ✓
                </span>
                <span>FastAPI backend</span>
              </div>

              <div className="flex items-center gap-3">
                <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/15">
                  ✓
                </span>
                <span>TensorFlow deep learning</span>
              </div>

              <div className="flex items-center gap-3">
                <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/15">
                  ✓
                </span>
                <span>EfficientNet image classification</span>
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
            Ready to check your plant?
          </h2>

          <p className="mx-auto mt-4 max-w-2xl text-green-50">
            Upload a plant leaf image and explore what Plant Guard
            AI can detect.
          </p>

          <button
            onClick={() => scrollToSection("analyzer")}
            className="mt-7 rounded-2xl bg-white px-7 py-4 font-black text-green-800 shadow-lg transition hover:-translate-y-0.5"
          >
            🔍 Start Analysis
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
                  AI Plant Health Assistant
                </p>
              </div>
            </div>

            <p className="mt-5 max-w-sm text-sm leading-6 text-slate-400">
              AI-powered plant disease detection and plant-care
              assistance.
            </p>
          </div>

          <div>
            <h3 className="font-bold">
              Quick Navigation
            </h3>

            <div className="mt-4 space-y-3 text-sm text-slate-400">

              <button
                onClick={() => scrollToSection("home")}
                className="block transition hover:text-white"
              >
                Home
              </button>

              <button
                onClick={() => scrollToSection("analyzer")}
                className="block transition hover:text-white"
              >
                Disease Detection
              </button>

              <button
                onClick={() =>
                  scrollToSection("how-it-works")
                }
                className="block transition hover:text-white"
              >
                How It Works
              </button>

              <button
                onClick={() => scrollToSection("about")}
                className="block transition hover:text-white"
              >
                About
              </button>

            </div>
          </div>

          <div>
            <h3 className="font-bold">
              Project
            </h3>

            <p className="mt-4 text-sm leading-6 text-slate-400">
              B.Tech Artificial Intelligence & Data Science
            </p>

            <p className="mt-3 text-sm text-slate-500">
              Mini Project
            </p>
          </div>

        </div>

        <div className="mx-auto mt-10 max-w-6xl border-t border-slate-800 pt-6 text-center text-xs text-slate-500">
          © 2026 Plant Guard AI. Built as an academic mini-project.
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
                    Plant Guard AI
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
                onChange={(event) =>
                  setChatMessage(event.target.value)
                }
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    sendChatMessage();
                  }
                }}
                placeholder="Ask about plant health..."
                className="min-w-0 flex-1 rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-sm outline-none focus:border-green-500 focus:ring-2 focus:ring-green-100"
              />

              <button
                onClick={sendChatMessage}
                className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-green-700 text-lg text-white transition hover:bg-green-800"
              >
                ➤
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