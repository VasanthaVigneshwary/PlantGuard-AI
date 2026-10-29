const VALID_MODES = new Set(["acres", "cents", "plants"]);
const AREA_SQUARE_FEET = { acres: 43560, cents: 435.6 };

function hasAuthoritativeHttpsSource(source) {
  try {
    const url = new URL(String(source));
    const host = url.hostname.toLowerCase().replace(/\.$/, "");
    return url.protocol === "https:"
      && !url.username
      && !url.password
      && (!url.port || url.port === "443")
      && (host === "fao.org" || host === "www.fao.org"
        || [".gov", ".gov.in", ".edu", ".ac.in"].some((suffix) => host.endsWith(suffix)));
  } catch {
    return false;
  }
}

function parseRateUnit(measurementUnit, basis) {
  if (typeof measurementUnit !== "string" || typeof basis !== "string") return null;
  const match = measurementUnit.trim().toLowerCase().match(/^(g|kg|ml|l)\s*\/\s*(acre|cent|plant)$/);
  if (!match || basis.trim().toLowerCase() !== `per ${match[2]}`) return null;
  return { numeratorUnit: match[1], denominatorUnit: match[2] };
}

/**
 * @param {unknown} input
 * @returns {{ valid: true, value: number } | { valid: false, error: "empty" | "invalid" | "non_positive" }}
 */
export function validateQuantityInput(input, mode) {
  if (typeof input !== "string" || input.trim() === "") {
    return { valid: false, error: "empty" };
  }

  const normalized = input.trim();
  if (!/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$/.test(normalized)) {
    return { valid: false, error: "invalid" };
  }

  const value = Number(normalized);
  if (!Number.isFinite(value)) {
    return { valid: false, error: "invalid" };
  }
  if (value <= 0) {
    return { valid: false, error: "non_positive" };
  }
  if (mode === "plants" && !Number.isSafeInteger(value)) {
    return { valid: false, error: "invalid" };
  }
  return { valid: true, value };
}

// Kept as an alias for callers using the earlier acres-only helper name.
export const validateAreaInput = validateQuantityInput;

export function getAreaSquareFeet(quantityInput, mode) {
  const validation = validateQuantityInput(quantityInput, mode);
  if (!validation.valid) return null;
  let squareFeet = null;
  if (mode === "acres") squareFeet = validation.value * AREA_SQUARE_FEET.acres;
  if (mode === "cents") squareFeet = validation.value * AREA_SQUARE_FEET.cents;
  if (squareFeet !== null) return Number.isFinite(squareFeet) ? squareFeet : null;
  return null;
}

/**
 * Return only verified, disease-matched rates with product and source metadata
 * and an exact supported rate unit (per acre, per cent, or per plant).
 */
export function getCalculableRates(treatments, diseaseId) {
  if (!Array.isArray(treatments) || !Number.isInteger(diseaseId)) return [];

  return treatments.flatMap((treatment) =>
    (Array.isArray(treatment.application_rates) ? treatment.application_rates : [])
      .filter((rate) => {
        const measurementUnit = rate.measurement_unit_key ?? rate.measurement_unit;
        const basis = rate.basis_key ?? rate.basis;
        return rate.verified === true
          && rate.disease_id === diseaseId
          && Number.isInteger(Number(rate.id))
          && typeof rate.product_formulation === "string"
          && rate.product_formulation.trim().length > 0
          && hasAuthoritativeHttpsSource(rate.source_url)
          && typeof rate.rate === "number"
          && Number.isFinite(rate.rate)
          && rate.rate > 0
          && parseRateUnit(measurementUnit, basis) !== null;
      })
      .map((rate) => {
        const measurementUnit = String(rate.measurement_unit_key ?? rate.measurement_unit).trim();
        const basis = String(rate.basis_key ?? rate.basis).trim();
        const parsedUnit = parseRateUnit(measurementUnit, basis);
        return {
          ...rate,
          id: Number(rate.id),
          rateId: Number(rate.id),
          treatmentId: Number(treatment.id),
          treatmentName: String(treatment.name || ""),
          productName: String(rate.product_formulation).trim(),
          applicationMethod: String(rate.application_method || ""),
          productFormulation: String(rate.product_formulation).trim(),
          rate: Number(rate.rate),
          measurementUnit,
          basis,
          displayBasis: String(rate.basis || basis).trim(),
          sourceUrl: String(rate.source_url),
          numeratorUnit: parsedUnit.numeratorUnit,
          denominatorUnit: parsedUnit.denominatorUnit,
        };
      })
  );
}

export function getRatesForMode(rates, mode) {
  if (!VALID_MODES.has(mode) || !Array.isArray(rates)) return [];
  return rates.filter((rate) => mode === "plants"
    ? rate.denominatorUnit === "plant"
    : rate.denominatorUnit === "acre" || rate.denominatorUnit === "cent");
}

/**
 * Calculate only when the selected input mode and verified rate use compatible
 * bases. Acre/cent conversion uses the exact 100 cents per acre relationship.
 */
export function calculateTreatmentQuantity(quantityInput, mode, rate) {
  const validation = validateQuantityInput(quantityInput, mode);
  if (!validation.valid) {
    return { error: validation.error, enteredQuantity: null, basisQuantity: null, total: null, unit: "" };
  }
  if (!VALID_MODES.has(mode)) {
    return { error: "invalid_mode", enteredQuantity: null, basisQuantity: null, total: null, unit: "" };
  }
  if (!rate) {
    return { error: "missing_rate", enteredQuantity: validation.value, basisQuantity: null, total: null, unit: "" };
  }

  const measurementUnit = rate.measurement_unit_key ?? rate.measurementUnit;
  const basis = rate.basis_key ?? rate.basis;
  const parsedUnit = parseRateUnit(measurementUnit, basis);
  if (rate.verified !== true
    || !Number.isInteger(rate.disease_id)
    || typeof (rate.product_formulation ?? rate.productFormulation) !== "string"
    || String(rate.product_formulation ?? rate.productFormulation).trim() === ""
    || !hasAuthoritativeHttpsSource(rate.source_url ?? rate.sourceUrl)) {
    return { error: "unverified_rate", enteredQuantity: validation.value, basisQuantity: null, total: null, unit: "" };
  }
  if (!parsedUnit || typeof rate.rate !== "number" || !Number.isFinite(rate.rate) || rate.rate <= 0) {
    return { error: "incompatible_unit", enteredQuantity: validation.value, basisQuantity: null, total: null, unit: "" };
  }

  const isAreaMode = mode === "acres" || mode === "cents";
  const isAreaRate = parsedUnit.denominatorUnit === "acre" || parsedUnit.denominatorUnit === "cent";
  if (isAreaMode !== isAreaRate) {
    return { error: "incompatible_unit", enteredQuantity: validation.value, basisQuantity: null, total: null, unit: "" };
  }
  const squareFeet = getAreaSquareFeet(quantityInput, mode);
  if (isAreaMode && squareFeet === null) {
    return { error: "invalid", enteredQuantity: validation.value, basisQuantity: null, total: null, unit: "" };
  }

  let basisQuantity;
  if (mode === "plants") {
    basisQuantity = validation.value;
  } else if (mode === "acres") {
    basisQuantity = parsedUnit.denominatorUnit === "acre"
      ? validation.value
      : validation.value * 100;
  } else {
    basisQuantity = parsedUnit.denominatorUnit === "cent"
      ? validation.value
      : validation.value / 100;
  }

  const total = basisQuantity * rate.rate;
  if (!Number.isFinite(basisQuantity) || !Number.isFinite(total) || total <= 0) {
    return { error: "invalid", enteredQuantity: validation.value, basisQuantity: null, total: null, unit: "" };
  }

  return {
    error: null,
    enteredQuantity: validation.value,
    inputMode: mode,
    basisQuantity,
    basisUnit: parsedUnit.denominatorUnit,
    squareFeet,
    total,
    unit: parsedUnit.numeratorUnit,
  };
}

export function formatCalculatedQuantity(value) {
  if (!Number.isFinite(value)) return "";
  return Number(value.toPrecision(8)).toString();
}
