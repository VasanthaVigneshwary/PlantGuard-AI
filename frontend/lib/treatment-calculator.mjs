const AREA_UNITS = new Set(["g/acre", "kg/acre", "ml/acre"]);

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

/**
 * @param {unknown} input
 * @returns {{ valid: true, value: number } | { valid: false, error: "empty" | "invalid" | "non_positive" }}
 */
export function validateAreaInput(input) {
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
  return { valid: true, value };
}

/**
 * Only rates tied to this exact disease and carrying verified product/source
 * metadata with a supported area unit can be offered for calculation.
 * @param {Array<{name?: string, application_rates?: Array<Record<string, unknown>>}> | undefined} treatments
 * @param {number | null} diseaseId
 * @returns {Array<Record<string, unknown> & {id: number, rateId: number, treatmentId: number, treatmentName: string, productName: string, applicationMethod: string, productFormulation: string, rate: number, measurementUnit: string, basis: string, sourceUrl: string, disease_id: number}>}
 */
export function getCalculableAreaRates(treatments, diseaseId) {
  if (!Array.isArray(treatments) || !Number.isInteger(diseaseId)) return [];

  return treatments.flatMap((treatment) =>
    (Array.isArray(treatment.application_rates) ? treatment.application_rates : [])
      .filter((rate) => {
        const unit = typeof rate.measurement_unit === "string"
          ? rate.measurement_unit.trim().toLowerCase()
          : "";
        const basis = typeof rate.basis === "string" ? rate.basis.trim().toLowerCase() : "";
        return rate.verified === true
          && rate.disease_id === diseaseId
          && typeof rate.product_formulation === "string"
          && rate.product_formulation.trim().length > 0
          && hasAuthoritativeHttpsSource(rate.source_url)
          && typeof rate.rate === "number"
          && Number.isFinite(rate.rate)
          && rate.rate > 0
          && AREA_UNITS.has(unit)
          && basis === "per acre";
      })
      .map((rate) => ({
        ...rate,
        id: Number(rate.id),
        rateId: Number(rate.id),
        treatmentId: Number(treatment.id),
        treatmentName: String(treatment.name || ""),
        productName: String(rate.product_formulation).trim(),
        applicationMethod: String(rate.application_method || ""),
        productFormulation: String(rate.product_formulation).trim(),
        rate: Number(rate.rate),
        measurementUnit: String(rate.measurement_unit).trim(),
        basis: String(rate.basis).trim(),
        sourceUrl: String(rate.source_url),
      }))
  );
}

/**
 * @param {string} areaInput
 * @param {Record<string, unknown> | null} rate
 * @returns {{error: null, area: number, total: number, unit: string} | {error: string, area: null, total: null, unit: ""}}
 */
export function calculateTreatmentQuantity(areaInput, rate) {
  const validation = validateAreaInput(areaInput);
  if (!validation.valid) {
    return { error: validation.error, area: null, total: null, unit: "" };
  }
  if (!rate || typeof rate.rate !== "number" || typeof rate.measurementUnit !== "string") {
    return { error: "missing_rate", area: null, total: null, unit: "" };
  }
  if (rate.verified !== true
    || !Number.isInteger(rate.disease_id)
    || typeof rate.productFormulation !== "string"
    || rate.productFormulation.trim() === ""
    || !hasAuthoritativeHttpsSource(rate.sourceUrl)) {
    return { error: "unverified_rate", area: null, total: null, unit: "" };
  }

  const unit = rate.measurementUnit.trim().toLowerCase();
  if (!AREA_UNITS.has(unit)
    || String(rate.basis).trim().toLowerCase() !== "per acre"
    || !Number.isFinite(rate.rate)
    || rate.rate <= 0) {
    return { error: "incompatible_unit", area: null, total: null, unit: "" };
  }
  const total = validation.value * rate.rate;
  if (!Number.isFinite(total) || total <= 0) {
    return { error: "invalid", area: null, total: null, unit: "" };
  }
  return {
    error: null,
    area: validation.value,
    total,
    unit: unit.split("/")[0],
  };
}
