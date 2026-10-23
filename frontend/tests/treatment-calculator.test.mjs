import assert from "node:assert/strict";
import test from "node:test";

import {
  calculateTreatmentQuantity,
  getCalculableAreaRates,
  validateAreaInput,
} from "../lib/treatment-calculator.mjs";

const verifiedRate = (overrides = {}) => ({
  id: 7,
  disease_id: 42,
  verified: true,
  product_formulation: "Example product 75% WP",
  source_url: "https://extension.example.edu/label",
  rate: 250,
  measurement_unit: "g/acre",
  basis: "per acre",
  ...overrides,
});

const treatmentsWith = (...rates) => [{
  name: "Leaf treatment",
  application_rates: rates,
}];

test("validates empty, zero, negative, non-numeric, and positive area values", () => {
  assert.equal(validateAreaInput("").error, "empty");
  assert.equal(validateAreaInput("  ").error, "empty");
  assert.equal(validateAreaInput("0").error, "non_positive");
  assert.equal(validateAreaInput("-1").error, "non_positive");
  assert.equal(validateAreaInput("abc").error, "invalid");
  assert.equal(validateAreaInput("Infinity").error, "invalid");
  assert.deepEqual(validateAreaInput("0.25"), { valid: true, value: 0.25 });
});

test("calculates only an exact-disease verified rate with product and HTTPS source", () => {
  const rates = getCalculableAreaRates(treatmentsWith(verifiedRate()), 42);
  assert.equal(rates.length, 1);
  assert.equal(rates[0].productFormulation, "Example product 75% WP");
  assert.equal(rates[0].sourceUrl, "https://extension.example.edu/label");
  assert.deepEqual(calculateTreatmentQuantity("0.5", rates[0]), {
    error: null,
    area: 0.5,
    total: 125,
    unit: "g",
  });
});

test("returns no selectable rate when matching verified data is missing", () => {
  assert.deepEqual(getCalculableAreaRates([], 42), []);
  assert.deepEqual(getCalculableAreaRates(treatmentsWith(verifiedRate()), 99), []);
  assert.equal(calculateTreatmentQuantity("1", null).error, "missing_rate");
});

test("rejects unsupported or incompatible units without converting them", () => {
  const incompatible = [
    verifiedRate({ measurement_unit: "g/hectare", basis: "per hectare" }),
    verifiedRate({ measurement_unit: "g/acre", basis: "per hectare" }),
    verifiedRate({ measurement_unit: "g/plant", basis: "per plant" }),
  ];
  assert.deepEqual(getCalculableAreaRates(treatmentsWith(...incompatible), 42), []);
  assert.equal(
    calculateTreatmentQuantity("1", {
      rate: 2,
      measurementUnit: "g/hectare",
      basis: "per hectare",
      verified: true,
      disease_id: 42,
      productFormulation: "Example product",
      sourceUrl: "https://extension.example.edu/label",
    }).error,
    "incompatible_unit",
  );
});

test("supports each area unit present in the database without unit conversion", () => {
  for (const unit of ["g/acre", "kg/acre", "ml/acre"]) {
    const options = getCalculableAreaRates(
      treatmentsWith(verifiedRate({ measurement_unit: unit })),
      42,
    );
    assert.equal(options.length, 1, unit);
    assert.equal(calculateTreatmentQuantity("2", options[0]).unit, unit.split("/")[0]);
  }
});

test("never calculates from unverified or incomplete source records", () => {
  const unsafe = [
    verifiedRate({ verified: false }),
    verifiedRate({ source_url: "http://extension.example.edu/label" }),
    verifiedRate({ source_url: "" }),
    verifiedRate({ source_url: "https://user:secret@extension.example.edu/label" }),
    verifiedRate({ product_formulation: "" }),
  ];
  assert.deepEqual(getCalculableAreaRates(treatmentsWith(...unsafe), 42), []);
  assert.equal(
    calculateTreatmentQuantity("1", {
      rate: 250,
      measurementUnit: "g/acre",
      basis: "per acre",
      verified: false,
      disease_id: 42,
      productFormulation: "Example product",
      sourceUrl: "https://extension.example.edu/label",
    }).error,
    "unverified_rate",
  );
});
