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
      disease: prediction.replaceAll("_", " "),
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

  if (lower.includes("healthy")) {
    return {
      about:
        "The AI model did not detect a known disease in the uploaded plant image.",
      symptoms: [
        "No major disease symptoms were detected by the model.",
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
    return "Late blight can spread quickly under cool and humid conditions.";
  }

  if (lower.includes("early blight")) {
    return "Early blight can cause dark spots on leaves and may reduce plant growth.";
  }

  if (lower.includes("powdery mildew")) {
    return "Powdery mildew commonly appears as a white powder-like coating on leaves.";
  }

  if (lower.includes("bacterial spot")) {
    return "Bacterial spot can cause small dark or water-soaked spots on leaves.";
  }

  if (lower.includes("leaf spot")) {
    return "Leaf spot diseases can create visible spots or damaged areas on plant leaves.";
  }

  return "The AI model detected a possible plant disease. Further observation may be useful.";
}

export default function Home() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [affectedPlants, setAffectedPlants] = useState("");
  const [ratePerPlant, setRatePerPlant] = useState("");

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

    if (!plants || !rate) {
      return null;
    }

    return plants * rate;
  };

  const treatmentAmount = calculateTreatment();

  const diseaseData = result
    ? formatDiseaseName(result.prediction)
    : null;

  const diseaseInfo = diseaseData
    ? getDiseaseInfo(diseaseData.disease)
    : null;

  const confidence = result
    ? Math.max(0, Math.min(Number(result.confidence), 100))
    : 0;

  return (
    <main className="min-h-screen bg-gradient-to-b from-green-50 to-white text-gray-800">

      {/* NAVBAR */}
      <nav className="sticky top-0 z-50 border-b bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <button
            onClick={() => scrollToSection("home")}
            className="text-2xl font-bold text-green-700"
          >
            🌱 Plant Guard AI
          </button>

          <div className="hidden gap-8 md:flex">
            <button
              onClick={() => scrollToSection("home")}
              className="font-medium hover:text-green-700"
            >
              Home
            </button>

            <button
              onClick={() => scrollToSection("how-it-works")}
              className="font-medium hover:text-green-700"
            >
              How It Works
            </button>

            <button
              onClick={() => scrollToSection("about")}
              className="font-medium hover:text-green-700"
            >
              About
            </button>
          </div>
        </div>
      </nav>

      {/* HERO */}
      <section
        id="home"
        className="px-6 py-20 text-center"
      >
        <div className="mx-auto max-w-4xl">
          <div className="mb-5 text-6xl">
            🌱
          </div>

          <h1 className="text-4xl font-bold tracking-tight text-green-800 md:text-6xl">
            Plant Guard AI
          </h1>

          <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-gray-600">
            AI-powered plant disease detection system that helps
            identify possible plant diseases from leaf images.
          </p>

          <button
            onClick={() => scrollToSection("analyzer")}
            className="mt-8 rounded-xl bg-green-600 px-8 py-4 font-semibold text-white shadow-lg transition hover:bg-green-700"
          >
            Analyze Your Plant 🌿
          </button>
        </div>
      </section>

      {/* ANALYZER */}
      <section
        id="analyzer"
        className="px-6 py-16"
      >
        <div className="mx-auto max-w-5xl rounded-3xl bg-white p-6 shadow-xl md:p-10">

          <div className="text-center">
            <h2 className="text-3xl font-bold text-green-800">
              Plant Disease Detection
            </h2>

            <p className="mt-3 text-gray-600">
              Upload a clear image of a plant leaf to analyze it.
            </p>
          </div>

          {/* UPLOAD */}
          <div className="mt-10 rounded-2xl border-2 border-dashed border-green-300 bg-green-50 p-8 text-center">

            <div className="text-5xl">
              📷
            </div>

            <h3 className="mt-4 text-xl font-semibold">
              Upload Plant Image
            </h3>

            <p className="mt-2 text-sm text-gray-500">
              JPG, JPEG, PNG or WEBP
            </p>

            <label className="mt-6 inline-block cursor-pointer rounded-xl bg-green-600 px-6 py-3 font-semibold text-white transition hover:bg-green-700">
              Choose Image

              <input
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className="hidden"
              />
            </label>

            {selectedFile && (
              <p className="mt-4 text-sm font-medium text-green-700">
                Selected: {selectedFile.name}
              </p>
            )}
          </div>

          {/* IMAGE PREVIEW */}
          {preview && (
            <div className="mt-8 text-center">
              <h3 className="mb-4 text-xl font-semibold">
                Image Preview
              </h3>

              <div className="mx-auto max-w-md overflow-hidden rounded-2xl border shadow">
                <img
                  src={preview}
                  alt="Selected plant"
                  className="max-h-96 w-full object-contain"
                />
              </div>

              <button
                onClick={analyzePlant}
                disabled={loading}
                className="mt-6 rounded-xl bg-green-700 px-8 py-4 font-semibold text-white transition hover:bg-green-800 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loading
                  ? "🔄 Analyzing..."
                  : "🔍 Analyze Plant"}
              </button>
            </div>
          )}

          {/* ERROR */}
          {error && (
            <div className="mt-8 rounded-xl border border-red-200 bg-red-50 p-5 text-center text-red-700">
              <p className="font-semibold">
                ⚠️ {error}
              </p>

              <p className="mt-2 text-sm">
                Start the FastAPI backend and try again.
              </p>
            </div>
          )}

          {/* RESULT */}
          {result && diseaseData && diseaseInfo && (
            <div className="mt-10">

              <div className="rounded-2xl border border-green-200 bg-green-50 p-6">

                <div className="text-center">
                  <div className="text-5xl">
                    🌿
                  </div>

                  <p className="mt-3 text-sm font-medium uppercase tracking-wide text-green-600">
                    AI Detection Result
                  </p>

                  <h2 className="mt-2 text-3xl font-bold text-green-900">
                    {diseaseData.disease}
                  </h2>

                  <p className="mt-2 text-lg text-gray-700">
                    Plant:{" "}
                    <span className="font-semibold">
                      {diseaseData.plant}
                    </span>
                  </p>
                </div>

                {/* CONFIDENCE */}
                <div className="mx-auto mt-8 max-w-2xl">

                  <div className="mb-2 flex justify-between">
                    <span className="font-semibold">
                      Confidence
                    </span>

                    <span className="font-bold text-green-700">
                      {confidence.toFixed(2)}%
                    </span>
                  </div>

                  <div className="h-4 overflow-hidden rounded-full bg-gray-200">
                    <div
                      className="h-full rounded-full bg-green-600 transition-all"
                      style={{
                        width: Math.min(confidence, 100) + "%",
                      }}
                    />
                  </div>

                  <p className="mt-3 text-center text-sm text-gray-600">
                    {confidence >= 70
                      ? "High confidence result"
                      : confidence >= 40
                      ? "Moderate confidence result"
                      : "Low confidence result - verify the plant condition manually"}
                  </p>
                </div>

                {/* EXPLANATION */}
                <div className="mt-8 rounded-xl bg-white p-5 shadow-sm">
                  <h3 className="text-xl font-bold text-green-800">
                    💡 What does this result mean?
                  </h3>

                  <p className="mt-3 leading-7 text-gray-600">
                    {getExplanation(diseaseData.disease)}
                  </p>
                </div>

              </div>

              {/* CONDITION INFO */}
              <div className="mt-8 grid gap-6 md:grid-cols-2">

                <div className="rounded-2xl bg-white p-6 shadow-md">
                  <h3 className="text-xl font-bold text-green-800">
                    📖 About This Condition
                  </h3>

                  <p className="mt-3 leading-7 text-gray-600">
                    {diseaseInfo.about}
                  </p>
                </div>

                <div className="rounded-2xl bg-white p-6 shadow-md">
                  <h3 className="text-xl font-bold text-green-800">
                    🔎 Common Symptoms
                  </h3>

                  <ul className="mt-3 space-y-2 text-gray-600">
                    {diseaseInfo.symptoms.map(
                      (symptom, index) => (
                        <li key={index}>
                          • {symptom}
                        </li>
                      )
                    )}
                  </ul>
                </div>

              </div>

              {/* TREATMENT */}
              <div className="mt-6 grid gap-6 md:grid-cols-2">

                <div className="rounded-2xl bg-white p-6 shadow-md">
                  <h3 className="text-xl font-bold text-green-800">
                    🩺 Recommended Action
                  </h3>

                  <ul className="mt-4 space-y-3 text-gray-600">
                    {diseaseInfo.treatment.map(
                      (item, index) => (
                        <li key={index}>
                          • {item}
                        </li>
                      )
                    )}
                  </ul>
                </div>

                <div className="rounded-2xl bg-white p-6 shadow-md">
                  <h3 className="text-xl font-bold text-green-800">
                    🛡️ Prevention Tips
                  </h3>

                  <ul className="mt-4 space-y-3 text-gray-600">
                    {diseaseInfo.prevention.map(
                      (item, index) => (
                        <li key={index}>
                          • {item}
                        </li>
                      )
                    )}
                  </ul>
                </div>

              </div>

              {/* CALCULATOR */}
              <div className="mt-8 rounded-2xl bg-green-50 p-6 shadow-md">

                <div className="text-center">
                  <h3 className="text-2xl font-bold text-green-800">
                    🧮 Treatment Calculator
                  </h3>

                  <p className="mt-2 text-gray-600">
                    Enter the number of affected plants and the
                    recommended treatment amount per plant.
                  </p>
                </div>

                <div className="mx-auto mt-6 grid max-w-2xl gap-4 md:grid-cols-2">

                  <div>
                    <label className="mb-2 block font-semibold">
                      Affected Plants
                    </label>

                    <input
                      type="number"
                      min="0"
                      value={affectedPlants}
                      onChange={(e) =>
                        setAffectedPlants(e.target.value)
                      }
                      placeholder="Example: 10"
                      className="w-full rounded-xl border border-gray-300 bg-white px-4 py-3 outline-none focus:border-green-500"
                    />
                  </div>

                  <div>
                    <label className="mb-2 block font-semibold">
                      Rate Per Plant
                    </label>

                    <input
                      type="number"
                      min="0"
                      value={ratePerPlant}
                      onChange={(e) =>
                        setRatePerPlant(e.target.value)
                      }
                      placeholder="Example: 5"
                      className="w-full rounded-xl border border-gray-300 bg-white px-4 py-3 outline-none focus:border-green-500"
                    />
                  </div>

                </div>

                {treatmentAmount !== null && (
                  <div className="mx-auto mt-6 max-w-2xl rounded-xl bg-white p-5 text-center shadow">
                    <p className="text-sm text-gray-500">
                      Estimated total treatment quantity
                    </p>

                    <p className="mt-1 text-3xl font-bold text-green-700">
                      {treatmentAmount}
                    </p>

                    <p className="mt-1 text-sm text-gray-500">
                      units
                    </p>
                  </div>
                )}

                <p className="mx-auto mt-5 max-w-2xl text-center text-xs text-gray-500">
                  Always follow the product label and local
                  agricultural recommendations for actual dosage.
                </p>

              </div>

              {/* DISCLAIMER */}
              <div className="mt-8 rounded-xl border border-yellow-200 bg-yellow-50 p-5">
                <h3 className="font-bold text-yellow-800">
                  ⚠️ Disclaimer
                </h3>

                <p className="mt-2 text-sm leading-6 text-yellow-800">
                  Plant Guard AI provides an AI-based prediction and
                  should not be considered a confirmed agricultural
                  diagnosis. For serious crop problems, consult a
                  qualified agricultural expert.
                </p>
              </div>

              {/* RESET */}
              <div className="mt-8 text-center">
                <button
                  onClick={resetAnalysis}
                  className="rounded-xl border border-green-600 px-7 py-3 font-semibold text-green-700 transition hover:bg-green-50"
                >
                  🔄 Analyze Another Plant
                </button>
              </div>

            </div>
          )}

        </div>
      </section>

      {/* HOW IT WORKS */}
      <section
        id="how-it-works"
        className="bg-green-50 px-6 py-20"
      >
        <div className="mx-auto max-w-6xl">

          <div className="text-center">
            <h2 className="text-3xl font-bold text-green-800">
              How It Works
            </h2>

            <p className="mt-3 text-gray-600">
              Plant Guard AI follows three simple steps.
            </p>
          </div>

          <div className="mt-12 grid gap-8 md:grid-cols-3">

            <div className="rounded-2xl bg-white p-8 text-center shadow-md">
              <div className="text-5xl">
                📷
              </div>

              <h3 className="mt-5 text-xl font-bold">
                1. Upload
              </h3>

              <p className="mt-3 text-gray-600">
                Upload an image of the plant leaf you want to
                analyze.
              </p>
            </div>

            <div className="rounded-2xl bg-white p-8 text-center shadow-md">
              <div className="text-5xl">
                🤖
              </div>

              <h3 className="mt-5 text-xl font-bold">
                2. AI Analysis
              </h3>

              <p className="mt-3 text-gray-600">
                The trained deep learning model analyzes the image
                and predicts a possible condition.
              </p>
            </div>

            <div className="rounded-2xl bg-white p-8 text-center shadow-md">
              <div className="text-5xl">
                🌱
              </div>

              <h3 className="mt-5 text-xl font-bold">
                3. Get Results
              </h3>

              <p className="mt-3 text-gray-600">
                View the predicted disease, confidence level,
                symptoms, treatment guidance and prevention tips.
              </p>
            </div>

          </div>

        </div>
      </section>

      {/* ABOUT */}
      <section
        id="about"
        className="px-6 py-20"
      >
        <div className="mx-auto max-w-4xl text-center">

          <h2 className="text-3xl font-bold text-green-800">
            About Plant Guard AI
          </h2>

          <p className="mt-6 leading-8 text-gray-600">
            Plant Guard AI is a student mini-project designed to
            demonstrate how artificial intelligence and deep
            learning can be used to assist with plant disease
            identification.
          </p>

          <p className="mt-4 leading-8 text-gray-600">
            The system accepts a plant leaf image, sends it to the
            FastAPI backend, and uses a trained deep learning model
            to generate a disease prediction and confidence score.
          </p>

        </div>
      </section>

      {/* FOOTER */}
      <footer className="bg-green-900 px-6 py-10 text-center text-white">

        <div className="text-2xl font-bold">
          🌱 Plant Guard AI
        </div>

        <p className="mt-3 text-green-100">
          AI-powered plant disease detection
        </p>

        <p className="mt-6 text-sm text-green-200">
          Mini Project • B.Tech Artificial Intelligence & Data Science
        </p>

      </footer>

    </main>
  );
}