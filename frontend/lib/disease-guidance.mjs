const hasTrustedDiseaseSource = (item, diseaseId) => {
  if (!item || item.verified !== true || item.disease_id !== diseaseId) {
    return false;
  }

  try {
    const source = new URL(item.source_url);
    const host = source.hostname.toLowerCase();
    const trustedHost = host === "fao.org"
      || host === "www.fao.org"
      || host.endsWith(".gov")
      || host.endsWith(".gov.in")
      || host.endsWith(".edu")
      || host.endsWith(".ac.in");
    return source.protocol === "https:"
      && !source.username
      && !source.password
      && (!source.port || source.port === "443")
      && trustedHost;
  } catch {
    return false;
  }
};

const onlySourcedForDisease = (items, diseaseId) =>
  Array.isArray(items)
    ? items.filter((item) => hasTrustedDiseaseSource(item, diseaseId))
    : [];

export function getDisplayableDiseaseGuidance(result) {
  const diseaseId = result?.disease?.id;
  if (!Number.isInteger(diseaseId) || diseaseId <= 0) {
    return { about: null, symptoms: [], causes: [], treatments: [], prevention: [] };
  }

  const disease = result.disease;
  return {
    about: hasTrustedDiseaseSource(disease, diseaseId) ? disease.description : null,
    symptoms: onlySourcedForDisease(result.symptoms, diseaseId),
    causes: onlySourcedForDisease(result.causes, diseaseId),
    treatments: result.is_healthy || result.uncertainty_warning
      ? []
      : onlySourcedForDisease(result.treatments, diseaseId),
    prevention: onlySourcedForDisease(result.prevention, diseaseId),
  };
}

export function getGuidanceUnavailableMessage(language) {
  return language === "ta"
    ? "இந்த தகவலுக்கு சரிபார்க்கப்பட்ட ஆதாரம் இணைக்கப்படவில்லை. இதைப் பயன்படுத்துவதற்கு முன் தகுதியான வேளாண் நிபுணரிடம் உறுதிப்படுத்தவும்."
    : "No verified source is attached to this knowledge-base entry. Confirm it with a qualified agricultural expert before relying on it.";
}
