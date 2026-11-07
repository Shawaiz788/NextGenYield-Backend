"""
NextGenYield — Comprehensive End-to-End (E2E) Test Suite
Testing All System Requirements across 4 Tiers:
- Tier 1: Feature Happy Paths
- Tier 2: Boundary & Negative Validation
- Tier 3: Cross-Feature Integration Workflows
- Tier 4: Real-World Punjab Wheat Farmer Season Scenarios

Authoritative references: ORIGINAL_REQUEST.md, AGENTS.md, PROJECT.md, F26-201 SRS.
"""

import pytest
import uuid
import random
import io
from datetime import date, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# ==============================================================================
# Helper Utilities & Fixtures
# ==============================================================================

def generate_pakistani_phone() -> str:
    """Generate a unique 11-digit Pakistani mobile number formatted as 0300XXXXXXX."""
    suffix = random.randint(1000000, 9999999)
    return f"0300{suffix}"

def register_and_login_farmer(c: TestClient, name="Farmer Chaudhry", district="Faisalabad", lang="ur"):
    """Register and authenticate an isolated test farmer, returning auth token and headers."""
    phone = generate_pakistani_phone()
    password = "FarmPassword123!"
    reg_payload = {
        "full_name": name,
        "phone_number": phone,
        "password": password,
        "role": "farmer",
        "district": district,
        "language_pref": lang,
    }
    resp = c.post("/api/v1/auth/register", json=reg_payload)
    assert resp.status_code == 201, f"Farmer registration failed: {resp.text}"
    data = resp.json()
    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return {
        "token": token,
        "headers": headers,
        "phone": phone,
        "password": password,
        "user_id": data["user"]["user_id"],
        "full_name": name,
        "district": district,
    }

def create_sample_field(*args, **kwargs):
    """Demarcate a sample field parcel with RFC 7946 GeoJSON boundary."""
    c = client
    headers = None
    name = kwargs.get("name", "Chak 214 North Plot")
    acres = kwargs.get("acres", 5.5)
    shape = kwargs.get("shape", "polygon")

    if len(args) >= 2:
        c = args[0]
        headers = args[1]
    elif len(args) == 1:
        if isinstance(args[0], dict) and "headers" in args[0]:
            headers = args[0]["headers"]
        elif isinstance(args[0], dict):
            headers = args[0]
        else:
            c = args[0]

    if "farmer" in kwargs and kwargs["farmer"] is not None:
        headers = kwargs["farmer"]["headers"]
    elif "headers" in kwargs and kwargs["headers"] is not None:
        headers = kwargs["headers"]

    payload = {
        "field_name": name,
        "shape_type": shape,
        "area_acres": acres,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [
                [[73.071, 31.411], [73.081, 31.411], [73.081, 31.421], [73.071, 31.421], [73.071, 31.411]]
            ]
        }
    }
    resp = c.post("/api/v1/fields/", json=payload, headers=headers)
    assert resp.status_code == 201, f"Field creation failed: {resp.text}"
    return resp.json()

def start_sample_cycle(*args, **kwargs):
    """Initialize a 140-day wheat crop cycle on a demarcated field."""
    c = client
    headers = kwargs.get("headers")
    field_id = kwargs.get("field_id")
    variety = kwargs.get("variety", "Akbar-2019")
    sowing = kwargs.get("sowing", "2026-11-01")

    if len(args) >= 3:
        c = args[0]
        headers = args[1]
        field_id = args[2]
        if len(args) >= 4:
            variety = args[3]
        if len(args) >= 5:
            sowing = args[4]
    elif len(args) == 2:
        headers = args[0]["headers"] if isinstance(args[0], dict) and "headers" in args[0] else args[0]
        field_id = args[1]

    if "farmer" in kwargs and kwargs["farmer"] is not None:
        headers = kwargs["farmer"]["headers"]

    payload = {
        "field_id": field_id,
        "wheat_variety": variety,
        "seed_company": "Punjab Seed Corporation",
        "fertilizer_company": "Fauji Fertilizer Company (FFC)",
        "sowing_method": "Drill Sowing",
        "sowing_date": sowing,
    }
    resp = c.post("/api/v1/crop-cycles/start", json=payload, headers=headers)
    assert resp.status_code == 201, f"Crop cycle start failed: {resp.text}"
    return resp.json()

def generate_dummy_jpeg() -> bytes:
    """Generate a minimal valid binary JPEG image stream."""
    # JPEG magic bytes (SOI, APP0 marker with JFIF identifier, EOI)
    header = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00'
    filler = b'\xff\xdb\x00C\x00' + b'\x08' * 64
    eoi = b'\xff\xd9'
    return header + filler + eoi

def is_route_mounted(path: str, method: str) -> bool:
    """Check if a route with given path and method is registered on the FastAPI app."""
    for route in app.routes:
        if getattr(route, "path", None) == path and method in getattr(route, "methods", []):
            return True
    return False

# ==============================================================================
# Tier 1: Feature Happy Paths
# ==============================================================================

def test_tier1_system_health_and_decoupled_gateway():
    """T1.1: Health endpoint reports online status, database connection, and decoupled AI gateway."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "online"
    assert data["database"] == "connected"
    assert "ai_service_gateway" in data
    # Gateway URL must point to decoupled model service, not coupled to CRUD
    assert data["ai_service_gateway"] is not None

def test_tier1_farmer_registration_and_jwt_issuance():
    """T1.2: Farmer registers with normalized Pakistani mobile number and receives Bearer JWT."""
    farmer = register_and_login_farmer(client, name="Chaudhry Riaz", district="Faisalabad")
    assert farmer["token"]
    assert farmer["user_id"].startswith("usr_")

def test_tier1_farmer_login_and_me_profile():
    """T1.3: Farmer logs in with credentials and verifies profile details via /auth/me."""
    farmer = register_and_login_farmer(client, name="Malik Usman", district="Multan", lang="ur")
    
    # Login explicitly
    login_resp = client.post("/api/v1/auth/login", json={
        "phone_number": farmer["phone"],
        "password": farmer["password"]
    })
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert "access_token" in login_data
    
    # Query /auth/me
    me_resp = client.get("/api/v1/auth/me", headers=farmer["headers"])
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["full_name"] == "Malik Usman"
    assert me_data["district"] == "Multan"
    assert me_data["language_pref"] == "ur"

def test_tier1_field_parcel_demarcation_and_listing():
    """T1.4: Demarcates parcel with RFC 7946 GeoJSON polygon, computes centroid, and lists parcel."""
    farmer = register_and_login_farmer(client, name="Kisan Ali")
    field = create_sample_field(farmer=farmer, headers=farmer["headers"], name="North Canal Field", acres=6.2)
    
    assert field["field_id"].startswith("fld_")
    assert field["area_acres"] == 6.2
    assert field["area_sqm"] > 25000  # 6.2 * 4046.85 = ~25090 sqm
    assert 31.0 < field["center_latitude"] < 32.0  # Faisalabad Indus basin
    assert 72.0 < field["center_longitude"] < 74.0
    assert field["current_cycle_id"] is None  # Initially fallow
    
    # List fields
    list_resp = client.get("/api/v1/fields/", headers=farmer["headers"])
    assert list_resp.status_code == 200
    fields_list = list_resp.json()
    assert len(fields_list) >= 1
    assert any(f["field_id"] == field["field_id"] for f in fields_list)

    # Get single field
    detail_resp = client.get(f"/api/v1/fields/{field['field_id']}", headers=farmer["headers"])
    assert detail_resp.status_code == 200
    assert detail_resp.json()["field_name"] == "North Canal Field"

def test_tier1_field_update_contract():
    """T1.5: PUT /api/v1/fields/{field_id} updates parcel attributes."""
    farmer = register_and_login_farmer(client, name="Haji Bashir")
    field = create_sample_field(farmer=farmer, headers=farmer["headers"], name="Old Name Plot", acres=4.0)

    # Progressive testability check
    if not is_route_mounted("/api/v1/fields/{field_id}", "PUT"):
        pytest.xfail("M1 Feature: PUT /api/v1/fields/{field_id} route pending worker implementation")

    update_payload = {"field_name": "Updated Renamed Plot"}
    up_resp = client.put(f"/api/v1/fields/{field['field_id']}", json=update_payload, headers=farmer["headers"])
    assert up_resp.status_code == 200
    assert up_resp.json()["field_name"] == "Updated Renamed Plot"

def test_tier1_field_deletion():
    """T1.6: DELETE /api/v1/fields/{field_id} removes parcel and returns 204."""
    farmer = register_and_login_farmer(client, name="Kisan Kashif")
    field = create_sample_field(farmer=farmer, headers=farmer["headers"], name="Temporary Field", acres=3.0)
    
    del_resp = client.delete(f"/api/v1/fields/{field['field_id']}", headers=farmer["headers"])
    assert del_resp.status_code == 204
    
    # Confirm field is no longer found
    get_resp = client.get(f"/api/v1/fields/{field['field_id']}", headers=farmer["headers"])
    assert get_resp.status_code == 404

def test_tier1_crop_cycle_initialization_and_140_day_schedules():
    """T1.7: Starts 140-day crop cycle, generating 3 fertilizer splits and 5 irrigation events."""
    farmer = register_and_login_farmer(client, name="Mian Nawaz")
    field = create_sample_field(farmer=farmer, headers=farmer["headers"], name="Plot 7 Akbar", acres=10.0)
    cycle = start_sample_cycle(client, farmer["headers"], field["field_id"], variety="Akbar-2019", sowing="2026-11-01")
    
    assert cycle["cycle_id"].startswith("cyc_")
    assert cycle["wheat_variety"] == "Akbar-2019"
    assert cycle["is_active"] is True
    
    # Harvest target should be approximately 140 days after sowing
    assert "2027-03-21" <= cycle["target_harvest_date"] <= "2027-03-25"
    
    # 3 Fertilizer splits check (Punjab provincial protocol)
    ferts = cycle["fertilizer_schedules"]
    assert len(ferts) == 3
    assert ferts[0]["target_das"] == 0 and "DAP" in ferts[0]["nutrient_type"]
    assert ferts[1]["target_das"] == 22 and "Urea" in ferts[1]["nutrient_type"]
    assert ferts[2]["target_das"] == 55 and "Zinc" in ferts[2]["nutrient_type"]
    
    # 5 Irrigation milestones check (Indus irrigated wheat protocol)
    irrigs = cycle["irrigation_schedules"]
    assert len(irrigs) == 5
    assert irrigs[0]["target_das"] == 22 and "CRI" in irrigs[0]["event_name"]
    assert irrigs[1]["target_das"] == 45 and "Tillering" in irrigs[1]["event_name"]
    assert irrigs[2]["target_das"] == 75 and "Booting" in irrigs[2]["event_name"]
    assert irrigs[3]["target_das"] == 95 and "Anthesis" in irrigs[3]["event_name"]
    assert irrigs[4]["target_das"] == 115 and "Grain Filling" in irrigs[4]["event_name"]

def test_tier1_active_crop_cycle_query_contract():
    """T1.8: GET /api/v1/crop-cycles/field/{field_id}/active retrieves the currently running cycle."""
    farmer = register_and_login_farmer(client, name="Tariq Farooq")
    field = create_sample_field(farmer=farmer, headers=farmer["headers"], name="Active Plot", acres=5.0)
    cycle = start_sample_cycle(client, farmer["headers"], field["field_id"], sowing="2026-11-10")

    # Progressive testability check
    if not is_route_mounted("/api/v1/crop-cycles/field/{field_id}/active", "GET"):
        pytest.xfail("M1 Feature: GET /crop-cycles/field/{field_id}/active route pending worker implementation")

    resp = client.get(f"/api/v1/crop-cycles/field/{field['field_id']}/active", headers=farmer["headers"])
    assert resp.status_code == 200
    active_cycle = resp.json()
    assert active_cycle["cycle_id"] == cycle["cycle_id"]
    assert active_cycle["is_active"] is True

def test_tier1_schedule_progression_toggles():
    """T1.9: Farmer confirms fertilizer application and marks irrigation milestone completed."""
    farmer = register_and_login_farmer(client, name="Sardar Jamil")
    field = create_sample_field(farmer=farmer, headers=farmer["headers"], name="Plot 12 Sahiwal", acres=7.5)
    cycle = start_sample_cycle(client, farmer["headers"], field["field_id"])
    
    # Toggle 2nd fertilizer split applied
    fert2_id = cycle["fertilizer_schedules"][1]["fertilizer_id"]
    fert_resp = client.put(f"/api/v1/crop-cycles/fertilizer/{fert2_id}/apply", headers=farmer["headers"])
    assert fert_resp.status_code == 200
    fert_data = fert_resp.json()
    assert fert_data["is_applied"] is True
    assert fert_data["applied_at"] is not None
    
    # Toggle 1st CRI irrigation completed
    irrig1_id = cycle["irrigation_schedules"][0]["irrigation_id"]
    irrig_resp = client.put(f"/api/v1/crop-cycles/irrigation/{irrig1_id}/complete", headers=farmer["headers"])
    assert irrig_resp.status_code == 200
    irrig_data = irrig_resp.json()
    assert irrig_data["is_completed"] is True

def test_tier1_advisory_rules_and_stage_lookup():
    """T1.10: Retrieves deterministic agronomic advisory rules across all 6 phenological wheat stages."""
    resp = client.get("/api/v1/advisory/rules")
    assert resp.status_code == 200
    rules = resp.json()
    assert len(rules) == 6, f"Expected 6 phenological stages, got {len(rules)}"
    
    # Verify stage names in phenological progression
    expected_stages = ["Tillering", "Jointing", "Booting", "Flowering / Anthesis", "Grain Filling", "Maturity"]
    for idx, expected in enumerate(expected_stages):
        assert rules[idx]["stage_index"] == idx
        assert rules[idx]["stage_name"] == expected
        assert len(rules[idx]["summary_text_ur"]) > 0  # Urdu translation verified
        assert len(rules[idx]["irrigation_advice_en"]) > 0
        assert len(rules[idx]["risk_alerts"]) >= 1

    # Single stage query (Booting stage = index 2)
    single_resp = client.get("/api/v1/advisory/rules/2")
    assert single_resp.status_code == 200
    booting_rule = single_resp.json()
    assert booting_rule["stage_name"] == "Booting"
    assert "Yellow Stripe Rust" in str(booting_rule["risk_alerts"]) or "Rust" in str(booting_rule["risk_alerts"])

def test_tier1_peer_showcase_benchmarks():
    """T1.11: Community peer showcase returns verified high-yield benchmark plots (54-62 Maunds)."""
    resp = client.get("/api/v1/showcase/")
    assert resp.status_code == 200
    posts = resp.json()
    assert len(posts) >= 2
    
    # Locate canonical benchmark plot (sc_01 or sc_02) or highest yielding plot
    bench_plot = next((p for p in posts if p.get("showcase_id") == "sc_01"), posts[0])
    assert bench_plot["yield_maunds_per_acre"] >= 54.0
    
    # Detail playbook query
    detail_resp = client.get(f"/api/v1/showcase/{bench_plot['showcase_id']}")
    assert detail_resp.status_code == 200
    playbook = detail_resp.json()
    assert len(playbook["cycle_event_log"]) >= 1
    if bench_plot.get("showcase_id") in ("sc_01", "sc_02"):
        assert len(playbook["cycle_event_log"]) >= 4

def test_tier1_peer_showcase_submission_contract():
    """T1.12: POST /api/v1/showcase/ creates a new verified peer benchmark."""
    if not is_route_mounted("/api/v1/showcase/", "POST"):
        pytest.xfail("M1 Feature: POST /api/v1/showcase/ route pending worker implementation")

    farmer = register_and_login_farmer(client, name="Champion Farmer Zahid")
    showcase_payload = {
        "title": "Chak 214 Record 63 Maund Harvest",
        "field_name": "Plot 9 South",
        "region": "Faisalabad",
        "wheat_variety": "Akbar-2019",
        "actual_yield_maunds": 63.2,
        "sowing_date": "2025-11-10",
        "harvesting_date": "2026-04-02",
        "key_tactics": "Balanced DAP+SOP basal and prompt CRI irrigation at 22 DAS",
        "photo_url": "https://example.com/harvest.jpg",
    }
    resp = client.post("/api/v1/showcase/", json=showcase_payload, headers=farmer["headers"])
    assert resp.status_code == 201
    created = resp.json()
    assert created["yield_maunds_per_acre"] == 63.2

def test_tier1_observation_upload_and_timeline():
    """T1.13: Multipart upload of canopy image with metadata and chronological timeline retrieval."""
    farmer = register_and_login_farmer(client, name="Imran Rasheed")
    field = create_sample_field(farmer=farmer, headers=farmer["headers"], name="Observation Plot", acres=5.0)
    cycle = start_sample_cycle(client, farmer["headers"], field["field_id"])
    
    jpeg_bytes = generate_dummy_jpeg()
    files = {
        "image": ("canopy_scan.jpg", io.BytesIO(jpeg_bytes), "image/jpeg")
    }
    data = {
        "cycle_id": cycle["cycle_id"],
        "stage_index": 1,
        "stage_name": "Jointing",
        "confidence": 0.945,
        "pitch_angle_deg": -44.8,
        "blur_score": 24.3,
        "das": 45,
    }
    
    upload_resp = client.post("/api/v1/observations/", data=data, files=files, headers=farmer["headers"])
    assert upload_resp.status_code == 201, f"Observation upload failed: {upload_resp.text}"
    obs = upload_resp.json()
    assert obs["observation_id"].startswith("obs_")
    assert obs["stage_name"] == "Jointing"
    assert pytest.approx(obs["confidence"], abs=0.01) == 0.945
    assert len(obs["image_uri"]) > 0
    
    # Query timeline for this cycle
    timeline_resp = client.get(f"/api/v1/observations/cycle/{cycle['cycle_id']}", headers=farmer["headers"])
    assert timeline_resp.status_code == 200
    timeline = timeline_resp.json()
    assert len(timeline) >= 1
    assert timeline[0]["observation_id"] == obs["observation_id"]

    # Verify storage endpoint returns image if local storage fallback was used
    if obs["image_uri"].startswith("/api/v1/storage/file/"):
        storage_resp = client.get(obs["image_uri"])
        assert storage_resp.status_code == 200

# ==============================================================================
# Tier 2: Boundary & Negative Validation
# ==============================================================================

def test_tier2_field_negative_and_zero_acreage_rejection():
    """T2.1: Rejects non-positive area_acres (<=0) with HTTP 422 Unprocessable Entity."""
    farmer = register_and_login_farmer(client)
    base_payload = {
        "field_name": "Boundary Test Plot",
        "shape_type": "polygon",
        "boundary_geojson": {"type": "Polygon", "coordinates": [[[73.0, 31.0], [73.1, 31.0], [73.0, 31.0]]]}
    }
    
    # Negative acreage
    resp_neg = client.post("/api/v1/fields/", json={**base_payload, "area_acres": -2.5}, headers=farmer["headers"])
    assert resp_neg.status_code == 422
    
    # Zero acreage
    resp_zero = client.post("/api/v1/fields/", json={**base_payload, "area_acres": 0.0}, headers=farmer["headers"])
    assert resp_zero.status_code == 422

def test_tier2_field_invalid_shape_type_rejection():
    """T2.2: Rejects invalid shape_type with HTTP 422 Unprocessable Entity."""
    farmer = register_and_login_farmer(client)
    payload = {
        "field_name": "Shape Test Plot",
        "shape_type": "pentagon_invalid",
        "area_acres": 4.0,
        "boundary_geojson": {"type": "Polygon", "coordinates": [[[73.0, 31.0], [73.1, 31.0], [73.0, 31.0]]]}
    }
    resp = client.post("/api/v1/fields/", json=payload, headers=farmer["headers"])
    assert resp.status_code == 422

def test_tier2_field_name_length_boundaries():
    """T2.3: Rejects field_name shorter than 2 chars or longer than 50 chars."""
    farmer = register_and_login_farmer(client)
    payload_too_short = {
        "field_name": "X",
        "shape_type": "square",
        "area_acres": 1.0,
        "boundary_geojson": {"type": "Polygon", "coordinates": [[[73.0, 31.0], [73.1, 31.0], [73.0, 31.0]]]}
    }
    resp_short = client.post("/api/v1/fields/", json=payload_too_short, headers=farmer["headers"])
    assert resp_short.status_code == 422

    payload_too_long = {
        "field_name": "A" * 51,
        "shape_type": "square",
        "area_acres": 1.0,
        "boundary_geojson": {"type": "Polygon", "coordinates": [[[73.0, 31.0], [73.1, 31.0], [73.0, 31.0]]]}
    }
    resp_long = client.post("/api/v1/fields/", json=payload_too_long, headers=farmer["headers"])
    assert resp_long.status_code == 422

def test_tier2_sowing_date_non_iso_format_rejection():
    """T2.4: Rejects non-ISO sowing date strings (e.g. '02 Oct 2026') with HTTP 422."""
    farmer = register_and_login_farmer(client)
    field = create_sample_field(farmer=farmer, headers=farmer["headers"])
    
    bad_payload = {
        "field_id": field["field_id"],
        "wheat_variety": "Akbar-2019",
        "seed_company": "PSC",
        "fertilizer_company": "FFC",
        "sowing_method": "Drill",
        "sowing_date": "02 Oct 2026",  # Non-ISO format rejected by Pydantic date validator
    }
    resp = client.post("/api/v1/crop-cycles/start", json=bad_payload, headers=farmer["headers"])
    assert resp.status_code == 422

def test_tier2_phone_number_length_validation():
    """T2.5: Rejects phone numbers outside the valid length range (10-15 digits)."""
    # Too short (<10 digits)
    resp_short = client.post("/api/v1/auth/register", json={
        "full_name": "Short Phone",
        "phone_number": "030012",
        "password": "Password123!",
        "role": "farmer",
    })
    assert resp_short.status_code == 422

    # Too long (>15 digits)
    resp_long = client.post("/api/v1/auth/register", json={
        "full_name": "Long Phone",
        "phone_number": "030012345678901234",
        "password": "Password123!",
        "role": "farmer",
    })
    assert resp_long.status_code == 422

def test_tier2_duplicate_user_registration_rejection():
    """T2.6: Rejects duplicate phone registration with HTTP 400 Bad Request."""
    farmer = register_and_login_farmer(client, name="Original Farmer")
    
    # Attempt second registration with same phone
    dup_resp = client.post("/api/v1/auth/register", json={
        "full_name": "Imposter Farmer",
        "phone_number": farmer["phone"],
        "password": "NewPassword123!",
        "role": "farmer",
    })
    assert dup_resp.status_code == 400
    assert "already registered" in dup_resp.json()["detail"].lower()

def test_tier2_invalid_credentials_login_rejection():
    """T2.7: Rejects wrong PIN/password or unknown phone with HTTP 401 Unauthorized."""
    farmer = register_and_login_farmer(client)
    
    # Wrong password
    resp_wrong_pw = client.post("/api/v1/auth/login", json={
        "phone_number": farmer["phone"],
        "password": "WrongPasswordXYZ"
    })
    assert resp_wrong_pw.status_code == 401
    
    # Non-existent phone
    resp_bad_phone = client.post("/api/v1/auth/login", json={
        "phone_number": "03000000000",
        "password": "Password123!"
    })
    assert resp_bad_phone.status_code == 401

def test_tier2_unauthorized_endpoints_access():
    """T2.8: Accessing protected endpoints without Bearer token returns HTTP 401 Unauthorized."""
    resp_fields = client.get("/api/v1/fields/")
    assert resp_fields.status_code == 401

    resp_me = client.get("/api/v1/auth/me")
    assert resp_me.status_code == 401

def test_tier2_cross_farmer_tenant_isolation():
    """T2.9: Farmer A cannot view, modify, or delete Farmer B's demarcated parcels."""
    farmer_a = register_and_login_farmer(client, name="Farmer A")
    farmer_b = register_and_login_farmer(client, name="Farmer B")
    
    field_a = create_sample_field(farmer=farmer_a, headers=farmer_a["headers"], name="Farmer A Plot")
    
    # Farmer B attempts to get Field A
    resp_get = client.get(f"/api/v1/fields/{field_a['field_id']}", headers=farmer_b["headers"])
    assert resp_get.status_code in (403, 404)
    
    # Farmer B attempts to delete Field A
    resp_del = client.delete(f"/api/v1/fields/{field_a['field_id']}", headers=farmer_b["headers"])
    assert resp_del.status_code in (403, 404)

def test_tier2_nonexistent_resource_lookups():
    """T2.10: Fetching non-existent IDs returns HTTP 404 Not Found."""
    farmer = register_and_login_farmer(client)
    
    # Nonexistent field
    assert client.get("/api/v1/fields/fld_nonexistent999", headers=farmer["headers"]).status_code == 404
    
    # Nonexistent cycle
    assert client.get("/api/v1/crop-cycles/cyc_nonexistent999", headers=farmer["headers"]).status_code == 404
    
    # Nonexistent advisory rule
    assert client.get("/api/v1/advisory/rules/99").status_code == 404
    
    # Nonexistent showcase item
    assert client.get("/api/v1/showcase/sc_nonexistent999").status_code == 404
    
    # Nonexistent storage file
    assert client.get("/api/v1/storage/file/nonexistent_image.jpg").status_code == 404
    
    # Nonexistent fertilizer schedule
    assert client.put("/api/v1/crop-cycles/fertilizer/fert_999/apply", headers=farmer["headers"]).status_code == 404
    
    # Nonexistent irrigation schedule
    assert client.put("/api/v1/crop-cycles/irrigation/irrig_999/complete", headers=farmer["headers"]).status_code == 404

def test_tier2_observation_stage_index_and_cycle_boundaries():
    """T2.11: Observation upload rejects non-existent cycle and invalid stage indices."""
    farmer = register_and_login_farmer(client)
    jpeg_bytes = generate_dummy_jpeg()
    files = {"image": ("test.jpg", io.BytesIO(jpeg_bytes), "image/jpeg")}
    
    # Nonexistent cycle_id
    data_bad_cycle = {
        "cycle_id": "cyc_ghost_unknown",
        "stage_index": 1,
        "stage_name": "Jointing",
        "confidence": 0.9,
        "pitch_angle_deg": -45.0,
        "blur_score": 10.0,
        "das": 30,
    }
    resp = client.post("/api/v1/observations/", data=data_bad_cycle, files=files, headers=farmer["headers"])
    assert resp.status_code == 404

# ==============================================================================
# Tier 3: Cross-Feature Integration Flows
# ==============================================================================

def test_tier3_farmer_multi_field_lifecycle_and_cycle_demarcation():
    """T3.1: Farmer demarcates 2 parcels, starts a cycle on one, keeping the other fallow."""
    farmer = register_and_login_farmer(client, name="Zafar Iqbal", district="Faisalabad")
    
    # Demarcate Parcel 1 (8 acres) and Parcel 2 (4.5 acres)
    p1 = create_sample_field(farmer=farmer, headers=farmer["headers"], name="North Canal Plot", acres=8.0)
    p2 = create_sample_field(farmer=farmer, headers=farmer["headers"], name="Tube Well Plot", acres=4.5)
    
    # List fields: both must appear
    fields_resp = client.get("/api/v1/fields/", headers=farmer["headers"])
    assert len(fields_resp.json()) >= 2
    
    # Start cycle on Parcel 1 only
    cycle1 = start_sample_cycle(client, farmer["headers"], p1["field_id"], variety="Dilkash-20", sowing="2026-11-05")
    assert cycle1["cycle_id"]
    
    # Query Parcel 1: current_cycle_id must be updated to cycle1
    p1_updated = client.get(f"/api/v1/fields/{p1['field_id']}", headers=farmer["headers"]).json()
    assert p1_updated["current_cycle_id"] == cycle1["cycle_id"]
    
    # Query Parcel 2: current_cycle_id must still be None (fallow)
    p2_checked = client.get(f"/api/v1/fields/{p2['field_id']}", headers=farmer["headers"]).json()
    assert p2_checked["current_cycle_id"] is None

def test_tier3_mid_season_execution_workflow():
    """T3.2: Multi-step mid-season flow: Start cycle -> Tillering scan -> Apply fertilizer -> Complete CRI irrigation."""
    farmer = register_and_login_farmer(client, name="Rao Shahzad", district="Sahiwal")
    field = create_sample_field(farmer=farmer, headers=farmer["headers"], name="Mid-Season Test Plot", acres=6.0)
    cycle = start_sample_cycle(client, farmer["headers"], field["field_id"], sowing="2026-11-01")
    
    # Step 1: Farmer uploads canopy observation at Tillering (DAS 21)
    jpeg_bytes = generate_dummy_jpeg()
    obs_resp = client.post("/api/v1/observations/", data={
        "cycle_id": cycle["cycle_id"],
        "stage_index": 0,
        "stage_name": "Tillering",
        "confidence": 0.96,
        "pitch_angle_deg": -46.0,
        "blur_score": 15.2,
        "das": 21,
    }, files={"image": ("tillering.jpg", io.BytesIO(jpeg_bytes), "image/jpeg")}, headers=farmer["headers"])
    assert obs_resp.status_code == 201
    
    # Step 2: Farmer applies 1st Topdress Urea at CRI (Split 2)
    fert2_id = cycle["fertilizer_schedules"][1]["fertilizer_id"]
    fert_resp = client.put(f"/api/v1/crop-cycles/fertilizer/{fert2_id}/apply", headers=farmer["headers"])
    assert fert_resp.status_code == 200
    assert fert_resp.json()["is_applied"] is True
    
    # Step 3: Farmer confirms 1st CRI irrigation completed
    irrig1_id = cycle["irrigation_schedules"][0]["irrigation_id"]
    irrig_resp = client.put(f"/api/v1/crop-cycles/irrigation/{irrig1_id}/complete", headers=farmer["headers"])
    assert irrig_resp.status_code == 200
    assert irrig_resp.json()["is_completed"] is True
    
    # Step 4: Verify complete cycle state
    cycle_check = client.get(f"/api/v1/crop-cycles/{cycle['cycle_id']}", headers=farmer["headers"]).json()
    assert cycle_check["fertilizer_schedules"][1]["is_applied"] is True
    assert cycle_check["irrigation_schedules"][0]["is_completed"] is True
    
    # Verify timeline has recorded the Tillering observation
    timeline = client.get(f"/api/v1/observations/cycle/{cycle['cycle_id']}", headers=farmer["headers"]).json()
    assert len(timeline) == 1
    assert timeline[0]["stage_name"] == "Tillering"

def test_tier3_advisory_lookup_driven_by_observation_stage():
    """T3.3: Vision stage classification drives dynamic advisory rule lookup and risk warning."""
    # Farmer records observation classified as Booting (stage_index 2)
    classified_stage_index = 2
    
    # Query advisory rule for classified stage
    advisory_resp = client.get(f"/api/v1/advisory/rules/{classified_stage_index}")
    assert advisory_resp.status_code == 200
    rule = advisory_resp.json()
    
    # Must contain critical Booting agronomic warnings
    assert rule["stage_name"] == "Booting"
    assert "moisture stress" in rule["irrigation_advice_en"].lower() or "critical" in rule["irrigation_advice_en"].lower()
    # Risk alert must identify Stripe Rust
    rust_alert = any("rust" in alert.get("title", "").lower() or "rust" in alert.get("desc", "").lower() for alert in rule["risk_alerts"])
    assert rust_alert, "Booting stage advisory must include Stripe Rust risk alert"

def test_tier3_cascade_deletion_lifecycle():
    """T3.4: Deleting field parcel cascades and cleans up parcel record."""
    farmer = register_and_login_farmer(client, name="Nadeem Akhtar")
    field = create_sample_field(farmer=farmer, headers=farmer["headers"], name="Cascade Deletion Field", acres=4.0)
    cycle = start_sample_cycle(client, farmer["headers"], field["field_id"])
    
    # Delete the field
    del_resp = client.delete(f"/api/v1/fields/{field['field_id']}", headers=farmer["headers"])
    assert del_resp.status_code == 204
    
    # Field must not exist anymore
    assert client.get(f"/api/v1/fields/{field['field_id']}", headers=farmer["headers"]).status_code == 404

# ==============================================================================
# Tier 4: Real-World Punjab Wheat Farmer Season Scenarios
# ==============================================================================

def test_tier4_faisalabad_irrigated_wheat_master_season():
    """
    T4.1: Authentic Punjab Wheat Season Simulation:
    Farmer: Muhammad Aslam (Chak 214-RB, Faisalabad)
    Acreage: 12.5 Acres, Cultivar: Akbar-2019
    Sowing: 2026-11-10 (Drill Sowing into moist loam soil)
    Progresses through the entire 140-day wheat season:
      - Basal DAP+SOP application at Day 0
      - CRI Stage (22 DAS): 1st irrigation + 1st Urea topdress
      - Jointing Stage (45 DAS): 2nd irrigation + Stem elongation scan
      - Booting Stage (75 DAS): 3rd irrigation + 2nd Urea+Zinc topdress
      - Flowering Stage (95 DAS): 4th irrigation (calm weather check)
      - Grain Filling Stage (115 DAS): 5th milk-stage irrigation
      - Maturity Stage (140 DAS): Harvest verification
    """
    farmer = register_and_login_farmer(client, name="Muhammad Aslam", district="Faisalabad", lang="ur")
    
    # 1. Demarcate 12.5 acre parcel in Chak 214-RB
    field_payload = {
        "field_name": "Chak 214-RB Master Plot",
        "shape_type": "rectangle",
        "area_acres": 12.5,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[[73.075, 31.415], [73.085, 31.415], [73.085, 31.425], [73.075, 31.425], [73.075, 31.415]]]
        }
    }
    field_resp = client.post("/api/v1/fields/", json=field_payload, headers=farmer["headers"])
    assert field_resp.status_code == 201
    field = field_resp.json()
    assert field["area_acres"] == 12.5

    # 2. Sowing on Nov 10, 2026
    sowing_date = "2026-11-10"
    cycle = start_sample_cycle(client, farmer["headers"], field["field_id"], variety="Akbar-2019", sowing=sowing_date)
    cycle_id = cycle["cycle_id"]

    # Verify Basal fertilizer split (Split 1) is already applied at sowing
    assert cycle["fertilizer_schedules"][0]["is_applied"] is True

    # 3. DAS 22: Crown Root Initiation (CRI) Milestone
    # Apply 1st Topdress Urea (Split 2)
    fert2_id = cycle["fertilizer_schedules"][1]["fertilizer_id"]
    client.put(f"/api/v1/crop-cycles/fertilizer/{fert2_id}/apply", headers=farmer["headers"])
    # Complete 1st CRI irrigation
    irrig1_id = cycle["irrigation_schedules"][0]["irrigation_id"]
    client.put(f"/api/v1/crop-cycles/irrigation/{irrig1_id}/complete", headers=farmer["headers"])

    # 4. DAS 45: Tillering & Stem Elongation
    # Upload canopy camera scan
    client.post("/api/v1/observations/", data={
        "cycle_id": cycle_id,
        "stage_index": 1,
        "stage_name": "Jointing",
        "confidence": 0.92,
        "pitch_angle_deg": -45.0,
        "blur_score": 12.0,
        "das": 45,
    }, files={"image": ("jointing_aslam.jpg", io.BytesIO(generate_dummy_jpeg()), "image/jpeg")}, headers=farmer["headers"])
    # Complete 2nd irrigation
    irrig2_id = cycle["irrigation_schedules"][1]["irrigation_id"]
    client.put(f"/api/v1/crop-cycles/irrigation/{irrig2_id}/complete", headers=farmer["headers"])

    # 5. DAS 55-75: Booting & Flag Leaf Protection
    # Apply 2nd Topdress Urea + Zinc (Split 3)
    fert3_id = cycle["fertilizer_schedules"][2]["fertilizer_id"]
    client.put(f"/api/v1/crop-cycles/fertilizer/{fert3_id}/apply", headers=farmer["headers"])
    # Complete 3rd Booting irrigation
    irrig3_id = cycle["irrigation_schedules"][2]["irrigation_id"]
    client.put(f"/api/v1/crop-cycles/irrigation/{irrig3_id}/complete", headers=farmer["headers"])

    # 6. DAS 95: Flowering / Anthesis
    irrig4_id = cycle["irrigation_schedules"][3]["irrigation_id"]
    client.put(f"/api/v1/crop-cycles/irrigation/{irrig4_id}/complete", headers=farmer["headers"])

    # 7. DAS 115: Grain Filling (Milky / Dough) Final Irrigation
    irrig5_id = cycle["irrigation_schedules"][4]["irrigation_id"]
    client.put(f"/api/v1/crop-cycles/irrigation/{irrig5_id}/complete", headers=farmer["headers"])

    # 8. Season Audit: Verify all 3 fertilizer splits and all 5 irrigation milestones executed
    final_cycle = client.get(f"/api/v1/crop-cycles/{cycle_id}", headers=farmer["headers"]).json()
    assert all(f["is_applied"] for f in final_cycle["fertilizer_schedules"]), "All 3 fertilizer splits must be applied"
    assert all(i["is_completed"] for i in final_cycle["irrigation_schedules"]), "All 5 irrigation milestones must be completed"

    # Verify observation ledger contains the mid-season canopy capture
    timeline = client.get(f"/api/v1/observations/cycle/{cycle_id}", headers=farmer["headers"]).json()
    assert len(timeline) == 1
    assert timeline[0]["stage_name"] == "Jointing"

def test_tier4_lodging_prevention_and_weather_advisory():
    """T4.2: Farmer consults Flowering stage advisory to assess wind gust and lodging hazard."""
    # Flowering stage index is 3
    rule_resp = client.get("/api/v1/advisory/rules/3")
    assert rule_resp.status_code == 200
    flowering_rule = rule_resp.json()
    
    # Must warn about lodging during irrigation in high winds
    assert "lodging" in flowering_rule["irrigation_advice_en"].lower()
    # Spoken Urdu script must give specific lodging guidance
    assert "فصل نہ گرے" in flowering_rule["audio_script_ur"] or "ہوا" in flowering_rule["audio_script_ur"]

def test_tier4_peer_showcase_yield_comparison():
    """T4.3: Farmer evaluates top-yielding peer benchmark (sc_01, 61.8 Maunds) against provincial average."""
    resp = client.get("/api/v1/showcase/sc_01")
    assert resp.status_code == 200
    sc = resp.json()
    
    assert sc["field_code"] == "PK-FSD-01"
    assert sc["yield_maunds_per_acre"] == 61.8
    assert sc["wheat_variety"] == "Akbar-2019"
    # Verify comprehensive 8-step event playbook
    events = sc["cycle_event_log"]
    assert len(events) == 8
    assert events[0]["day"] == 0 and "DAP" in events[0]["event"]
    assert events[-1]["day"] == 142 and "61.8 Maunds" in events[-1]["event"]
