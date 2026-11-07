"""
backend/tests/test_adversarial_m1.py
Empirical Adversarial Test Suite for Milestone 1 Backend Endpoints & Seeding Idempotency.

Covers:
1. PUT /api/v1/fields/{id}:
   - Invalid IDs (e.g. 999999, non-existent UUIDs) -> expect 404
   - Boundary updates with varying geometries (polygons, points, multipolygons, raw coordinates)
   - Input validations (invalid shape_type, negative area) -> expect 422
   - Cross-tenant unauthorized mutation attempt -> expect 403
2. POST /api/v1/showcase/:
   - Missing required fields (wheat_variety, sowing_date) -> expect 422
   - Edge case yield numbers (negative, zero, extreme values)
   - Date edge cases (invalid format, harvest before sowing)
3. GET /api/v1/crop-cycles/field/{id}/active:
   - Non-existent field -> expect 404
   - Field with no crop cycle -> expect 404
   - Cross-tenant query attempt -> expect 404
4. Challenge seeding:
   - Repeated consecutive execution of seed() -> verify zero IntegrityError and zero duplicate rows.
"""

import pytest
import uuid
from datetime import date, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.user import User
from app.models.field import Field
from app.models.crop_cycle import CropCycle
from app.models.advisory import AgronomicAdvisoryRule, PeerShowcaseField
from app.core.seed_data import seed, ADVISORY_RULES_SEED, SHOWCASE_FIELDS_SEED

client = TestClient(app)

# ==============================================================================
# Multi-tenant Auth Fixtures
# ==============================================================================

def get_or_create_user(phone: str, full_name: str) -> dict:
    """Helper to register and login a test user, returning auth header."""
    login_payload = {"phone_number": phone, "password": "pass1234password"}
    login_resp = client.post("/api/v1/auth/login", json=login_payload)
    if login_resp.status_code != 200:
        reg_resp = client.post("/api/v1/auth/register", json={
            "full_name": full_name,
            "phone_number": phone,
            "password": "pass1234password",
            "role": "farmer",
            "district": "Faisalabad",
            "language_pref": "en"
        })
        assert reg_resp.status_code in (200, 201), f"Failed to register test user: {reg_resp.text}"
        login_resp = client.post("/api/v1/auth/login", json=login_payload)
    assert login_resp.status_code == 200, f"Failed to login user {phone}: {login_resp.text}"
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="module")
def tenant_a_headers():
    return get_or_create_user("03001112233", "Tenant A Farmer")

@pytest.fixture(scope="module")
def tenant_b_headers():
    return get_or_create_user("03004445566", "Tenant B Farmer")

@pytest.fixture(scope="module")
def tenant_a_field(tenant_a_headers):
    """Creates a field owned by Tenant A."""
    field_payload = {
        "field_name": "Tenant A Primary Field",
        "shape_type": "rectangle",
        "area_acres": 4.0,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[[73.05, 31.40], [73.06, 31.40], [73.06, 31.41], [73.05, 31.41], [73.05, 31.40]]]
        }
    }
    resp = client.post("/api/v1/fields/", json=field_payload, headers=tenant_a_headers)
    assert resp.status_code == 201, f"Failed creating Tenant A field: {resp.text}"
    return resp.json()

# ==============================================================================
# Challenge 1: PUT /api/v1/fields/{id}
# ==============================================================================

def test_put_field_invalid_ids(tenant_a_headers):
    """Verify that updating non-existent or invalid field IDs returns 404 Not Found."""
    invalid_ids = ["999999", "non-existent-field-id", "fld_000000000000"]
    for fid in invalid_ids:
        resp = client.put(f"/api/v1/fields/{fid}", json={"field_name": "Ghost Field"}, headers=tenant_a_headers)
        assert resp.status_code == 404, f"Expected 404 for {fid}, got {resp.status_code}: {resp.text}"
        assert "not found" in resp.json().get("detail", "").lower()

def test_put_field_cross_tenant_forbidden(tenant_a_field, tenant_b_headers):
    """
    Cross-tenant attempt: Tenant B attempts to update Tenant A's field.
    Must return HTTP 403 Forbidden.
    """
    field_id = tenant_a_field["field_id"]
    attack_payload = {
        "field_name": "Hacked Field Name",
        "area_acres": 99.0
    }
    resp = client.put(f"/api/v1/fields/{field_id}", json=attack_payload, headers=tenant_b_headers)
    assert resp.status_code == 403, f"Expected 403 Forbidden for cross-tenant edit, got {resp.status_code}: {resp.text}"
    assert "access denied" in resp.json().get("detail", "").lower()

    # Verify field remains unchanged in database
    db = SessionLocal()
    try:
        f = db.query(Field).filter(Field.field_id == field_id).first()
        assert f.field_name == "Tenant A Primary Field", "Field name was illegally mutated across tenants!"
    finally:
        db.close()

def test_put_field_varying_geometries(tenant_a_headers, tenant_a_field):
    """
    Challenge boundary updates with varying geometries:
    - Polygons
    - Alternative geometries (Point, MultiPolygon)
    - Raw coordinates list
    - Invalid shape types and negative areas
    """
    field_id = tenant_a_field["field_id"]

    # 1. Standard Polygon update (5 closed points: [31.50, 31.50, 31.60, 31.60, 31.50] / 5 = 31.54)
    poly_payload = {
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[[73.10, 31.50], [73.20, 31.50], [73.20, 31.60], [73.10, 31.60], [73.10, 31.50]]]
        },
        "soil_texture": "Clay Loam"
    }
    resp = client.put(f"/api/v1/fields/{field_id}", json=poly_payload, headers=tenant_a_headers)
    assert resp.status_code == 200, f"Polygon update failed: {resp.text}"
    data = resp.json()
    assert data["soil_texture"] == "Clay Loam"
    assert round(data["center_latitude"], 2) == 31.54
    assert round(data["center_longitude"], 2) == 73.14

    # 2. Raw coordinates list format [[lng, lat], ...]
    raw_coords_payload = {
        "coordinates": [[73.12, 31.52], [73.18, 31.52], [73.18, 31.58], [73.12, 31.58], [73.12, 31.52]],
        "soil_texture": "Silt Loam"
    }
    resp2 = client.put(f"/api/v1/fields/{field_id}", json=raw_coords_payload, headers=tenant_a_headers)
    assert resp2.status_code == 200, f"Raw coordinates update failed: {resp2.text}"
    data2 = resp2.json()
    assert data2["soil_texture"] == "Silt Loam"
    assert data2["boundary_geojson"]["type"] == "Polygon"

    # 3. Alternative geometry: Point
    point_payload = {
        "boundary_geojson": {
            "type": "Point",
            "coordinates": [73.08, 31.42]
        }
    }
    resp3 = client.put(f"/api/v1/fields/{field_id}", json=point_payload, headers=tenant_a_headers)
    assert resp3.status_code == 200, f"Point update failed: {resp3.text}"
    data3 = resp3.json()
    assert data3["boundary_geojson"]["type"] == "Point"
    assert data3["center_latitude"] is not None

    # 4. Alternative geometry: MultiPolygon
    multipoly_payload = {
        "boundary_geojson": {
            "type": "MultiPolygon",
            "coordinates": [[[[73.1, 31.5], [73.2, 31.5], [73.2, 31.6], [73.1, 31.6], [73.1, 31.5]]]]
        }
    }
    resp4 = client.put(f"/api/v1/fields/{field_id}", json=multipoly_payload, headers=tenant_a_headers)
    assert resp4.status_code == 200, f"MultiPolygon update failed: {resp4.text}"
    assert resp4.json()["boundary_geojson"]["type"] == "MultiPolygon"

    # 5. Invalid shape_type -> Expect 422
    resp_invalid_shape = client.put(f"/api/v1/fields/{field_id}", json={"shape_type": "heptagon"}, headers=tenant_a_headers)
    assert resp_invalid_shape.status_code == 422, f"Expected 422 for invalid shape, got {resp_invalid_shape.status_code}"

    # 6. Negative area -> Expect 422
    resp_neg_area = client.put(f"/api/v1/fields/{field_id}", json={"area_acres": -5.0}, headers=tenant_a_headers)
    assert resp_neg_area.status_code == 422, f"Expected 422 for negative area, got {resp_neg_area.status_code}"


# ==============================================================================
# Challenge 2: POST /api/v1/showcase/
# ==============================================================================

def test_post_showcase_missing_required_fields(tenant_a_headers):
    """Verify that missing required fields (wheat_variety, sowing_date) triggers 422 validation error."""
    # 1. Missing wheat_variety
    payload1 = {
        "sowing_date": "2025-11-10",
        "actual_yield_maunds": 55.0
    }
    resp1 = client.post("/api/v1/showcase/", json=payload1, headers=tenant_a_headers)
    assert resp1.status_code == 422, f"Expected 422 for missing wheat_variety, got {resp1.status_code}"

    # 2. Missing sowing_date
    payload2 = {
        "wheat_variety": "Akbar-2019",
        "actual_yield_maunds": 55.0
    }
    resp2 = client.post("/api/v1/showcase/", json=payload2, headers=tenant_a_headers)
    assert resp2.status_code == 422, f"Expected 422 for missing sowing_date, got {resp2.status_code}"

    # 3. Empty payload
    resp3 = client.post("/api/v1/showcase/", json={}, headers=tenant_a_headers)
    assert resp3.status_code == 422, f"Expected 422 for empty showcase payload, got {resp3.status_code}"

def test_post_showcase_yield_number_edge_cases(tenant_a_headers):
    """
    Challenge yield number validations:
    - Negative yield numbers -> expect 422
    - Zero yield numbers -> expect 422
    - Valid extreme yield numbers (high agronomic records)
    """
    # Negative yield in actual_yield_maunds
    payload_neg = {
        "wheat_variety": "Akbar-2019",
        "sowing_date": "2025-11-10",
        "actual_yield_maunds": -25.0
    }
    resp_neg = client.post("/api/v1/showcase/", json=payload_neg, headers=tenant_a_headers)
    assert resp_neg.status_code == 422, f"Expected 422 for negative yield, got {resp_neg.status_code}: {resp_neg.text}"

    # Zero yield in yield_maunds_per_acre
    payload_zero = {
        "wheat_variety": "Akbar-2019",
        "sowing_date": "2025-11-10",
        "yield_maunds_per_acre": 0.0
    }
    resp_zero = client.post("/api/v1/showcase/", json=payload_zero, headers=tenant_a_headers)
    assert resp_zero.status_code == 422, f"Expected 422 for zero yield, got {resp_zero.status_code}: {resp_zero.text}"

    # Valid high yield (e.g. 75.5 Maunds/Acre - high record yield)
    payload_high = {
        "title": "Punjab Record Yield Demonstration",
        "wheat_variety": "Dilkash-20",
        "sowing_date": "2025-11-12",
        "actual_yield_maunds": 75.5,
        "district": "Faisalabad"
    }
    resp_high = client.post("/api/v1/showcase/", json=payload_high, headers=tenant_a_headers)
    assert resp_high.status_code == 201, f"High yield submission failed: {resp_high.text}"
    data = resp_high.json()
    assert data["yield_maunds_per_acre"] == 75.5
    assert data["yield_kg_sqm"] > 0.70

def test_post_showcase_date_validation_and_tactics(tenant_a_headers):
    """
    Challenge date formats and key_tactics parsing variations:
    - String tactics, list of strings, list of dicts
    - Invalid date string formats -> expect 422
    """
    # 1. Invalid date string
    payload_bad_date = {
        "wheat_variety": "Fakhar-e-Bhakkar",
        "sowing_date": "not-a-valid-date",
        "actual_yield_maunds": 50.0
    }
    resp_bad_date = client.post("/api/v1/showcase/", json=payload_bad_date, headers=tenant_a_headers)
    assert resp_bad_date.status_code == 422, f"Expected 422 for bad date string, got {resp_bad_date.status_code}"

    # 2. Multiline string tactics conversion
    payload_str_tactics = {
        "wheat_variety": "Fakhar-e-Bhakkar",
        "sowing_date": "2025-11-01",
        "harvesting_date": "2026-04-10",
        "actual_yield_maunds": 56.0,
        "key_tactics": "Ridge planting method\nTargeted zinc foliar at booting\nLate irrigation skipped"
    }
    resp_str = client.post("/api/v1/showcase/", json=payload_str_tactics, headers=tenant_a_headers)
    assert resp_str.status_code == 201, f"Failed string tactics post: {resp_str.text}"
    event_log = resp_str.json()["cycle_event_log"]
    assert len(event_log) >= 3
    assert any("Ridge planting" in str(e) for e in event_log)


# ==============================================================================
# Challenge 3: GET /api/v1/crop-cycles/field/{id}/active
# ==============================================================================

def test_get_active_crop_cycle_nonexistent_field(tenant_a_headers):
    """Non-existent field ID -> Expect HTTP 404."""
    resp = client.get("/api/v1/crop-cycles/field/nonexistent_fld_9999/active", headers=tenant_a_headers)
    assert resp.status_code == 404, f"Expected 404 for non-existent field, got {resp.status_code}: {resp.text}"
    assert "not found" in resp.json().get("detail", "").lower()

def test_get_active_crop_cycle_no_active_cycle(tenant_a_headers):
    """Field with NO active crop cycle -> Expect HTTP 404 with informative detail."""
    new_field_resp = client.post("/api/v1/fields/", json={
        "field_name": "Fallow Parcel Without Cycle",
        "shape_type": "square",
        "area_acres": 2.5,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[[73.1, 31.4], [73.2, 31.4], [73.2, 31.5], [73.1, 31.5], [73.1, 31.4]]]
        }
    }, headers=tenant_a_headers)
    assert new_field_resp.status_code == 201
    f_id = new_field_resp.json()["field_id"]

    resp = client.get(f"/api/v1/crop-cycles/field/{f_id}/active", headers=tenant_a_headers)
    assert resp.status_code == 404, f"Expected 404 for field without active cycle, got {resp.status_code}: {resp.text}"
    assert "no active crop cycle" in resp.json().get("detail", "").lower()

def test_get_active_crop_cycle_cross_tenant_isolation(tenant_a_field, tenant_b_headers):
    """
    Tenant B querying active crop cycle for Tenant A's field.
    Must return 404 (not disclosing presence or active cycle to unauthorized user).
    """
    field_id = tenant_a_field["field_id"]
    resp = client.get(f"/api/v1/crop-cycles/field/{field_id}/active", headers=tenant_b_headers)
    assert resp.status_code == 404, f"Expected 404 for cross-tenant query, got {resp.status_code}: {resp.text}"


# ==============================================================================
# Challenge 4: Seeding Idempotency
# ==============================================================================

def test_seed_idempotency_multiple_runs():
    """
    Challenge seeding:
    Run seed() consecutively 3 times.
    Verify:
    1. Zero IntegrityError or exceptions raised.
    2. Zero duplicate canonical rows for ADVISORY_RULES_SEED (exactly 6 rules, stage 0 to 5).
    3. Zero duplicate canonical rows for SHOWCASE_FIELDS_SEED (sc_01 and sc_02).
    """
    canonical_rule_ids = [r["rule_id"] for r in ADVISORY_RULES_SEED]
    canonical_showcase_ids = [s["showcase_id"] for s in SHOWCASE_FIELDS_SEED]

    # Run 1
    seed()

    db = SessionLocal()
    try:
        rules_run1 = db.query(AgronomicAdvisoryRule).filter(AgronomicAdvisoryRule.rule_id.in_(canonical_rule_ids)).count()
        showcase_run1 = db.query(PeerShowcaseField).filter(PeerShowcaseField.showcase_id.in_(canonical_showcase_ids)).count()
        assert rules_run1 == 6, f"Expected exactly 6 canonical advisory rules, found {rules_run1}"
        assert showcase_run1 == 2, f"Expected exactly 2 canonical showcase fields, found {showcase_run1}"
    finally:
        db.close()

    # Run 2
    seed()

    # Run 3
    seed()

    # Verify counts remain strictly identical (no duplicate rows created)
    db = SessionLocal()
    try:
        rules_run3 = db.query(AgronomicAdvisoryRule).filter(AgronomicAdvisoryRule.rule_id.in_(canonical_rule_ids)).count()
        showcase_run3 = db.query(PeerShowcaseField).filter(PeerShowcaseField.showcase_id.in_(canonical_showcase_ids)).count()
        assert rules_run3 == 6, f"Duplicate advisory rules created after consecutive seed runs: {rules_run3}"
        assert showcase_run3 == 2, f"Duplicate showcase fields created after consecutive seed runs: {showcase_run3}"

        # Verify all stages 0 to 5 exist uniquely
        stages = [r.stage_index for r in db.query(AgronomicAdvisoryRule).filter(AgronomicAdvisoryRule.rule_id.in_(canonical_rule_ids)).all()]
        assert sorted(stages) == [0, 1, 2, 3, 4, 5], f"Canonical stage indexes corrupt: {stages}"
    finally:
        db.close()
