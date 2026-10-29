import asyncio
import time
import json
import httpx
from pathlib import Path

# Configuration – adjust if your backend runs on a different port/url
API_URL = "http://127.0.0.1:8000/api/upload"
TEST_IMAGE = Path(r"D:\PlantGuard-AI\datasets\plantdoc\test\Apple leaf\apple-leaf-14319997.jpg")

if not TEST_IMAGE.is_file():
    raise FileNotFoundError(f"Test image not found: {TEST_IMAGE}")

async def single_upload(session: httpx.AsyncClient):
    start_total = time.perf_counter()
    with open(TEST_IMAGE, "rb") as f:
        files = {"file": (TEST_IMAGE.name, f, "image/jpeg")}
        resp = await session.post(API_URL, files=files)
    elapsed = (time.perf_counter() - start_total) * 1000
    data = resp.json()
    return {"client_total_ms": elapsed, "server": data.get("stage_timings", {}), "response": data}

async def main():
    async with httpx.AsyncClient(timeout=30.0) as client:
        results = []
        for i in range(2):
            results.append(await single_upload(client))
        overlap = await asyncio.gather(
            single_upload(client),
            single_upload(client),
        )
        results.extend(overlap)
        print(json.dumps({"runs": results}, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
