import assert from "node:assert/strict";
import test from "node:test";

import {
  getDisplayableDiseaseGuidance,
  getGuidanceUnavailableMessage,
} from "../lib/disease-guidance.mjs";

const makeResult = (overrides = {}) => ({
  disease: { id: 7, name: "Tomato Early Blight", crop_name: "Tomato", description: "Disease text" },
  symptoms: [{ id: 1, name: "Spots", verified: true, source_url: "https://example.edu/source", disease_id: 7 }],
  causes: [{ id: 2, name: "Cause", verified: true, source_url: "https://example.edu/source", disease_id: 7 }],
  treatments: [{ id: 3, name: "Treatment", verified: true, source_url: "https://example.edu/source", disease_id: 7 }],
  prevention: [{ id: 4, title: "Prevention", verified: true, source_url: "https://example.edu/source", disease_id: 7 }],
  ...overrides,
});

test("keeps verified guidance associated with the exact disease ID", () => {
  const guidance = getDisplayableDiseaseGuidance(makeResult({
    disease: { id: 7, name: "Tomato Early Blight", crop_name: "Tomato", description: "Disease text", verified: true, source_url: "https://example.edu/source", disease_id: 7 },
  }));

  assert.equal(guidance.about, "Disease text");
  assert.equal(guidance.symptoms.length, 1);
  assert.equal(guidance.causes.length, 1);
  assert.equal(guidance.treatments.length, 1);
  assert.equal(guidance.prevention.length, 1);
});

test("does not fall back to records associated with another disease", () => {
  const guidance = getDisplayableDiseaseGuidance(makeResult({
    treatments: [{ id: 9, name: "Other disease treatment", verified: true, source_url: "https://example.edu/source", disease_id: 8 }],
  }));

  assert.deepEqual(guidance.treatments, []);
});

test("hides knowledge-base entries without explicit verification and an HTTPS source", () => {
  const guidance = getDisplayableDiseaseGuidance(makeResult({
    symptoms: [{ id: 1, name: "Unverified symptom" }],
    causes: [{ id: 2, name: "Unverified cause", verified: true, source_url: "http://example.edu/source", disease_id: 7 }],
    treatments: [{ id: 3, name: "Unverified treatment", verified: true, source_url: "https://example.edu/source", disease_id: 8 }],
    prevention: [{ id: 4, title: "Unverified prevention" }],
  }));

  assert.equal(guidance.about, null);
  assert.deepEqual(guidance.symptoms, []);
  assert.deepEqual(guidance.causes, []);
  assert.deepEqual(guidance.treatments, []);
  assert.deepEqual(guidance.prevention, []);
});

test("healthy, uncertain and unsupported results do not turn absent data into guidance", () => {
  const healthy = getDisplayableDiseaseGuidance(makeResult({ is_healthy: true, treatments: [], prevention: [] }));
  const uncertain = getDisplayableDiseaseGuidance(makeResult({ uncertainty_warning: "Uncalibrated model score" }));
  const unsupported = getDisplayableDiseaseGuidance(makeResult({ disease: { ...makeResult().disease, id: null } }));

  assert.deepEqual(healthy.treatments, []);
  assert.deepEqual(healthy.prevention, []);
  assert.deepEqual(uncertain.treatments, []);
  assert.deepEqual(unsupported, { about: null, symptoms: [], causes: [], treatments: [], prevention: [] });
});

test("source-unavailable notice stays localized in English and Tamil", () => {
  assert.match(getGuidanceUnavailableMessage("en"), /No verified source/);
  assert.match(getGuidanceUnavailableMessage("ta"), /சரிபார்க்கப்பட்ட ஆதாரம்/);
});
