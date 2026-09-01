"use client";

import { useState } from "react";

interface PredictionResult {
  message: string;
  filename: string;
  prediction: string;
  confidence: number;
  status: string;
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
      disease: prediction,
    };
  }

  return {
    plant: parts[0]
      .replaceAll("_", " ")
      .replaceAll(",", "")
      .trim(),

    disease: parts[1]
      .replaceAll("_", " ")
      .trim(),
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
        "Maintain proper spacing.",
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
        "White powder-like patches.",
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
    const scrollToSection = (sectionId: string) => {
    document.getElementById(sectionId)?.scrollIntoView({
      behavior: "smooth",
    });
  };
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);

  const [result, setResult] =
    useState<PredictionResult | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [affectedPlants, setAffectedPlants] = useState("");
  const [ratePerPlant, setRatePerPlant] = useState("");

  const handleFileChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];

    if (!file) return;

    setSelectedFile(file);
    setPreview(URL.createObjectURL(file));

    setResult(null);
    setError("");
  };

  const analyzePlant = async () => {
    if (!selectedFile) return;

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

  return (
    <main className="min-h-screen bg-gradient-to-b from-green-50 to-white">

      {/* NAVBAR */}

      <nav className="sticky top-0 z-50 border-b border-green-100 bg-white/95 backdrop-blur">

  <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">

    {/* LOGO */}

    <button
      onClick={() => scrollToSection("home")}
      className="flex items-center gap-3"
    >

      <div className="flex h-11 w-11 items-center justify-center rounded-full bg-green-100 text-2xl">
        🌱
      </div>

      <div className="text-left">

        <h1 className="text-lg font-bold text-green-800">
          Plant Guard AI
        </h1>

        <p className="text-xs text-green-600">
          Intelligent Plant Protection
        </p>

      </div>

    </button>


    {/* NAVIGATION */}

    <div className="hidden items-center gap-8 md:flex">

      <button
        onClick={() => scrollToSection("home")}
        className="font-medium text-gray-600 transition hover:text-green-700"
      >
        Home
      </button>

      <button
        onClick={() => scrollToSection("how-it-works")}
        className="font-medium text-gray-600 transition hover:text-green-700"
      >
        How It Works
      </button>

      <button
        onClick={() => scrollToSection("about")}
        className="font-medium text-gray-600 transition hover:text-green-700"
      >
        About
      </button>

    </div>


    {/* STATUS */}

    <div className="hidden rounded-full bg-green-50 px-4 py-2 text-sm font-medium text-green-700 sm:block">
      AI Disease Detection
    </div>

  </div>

</nav>


      {/* HERO */}

<section
  id="home"
  className="mx-auto max-w-6xl px-6 pb-12 pt-16 text-center"
>
        <div className="mx-auto max-w-3xl">

          <div className="mb-5 text-6xl">
            🌿
          </div>

          <h2 className="text-4xl font-bold tracking-tight text-green-900 sm:text-5xl">
            Protect Your Plants
            <span className="block text-green-600">
              With AI
            </span>
          </h2>

          <p className="mx-auto mt-5 max-w-2xl text-lg leading-8 text-gray-600">
            Upload a plant leaf image and let Plant Guard AI
            identify possible diseases and provide useful
            information for better plant care.
          </p>

        </div>

      </section>


      {/* MAIN CARD */}

      <section className="mx-auto max-w-4xl px-6">

        <div className="rounded-3xl border border-green-100 bg-white p-6 shadow-xl sm:p-10">

          <h3 className="text-center text-2xl font-bold text-gray-800">
            Upload a Plant Image
          </h3>

          <p className="mt-2 text-center text-gray-500">
            Choose a clear image of the affected leaf.
          </p>


          {/* UPLOAD */}

          <label
            htmlFor="plant-image"
            className="mx-auto mt-8 flex min-h-72 max-w-2xl cursor-pointer flex-col items-center justify-center rounded-3xl border-2 border-dashed border-green-300 bg-green-50 p-8 transition hover:border-green-500 hover:bg-green-100"
          >

            {preview ? (

              <img
                src={preview}
                alt="Selected plant"
                className="max-h-64 rounded-2xl object-contain shadow-md"
              />

            ) : (

              <>
                <div className="mb-4 text-5xl">
                  📷
                </div>

                <p className="text-lg font-semibold text-green-800">
                  Choose Plant Image
                </p>

                <p className="mt-2 text-sm text-gray-500">
                  JPG, JPEG, PNG or WEBP
                </p>
              </>

            )}

            <input
              id="plant-image"
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              className="hidden"
            />

          </label>


          {/* FILE */}

          {selectedFile && (

            <p className="mt-4 text-center text-sm text-gray-600">
              Selected file:{" "}
              <strong>{selectedFile.name}</strong>
            </p>

          )}


          {/* BUTTON */}

          <div className="mt-7 text-center">

            <button
              onClick={analyzePlant}
              disabled={!selectedFile || loading}
              className="rounded-full bg-green-700 px-10 py-3.5 font-semibold text-white shadow-md transition hover:bg-green-800 disabled:cursor-not-allowed disabled:bg-gray-300"
            >

              {loading
                ? "🔄 Analyzing..."
                : "🔍 Analyze Plant"}

            </button>

          </div>


          {/* ERROR */}

          {error && (

            <div className="mt-6 rounded-2xl bg-red-50 p-4 text-center text-red-700">
              {error}
            </div>

          )}


          {/* RESULT */}

          {result && (() => {

            const { plant, disease } =
              formatDiseaseName(result.prediction);

            const diseaseInfo =
              getDiseaseInfo(disease);

            const explanation =
              getExplanation(disease);

            return (

              <div className="mt-10 space-y-6">

                {/* RESULT HEADER */}

<div className="rounded-3xl border border-green-200 bg-green-50 p-7 shadow-sm">

  <div className="flex items-center gap-3">

    <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-green-700 text-2xl">
      🌱
    </div>

    <div>
      <p className="text-sm font-semibold uppercase tracking-wider text-green-700">
        AI Detection Result
      </p>

      <p className="text-sm text-gray-500">
        Analysis completed successfully
      </p>
    </div>

  </div>

  <div className="mt-6">

    <p className="text-sm font-medium text-gray-500">
      Possible condition detected
    </p>

    <h3 className="mt-1 text-3xl font-bold text-green-900">
      {disease}
    </h3>

    <p className="mt-2 text-lg text-gray-600">
      Plant:{" "}
      <strong className="text-gray-800">
        {plant}
      </strong>
    </p>

  </div>

</div>

                  {/* CONFIDENCE */}

                  <div className="mt-6">

                    <div className="mb-2 flex justify-between text-sm">

                      <span className="font-medium text-gray-600">
                        Confidence
                      </span>

                      <span className="font-bold text-green-700">
                        {result.confidence}%
                      </span>

                    </div>

                    <div className="h-3 overflow-hidden rounded-full bg-green-200">

                      <div
                        className="h-full rounded-full bg-green-600 transition-all"
                        style={{
                          width: `${Math.min(
                            result.confidence,
                            100
                          )}%`,
                        }}
                      />

                    </div>

                  </div>


                {/* STATUS */}

<div className="mt-5 rounded-2xl bg-white p-5 shadow-sm">

  <div className="flex items-center justify-between">

    <p className="text-sm font-medium text-gray-500">
      Confidence Status
    </p>

    <span
      className={`rounded-full px-3 py-1 text-xs font-bold ${
        result.confidence >= 80
          ? "bg-green-100 text-green-700"
          : result.confidence >= 50
          ? "bg-yellow-100 text-yellow-700"
          : "bg-red-100 text-red-700"
      }`}
    >
      {result.status}
    </span>

  </div>

  <p className="mt-3 text-2xl font-bold text-gray-800">
    {result.confidence.toFixed(2)}%
  </p>

  <p className="mt-1 text-sm text-gray-500">
    Model confidence for this prediction
  </p>

</div>


                  
{/* EXPLANATION */}

<div className="mt-4 rounded-2xl bg-white p-5">

  <p className="text-sm font-medium text-gray-500">
    💡 What does this mean?
  </p>

  <p className="mt-2 leading-7 text-gray-700">
    {explanation}
  </p>

</div>
{/* ABOUT */}

<div className="rounded-3xl bg-white p-7 shadow">

  <h3 className="text-xl font-bold text-green-800">
    📖 About This Condition
  </h3>

  <p className="mt-4 leading-7 text-gray-700">
    {diseaseInfo.about}
  </p>

</div>

                {/* SYMPTOMS */}

                <div className="rounded-3xl bg-white p-7 shadow">

                  <h3 className="text-xl font-bold text-green-800">
                    🔎 Common Symptoms
                  </h3>

                  <ul className="mt-5 space-y-3">

                    {diseaseInfo.symptoms.map(
                      (symptom, index) => (

                        <li
                          key={index}
                          className="flex gap-3 text-gray-700"
                        >
                          <span className="font-bold text-green-600">
                            ✓
                          </span>

                          <span>{symptom}</span>

                        </li>

                      )
                    )}

                  </ul>

                </div>


                {/* TREATMENT */}

                <div className="rounded-3xl bg-green-50 p-7">

                  <h3 className="text-xl font-bold text-green-800">
                    🌿 Recommended Action
                  </h3>

                  <ul className="mt-5 space-y-3">

                    {diseaseInfo.treatment.map(
                      (item, index) => (

                        <li
                          key={index}
                          className="flex gap-3 rounded-xl bg-white p-4 text-gray-700"
                        >

                          <span className="font-bold text-green-600">
                            {index + 1}.
                          </span>

                          <span>{item}</span>

                        </li>

                      )
                    )}

                  </ul>

                </div>


                {/* PREVENTION */}

                <div className="rounded-3xl bg-white p-7 shadow">

                  <h3 className="text-xl font-bold text-green-800">
                    🛡️ Prevention Tips
                  </h3>

                  <ul className="mt-5 space-y-3">

                    {diseaseInfo.prevention.map(
                      (tip, index) => (

                        <li
                          key={index}
                          className="flex gap-3 text-gray-700"
                        >

                          <span className="font-bold text-green-600">
                            ✓
                          </span>

                          <span>{tip}</span>

                        </li>

                      )
                    )}

                  </ul>

                </div>


                {/* CALCULATOR */}

                <div className="rounded-3xl border border-green-200 bg-white p-7 shadow">

                  <h3 className="text-xl font-bold text-green-800">
                    🧮 Treatment Calculator
                  </h3>

                  <p className="mt-3 text-sm leading-6 text-gray-600">
                    Enter the number of affected plants and
                    the recommended solution per plant.
                  </p>


                  <div className="mt-6">

                    <label className="font-medium text-gray-700">
                      🌱 Number of affected plants
                    </label>

                    <input
                      type="number"
                      min="1"
                      value={affectedPlants}
                      onChange={(e) =>
                        setAffectedPlants(e.target.value)
                      }
                      placeholder="Example: 20"
                      className="mt-2 w-full rounded-xl border border-gray-300 px-4 py-3 outline-none focus:border-green-600"
                    />

                  </div>


                  <div className="mt-5">

                    <label className="font-medium text-gray-700">
                      💧 Solution per plant (ml)
                    </label>

                    <input
                      type="number"
                      min="0"
                      value={ratePerPlant}
                      onChange={(e) =>
                        setRatePerPlant(e.target.value)
                      }
                      placeholder="Example: 50"
                      className="mt-2 w-full rounded-xl border border-gray-300 px-4 py-3 outline-none focus:border-green-600"
                    />

                  </div>


                  {affectedPlants &&
                    ratePerPlant && (

                      <div className="mt-6 rounded-2xl bg-green-50 p-6">

                        <p className="text-sm text-gray-600">
                          Estimated total solution
                        </p>

                        <p className="mt-2 text-3xl font-bold text-green-800">

                          {(
                            Number(affectedPlants) *
                            Number(ratePerPlant)
                          ).toLocaleString()}{" "}
                          ml

                        </p>

                        <p className="mt-2 text-sm text-gray-600">

                          ≈{" "}
                          {(
                            (Number(affectedPlants) *
                              Number(ratePerPlant)) /
                            1000
                          ).toFixed(2)}{" "}
                          litres

                        </p>

                      </div>

                    )}

                </div>


                {/* DISCLAIMER */}

                <div className="rounded-2xl bg-yellow-50 p-5 text-sm leading-6 text-yellow-800">

                  ⚠️ <strong>Important:</strong>{" "}
                  Plant Guard AI provides an AI-based prediction
                  and general guidance. It should not be treated
                  as a confirmed agricultural diagnosis. Always
                  follow product label instructions and consult
                  an agricultural expert for serious crop damage.

                </div>


                {/* RESET */}

                <div className="pt-2 text-center">

                  <button
                    onClick={resetAnalysis}
                    className="rounded-full border-2 border-green-700 px-8 py-3 font-semibold text-green-700 transition hover:bg-green-700 hover:text-white"
                  >
                    🔄 Analyze Another Plant
                  </button>

                </div>

              </div>

            );

          })()}

        </div>

      </section>


      {/* THREE STEPS */}

<section
  id="how-it-works"
  className="mx-auto mt-14 max-w-6xl px-6"
>
        <div className="grid gap-6 md:grid-cols-3">

          <div className="rounded-3xl bg-white p-7 text-center shadow">

            <div className="text-4xl">
              📷
            </div>

            <h3 className="mt-4 text-lg font-bold text-gray-800">
              1. Upload
            </h3>

            <p className="mt-2 text-sm leading-6 text-gray-500">
              Upload a clear image of the affected plant leaf.
            </p>

          </div>


          <div className="rounded-3xl bg-white p-7 text-center shadow">

            <div className="text-4xl">
              🤖
            </div>

            <h3 className="mt-4 text-lg font-bold text-gray-800">
              2. AI Analysis
            </h3>

            <p className="mt-2 text-sm leading-6 text-gray-500">
              Our trained AI model analyzes the uploaded image.
            </p>

          </div>


          <div className="rounded-3xl bg-white p-7 text-center shadow">

            <div className="text-4xl">
              🌿
            </div>

            <h3 className="mt-4 text-lg font-bold text-gray-800">
              3. Get Results
            </h3>

            <p className="mt-2 text-sm leading-6 text-gray-500">
              View the predicted disease and plant care guidance.
            </p>

          </div>

        </div>

      </section>


      {/* FOOTER */}

<footer
  id="about"
  className="mt-16 border-t border-green-100 bg-white py-8 text-center"
>
        <p className="font-semibold text-green-800">
          🌱 Plant Guard AI
        </p>

        <p className="mt-2 text-sm text-gray-500">
          Protecting plants with artificial intelligence.
        </p>

      </footer>

    </main>
  );
}