import assert from "node:assert/strict";
import test from "node:test";

import {
  calculateTreatmentQuantity,
  formatCalculatedQuantity,
  getAreaSquareFeet,
  getCalculableRates,
  getRatesForMode,
  validateQuantityInput,
} from "../lib/treatment-calculator.mjs";

const verifiedRate = (overrides = {}) => ({
  id: 7,
  disease_id: 42,
  verified: true,
  product_formulation: "Example product 75% WP",
  source_url: "https://agritech.tnau.ac.in/label",
  rate: 2,
  measurement_unit: "kg/acre",
  basis: "per acre",
  ...overrides,
});

const treatmentsWith = (...rates) => [{
  id: 3,
  name: "Disease-specific treatment",
  application_rates: rates,
}];

test("validates empty, zero, negative, non-numeric, and positive quantities", () => {
  assert.equal(validateQuantityInput("").error, "empty");
  assert.equal(validateQuantityInput("  ").error, "empty");
  assert.equal(validateQuantityInput("0").error, "non_positive");
  assert.equal(validateQuantityInput("-1").error, "non_positive");
  assert.equal(validateQuantityInput("abc").error, "invalid");
  assert.equal(validateQuantityInput("Infinity").error, "invalid");
  assert.equal(validateQuantityInput("2.5", "plants").error, "invalid");
  assert.equal(validateQuantityInput("9007199254740992", "plants").error, "invalid");
  assert.deepEqual(validateQuantityInput("0.25", "acres"), { valid: true, value: 0.25 });
  assert.deepEqual(validateQuantityInput("10", "plants"), { valid: true, value: 10 });
});

test("calculates an acre rate for acres and reports square feet", () => {
  const [rate] = getCalculableRates(treatmentsWith(verifiedRate()), 42);
  assert.deepEqual(calculateTreatmentQuantity("1", "acres", rate), {
    error: null,
    enteredQuantity: 1,
    inputMode: "acres",
    basisQuantity: 1,
    basisUnit: "acre",
    squareFeet: 43560,
    total: 2,
    unit: "kg",
  });
});

test("converts cents to acres exactly before applying an acre rate", () => {
  const [rate] = getCalculableRates(treatmentsWith(verifiedRate()), 42);
  const result = calculateTreatmentQuantity("25", "cents", rate);
  assert.equal(result.basisQuantity, 0.25);
  assert.equal(result.squareFeet, 10890);
  assert.equal(result.total, 0.5);
  assert.equal(result.unit, "kg");
});

test("converts acres to cents when the verified rate is per cent", () => {
  const rate = verifiedRate({ rate: 0.25, measurement_unit: "g/cent", basis: "per cent" });
  const [calculableRate] = getCalculableRates(treatmentsWith(rate), 42);
  const result = calculateTreatmentQuantity("1", "acres", calculableRate);
  assert.equal(result.basisQuantity, 100);
  assert.equal(result.total, 25);
  assert.equal(result.unit, "g");
});

test("uses only per-plant rates for an integer plant count", () => {
  const rate = verifiedRate({ rate: 0.5, measurement_unit: "ml/plant", basis: "per plant" });
  const [calculableRate] = getCalculableRates(treatmentsWith(rate), 42);
  const result = calculateTreatmentQuantity("4", "plants", calculableRate);
  assert.equal(result.basisQuantity, 4);
  assert.equal(result.basisUnit, "plant");
  assert.equal(result.squareFeet, null);
  assert.equal(result.total, 2);
  assert.equal(result.unit, "ml");
});

test("reads canonical units while keeping localized display values separate", () => {
  const rate = verifiedRate({
    measurement_unit: "g/acre",
    measurement_unit_key: "g/acre",
    basis: "ஒரு ஏக்கருக்கு",
    basis_key: "per acre",
  });
  const [calculableRate] = getCalculableRates(treatmentsWith(rate), 42);
  assert.equal(calculableRate.displayBasis, "ஒரு ஏக்கருக்கு");
  assert.equal(calculateTreatmentQuantity("1", "acres", calculableRate).total, 2);
});

test("returns no usable rate for missing or disease-mismatched data", () => {
  assert.deepEqual(getCalculableRates([], 42), []);
  assert.deepEqual(getCalculableRates(treatmentsWith(verifiedRate()), 99), []);
  assert.equal(calculateTreatmentQuantity("1", "acres", null).error, "missing_rate");
});

test("rejects rate units or bases that cannot safely match a quantity mode", () => {
  const incompatible = [
    verifiedRate({ measurement_unit: "g/hectare", basis: "per hectare" }),
    verifiedRate({ measurement_unit: "g/acre", basis: "per cent" }),
    verifiedRate({ measurement_unit: "g/litre", basis: "per litre" }),
  ];
  assert.deepEqual(getCalculableRates(treatmentsWith(...incompatible), 42), []);

  const [acreRate] = getCalculableRates(treatmentsWith(verifiedRate()), 42);
  assert.equal(calculateTreatmentQuantity("3", "plants", acreRate).error, "incompatible_unit");
  assert.deepEqual(getRatesForMode([acreRate], "plants"), []);
  assert.deepEqual(getRatesForMode([acreRate], "invalid"), []);
  const [plantRate] = getCalculableRates(treatmentsWith(
    verifiedRate({ measurement_unit: "g/plant", basis: "per plant" }),
  ), 42);
  assert.deepEqual(getRatesForMode([plantRate], "acres"), []);
});

test("rejects unverified rates, invalid sources, and incomplete products", () => {
  const unsafe = [
    verifiedRate({ verified: false }),
    verifiedRate({ source_url: "http://agritech.tnau.ac.in/label" }),
    verifiedRate({ source_url: "https://user:secret@agritech.tnau.ac.in/label" }),
    verifiedRate({ product_formulation: "" }),
  ];
  assert.deepEqual(getCalculableRates(treatmentsWith(...unsafe), 42), []);
});

test("preserves boundary conversions and formats floating-point output cleanly", () => {
  const [rate] = getCalculableRates(treatmentsWith(verifiedRate({ rate: 1 })), 42);
  assert.equal(calculateTreatmentQuantity("100", "cents", rate).basisQuantity, 1);
  assert.equal(calculateTreatmentQuantity("0.01", "acres", rate).squareFeet, 435.6);
  assert.equal(getAreaSquareFeet("1", "acres"), 43560);
  assert.equal(getAreaSquareFeet("25", "cents"), 10890);
  assert.equal(getAreaSquareFeet("5", "plants"), null);
  assert.equal(formatCalculatedQuantity(0.30000000000000004), "0.3");
  assert.equal(formatCalculatedQuantity(1 / 3), "0.33333333");
  assert.equal(formatCalculatedQuantity(1e-12), "1e-12");
});
