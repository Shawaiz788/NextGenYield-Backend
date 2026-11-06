import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["database"] == "connected"

def test_auth_registration_and_login():
    # 1. Register a test farmer
    register_payload = {
        "full_name": "Farmer Test Khan",
        "phone_number": "03009988776",
        "password": "pass1234password",
        "role": "farmer",
        "district": "Faisalabad",
        "language_pref": "ur"
    }
    reg_resp = client.post("/api/v1/auth/register", json=register_payload)
    assert reg_resp.status_code in (201, 400)
    
    # 2. Login with registered phone & password
    login_payload = {
        "phone_number": "03009988776",
        "password": "pass1234password"
    }
    login_resp = client.post("/api/v1/auth/login", json=login_payload)
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # 3. Access /auth/me with Bearer token
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    user_data = me_resp.json()
    assert user_data["full_name"] == "Farmer Test Khan"

def test_field_and_crop_cycle_flow():
    # Login as test user
    login_resp = client.post("/api/v1/auth/login", json={
        "phone_number": "03009988776",
        "password": "pass1234password"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Demarcate a new field (GeoJSON)
    field_payload = {
        "field_name": "Chak 214 North Plot",
        "shape_type": "polygon",
        "area_acres": 5.5,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[[73.07, 31.41], [73.08, 31.41], [73.08, 31.42], [73.07, 31.42], [73.07, 31.41]]]
        }
    }
    f_resp = client.post("/api/v1/fields/", json=field_payload, headers=headers)
    assert f_resp.status_code == 201
    field_data = f_resp.json()
    field_id = field_data["field_id"]
    assert field_data["area_acres"] == 5.5

    # 2. Initialize a 140-day crop cycle on the field
    cycle_payload = {
        "field_id": field_id,
        "wheat_variety": "Akbar-2019",
        "seed_company": "Punjab Seed Corporation",
        "fertilizer_company": "Fauji Fertilizer Company (FFC)",
        "sowing_method": "Drill Sowing",
        "sowing_date": "2026-11-01"
    }
    c_resp = client.post("/api/v1/crop-cycles/start", json=cycle_payload, headers=headers)
    assert c_resp.status_code == 201
    cycle_data = c_resp.json()
    assert cycle_data["wheat_variety"] == "Akbar-2019"
    # Ensure schedules were automatically generated
    assert len(cycle_data["fertilizer_schedules"]) == 3
    assert len(cycle_data["irrigation_schedules"]) == 5

def test_advisory_rules():
    resp = client.get("/api/v1/advisory/rules")
    assert resp.status_code == 200
    rules = resp.json()
    assert len(rules) == 6  # 6 phenological wheat stages
    assert rules[2]["stage_name"] == "Booting"

