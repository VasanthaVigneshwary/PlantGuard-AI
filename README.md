# Plant Guard AI

Plant Guard AI is an academic plant-leaf image classifier with a FastAPI backend, a PostgreSQL agricultural knowledge base, and a Next.js interface. It predicts one of 38 PlantVillage classes and can return database guidance for the predicted class. A prediction is a model output, not a confirmed diagnosis.

## Architecture and model

- Frontend: Next.js 16, React 19, TypeScript, Tailwind CSS.
- Backend: Python 3.12, FastAPI, ONNX Runtime.
- Database: PostgreSQL, configured with `DATABASE_URL`.
- Model: EfficientNetV2-S ONNX graph and its external `.onnx.data` tensor file, tracked with Git LFS.
- Model labels: `backend/ml/models/classes.json` in output-index order.

The active model files and class list match the [BiernyVR/crop-disease-classifier model card](https://huggingface.co/BiernyVR/crop-disease-classifier). The model card identifies the model as MIT-licensed and reports 99.89% validation accuracy on PlantVillage. That figure has not been reproduced in this project and is not a field-performance claim. See [backend/ml/models/README.md](backend/ml/models/README.md) for artifact and preprocessing details.

The model returns a raw softmax score. It is not calibrated confidence and does not reliably reject unsupported images. The interface labels the score accordingly and asks users to verify predictions against symptoms or qualified agricultural guidance.

## Supported model classes

The 38 classes cover Apple, Blueberry, Cherry, Corn (maize), Grape, Orange, Peach, Bell pepper, Potato, Raspberry, Soybean, Squash, Strawberry, and Tomato. Coverage includes healthy classes where present in the model. This is model-label coverage; it does not mean every disease or crop can be diagnosed reliably.

## Local setup

### Backend and PostgreSQL

1. Use Python 3.12 and create/configure the PostgreSQL database `plant_guard_ai`.
2. Copy `.env.example` to `.env`, then set a local `DATABASE_URL`. Set `CORS_ORIGINS` to the exact frontend origins, comma-separated. Do not use `*`.
3. Install backend dependencies from the repository root:

   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
   ```

4. Start the API from the repository root:

   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn main:app --app-dir backend --reload
   ```

The active local database was checked on October 23, 2026: 17 crop rows and unique mappings for all 38 model classes were present. All 38 disease detail lookups resolved. To initialize a **new, empty database**, review `database/schema.sql` first: it is a PostgreSQL dump, not a migration, and drops/recreates constraints. The seed script also updates existing knowledge records, so review its data and back up the database before using it on any populated database. Do not run it as a routine deployment step.

### Frontend

1. Copy `frontend/.env.example` to `frontend/.env.local`.
2. Set `NEXT_PUBLIC_API_URL` to the API origin, such as `http://localhost:8000`. Next.js embeds this public value at build time, so set the deployment value before building.
3. Install and run the frontend:

   ```powershell
   cd frontend
   npm ci
   npm run dev
   ```

For a production build, run `npm run build`. The project uses Next.js's webpack build option because the installed Turbopack path fails while starting its CSS worker in the verified Windows environment.

## Verification

From the repository root:

```powershell
.\.venv\Scripts\python.exe backend\test_model.py
.\.venv\Scripts\python.exe -m unittest backend.test_api_endpoints -v
.\.venv\Scripts\python.exe -m compileall -q backend
```

From `frontend/`:

```powershell
npm run build
npm run lint
```

The model smoke checks use two available images to verify loading, input/output shape, finite scores, class mapping, and invalid-image rejection. One image is the model-card Apple scab sample; neither image is an independent field-validation sample. The checks report no accuracy metric. Database-isolated API tests mock database writes; the local end-to-end verification separately exercised an actual upload, inference, PostgreSQL guidance lookup, prediction save, and history retrieval, then removed its test history row.

## Current behavior and limitations

- Image upload validates file content, limits uploads to 10 MB, rejects very large pixel dimensions, uses a generated temporary file, and removes that file after inference.
- The API retrieves disease details from PostgreSQL. When a class has no matching record, the response contains no invented disease guidance.
- Prediction history stores the raw score as a fraction in PostgreSQL and exposes the existing API field as a percentage. Uploaded image bytes are not retained.
- The local database has complete class-key coverage. That does not verify the scientific quality of every description or treatment entry.
- The current database contains 27 application-rate rows, but they lack both an explicit verification marker and a source URL. The application withholds those rates from the API and calculator until each rate has been reviewed and its record marked with `[verified]` plus an HTTPS source URL in its notes. No pesticide dosage should be inferred from the existing unverified rows.
- English and Tamil interface strings are available. Agricultural database entries are shown in Tamil only where a translation exists; untranslated technical material remains in its source language.
- The chatbot uses keyword matching and database content. It is not a general-purpose LLM, and microphone input or scheduled notifications are not implemented.
- Notifications show database records only. Empty notification history remains empty; no scheduler or delivery service is claimed.
- The area calculator only works when a verified application-rate record is available. It currently reports unavailable guidance for the unverified rates above.

## API routes

- `GET /` — API status.
- `GET /api/db-test` — PostgreSQL connectivity.
- `GET /api/crops`, `GET /api/diseases`, `GET /api/diseases/{id}` — knowledge-base lookup.
- `POST /api/upload` — image validation, ONNX inference, database lookup, and history persistence.
- `GET /api/history` — recent prediction history.
- `GET /api/notifications` — database notifications.
- `POST /api/chat` — retrieval-based plant-health responses.

## Demonstration checklist

1. Start PostgreSQL, the API, and the frontend; confirm `/api/db-test` succeeds.
2. Switch between English and Tamil.
3. Upload a clear leaf image and show the predicted class, raw model score disclaimer, and database-backed guidance.
4. Show that a missing knowledge-base entry does not receive fabricated symptoms or treatment details.
5. Confirm the history item appears when persistence succeeds; show the empty state when there are no records.
6. Try an invalid or corrupted image and show the retry message.
7. Point out that model classes come from PlantVillage and the app has not established independent field accuracy.
