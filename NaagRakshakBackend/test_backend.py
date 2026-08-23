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

        # 5.5 Location Geocoding Endpoint
        res_geo = await client.get("/api/v1/location/geocode?query=Lohna,+Madhubani,+Bihar")
        assert res_geo.status_code == 200
        geo_json = res_geo.json()
        assert geo_json["source"] == "MANUAL_GEOCODED"
        assert geo_json["status"] == "MANUAL"
        assert geo_json["latitude"] is not None
        assert geo_json["longitude"] is not None
        print(f"\n[SUCCESS] GET /api/v1/location/geocode Passed: Geocoded 'Lohna, Madhubani, Bihar' to Lat={geo_json['latitude']}, Lng={geo_json['longitude']} (Source: {geo_json['source']}, Status: {geo_json['status']})")

        # 6. Predict Endpoint Test (SNAKE_ENCOUNTER & Accurate Location)
        img_bytes = create_sample_snake_image_bytes()
        files = {"image": ("test_snake.jpg", img_bytes, "image/jpeg")}
        data = {"intent": "SNAKE_ENCOUNTER", "state": "Bihar", "user_lat": 26.1234, "user_lng": 86.4567, "user_accuracy": 1200}

        res_predict = await client.post("/api/v1/predict", files=files, data=data)
        assert res_predict.status_code == 200
        pred_json = res_predict.json()

        assert "request_id" in pred_json
        assert "snake_detected" in pred_json
        assert "detection_confidence" in pred_json
        assert "predictions" in pred_json
        assert "safety" in pred_json
        assert "location" in pred_json
        assert pred_json["location"]["status"] == "ACCURATE"
        assert pred_json["location"]["source"] == "GPS"

        print("\n[SUCCESS] POST /api/v1/predict (Accurate Location GPS <= 5km) Passed!")
        print("Location Status:", pred_json["location"]["status"])
        print("Location Source:", pred_json["location"]["source"])

        # 6.5 Predict Endpoint Test (Low Accuracy Location > 5km)
        data_low = {"intent": "SNAKE_ENCOUNTER", "state": "Bihar", "user_lat": 26.1234, "user_lng": 86.4567, "user_accuracy": 8500}
        res_low = await client.post("/api/v1/predict", files={"image": ("test_snake.jpg", img_bytes, "image/jpeg")}, data=data_low)
        assert res_low.status_code == 200
        low_json = res_low.json()
        assert low_json["location"]["status"] == "LOW_ACCURACY"
        print("\n[SUCCESS] POST /api/v1/predict (Low Accuracy GPS > 5km) Passed! Status:", low_json["location"]["status"])

        # 7. Predict Endpoint Test (SNAKE_BITE_EMERGENCY & Manual Location)
        data_bite = {"intent": "SNAKE_BITE_EMERGENCY", "state": "Bihar", "location_source": "MANUAL_GEOCODED"}
        res_bite = await client.post("/api/v1/predict", files={"image": ("test_snake.jpg", img_bytes, "image/jpeg")}, data=data_bite)
        assert res_bite.status_code == 200
        bite_json = res_bite.json()
        assert bite_json["safety"]["safety_level"] in ["CRITICAL", "HIGH", "CAUTION"]
        assert bite_json["location"]["status"] == "MANUAL"
        print("\n[SUCCESS] POST /api/v1/predict (Manual Geocoded Location) Passed!")

        # 8. Predict Endpoint Test (Non-Snake Image / NO_SNAKE_DETECTED)
        # Create a plain white 300x300 image (non-snake image)
        white_img = Image.new('RGB', (300, 300), color='white')
        w_buf = io.BytesIO()
        white_img.save(w_buf, format='JPEG')
        w_bytes = w_buf.getvalue()

        res_nonsnake = await client.post("/api/v1/predict", files={"image": ("blank.jpg", w_bytes, "image/jpeg")}, data={"intent": "SNAKE_ENCOUNTER", "state": "Bihar"})
        assert res_nonsnake.status_code == 200
        nonsnake_json = res_nonsnake.json()
        assert nonsnake_json["snake_detected"] is False
        assert nonsnake_json["identification_status"] == "NO_SNAKE_DETECTED"
        assert nonsnake_json["safety"]["safety_level"] == "SAFE"
        assert "YOU ARE SAFE" in nonsnake_json["safety"]["safety_message"]
        assert "Disclaimer" in nonsnake_json["safety"]["safety_message"]
        print("\n[SUCCESS] POST /api/v1/predict (Non-Snake Image NO_SNAKE_DETECTED -> SAFE + Disclaimer) Passed!")

    print("\n[SUCCESS] ALL 7 BACKEND SYSTEM VERIFICATION TESTS PASSED SUCCESSFULLY!")

    print("\n[SUCCESS] ALL BACKEND SYSTEM VERIFICATIONS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(run_system_tests())
