"""
NextGenYield Backend Integration Test Suite
===========================================
End-to-end integration tests verifying:
- System health & database connectivity
- JWT authentication (registration, login, /auth/me)
- Field demarcation and boundary updates (RFC 7946 GeoJSON)
- Crop cycle scheduling and active cycle querying
- Fertilizer and irrigation schedule progression toggles
- Agronomic deterministic advisory rules (6 wheat phenological stages)
- Peer showcase community benchmark submissions and playbook retrieval
- Field canopy visual observation multipart image uploads and storage fallback
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# ==============================================================================
# Shared Pytest Fixtures
# ==============================================================================

@pytest.fixture(scope="module")
def auth_headers():
    """
    Module-scoped fixture that registers/logs in the standard test farmer
    and yields a valid Authorization Bearer token header.
    """
    login_payload = {
        "phone_number": "03009988776",
        "password": "pass1234password"
    }
    login_resp = client.post("/api/v1/auth/login", json=login_payload)
    if login_resp.status_code != 200:
        # Register user if not already present in fresh test databases
        client.post("/api/v1/auth/register", json={
            "full_name": "Farmer Test Khan",
            "phone_number": "03009988776",
            "password": "pass1234password",
            "role": "farmer",
            "district": "Faisalabad",
            "language_pref": "ur"
        })
        login_resp = client.post("/api/v1/auth/login", json=login_payload)
    
    assert login_resp.status_code == 200, f"Login failed during fixture setup: {login_resp.text}"
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="module")
def active_field_and_cycle(auth_headers):
    """
    Module-scoped fixture that provides an initialized parcel and active crop cycle
    for downstream schedule progression and observation upload tests.
    """
    field_payload = {
        "field_name": "Chak 214 North Plot",
        "shape_type": "polygon",
        "area_acres": 5.5,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[[73.07, 31.41], [73.08, 31.41], [73.08, 31.42], [73.07, 31.42], [73.07, 31.41]]]
        }
    }
    f_resp = client.post("/api/v1/fields/", json=field_payload, headers=auth_headers)
    assert f_resp.status_code == 201, f"Failed to create fixture field: {f_resp.text}"
    field_data = f_resp.json()

    cycle_payload = {
        "field_id": field_data["field_id"],
        "wheat_variety": "Akbar-2019",
        "seed_company": "Punjab Seed Corporation",
        "fertilizer_company": "Fauji Fertilizer Company (FFC)",
        "sowing_method": "Drill Sowing",
        "sowing_date": "2026-11-01"
    }
    c_resp = client.post("/api/v1/crop-cycles/start", json=cycle_payload, headers=auth_headers)
    assert c_resp.status_code == 201, f"Failed to start fixture cycle: {c_resp.text}"
    cycle_data = c_resp.json()

    return {
        "field_id": field_data["field_id"],
        "cycle_id": cycle_data["cycle_id"],
        "field": field_data,
        "cycle": cycle_data,
    }


# ==============================================================================
# Core Integration Test Suite
# ==============================================================================

def test_health_check():
    """Verify backend API health status and database connectivity."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["database"] == "connected"

def test_auth_registration_and_login():
    """Verify farmer registration, JWT issuance on login, and /auth/me profile."""
    # 1. Register a test farmer (accept 201 created or 400 if already registered)
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

def test_field_and_crop_cycle_flow(auth_headers):
    """Verify field demarcation and 140-day agronomic crop cycle schedule generation."""
    # 1. Demarcate a new field (GeoJSON)
    field_payload = {
        "field_name": "Chak 214 North Plot Baseline",
        "shape_type": "polygon",
        "area_acres": 5.5,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[[73.07, 31.41], [73.08, 31.41], [73.08, 31.42], [73.07, 31.42], [73.07, 31.41]]]
        }
    }
    f_resp = client.post("/api/v1/fields/", json=field_payload, headers=auth_headers)
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
    c_resp = client.post("/api/v1/crop-cycles/start", json=cycle_payload, headers=auth_headers)
    assert c_resp.status_code == 201
    cycle_data = c_resp.json()
    assert cycle_data["wheat_variety"] == "Akbar-2019"
    # Ensure schedules were automatically generated
    assert len(cycle_data["fertilizer_schedules"]) == 3
    assert len(cycle_data["irrigation_schedules"]) == 5

def test_advisory_rules():
    """Verify retrieval of deterministic agronomic rules across all 6 wheat phenological stages."""
    resp = client.get("/api/v1/advisory/rules")
    assert resp.status_code == 200
    rules = resp.json()
    assert len(rules) == 6  # 6 phenological wheat stages
    assert rules[2]["stage_name"] == "Booting"


# ==============================================================================
# Milestone 1 Expanded Integration Tests
# ==============================================================================

def test_field_update_and_persistence(auth_headers):
    """
    Verify PUT /api/v1/fields/{field_id} updates parcel attributes:
    - Modifies field_name, area_acres, shape_type, coordinates, and soil_texture.
    - Verifies immediate 200 OK response with updated values.
    - Verifies persistence via GET /api/v1/fields/{field_id}.
    - Verifies 404 Not Found error handling for non-existent fields.
    """
    # 1. Create a parcel to update
    create_payload = {
        "field_name": "Parcel Before Update",
        "shape_type": "rectangle",
        "area_acres": 4.0,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[[73.00, 31.40], [73.10, 31.40], [73.10, 31.50], [73.00, 31.50], [73.00, 31.40]]]
        }
    }
    create_resp = client.post("/api/v1/fields/", json=create_payload, headers=auth_headers)
    assert create_resp.status_code == 201
    field_id = create_resp.json()["field_id"]

    # 2. Update field via PUT
    updated_coordinates = [[[73.05, 31.45], [73.15, 31.45], [73.15, 31.55], [73.05, 31.55], [73.05, 31.45]]]
    update_payload = {
        "field_name": "Parcel After Update",
        "area_acres": 6.8,
        "shape_type": "polygon",
        "soil_texture": "Clay Loam",
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": updated_coordinates
        }
    }
    put_resp = client.put(f"/api/v1/fields/{field_id}", json=update_payload, headers=auth_headers)
    assert put_resp.status_code == 200
    updated_data = put_resp.json()
    assert updated_data["field_id"] == field_id
    assert updated_data["field_name"] == "Parcel After Update"
    assert updated_data["area_acres"] == 6.8
    assert updated_data["shape_type"] == "polygon"
    assert updated_data["boundary_geojson"]["coordinates"] == updated_coordinates
    assert updated_data["soil_texture"] == "Clay Loam"

    # 3. Verify persistence with GET /api/v1/fields/{field_id}
    get_resp = client.get(f"/api/v1/fields/{field_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    persisted = get_resp.json()
    assert persisted["field_name"] == "Parcel After Update"
    assert persisted["area_acres"] == 6.8
    assert persisted["shape_type"] == "polygon"
    assert persisted["boundary_geojson"]["coordinates"] == updated_coordinates
    assert persisted["soil_texture"] == "Clay Loam"

    # 4. Negative test: Attempt to update non-existent field
    bad_resp = client.put("/api/v1/fields/fld_nonexistent_999", json=update_payload, headers=auth_headers)
    assert bad_resp.status_code == 404

def test_active_crop_cycle_query(auth_headers):
    """
    Verify GET /api/v1/crop-cycles/field/{field_id}/active:
    - Asserts 404 when querying an unstarted / fallow parcel.
    - Starts a crop cycle and confirms active query returns 200 OK with schedules.
    - Confirms is_active is True and schedule count matches requirements.
    - Asserts 404 when querying a non-existent field_id.
    """
    # 1. Create a fresh field with no active cycle
    f_resp = client.post("/api/v1/fields/", json={
        "field_name": "Active Cycle Test Parcel",
        "shape_type": "square",
        "area_acres": 3.0,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[[73.12, 31.42], [73.13, 31.42], [73.13, 31.43], [73.12, 31.43], [73.12, 31.42]]]
        }
    }, headers=auth_headers)
    assert f_resp.status_code == 201
    field_id = f_resp.json()["field_id"]

    # 2. Query active cycle when unstarted -> expect 404
    empty_resp = client.get(f"/api/v1/crop-cycles/field/{field_id}/active", headers=auth_headers)
    assert empty_resp.status_code == 404

    # 3. Start a cycle on the parcel
    start_payload = {
        "field_id": field_id,
        "wheat_variety": "Dilkash-20",
        "seed_company": "Punjab Seed Corporation",
        "fertilizer_company": "Engro Fertilizers",
        "sowing_method": "Bed Planting",
        "sowing_date": "2026-11-05"
    }
    start_resp = client.post("/api/v1/crop-cycles/start", json=start_payload, headers=auth_headers)
    assert start_resp.status_code == 201
    started_cycle = start_resp.json()
    cycle_id = started_cycle["cycle_id"]

    # 4. Query active cycle -> expect 200 with full schedules
    active_resp = client.get(f"/api/v1/crop-cycles/field/{field_id}/active", headers=auth_headers)
    assert active_resp.status_code == 200
    active_data = active_resp.json()
    assert active_data["cycle_id"] == cycle_id
    assert active_data["field_id"] == field_id
    assert active_data["wheat_variety"] == "Dilkash-20"
    assert active_data["is_active"] is True
    assert len(active_data["fertilizer_schedules"]) == 3
    assert len(active_data["irrigation_schedules"]) == 5

    # 5. Negative test: Non-existent field ID
    bad_resp = client.get("/api/v1/crop-cycles/field/fld_invalid_nonexistent/active", headers=auth_headers)
    assert bad_resp.status_code == 404

def test_schedule_progression_toggles(auth_headers, active_field_and_cycle):
    """
    Verify schedule progression mutations and persistence:
    - PUT /api/v1/crop-cycles/fertilizer/{fertilizer_id}/apply
    - PUT /api/v1/crop-cycles/irrigation/{irrigation_id}/complete
    - Verify persistence by inspecting GET /api/v1/crop-cycles/{cycle_id}
    - Verify 404 Not Found error handling for invalid schedule IDs.
    """
    cycle_data = active_field_and_cycle["cycle"]
    cycle_id = cycle_data["cycle_id"]
    fert_id = cycle_data["fertilizer_schedules"][0]["fertilizer_id"]
    irrig_id = cycle_data["irrigation_schedules"][0]["irrigation_id"]

    # 1. Apply fertilizer split
    fert_resp = client.put(f"/api/v1/crop-cycles/fertilizer/{fert_id}/apply", headers=auth_headers)
    assert fert_resp.status_code == 200
    fert_res = fert_resp.json()
    assert fert_res["fertilizer_id"] == fert_id
    assert fert_res["is_applied"] is True
    assert fert_res["applied_at"] is not None

    # 2. Complete irrigation milestone
    irrig_resp = client.put(f"/api/v1/crop-cycles/irrigation/{irrig_id}/complete", headers=auth_headers)
    assert irrig_resp.status_code == 200
    irrig_res = irrig_resp.json()
    assert irrig_res["irrigation_id"] == irrig_id
    assert irrig_res["is_completed"] is True

    # 3. Verify persistence on cycle details endpoint
    get_cycle_resp = client.get(f"/api/v1/crop-cycles/{cycle_id}", headers=auth_headers)
    assert get_cycle_resp.status_code == 200
    cycle_detail = get_cycle_resp.json()
    persisted_fert = next(f for f in cycle_detail["fertilizer_schedules"] if f["fertilizer_id"] == fert_id)
    assert persisted_fert["is_applied"] is True
    persisted_irrig = next(i for i in cycle_detail["irrigation_schedules"] if i["irrigation_id"] == irrig_id)
    assert persisted_irrig["is_completed"] is True

    # 4. Negative tests on non-existent schedule records
    bad_fert = client.put("/api/v1/crop-cycles/fertilizer/fert_invalid_nonexistent/apply", headers=auth_headers)
    assert bad_fert.status_code == 404

    bad_irrig = client.put("/api/v1/crop-cycles/irrigation/irrig_invalid_nonexistent/complete", headers=auth_headers)
    assert bad_irrig.status_code == 404

def test_peer_showcase_submission_and_retrieval(auth_headers):
    """
    Verify peer showcase community benchmark submission and retrieval:
    - POST /api/v1/showcase/ creates a benchmark with yield and tactics playbook.
    - Asserts 201 Created and verifies metric yield calculation.
    - GET /api/v1/showcase/{id} retrieves the complete playbook.
    - GET /api/v1/showcase/ includes the newly submitted benchmark.
    - Negative test verifies 404 for non-existent showcase IDs.
    """
    showcase_payload = {
        "title": "Chak 45 Record Yield",
        "field_name": "East Block Plot 1",
        "region": "Faisalabad",
        "wheat_variety": "Akbar-2019",
        "actual_yield_maunds": 63.2,
        "sowing_date": "2025-11-08",
        "harvesting_date": "2026-04-12",
        "key_tactics": [
            "Drill sowing with DAP and Potash",
            "CRI watering at 22 DAS",
            "Flag leaf protection against rust"
        ],
        "photo_url": "https://example.com/harvest-canopy.jpg",
        "seed_company": "Punjab Seed Corporation",
        "fertilizer_company": "FFC Gohar",
        "area_acres": 10.0,
        "shape_type": "rectangle"
    }

    # 1. Post showcase entry
    post_resp = client.post("/api/v1/showcase/", json=showcase_payload, headers=auth_headers)
    assert post_resp.status_code == 201
    showcase_data = post_resp.json()
    sc_id = showcase_data["showcase_id"]
    assert sc_id.startswith("sc_")
    assert showcase_data["yield_maunds_per_acre"] == 63.2
    assert showcase_data["wheat_variety"] == "Akbar-2019"
    assert showcase_data["district"] == "Faisalabad"
    assert len(showcase_data["cycle_event_log"]) >= 1

    # 2. Get playbook by ID
    get_resp = client.get(f"/api/v1/showcase/{sc_id}")
    assert get_resp.status_code == 200
    fetched_data = get_resp.json()
    assert fetched_data["showcase_id"] == sc_id
    assert fetched_data["yield_maunds_per_acre"] == 63.2
    assert fetched_data["wheat_variety"] == "Akbar-2019"

    # 3. Verify presence in public list
    list_resp = client.get("/api/v1/showcase/")
    assert list_resp.status_code == 200
    all_benchmarks = list_resp.json()
    assert any(b["showcase_id"] == sc_id for b in all_benchmarks)

    # 4. Negative test: Non-existent showcase ID
    bad_resp = client.get("/api/v1/showcase/sc_invalid_nonexistent")
    assert bad_resp.status_code == 404

    # 5. Cleanup test showcase entry so repeated test runs do not pollute Proven Yields
    from app.database import SessionLocal
    from app.models.advisory import PeerShowcaseField
    db = SessionLocal()
    try:
        db.query(PeerShowcaseField).filter(PeerShowcaseField.showcase_id == sc_id).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()

def test_observation_upload_and_retrieval(auth_headers, active_field_and_cycle):
    """
    Verify multipart visual observation upload and timeline retrieval:
    - POST /api/v1/observations/ with multipart dummy JPEG image.
    - Asserts 201 Created and verifies Supabase Storage URI or local disk fallback URI.
    - GET /api/v1/observations/cycle/{cycle_id} confirms chronological logging.
    - Negative test verifies 404 when uploading for a non-existent cycle_id.
    """
    cycle_id = active_field_and_cycle["cycle_id"]

    # Minimal valid JPEG binary image (SOI, APP0, SOF0, SOS, EOI)
    dummy_jpeg_bytes = (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00"
        b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08"
        b"\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e"
        b"\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342"
        b"\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00"
        b"\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b"
        b"\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9"
    )

    form_data = {
        "cycle_id": cycle_id,
        "stage_index": "2",
        "stage_name": "Booting",
        "confidence": "0.96",
        "pitch_angle_deg": "45.0",
        "blur_score": "142.8",
        "das": "75"
    }
    files = {
        "image": ("test_canopy_das75.jpg", dummy_jpeg_bytes, "image/jpeg")
    }

    # 1. Upload observation via multipart POST
    upload_resp = client.post(
        "/api/v1/observations/",
        data=form_data,
        files=files,
        headers=auth_headers
    )
    assert upload_resp.status_code == 201
    obs_data = upload_resp.json()
    obs_id = obs_data["observation_id"]
    assert obs_id.startswith("obs_")
    assert obs_data["cycle_id"] == cycle_id
    assert obs_data["stage_index"] == 2
    assert obs_data["stage_name"] == "Booting"
    assert obs_data["confidence"] == pytest.approx(0.96, abs=1e-2)
    assert obs_data["das"] == 75

    # 2. Check storage URI: Supabase public URL or local disk fallback
    image_uri = obs_data["image_uri"]
    assert (
        image_uri.startswith("http://") or
        image_uri.startswith("https://") or
        image_uri.startswith("/api/v1/storage/file/")
    ), f"Invalid image_uri: {image_uri}"

    # 3. Retrieve cycle timeline and verify observation is listed
    timeline_resp = client.get(f"/api/v1/observations/cycle/{cycle_id}", headers=auth_headers)
    assert timeline_resp.status_code == 200
    timeline = timeline_resp.json()
    assert len(timeline) >= 1
    matching = [o for o in timeline if o["observation_id"] == obs_id]
    assert len(matching) == 1
    assert matching[0]["stage_name"] == "Booting"
    assert matching[0]["confidence"] == pytest.approx(0.96, abs=1e-2)
    assert matching[0]["das"] == 75

    # 4. Negative test: Upload with invalid cycle_id -> 404 Not Found
    bad_form = dict(form_data, cycle_id="cyc_invalid_nonexistent")
    bad_upload_resp = client.post(
        "/api/v1/observations/",
        data=bad_form,
        files={"image": ("test.jpg", dummy_jpeg_bytes, "image/jpeg")},
        headers=auth_headers
    )
    assert bad_upload_resp.status_code == 404


# ==============================================================================
# New Feature Integration Tests (Machinery, Employees, Community, Marketplace)
# ==============================================================================

def test_machinery_rental_and_booking_flow(auth_headers):
    """Verify machinery listing, filtering, booking, and price estimation."""
    # 1. Create a machinery listing
    create_payload = {
        "title": "Al-Ghazi Laser Leveler Setup",
        "machinery_type": "laser_leveler",
        "brand_model": "NH 640 + Dual Transmitter",
        "horsepower": 75.0,
        "hourly_rate_pkr": 2500.0,
        "daily_rate_pkr": 18000.0,
        "district": "Faisalabad",
        "location_address": "Chak 214 RB, Faisalabad",
        "contact_phone": "03001234567",
        "description": "High precision leveling bucket"
    }
    create_resp = client.post("/api/v1/machinery/", json=create_payload, headers=auth_headers)
    assert create_resp.status_code == 201
    mach_data = create_resp.json()
    mach_id = mach_data["machinery_id"]
    assert mach_id.startswith("mach_")
    assert mach_data["daily_rate_pkr"] == 18000.0

    # 2. List machinery with type filter
    list_resp = client.get("/api/v1/machinery/?machinery_type=laser_leveler", headers=auth_headers)
    assert list_resp.status_code == 200
    listings = list_resp.json()
    assert len(listings) >= 1

    # 3. Book a 2-day slot
    from datetime import datetime, timedelta
    start = datetime.utcnow() + timedelta(days=1)
    end = start + timedelta(days=2)
    book_payload = {
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "purpose_step": "laser_leveling",
        "notes": "Pre-sowing leveling for wheat parcel"
    }
    book_resp = client.post(f"/api/v1/machinery/{mach_id}/book", json=book_payload, headers=auth_headers)
    assert book_resp.status_code == 201
    booking = book_resp.json()
    assert booking["booking_id"].startswith("book_")
    assert booking["status"] == "confirmed"
    assert booking["total_amount_pkr"] >= 18000.0

    # 4. View user bookings
    my_bookings = client.get("/api/v1/machinery/user/my-bookings", headers=auth_headers)
    assert my_bookings.status_code == 200
    assert len(my_bookings.json()) >= 1

    # 5. Verify machinery schedule endpoint
    sched_resp = client.get(f"/api/v1/machinery/{mach_id}/schedule", headers=auth_headers)
    assert sched_resp.status_code == 200
    sched_data = sched_resp.json()
    assert "days" in sched_data
    assert len(sched_data["days"]) >= 28

    # 6. Verify conflict prevention with 1-hour transit buffer
    conflict_payload = {
        "start_date": (end - timedelta(hours=2)).isoformat(),
        "end_date": (end + timedelta(hours=2)).isoformat(),
        "purpose_step": "laser_leveling"
    }
    conflict_resp = client.post(f"/api/v1/machinery/{mach_id}/book", json=conflict_payload, headers=auth_headers)
    assert conflict_resp.status_code == 400
    assert "conflict" in conflict_resp.json()["detail"].lower()


def test_farm_employee_delegation_flow(auth_headers, active_field_and_cycle):
    """Verify owner adding employee, delegating fields, and employee field query."""
    field_id = active_field_and_cycle["field_id"]

    # 1. Add employee
    emp_payload = {
        "employee_name": "Bashir Ahmad",
        "employee_phone": "03008765432",
        "role": "farmhand",
        "access_all_fields": False,
        "assigned_field_ids": [field_id]
    }
    emp_resp = client.post("/api/v1/employees/", json=emp_payload, headers=auth_headers)
    assert emp_resp.status_code == 201
    emp_data = emp_resp.json()
    emp_id = emp_data["employee_record_id"]
    assert emp_id.startswith("emp_")
    assert len(emp_data["assigned_fields"]) == 1
    assert emp_data["assigned_fields"][0]["field_id"] == field_id

    # 2. List employees
    list_resp = client.get("/api/v1/employees/", headers=auth_headers)
    assert list_resp.status_code == 200
    assert any(e["employee_record_id"] == emp_id for e in list_resp.json())

    # 3. Re-assign to all fields
    assign_resp = client.post(
        f"/api/v1/employees/{emp_id}/assign-fields",
        json={"field_ids": [], "access_all_fields": True},
        headers=auth_headers
    )
    assert assign_resp.status_code == 200
    assert assign_resp.json()["access_all_fields"] is True

    # 4. Delete employee
    del_resp = client.delete(f"/api/v1/employees/{emp_id}", headers=auth_headers)
    assert del_resp.status_code == 204


def test_community_posts_and_chat_flow(auth_headers):
    """Verify community posting, liking, commenting, and direct messaging."""
    # 1. Create a community post
    post_payload = {
        "title": "Best Fertilizer Timing for Akbar-2019",
        "category": "agronomy_tips",
        "content": "Split urea 3x: 1/3 at sowing, 1/3 at 1st watering, 1/3 at booting."
    }
    post_resp = client.post("/api/v1/community/posts", json=post_payload, headers=auth_headers)
    assert post_resp.status_code == 201
    post_data = post_resp.json()
    post_id = post_data["post_id"]
    assert post_id.startswith("post_")
    assert post_data["likes_count"] == 0

    # 2. Toggle like
    like_resp = client.post(f"/api/v1/community/posts/{post_id}/like", headers=auth_headers)
    assert like_resp.status_code == 200
    assert like_resp.json()["liked"] is True
    assert like_resp.json()["likes_count"] == 1

    # 3. Add comment
    cmt_resp = client.post(
        f"/api/v1/community/posts/{post_id}/comments",
        json={"content": "Very helpful advice, thank you!"},
        headers=auth_headers
    )
    assert cmt_resp.status_code == 201
    assert cmt_resp.json()["content"] == "Very helpful advice, thank you!"

    # 4. List comments
    cmts = client.get(f"/api/v1/community/posts/{post_id}/comments", headers=auth_headers)
    assert cmts.status_code == 200
    assert len(cmts.json()) >= 1

    # 5. List conversations
    convs = client.get("/api/v1/community/conversations", headers=auth_headers)
    assert convs.status_code == 200

    # 6. Cleanup test post so repeated test runs do not leave duplicate posts in DB
    from app.database import SessionLocal
    from app.models.community import CommunityPost, PostComment, PostLike
    db = SessionLocal()
    try:
        db.query(PostComment).filter(PostComment.post_id == post_id).delete(synchronize_session=False)
        db.query(PostLike).filter(PostLike.post_id == post_id).delete(synchronize_session=False)
        db.query(CommunityPost).filter(CommunityPost.post_id == post_id).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def test_marketplace_items_flow(auth_headers):
    """Verify Facebook-style marketplace listing, filtering, and sold toggle."""
    # 1. Create product listing
    item_payload = {
        "title": "Certified Dilkash-20 Wheat Seed 50kg",
        "category": "seeds",
        "price_pkr": 4900.0,
        "condition": "new",
        "district": "Faisalabad",
        "location_address": "Grain Market Shop #5",
        "contact_phone": "03009988776",
        "description": "Punjab Seed Corp certified, germination rate 92%"
    }
    create_resp = client.post("/api/v1/marketplace/items", json=item_payload, headers=auth_headers)
    assert create_resp.status_code == 201
    item_data = create_resp.json()
    item_id = item_data["item_id"]
    assert item_id.startswith("item_")
    assert item_data["price_pkr"] == 4900.0

    # 2. Browse items with category filter
    items_resp = client.get("/api/v1/marketplace/items?category=seeds", headers=auth_headers)
    assert items_resp.status_code == 200
    items = items_resp.json()
    assert any(i["item_id"] == item_id for i in items)

    # 3. Toggle item as sold
    sold_resp = client.patch(f"/api/v1/marketplace/items/{item_id}/sold", headers=auth_headers)
    assert sold_resp.status_code == 200
    assert sold_resp.json()["is_sold"] is True

    # 4. Delete item
    del_resp = client.delete(f"/api/v1/marketplace/items/{item_id}", headers=auth_headers)
    assert del_resp.status_code == 204


def test_public_user_profile_and_disconnect_flow(auth_headers):
    """Verify retrieval of public farmer profile, friendship connect and disconnect."""
    # 1. Fetch current user info to get user_id
    me_resp = client.get("/api/v1/auth/me", headers=auth_headers)
    assert me_resp.status_code == 200
    my_user_id = me_resp.json()["user_id"]

    # 2. Get own profile -> connection_status should be 'self'
    self_profile_resp = client.get(f"/api/v1/community/users/{my_user_id}/profile", headers=auth_headers)
    assert self_profile_resp.status_code == 200
    self_profile = self_profile_resp.json()
    assert self_profile["user_id"] == my_user_id
    assert self_profile["connection_status"] == "self"
    assert "total_fields" in self_profile
    assert "total_acreage" in self_profile
    assert "posts_count" in self_profile

    # 3. Create or register a secondary peer farmer
    peer_phone = "03011122334"
    client.post("/api/v1/auth/register", json={
        "full_name": "Peer Farmer Ali",
        "phone_number": peer_phone,
        "password": "pass1234password",
        "role": "farmer",
        "district": "Sargodha",
        "language_pref": "ur"
    })
    peer_login = client.post("/api/v1/auth/login", json={
        "phone_number": peer_phone,
        "password": "pass1234password"
    })
    assert peer_login.status_code == 200
    peer_token = peer_login.json()["access_token"]
    peer_headers = {"Authorization": f"Bearer {peer_token}"}
    peer_me = client.get("/api/v1/auth/me", headers=peer_headers).json()
    peer_user_id = peer_me["user_id"]

    # 4. View peer profile before connecting -> connection_status should be 'none'
    peer_prof = client.get(f"/api/v1/community/users/{peer_user_id}/profile", headers=auth_headers)
    assert peer_prof.status_code == 200
    assert peer_prof.json()["connection_status"] == "none"

    # 5. Connect with peer farmer
    conn_resp = client.post(f"/api/v1/community/farmers/{peer_user_id}/connect", headers=auth_headers)
    assert conn_resp.status_code == 200
    assert conn_resp.json()["status"] == "accepted"

    # 6. View peer profile after connecting -> connection_status should be 'accepted'
    peer_prof2 = client.get(f"/api/v1/community/users/{peer_user_id}/profile", headers=auth_headers)
    assert peer_prof2.status_code == 200
    assert peer_prof2.json()["connection_status"] == "accepted"

    # 7. Disconnect with peer farmer
    disc_resp = client.delete(f"/api/v1/community/farmers/{peer_user_id}/disconnect", headers=auth_headers)
    assert disc_resp.status_code == 200
    assert disc_resp.json()["status"] == "none"

    # 8. View peer profile after disconnect -> connection_status should be 'none'
    peer_prof3 = client.get(f"/api/v1/community/users/{peer_user_id}/profile", headers=auth_headers)
    assert peer_prof3.status_code == 200
    assert peer_prof3.json()["connection_status"] == "none"

    # 9. Verify paginated farmer discovery and search
    search_resp = client.get("/api/v1/community/farmers?search=Ali&page=1&limit=5", headers=auth_headers)
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert "items" in search_data
    assert "total" in search_data
    assert "page" in search_data
    assert search_data["page"] == 1
    assert search_data["limit"] == 5


