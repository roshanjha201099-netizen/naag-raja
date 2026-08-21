import os
import io
import asyncio
from PIL import Image
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.init_db import init_db

def create_sample_snake_image_bytes():
    img = Image.new('RGB', (300, 300), color=(120, 90, 40))
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    return buf.getvalue()

async def run_system_tests():
    print("=" * 60)
    print("RUNNING NAAGRAKSHAK BACKEND ASYNC SYSTEM VERIFICATION")
    print("=" * 60)

    # Explicitly run DB initialization & seeding
    await init_db()

    # Initialize lifespan (DB tables & model warmup)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # 1. Health Endpoint
        res_health = await client.get("/api/v1/health")
        assert res_health.status_code == 200
        health_data = res_health.json()
        assert health_data["status"] in ["HEALTHY", "DEGRADED"]
        print("\n[SUCCESS] GET /api/v1/health Passed:", health_data)

        # 2. Species Endpoint
        res_species = await client.get("/api/v1/species")
        assert res_species.status_code == 200
        species_data = res_species.json()
        assert isinstance(species_data, list)
        assert len(species_data) > 0
        print(f"\n[SUCCESS] GET /api/v1/species Passed: Retrieved {len(species_data)} species records.")

        # 3. Species Detail Endpoint
        res_detail = await client.get("/api/v1/species/1")
        assert res_detail.status_code == 200
        detail_data = res_detail.json()
        assert detail_data["id"] == 1
        print(f"\n[SUCCESS] GET /api/v1/species/1 Passed: {detail_data['common_name']} ({detail_data['scientific_name']})")

        # 4. Medical Facilities Endpoint
        res_med = await client.get("/api/v1/medical-facilities?state=Bihar")
        assert res_med.status_code == 200
        med_data = res_med.json()
        assert isinstance(med_data, list)
        assert len(med_data) > 0
        print(f"\n[SUCCESS] GET /api/v1/medical-facilities Passed: Found {len(med_data)} ASV hospitals in Bihar.")

        # 5. Rescue Facilities Endpoint
        res_resc = await client.get("/api/v1/rescue")
        assert res_resc.status_code == 200
        resc_data = res_resc.json()
        assert isinstance(resc_data, list)
        print(f"\n[SUCCESS] GET /api/v1/rescue Passed: Found {len(resc_data)} rescue dispatch facilities.")

        # 6. Predict Endpoint
        img_bytes = create_sample_snake_image_bytes()
        files = {"image": ("test_snake.jpg", img_bytes, "image/jpeg")}
        data = {"intent": "SNAKE_ENCOUNTER", "state": "Bihar"}

        res_predict = await client.post("/api/v1/predict", files=files, data=data)
        assert res_predict.status_code == 200
        pred_json = res_predict.json()

        assert "request_id" in pred_json
        assert "snake_detected" in pred_json
        assert "predictions" in pred_json
        assert "safety" in pred_json
        assert "contextual_guidance" in pred_json
        assert "model_meta" in pred_json

        print("\n[SUCCESS] POST /api/v1/predict Passed!")
        print("Request ID:", pred_json["request_id"])
        print("Identification Status:", pred_json["identification_status"])
        print("Top Prediction:", pred_json["predictions"][0])
        print("Safety Level:", pred_json["safety"]["safety_level"])
        print("Safety Message:", pred_json["safety"]["safety_message"])

    print("\n[SUCCESS] ALL BACKEND SYSTEM VERIFICATIONS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(run_system_tests())
