# Read-only website knowledge-base audit (2026-11-27)

- Database transaction: `SET TRANSACTION READ ONLY`; no records/schema modified.
- API smoke test: `GET /api/diseases/39` returned HTTP 200, Tomato Septoria Leaf Spot, description, 3 symptoms, 2 causes, 1 treatment and 3 prevention rows; 0 verified application rates. Payload has no source fields.
- UI cause: `getDisplayableDiseaseGuidance` requires `verified === true`, matching `disease_id`, and a trusted HTTPS `source_url` for every content item. The API does not supply these fields for descriptions/symptoms/causes/treatments/prevention, and the schema has no source fields for those tables. It therefore suppresses stored but unverified content and shows its unavailable message.
- This is a provenance/data-evidence gap, not a failed fetch or disease-key mismatch. Treatment rows exist, but all 27 application-rate rows are unverified and correctly omitted from the calculator. No agriculture text or rates were fabricated.

- Mapping: 38/38 unique disease mappings; duplicates: 0.

| Approved class | map | description | symptom entries | cause entries | treatment rows (complete text) | prevention entries | rates (verified) |
|---|---:|---|---:|---:|---:|---:|---:|
| `Apple___Apple_scab` | 1 | present | 3 | 3 | 1 (1) | 3 | 1 (0) |
| `Apple___Black_rot` | 1 | present | 3 | 2 | 1 (1) | 2 | 1 (0) |
| `Apple___Cedar_apple_rust` | 1 | present | 3 | 2 | 1 (1) | 2 | 1 (0) |
| `Apple___healthy` | 1 | present | 3 | 1 | 1 (1) | 2 | 0 (0) |
| `Blueberry___healthy` | 1 | present | 2 | 1 | 1 (1) | 2 | 0 (0) |
| `Cherry_(including_sour)___Powdery_mildew` | 1 | present | 3 | 2 | 1 (1) | 2 | 1 (0) |
| `Cherry_(including_sour)___healthy` | 1 | present | 2 | 1 | 1 (1) | 2 | 0 (0) |
| `Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot` | 1 | present | 3 | 2 | 1 (1) | 3 | 1 (0) |
| `Corn_(maize)___Common_rust_` | 1 | present | 3 | 2 | 1 (1) | 2 | 1 (0) |
| `Corn_(maize)___Northern_Leaf_Blight` | 1 | present | 3 | 2 | 1 (1) | 2 | 1 (0) |
| `Corn_(maize)___healthy` | 1 | present | 3 | 1 | 1 (1) | 1 | 0 (0) |
| `Grape___Black_rot` | 1 | present | 3 | 2 | 1 (1) | 2 | 1 (0) |
| `Grape___Esca_(Black_Measles)` | 1 | present | 3 | 2 | 1 (1) | 2 | 0 (0) |
| `Grape___Leaf_blight_(Isariopsis_Leaf_Spot)` | 1 | present | 3 | 2 | 1 (1) | 2 | 1 (0) |
| `Grape___healthy` | 1 | present | 2 | 1 | 1 (1) | 1 | 0 (0) |
| `Orange___Haunglongbing_(Citrus_greening)` | 1 | present | 3 | 2 | 1 (1) | 2 | 1 (0) |
| `Peach___Bacterial_spot` | 1 | present | 3 | 2 | 1 (1) | 2 | 1 (0) |
| `Peach___healthy` | 1 | present | 2 | 1 | 1 (1) | 1 | 0 (0) |
| `Pepper,_bell___Bacterial_spot` | 1 | present | 3 | 2 | 1 (1) | 3 | 1 (0) |
| `Pepper,_bell___healthy` | 1 | present | 2 | 1 | 1 (1) | 1 | 0 (0) |
| `Potato___Early_blight` | 1 | present | 2 | 3 | 1 (1) | 5 | 0 (0) |
| `Potato___Late_blight` | 1 | present | 3 | 3 | 1 (1) | 5 | 0 (0) |
| `Potato___healthy` | 1 | present | 2 | 1 | 1 (1) | 1 | 0 (0) |
| `Raspberry___healthy` | 1 | present | 2 | 1 | 1 (1) | 1 | 0 (0) |
| `Soybean___healthy` | 1 | present | 2 | 1 | 1 (1) | 1 | 0 (0) |
| `Squash___Powdery_mildew` | 1 | present | 3 | 2 | 1 (1) | 2 | 1 (0) |
| `Strawberry___Leaf_scorch` | 1 | present | 3 | 2 | 1 (1) | 2 | 1 (0) |
| `Strawberry___healthy` | 1 | present | 2 | 1 | 1 (1) | 1 | 0 (0) |
| `Tomato___Bacterial_spot` | 1 | present | 3 | 2 | 1 (1) | 3 | 1 (0) |
| `Tomato___Early_blight` | 1 | present | 3 | 3 | 1 (1) | 5 | 4 (0) |
| `Tomato___Late_blight` | 1 | present | 3 | 4 | 1 (1) | 5 | 4 (0) |
| `Tomato___Leaf_Mold` | 1 | present | 2 | 3 | 1 (1) | 3 | 0 (0) |
| `Tomato___Septoria_leaf_spot` | 1 | present | 3 | 2 | 1 (1) | 3 | 1 (0) |
| `Tomato___Spider_mites Two-spotted_spider_mite` | 1 | present | 3 | 2 | 1 (1) | 2 | 1 (0) |
| `Tomato___Target_Spot` | 1 | present | 3 | 2 | 1 (1) | 2 | 1 (0) |
| `Tomato___Tomato_Yellow_Leaf_Curl_Virus` | 1 | present | 3 | 2 | 1 (1) | 3 | 1 (0) |
| `Tomato___Tomato_mosaic_virus` | 1 | present | 3 | 2 | 1 (1) | 3 | 0 (0) |
| `Tomato___healthy` | 1 | present | 3 | 1 | 1 (1) | 2 | 0 (0) |

- Coverage: descriptions 38/38; symptoms 38/38; causes 38/38; treatment rows 38/38 (complete text 38/38); prevention 38/38.
- Application rates: 27 total; 0 verified. No verified rate should be displayed or calculated.

## Safe next action

Attach reviewed, authoritative source provenance to knowledge records through the project’s approved data-governance process, then expose that metadata through the API. Until then, keep the current unavailable guidance message and verified-rate-only calculator behavior.
