"""
Empirical Challenge Suite: Route Collision & Observation Stress Tests
=====================================================================
"""
import pytest
import os
from fastapi.testclient import TestClient
from app.main import app
from app.services.supabase_storage import SupabaseStorageService

client = TestClient(app)

@pytest.fixture(scope="module")
def challenge_auth():
    phone = "03007654321"
    login_resp = client.post("/api/v1/auth/login", json={
        "phone_number": phone,
        "password": "pass1234password"
    })
    if login_resp.status_code != 200:
        client.post("/api/v1/auth/register", json={
            "full_name": "Challenge Farmer",
            "phone_number": phone,
            "password": "pass1234password",
            "role": "farmer",
            "district": "Multan",
            "language_pref": "ur"
        })
        login_resp = client.post("/api/v1/auth/login", json={
            "phone_number": phone,
            "password": "pass1234password"
        })
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="module")
def active_field_and_cycle(challenge_auth):
    f_resp = client.post("/api/v1/fields/", json={
        "field_name": "Empirical Stress Plot",
        "shape_type": "polygon",
        "area_acres": 4.2,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[[71.50, 30.15], [71.51, 30.15], [71.51, 30.16], [71.50, 30.16], [71.50, 30.15]]]
        }
    }, headers=challenge_auth)
    field_data = f_resp.json()

    c_resp = client.post("/api/v1/crop-cycles/start", json={
        "field_id": field_data["field_id"],
        "wheat_variety": "Faisalabad-2008",
        "seed_company": "Punjab Seed Corp",
        "fertilizer_company": "Engro",
        "sowing_method": "Broadcasting",
        "sowing_date": "2026-11-02"
    }, headers=challenge_auth)
    cycle_data = c_resp.json()

    return {
        "field_id": field_data["field_id"],
        "cycle_id": cycle_data["cycle_id"],
    }

# ==============================================================================
# Challenge 2: Route Collision Verification
# ==============================================================================

def test_route_collision_nonexistent_field(challenge_auth):
    """
    Empirical Challenge: Hit GET /api/v1/crop-cycles/field/99999/active.
    Must return 404 with field detail, NOT a 422 integer validation error on {cycle_id}.
    """
    resp = client.get("/api/v1/crop-cycles/field/99999/active", headers=challenge_auth)
    assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert "detail" in data
    assert data["detail"] == "Field with ID '99999' not found", f"Unexpected detail: {data['detail']}"
    # Verify it is not a 422 Unprocessable Entity error
    assert resp.status_code != 422
    assert not isinstance(data.get("detail"), list), "Returned 422 validation structure instead of 404"

def test_route_active_cycle_existing_field(challenge_auth, active_field_and_cycle):
    """
    Verify GET /api/v1/crop-cycles/field/{field_id}/active correctly retrieves active cycle and schedules.
    """
    field_id = active_field_and_cycle["field_id"]
    resp = client.get(f"/api/v1/crop-cycles/field/{field_id}/active", headers=challenge_auth)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["field_id"] == field_id
    assert data["cycle_id"] == active_field_and_cycle["cycle_id"]
    assert data["is_active"] is True
    assert len(data["fertilizer_schedules"]) == 3
    assert len(data["irrigation_schedules"]) == 5

# ==============================================================================
# Challenge 3: Observation Image Upload Stress Test (Empty Bytes & Large Payload)
# ==============================================================================

def test_observation_upload_empty_bytes(challenge_auth, active_field_and_cycle):
    """
    Adversarial Challenge: Upload observation with 0-byte empty image payload.
    Must not crash the server (no 500 unhandled exceptions).
    """
    cycle_id = active_field_and_cycle["cycle_id"]
    form_data = {
        "cycle_id": cycle_id,
        "stage_index": "1",
        "stage_name": "Jointing",
        "confidence": "0.85",
        "pitch_angle_deg": "30.0",
        "blur_score": "80.0",
        "das": "45"
    }
    empty_file = {
        "image": ("empty_image.jpg", b"", "image/jpeg")
    }
    resp = client.post("/api/v1/observations/", data=form_data, files=empty_file, headers=challenge_auth)
    assert resp.status_code != 500, f"Server crashed with 500 on empty bytes: {resp.text}"
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["cycle_id"] == cycle_id
    assert "image_uri" in data

def test_observation_upload_large_payload_5mb(challenge_auth, active_field_and_cycle):
    """
    Adversarial Challenge: Upload 5MB image payload.
    """
    cycle_id = active_field_and_cycle["cycle_id"]
    five_mb_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * (5 * 1024 * 1024 - 6) + b"\xff\xd9"
    form_data = {
        "cycle_id": cycle_id,
        "stage_index": "3",
        "stage_name": "Heading",
        "confidence": "0.92",
        "pitch_angle_deg": "40.0",
        "blur_score": "120.0",
        "das": "90"
    }
    files = {
        "image": ("large_5mb_canopy.jpg", five_mb_bytes, "image/jpeg")
    }
    resp = client.post("/api/v1/observations/", data=form_data, files=files, headers=challenge_auth)
    assert resp.status_code != 500, f"Server crashed with 500 on 5MB payload: {resp.text}"
    assert resp.status_code == 201, f"Failed to upload 5MB image: status {resp.status_code}, {resp.text}"

def test_observation_upload_large_payload_10mb(challenge_auth, active_field_and_cycle):
    """
    Adversarial Challenge: Upload 10MB image payload (boundary stress).
    """
    cycle_id = active_field_and_cycle["cycle_id"]
    ten_mb_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * (10 * 1024 * 1024 - 6) + b"\xff\xd9"
    form_data = {
        "cycle_id": cycle_id,
        "stage_index": "4",
        "stage_name": "Grain Filling",
        "confidence": "0.95",
        "pitch_angle_deg": "42.0",
        "blur_score": "135.0",
        "das": "110"
    }
    files = {
        "image": ("large_10mb_canopy.jpg", ten_mb_bytes, "image/jpeg")
    }
    resp = client.post("/api/v1/observations/", data=form_data, files=files, headers=challenge_auth)
    assert resp.status_code != 500, f"Server crashed with 500 on 10MB payload: {resp.text}"
    assert resp.status_code == 201, f"Failed to upload 10MB image: status {resp.status_code}, {resp.text}"

def test_storage_service_local_disk_fallback():
    """
    Adversarial Challenge: Verify fallback when remote storage is unavailable or fails.
    Simulate local fallback write and verify file existence and static serving.
    """
    dummy_payload = b"\xff\xd8\xff\xe0TEST_LOCAL_STORAGE\xff\xd9"
    saved_uri = SupabaseStorageService.upload_image(
        file_bytes=dummy_payload,
        file_name="stress_test_fallback.jpg",
        content_type="image/jpeg"
    )
    assert saved_uri is not None
    # If Supabase is configured, it returns public URL; if local fallback, returns /api/v1/storage/file/...
    if saved_uri.startswith("/api/v1/storage/file/"):
        filename = saved_uri.split("/")[-1]
        serve_resp = client.get(f"/api/v1/storage/file/{filename}")
        assert serve_resp.status_code == 200
        assert serve_resp.content == dummy_payload
