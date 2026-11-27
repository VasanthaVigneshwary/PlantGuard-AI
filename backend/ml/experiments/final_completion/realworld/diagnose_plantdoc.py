"""Summarize already-saved PlantDoc Stage 4 predictions; does not rerun inference."""
import csv, json
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[5]
INPUT = ROOT / "backend/ml/experiments/stage4_independent_validation/plantdoc_predictions.csv"
OUT = Path(__file__).resolve().parent
rows = list(csv.DictReader(INPUT.open(encoding="utf-8-sig")))
eligible = [r for r in rows if r["metric_eligible"].lower() == "true"]
def crop(label): return label.split("___", 1)[0] if "___" in label else None
crop_ok = sum(crop(r["mapped_true_class"]) == crop(r["predicted_class"]) for r in eligible)
disease_ok = sum(r["mapped_true_class"] == r["predicted_class"] for r in eligible)
pairs = Counter((r["mapped_true_class"], r["predicted_class"]) for r in eligible if r["mapped_true_class"] != r["predicted_class"])
result = {
 "input": "backend/ml/experiments/stage4_independent_validation/plantdoc_predictions.csv",
 "rows_total": len(rows), "eligible": len(eligible), "excluded": len(rows)-len(eligible),
 "observed_classes": len({r["mapped_true_class"] for r in eligible}),
 "crop_correct": crop_ok, "crop_accuracy": crop_ok/len(eligible),
 "disease_correct": disease_ok, "disease_accuracy": disease_ok/len(eligible),
 "top5_confused_disease_pairs": [{"true":a,"predicted":b,"count":n} for (a,b),n in pairs.most_common(5)],
 "exclusions": dict(Counter(r["exclusion_reason"] for r in rows if r["metric_eligible"].lower() != "true")),
 "interpretation": "Crop and exact-disease correctness are computed from the same 123 eligible saved prediction rows; partial PlantDoc class coverage limits conclusions."
}
(OUT/"diagnosis.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
lines = [
 f"Saved PlantDoc prediction rows: {len(rows)}; eligible for exact-class metrics: {len(eligible)}.",
 f"Crop/species accuracy: {crop_ok}/{len(eligible)} = {result['crop_accuracy']:.2%}.",
 f"Exact disease-class accuracy: {disease_ok}/{len(eligible)} = {result['disease_accuracy']:.2%}.",
 f"Observed mapped classes: {result['observed_classes']} of 38; {len(rows)-len(eligible)} rows excluded.",
 "Crop-level accuracy is derived by comparing the crop prefix before `___` in true and predicted approved labels.",
 "The top five confused disease pairs are recorded in `diagnosis.json`.",
 "Both wrong-crop errors and disease errors occur; crop/species confusion is a substantial failure mode.",
 "Source labels have exclusions and label-noise concerns; no model evaluation was rerun."
]
(OUT/"DIAGNOSIS.md").write_text("\n".join("- "+x for x in lines)+"\n", encoding="utf-8")
print(json.dumps({k:result[k] for k in ("eligible","observed_classes","crop_accuracy","disease_accuracy","top5_confused_disease_pairs","exclusions")},indent=2))
