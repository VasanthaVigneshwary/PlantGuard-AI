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

  const plant = parts[0]
    .replaceAll("_", " ")
    .replaceAll(",", "")
    .trim();

  const disease = parts[1]
    .replaceAll("_", " ")
    .trim();

  return {
    plant,
    disease,
  };
}

function getDiseaseInfo(disease: string): DiseaseInfo {
  const lowerDisease = disease.toLowerCase();

  if (lowerDisease.includes("late blight")) {
    return {
      about:
        "Late blight is a serious plant disease that can spread quickly, especially in cool and humid conditions.",

      symptoms: [
        "Dark or brown spots may appear on leaves.",
        "Affected leaves may become weak and die.",
        "The disease can spread rapidly to other parts of the plant.",
      ],

      treatment: [
        "Remove severely affected leaves and plant parts.",
        "Avoid watering directly over the leaves.",
        "Improve air circulation around the plants.",
        "Use an appropriate fungicide according to the product label and local agricultural guidance.",
      ],

      prevention: [
        "Maintain proper spacing between plants.",
        "Keep leaves as dry as possible.",
        "Remove infected plant material from the growing area.",
      ],
    };
  }

  if (lowerDisease.includes("early blight")) {
    return {
      about:
        "Early blight is a common fungal disease that mainly affects leaves and can reduce plant growth and crop production.",

      symptoms: [
        "Small dark spots may appear on older leaves.",
        "Spots can develop into larger brown areas.",
        "Affected leaves may turn yellow and fall.",
      ],

      treatment: [
        "Remove severely affected leaves.",
        "Keep the area around the plant clean.",
        "Avoid overhead watering.",
        "Use a suitable fungicide according to the product label and local agricultural guidance.",
      ],

      prevention: [
        "Provide good spacing between plants.",
        "Remove fallen infected leaves.",
        "Avoid keeping plant leaves wet for long periods.",
      ],
    };
  }

  if (lowerDisease.includes("powdery mildew")) {
    return {
      about:
        "Powdery mildew is a fungal disease that commonly appears as a white powder-like coating on plant leaves.",

      symptoms: [
        "White powder-like patches appear on leaves.",
        "Leaves may become distorted or yellow.",
        "Plant growth may become weaker.",
      ],

      treatment: [
        "Remove heavily infected leaves.",
        "Improve air circulation around the plant.",
        "Avoid excessive humidity around the foliage.",
        "Use an appropriate fungicide according to the product label.",
      ],

      prevention: [
        "Give plants enough space for air circulation.",
        "Avoid excessive watering.",
        "Keep the growing area clean.",
      ],
    };
  }

  if (lowerDisease.includes("bacterial spot")) {
    return {
      about:
        "Bacterial spot can cause dark or water-soaked spots on leaves and may reduce plant health.",

      symptoms: [
        "Small dark spots may appear on leaves.",
        "Spots can enlarge as the disease develops.",
        "Severely affected leaves may become damaged or fall.",
      ],

      treatment: [
        "Remove severely affected plant parts.",
        "Avoid working with plants when the leaves are wet.",
        "Improve air circulation.",
        "Use suitable treatment according to local agricultural guidance.",
      ],

      prevention: [
        "Use clean planting material.",
        "Avoid unnecessary leaf wetting.",
        "Remove infected plant debris.",
      ],
    };
  }

  if (lowerDisease.includes("healthy")) {
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
        "Regularly inspect leaves for changes.",
      ],
    };
  }

  return {
    about:
      "The AI model detected a possible plant disease. The result should be treated as an AI-based indication rather than a confirmed diagnosis.",

    symptoms: [
      "Visible symptoms may vary depending on the plant and disease.",
      "Inspect affected leaves and other plant parts carefully.",
    ],

    treatment: [
      "Remove severely affected plant parts when appropriate.",
      "Maintain good air circulation around the plant.",
      "Avoid unnecessary leaf wetting.",
      "Use treatment products only according to their labels and local agricultural recommendations.",
    ],

    prevention: [
      "Keep the growing area clean.",
      "Monitor plants regularly.",
      "Remove infected plant material when appropriate.",
    ],
  };
}

function getExplanation(disease: string) {
  const lowerDisease = disease.toLowerCase();

  if (lowerDisease === "healthy") {
    return "The AI model did not detect a known disease in this plant image.";
  }

  if (lowerDisease.includes("late blight")) {
    return "Late blight can spread quickly under cool and humid conditions.";
  }

  if (lowerDisease.includes("early blight")) {
    return "Early blight can cause dark spots on leaves and may reduce plant growth.";
  }

  if (lowerDisease.includes("powdery mildew")) {
    return "Powdery mildew commonly appears as a white powder-like coating on leaves.";
  }

  if (lowerDisease.includes("bacterial spot")) {
    return "Bacterial spot can cause small dark or water-soaked spots on plant leaves.";
  }

  if (lowerDisease.includes("leaf spot")) {
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
          data.detail ||
            "Something went wrong while analyzing the image."
        );
      }

      setResult(data);

    } catch (error) {
      console.error(error);

      setError(
        "Unable to connect to Plant Guard AI backend. Make sure the FastAPI server is running."
      );

    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-green-50 px-6 py-10">

      <div className="mx-auto max-w-5xl">

        {/* HEADER */}

        <header className="mb-12 text-center">

          <div className="mb-3 text-5xl">
            🌱
          </div>

          <h1 className="text-4xl font-bold text-green-800">
            Plant Guard AI
          </h1>

          <p className="mt-3 text-lg text-green-700">
            AI-powered plant disease detection
          </p>

        </header>


        {/* UPLOAD SECTION */}

        <section className="rounded-3xl bg-white p-8 shadow-lg">

          <h2 className="text-center text-2xl font-semibold text-gray-800">
            Upload a Plant Image
          </h2>

          <p className="mt-2 text-center text-gray-500">
            Upload a clear image of a plant leaf to detect possible diseases.
          </p>


          {/* IMAGE UPLOAD */}

          <label
            htmlFor="plant-image"
            className="mx-auto mt-8 flex max-w-xl cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-green-300 bg-green-50 p-10 transition hover:bg-green-100"
          >

            {preview ? (

              <img
                src={preview}
                alt="Selected plant"
                className="max-h-72 rounded-xl object-contain"
              />

            ) : (

              <>
                <div className="mb-4 text-5xl">
                  📷
                </div>

                <p className="text-lg font-medium text-green-800">
                  Choose a plant image
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


          {/* FILE NAME */}

          {selectedFile && (

            <p className="mt-5 text-center text-sm text-gray-600">

              Selected:{" "}

              <strong>
                {selectedFile.name}
              </strong>

            </p>

          )}


          {/* ANALYZE BUTTON */}

          <div className="mt-8 text-center">

            <button
              onClick={analyzePlant}
              disabled={!selectedFile || loading}
              className="rounded-full bg-green-700 px-8 py-3 text-lg font-semibold text-white transition hover:bg-green-800 disabled:cursor-not-allowed disabled:bg-gray-300"
            >

              {loading
                ? "🔄 Analyzing..."
                : "🔍 Analyze Plant"}

            </button>

          </div>


          {/* ERROR */}

          {error && (

            <div className="mx-auto mt-6 max-w-xl rounded-xl bg-red-50 p-4 text-center text-red-700">

              ❌ {error}

            </div>

          )}


          {/* RESULT */}

          {result && (

            <div className="mx-auto mt-10 max-w-3xl">

              {(() => {

                const formatted =
                  formatDiseaseName(result.prediction);

                const diseaseInfo =
                  getDiseaseInfo(formatted.disease);

                const explanation =
                  getExplanation(formatted.disease);

                return (

                  <div className="space-y-6">

                    {/* RESULT HEADER */}

                    <div className="rounded-3xl border border-green-200 bg-green-50 p-8">

                      <h2 className="text-center text-3xl font-bold text-green-800">
                        🌱 Plant Health Result
                      </h2>


                      {/* PLANT */}

                      <div className="mt-8 rounded-2xl bg-white p-5">

                        <p className="text-sm text-gray-500">
                          🌿 Plant
                        </p>

                        <p className="mt-1 text-xl font-bold text-gray-800">
                          {formatted.plant}
                        </p>

                      </div>


                      {/* DISEASE */}

                      <div className="mt-4 rounded-2xl bg-white p-5">

                        <p className="text-sm text-gray-500">
                          🦠 Detected Condition
                        </p>

                        <p className="mt-1 text-xl font-bold text-red-700">
                          {formatted.disease}
                        </p>

                      </div>


                      {/* CONFIDENCE */}

                      <div className="mt-4 rounded-2xl bg-white p-5">

                        <div className="flex items-center justify-between">

                          <p className="text-sm text-gray-500">
                            📊 AI Confidence
                          </p>

                          <p className="text-xl font-bold text-green-700">
                            {result.confidence}%
                          </p>

                        </div>


                        <div className="mt-3 h-3 overflow-hidden rounded-full bg-gray-200">

                          <div
                            className="h-full rounded-full bg-green-600"
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

                      <div className="mt-4 rounded-2xl bg-white p-5">

                        <p className="text-sm text-gray-500">
                          ⚠️ Confidence Status
                        </p>

                        <p className="mt-1 text-lg font-semibold text-gray-800">
                          {result.status}
                        </p>

                      </div>


                      {/* EXPLANATION */}

                      <div className="mt-4 rounded-2xl bg-white p-5">

                        <p className="text-sm text-gray-500">
                          💡 What does this mean?
                        </p>

                        <p className="mt-2 leading-7 text-gray-700">
                          {explanation}
                        </p>

                      </div>

                    </div>


                    {/* ABOUT DISEASE */}

                    <div className="rounded-3xl bg-white p-8 shadow">

                      <h3 className="text-2xl font-bold text-green-800">
                        🦠 About This Condition
                      </h3>

                      <p className="mt-4 leading-7 text-gray-700">
                        {diseaseInfo.about}
                      </p>

                    </div>


                    {/* SYMPTOMS */}

                    <div className="rounded-3xl bg-white p-8 shadow">

                      <h3 className="text-2xl font-bold text-green-800">
                        🔎 Common Symptoms
                      </h3>

                      <ul className="mt-5 space-y-3">

                        {diseaseInfo.symptoms.map(
                          (symptom, index) => (

                            <li
                              key={index}
                              className="flex gap-3 text-gray-700"
                            >

                              <span className="text-green-600">
                                ✓
                              </span>

                              <span>
                                {symptom}
                              </span>

                            </li>

                          )
                        )}

                      </ul>

                    </div>


                    {/* TREATMENT */}

                    <div className="rounded-3xl border border-green-200 bg-green-50 p-8">

                      <h3 className="text-2xl font-bold text-green-800">
                        🌿 Recommended Action
                      </h3>

                      <p className="mt-3 text-sm text-gray-600">
                        General guidance based on the AI prediction:
                      </p>

                      <ul className="mt-5 space-y-4">

                        {diseaseInfo.treatment.map(
                          (treatment, index) => (

                            <li
                              key={index}
                              className="flex gap-3 rounded-xl bg-white p-4 text-gray-700"
                            >

                              <span className="font-bold text-green-600">
                                {index + 1}.
                              </span>

                              <span>
                                {treatment}
                              </span>

                            </li>

                          )
                        )}

                      </ul>

                    </div>


                    {/* PREVENTION */}

                    <div className="rounded-3xl bg-white p-8 shadow">

                      <h3 className="text-2xl font-bold text-green-800">
                        🛡️ Prevention Tips
                      </h3>

                      <ul className="mt-5 space-y-3">

                        {diseaseInfo.prevention.map(
                          (tip, index) => (

                            <li
                              key={index}
                              className="flex gap-3 text-gray-700"
                            >

                              <span className="text-green-600">
                                ✓
                              </span>

                              <span>
                                {tip}
                              </span>

                            </li>

                          )
                        )}

                      </ul>

                    </div>


                    {/* DISCLAIMER */}

                    <div className="rounded-2xl bg-yellow-50 p-5 text-sm leading-6 text-yellow-800">

                      ⚠️ <strong>Important:</strong>{" "}
                      Plant Guard AI provides an AI-based prediction
                      and general guidance. The result should not be
                      treated as a confirmed agricultural diagnosis.
                      For serious crop damage, consult a qualified
                      agricultural expert and always follow the label
                      instructions for any agricultural product.

                    </div>

                  </div>

                );

              })()}

            </div>

          )}

        </section>


        {/* THREE FEATURE CARDS */}

        <section className="mt-10 grid gap-6 md:grid-cols-3">

          <div className="rounded-2xl bg-white p-6 text-center shadow">

            <div className="text-3xl">
              📷
            </div>

            <h3 className="mt-3 font-semibold text-gray-800">
              Upload
            </h3>

            <p className="mt-2 text-sm text-gray-500">
              Upload a clear image of the affected plant leaf.
            </p>

          </div>


          <div className="rounded-2xl bg-white p-6 text-center shadow">

            <div className="text-3xl">
              🤖
            </div>

            <h3 className="mt-3 font-semibold text-gray-800">
              AI Analysis
            </h3>

            <p className="mt-2 text-sm text-gray-500">
              Our AI model analyzes the image for possible diseases.
            </p>

          </div>


          <div className="rounded-2xl bg-white p-6 text-center shadow">

            <div className="text-3xl">
              🌿
            </div>

            <h3 className="mt-3 font-semibold text-gray-800">
              Get Results
            </h3>

            <p className="mt-2 text-sm text-gray-500">
              View the disease, symptoms, treatment and prevention.
            </p>

          </div>

        </section>


        {/* FOOTER */}

        <footer className="mt-12 text-center text-sm text-green-700">

          Plant Guard AI • Protecting plants with artificial intelligence 🌱

        </footer>

      </div>

    </main>
  );
}