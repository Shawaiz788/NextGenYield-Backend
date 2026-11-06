# NextGenYield Backend & Mobile Integration Walkthrough

## Overview
We built and integrated a production-grade **FastAPI Backend** inside the `backend/` directory for the **NextGenYield** project, strictly aligned with:
- **`schema.sql`** (All 8 relational tables and performance indexes)
- **`F26-201.pdf`** (SRS Chapters 4 & 5: System architecture, functional use cases UC1–UC9, sequence diagrams, and data dictionaries)
- **`NEXTGENYIELD_IMPLEMENTATION_REPORT.md`** & **`masterdoc.md`** (API contracts, phenological definitions, and Punjab agronomic protocol)
- **Supabase Integration** (PostgreSQL persistence & Supabase Storage for canopy photos)

---

## 1. Backend Architecture & Components Implemented

### Persistence Layer (`backend/app/models/`)
Directly mapped from `schema.sql`:
1. **`User`** (`users`): Primary key `user_id`, `full_name`, unique `phone_number`, `password_hash` (bcrypt), `role` (`farmer`, `landowner`, `stakeholder`), `district`, `language_pref` (`en`, `ur`), and timestamp.
2. **`Field`** (`fields`): `field_id`, foreign key `user_id`, `field_name`, `shape_type` (`square`, `rectangle`, `polygon`, `circle`), `area_acres`, `area_sqm`, `boundary_geojson` (RFC 7946 GeoJSON), `center_latitude`, `center_longitude`, and `current_cycle_id`.
3. **`CropCycle`** (`crop_cycles`): `cycle_id`, foreign key `field_id`, `wheat_variety`, `seed_company`, `fertilizer_company`, `sowing_method`, `sowing_date`, `target_harvest_date` (140-day wheat cycle), and `is_active`.
4. **`FieldObservation`** (`field_observations`): `observation_id`, `cycle_id`, `image_uri`, `stage_index` (0–5), `stage_name`, `confidence`, `pitch_angle_deg` ($45^\circ-60^\circ$ compliance), `blur_score`, and `das` (Days After Sowing).
5. **`FertilizerSchedule`** (`fertilizer_schedules`): 3 automated splits (Basal DAP + SOP, 1st Topdress Urea at CRI, 2nd Topdress Urea + Zinc).
6. **`IrrigationSchedule`** (`irrigation_schedules`): 5 key wheat watering milestones (Crown Root, Tillering, Booting, Flowering, Grain Filling).
7. **`PeerShowcaseField`** (`peer_showcase_fields`): Verified benchmark plots with yields of 54–62 Maunds/Acre and full 140-day timeline logs.
8. **`AgronomicAdvisoryRule`** (`agronomic_advisory_rules`): Bilingual (Urdu & English) deterministic advice, risk alerts, and spoken Urdu narration scripts for all 6 phenological wheat stages.

---

## 2. API Endpoints Created (`backend/app/routers/`)

| Route | Method | Description | Aligned Use Case |
|---|---|---|---|
| `/api/v1/auth/register` | `POST` | Registers farmer with phone, full name, district, PIN/password | **UC1 (Registration)** |
| `/api/v1/auth/login` | `POST` | Authenticates farmer by phone number & PIN; returns JWT | **UC2 (Login)** |
| `/api/v1/auth/me` | `GET`, `PUT` | View/update current farmer profile | **UC1, UC2** |
| `/api/v1/fields/` | `GET`, `POST` | Demarcate parcel with GeoJSON boundary & auto-centroid | **UC3 (Demarcation)** |
| `/api/v1/fields/{id}` | `GET`, `DELETE`| Inspect or remove field parcel | **UC3** |
| `/api/v1/crop-cycles/start` | `POST` | Initializes 140-day crop cycle & generates all schedules | **UC4 (Crop Cycle Init)** |
| `/api/v1/crop-cycles/{id}` | `GET` | View active cycle with fertilizer & irrigation plans | **UC4** |
| `/api/v1/crop-cycles/fertilizer/{id}/apply` | `PUT` | Mark fertilizer split as applied | **UC4** |
| `/api/v1/crop-cycles/irrigation/{id}/complete` | `PUT` | Mark irrigation milestone completed | **UC4** |
| `/api/v1/observations/` | `POST` | Upload canopy photo & sensor data (Supabase Storage) | **UC5 & UC7 (Timeline)** |
| `/api/v1/observations/cycle/{id}` | `GET` | Chronological photo timeline since sowing | **UC7** |
| `/api/v1/advisory/rules` | `GET` | Deterministic bilingual agronomic advisory rules (0–5) | **UC6 (Advisory)** |
| `/api/v1/showcase/` | `GET` | View verified top-yielding plots (54–62 Maunds/Acre) | **UC9 (Showcase)** |

---

## 3. Supabase Integration Setup

In `backend/.env.example` and `backend/app/config.py`:
- Configured direct PostgreSQL connection for Supabase:
  ```env
  DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
  ```
- Configured Supabase Storage service (`backend/app/services/supabase_storage.py`) for uploading canopy photos to bucket `field-observations`:
  ```env
  SUPABASE_URL=https://<project-ref>.supabase.co
  SUPABASE_KEY=<anon-or-service-role-key>
  SUPABASE_BUCKET_NAME=field-observations
  ```
- Graceful offline fallback: If Supabase credentials are not yet entered, the backend persists to local SQLite and saves images to `backend/uploads/` seamlessly.

---

## 4. Frontend Integration (`frontend/`)

1. **API Client (`frontend/services/api-client.ts`)**:
   - Manages bearer JWT authentication tokens.
   - Provides strongly-typed helper methods for `register`, `login`, `getFields`, `createField`, `startCropCycle`, `getAdvisoryRules`, and `getShowcaseFields`.
2. **Auth Screen (`frontend/app/auth.tsx`)**:
   - Connected `handleSubmit` to call `api.login` and `api.register`.
   - Normalizes phone numbers (e.g. `+92 300 ...` or `0300 ...`).
   - Implements resilient offline fallback so the farmer can still navigate and use the application even when in low-connectivity fields.
3. **Type Safety & Build Verification**:
   - Ran `npx tsc --noEmit` on the Expo frontend; completed with **0 errors**.

---

## 5. Verification Results

### Backend Automated Test Suite
Ran `pytest tests/test_backend_flow.py`:
```
collected 4 items
tests/test_backend_flow.py .... [100%]
======================== 4 passed, 1 warning in 2.92s =========================
```
- Verified `GET /health` online status and database connectivity.
- Verified registration of farmer `03009988776` with PIN `pass1234password`.
- Verified authentication via `POST /api/v1/auth/login` and JWT token exchange.
- Verified field parcel demarcation with GeoJSON polygon and acreage calculation.
- Verified starting 140-day crop cycle and automatic generation of 3 fertilizer splits and 5 irrigation events.
- Verified retrieval of deterministic advisory rules across all 6 phenological wheat growth stages.

