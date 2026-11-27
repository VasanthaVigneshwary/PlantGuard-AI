# Core Pipeline Deployment Checklist

- MISSING — Ship `efficientnet_v2_s_best.onnx.data` with the ONNX model using Git LFS or a deployment volume; production packaging is not verified.
- MISSING — Configure `DATABASE_URL` in the deployment secret store; do not copy the local `.env` file.
- MISSING — Configure explicit production `CORS_ORIGINS`; only localhost defaults are confirmed in source.
- READY — Local CPU inference works with ONNX Runtime `CPUExecutionProvider` and the model sidecar.
- MISSING — Verify target deployment migrations; this check only audited the reachable database contents.
- READY — Reachable database has unique disease records and required knowledge details for all 38 model classes.
- READY — Local root health endpoint is covered by the existing API tests; deployed health checks are not verified.
- MISSING — Verify deployed model/sidecar hashes and read access after packaging.
