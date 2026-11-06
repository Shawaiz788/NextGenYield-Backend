# NextGenYield — AI Agent Operational & Architectural Guidelines

This document serves as the permanent system instructions and standard operating procedure for all AI agents working on the **NextGenYield** codebase. Adhere strictly to these principles and techniques to maintain production-level quality, architectural consistency, and UI integrity.

---

## 1. System Architecture Overview

NextGenYield is an intelligent wheat crop decision support and vision AI platform consisting of two independent services:

```
NextGenYield/
├── frontend/               # Expo SDK 54 / React Native 0.81 / Expo Router v6
│   ├── app/                # File-based navigation screens
│   ├── components/         # Reusable UI widgets
│   ├── context/            # Global state (AppProvider: auth, language, active field)
│   ├── hooks/              # Custom React & TanStack Query hooks
│   ├── services/           # API clients, logger, model inference services
│   └── constants/          # Theme, colors, typography, layout tokens
│
└── backend/                # FastAPI (Python 3.11+) + SQLAlchemy 2.0 + Supabase
    ├── app/
    │   ├── api/            # API v1 routers (auth, fields, cycles, advisory, showcase)
    │   ├── core/           # Database engine, JWT, bcrypt security
    │   ├── models/         # SQLAlchemy 2.0 ORM models
    │   ├── schemas/        # Pydantic v2 validation models
    │   └── services/       # Agronomic schedule engine, Supabase storage
    └── tests/              # Pytest end-to-end integration test suite
```

### Decoupled Dual-API Architecture
- **Inference Server**: `EXPO_PUBLIC_MODEL_API_URL` (ViT-B/14 Vision Model, hardware telemetry, growth stage classification).
- **CRUD & Auth Server**: `EXPO_PUBLIC_BACKEND_API_URL` (FastAPI backend, Supabase PostgreSQL, canopy image storage).
- **Rule**: Never couple model inference requests to the CRUD backend. Keep network paths isolated.

---

## 2. Frontend Engineering Standards (React Native / Expo)

### A. State Management & API Calls: TanStack Query
- **Rule**: All asynchronous server state (queries and mutations) MUST use `@tanstack/react-query`.
- **Hooks Pattern**: Encapsulate API mutations and queries inside dedicated hooks under `frontend/hooks/` (e.g., `use-auth-mutations.ts`, `use-growth-stage.ts`).
- **Optimistic Updates & Invalidation**: Invalidate affected query keys upon mutation success (`queryClient.invalidateQueries(...)`).
- **Retries & Stale Time**: Use sensible defaults (e.g., retry 1 on transient failures, background polling intervals suited to battery life).

### B. Form Validation & Gatekeeping
- **Strict Pre-flight Validation**: Never allow an API call to be dispatched if form inputs are invalid or missing.
- **Pakistan Phone Standard**: Mobile numbers must be validated and normalized to standard Pakistani format (`03XXXXXXXXX` or `+923XXXXXXXXX`, 10/11 digits).
- **Immediate Inline Feedback**: Show clear error hints below invalid inputs and outline the input with error styling (`#EF4444`).
- **Forgiving UX**: Clear error state immediately as soon as the user edits the field.
- **Bilingual Support**: All error messages and validation texts must support both English and Urdu based on the user's active language preference (`isUrdu`).

### C. Progressive UI & Button States
- **Dynamic Feedback**: Action buttons must communicate their active state:
  - `idle`: Clear action label (e.g., "Sign In", "Create Account") with directional icon.
  - `sending`: Spinner (`ActivityIndicator`) + in-flight text (e.g., "Sending request...", "Connecting...").
  - `success`: Checkmark icon + transition confirmation (e.g., "Moving to home screen...").
- **Double-Submit Prevention**: Disable buttons (`disabled={true}`) whenever a mutation is pending or transitioning.

### D. Logging & Diagnostic Integrity (`logger.ts`)
- **No Raw Console Logs**: Do NOT place bare `console.log` in production code.
- **Use Logger Service**: Use `@/services/logger` (`logger.info`, `logger.warn`, `logger.error`, `logger.debug`).
- **Dev-Only Execution**: The logger checks `__DEV__` to ensure debugging traces are completely stripped/silenced in production releases.
- **Contextual Prefixes**: Always prefix logs with domain tags (e.g., `[NextGenYield:API]`, `[NextGenYield:Auth]`).

### E. Backend Reachability & Error Handling
- **Never Silently Swallow Errors**: Do not silently failover to offline mocks without informing the user.
- **Unreachable Backend Feedback**: If the backend cannot be reached (`BackendUnreachableError`, connection refused, network timeout):
  - Surface a prominent warning banner explaining that the server at `targetUrl` is unreachable.
  - Provide a "Retry" button and an optional explicit "Continue Offline" button.
  - Provide a dev-mode hint indicating that diagnostic logs have been written to the logger.

### F. UI / UX Design Integrity
- **Preserve Existing Styling**: Never modify or destroy established color palettes (`#16A34A`, `#F0FDF4`, `#F8FAFC`), fonts (Inter family), card elevation, border radiuses, or layout padding unless explicitly requested.
- **Urdu RTL & Typography**: Ensure Urdu typography renders legibly without clipping.

---

## 3. Backend Engineering Standards (FastAPI & Database)

### A. Supabase PostgreSQL Connectivity
- **IPv4 Pooler Required**: Always use the Supabase Connection Pooler (`aws-0-ap-southeast-2.pooler.supabase.com:5432` with user `postgres.<project-ref>`). Direct database endpoints may fail to resolve on IPv4-only networks.
- **Pydantic v2 Compliance**: Always use `ConfigDict(from_attributes=True)` and `model_validate`. Do not use deprecated Pydantic v1 methods (`from_orm`, class `Config`).
- **Password Security**: Use `bcrypt` directly with input clamping to 72 bytes to prevent buffer overflow/truncation errors.

### B. Supabase Storage
- **Service Role Key**: Use the `service_role` (Secret) key in backend environments to bypass storage RLS for field observation uploads.
- **Local Fallback**: Maintain local disk fallback (`uploads/`) if storage credentials are not provided.

### C. Execution Commands on Windows
- Always run the backend server with:
  ```powershell
  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
  ```
- Run tests with:
  ```powershell
  pytest tests/test_backend_flow.py -v
  ```

---

## 4. AI Agent Workflow & Verification Protocol

Before declaring any feature or fix complete, every AI assistant must execute the following checklist:

1. **Static Analysis & Types**:
   - Run `npx tsc --noEmit` inside `frontend/` and ensure 0 TypeScript errors.
2. **Backend Regression Test**:
   - Run `pytest` inside `backend/` and verify all integration tests pass.
3. **Environment Security**:
   - Verify that secrets, `.env` files, and credentials are never staged or committed to Git.
4. **Validation & State Check**:
   - Confirm all forms have pre-flight validation, progressive buttons, and graceful unreachable network banners.
