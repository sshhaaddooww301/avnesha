# Quantum-Inspired Cyber Threat Detection (QDS) SIEM Dashboard

A production-grade SIEM platform for quantum digital signature environments. All data flows from Qiskit simulation → FastAPI detection engine → PostgreSQL → WebSocket → Next.js dashboard. Zero hardcoded data.

## Environment

| Tool | Version | Status |
|------|---------|--------|
| Python | 3.10.0 | ✅ |
| Node.js | 24.11.0 | ✅ |
| npm | 11.6.2 | ✅ |
| PostgreSQL | User-managed | ✅ (localhost:5432, postgres/postgres) |
| Qiskit | To install | 🔄 |

---

## Architecture Overview

```mermaid
graph TB
    subgraph "Frontend (Next.js + TypeScript + Tailwind v3)"
        A[Dashboard] --> B[Logs & Events]
        A --> C[Threats]
        A --> D[Reports]
        A --> E[Settings]
        A --> WS[WebSocket Client]
    end

    subgraph "Backend (FastAPI + Python)"
        F[REST API Layer] --> G[Detection Engine]
        G --> H[Statistical Analyzer]
        G --> I[Rule Engine]
        G --> J[Risk Scorer]
        F --> K[Quantum Simulator - Qiskit]
        F --> L[Blockchain Audit Ledger]
        F --> M[WebSocket Server]
    end

    subgraph "Data Layer"
        N[(PostgreSQL)]
        O[security_events]
        P[threats]
        Q[audit_ledger]
        R[detection_rules]
        S[settings]
    end

    WS <--> M
    A <--> F
    G --> N
    K --> G
    L --> N
    N --> O
    N --> P
    N --> Q
    N --> R
    N --> S
```

---

## Project Structure

```
hackthon/
├── backend/                          # FastAPI application
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app, CORS, WebSocket, startup
│   │   ├── config.py                 # Environment/settings
│   │   ├── database.py               # SQLAlchemy engine + session
│   │   ├── models.py                 # ORM models (5 tables)
│   │   ├── schemas.py                # Pydantic schemas
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── dashboard.py          # /api/dashboard/*
│   │   │   ├── events.py             # /api/events/*
│   │   │   ├── threats.py            # /api/threats/*
│   │   │   ├── simulator.py          # /api/simulator/*
│   │   │   ├── ledger.py             # /api/ledger/*
│   │   │   ├── reports.py            # /api/reports/*
│   │   │   └── settings.py           # /api/settings/*
│   │   ├── engine/
│   │   │   ├── __init__.py
│   │   │   ├── detection.py          # Main detection pipeline
│   │   │   ├── rules.py              # Rule definitions (QDS-RPL-001, etc.)
│   │   │   ├── statistics.py         # Mean, variance, std, z-score, rolling avg
│   │   │   ├── risk_scorer.py        # Multi-factor risk score (0-100)
│   │   │   └── severity.py           # Risk→Severity mapping
│   │   ├── quantum/
│   │   │   ├── __init__.py
│   │   │   └── simulator.py          # Qiskit QDS simulator
│   │   ├── blockchain/
│   │   │   ├── __init__.py
│   │   │   └── ledger.py             # Hash-chain audit ledger
│   │   └── websocket/
│   │       ├── __init__.py
│   │       └── manager.py            # WebSocket connection manager
│   ├── requirements.txt
│   ├── .env
│   └── alembic/ (optional, can use create_all)
│
├── frontend/                         # Next.js application
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx            # Root layout, dark theme, fonts
│   │   │   ├── page.tsx              # Dashboard (main page)
│   │   │   ├── logs/page.tsx         # Logs & Events
│   │   │   ├── threats/
│   │   │   │   ├── page.tsx          # Threats list
│   │   │   │   └── [id]/page.tsx     # Threat detail
│   │   │   ├── reports/page.tsx      # Reports
│   │   │   └── settings/page.tsx     # Settings
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Navbar.tsx
│   │   │   │   └── Sidebar.tsx
│   │   │   ├── dashboard/
│   │   │   │   ├── AlertCards.tsx         # Severity count cards
│   │   │   │   ├── ActiveAlerts.tsx       # Alerts table
│   │   │   │   ├── AlertsOverTime.tsx     # Time-series chart
│   │   │   │   ├── SeverityDistribution.tsx # Pie/donut chart
│   │   │   │   ├── TopOffenses.tsx        # Bar chart
│   │   │   │   ├── RecentIncidents.tsx    # Recent threats
│   │   │   │   ├── LogTimeline.tsx        # Event timeline
│   │   │   │   └── SeverityBreakdown.tsx  # Stacked area chart
│   │   │   ├── common/
│   │   │   │   ├── DataTable.tsx
│   │   │   │   ├── StatusBadge.tsx
│   │   │   │   ├── SeverityBadge.tsx
│   │   │   │   ├── EmptyState.tsx
│   │   │   │   └── LoadingSpinner.tsx
│   │   │   └── threats/
│   │   │       ├── ThreatDetail.tsx
│   │   │       ├── QuantumAnalysis.tsx
│   │   │       └── AuditTrail.tsx
│   │   ├── lib/
│   │   │   ├── api.ts                # API client (fetch wrapper)
│   │   │   ├── websocket.ts          # WebSocket hook
│   │   │   └── types.ts              # TypeScript interfaces
│   │   └── hooks/
│   │       ├── useWebSocket.ts
│   │       ├── useDashboard.ts
│   │       └── useEvents.ts
│   ├── tailwind.config.ts
│   ├── next.config.js
│   ├── package.json
│   └── tsconfig.json
│
└── README.md
```

---

## Proposed Changes

### Phase 1: Backend Foundation

#### [NEW] `backend/requirements.txt`
Python dependencies: fastapi, uvicorn, sqlalchemy, asyncpg, psycopg2-binary, pydantic, python-dotenv, qiskit, qiskit-aer, websockets, python-jose, passlib, alembic.

#### [NEW] `backend/.env`
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/qds_siem
DATABASE_URL_SYNC=postgresql://postgres:postgres@localhost:5432/qds_siem
SECRET_KEY=<generated>
CORS_ORIGINS=http://localhost:3000
```

#### [NEW] `backend/app/config.py`
Pydantic Settings class loading from `.env`. All thresholds have defaults but are configurable.

#### [NEW] `backend/app/database.py`
Async SQLAlchemy engine with `create_async_engine`, session factory, and `create_all` on startup.

#### [NEW] `backend/app/models.py`

**5 PostgreSQL tables:**

| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `security_events` | id, event_id (UUID), timestamp, session_id, source_node, event_type, quantum_state, expected_measurement, observed_measurement, measurement_deviation, verification_result, signature_hash, metadata (JSONB), created_at | Raw QDS events |
| `threats` | id, threat_id (UUID), event_id (FK), threat_type, severity, risk_score, detection_rule, confidence, status, evidence (JSONB), detected_at, resolved_at | Detected threats |
| `audit_ledger` | id, block_index, event_id, event_hash, previous_hash, block_hash, timestamp, payload_hash | Tamper-evident chain |
| `detection_rules` | id, rule_id, name, description, enabled, parameters (JSONB) | Configurable rules |
| `system_settings` | id, key, value (JSONB), updated_at | Runtime config |

#### [NEW] `backend/app/schemas.py`
Pydantic models for request/response validation. Every API response is typed.

---

### Phase 2: Detection Engine

#### [NEW] `backend/app/engine/statistics.py`

Mathematical functions — **no faking**:

```python
def mean(values: list[float]) -> float
def variance(values: list[float]) -> float
def std_deviation(values: list[float]) -> float
def z_score(value: float, mean: float, std: float) -> float
def rolling_average(values: list[float], window: int) -> list[float]
def measurement_deviation(observed: float, expected: float) -> float
    # |observed - expected| / max(|expected|, epsilon)
def verification_failure_rate(session_events: list) -> float
def repeated_event_frequency(events: list, time_window: timedelta) -> float
```

#### [NEW] `backend/app/engine/rules.py`

5 detection rules, each a Python class:

| Rule ID | Name | Logic |
|---------|------|-------|
| QDS-RPL-001 | Replay Detection | Same signature_hash reused within configurable window (default 300s) |
| QDS-MITM-001 | MITM Detection | Verification failure + measurement deviation > threshold (default 30%) |
| QDS-FRG-001 | Forgery Detection | Signature hash mismatch against expected |
| QDS-IMP-001 | Impersonation Detection | Unauthorized session/source inconsistency |
| QDS-ANM-001 | Anomaly Detection | Z-score of measurement exceeds threshold (default 2.5σ) |

Each rule returns: `(triggered: bool, confidence: float, evidence: dict)`

#### [NEW] `backend/app/engine/risk_scorer.py`

Multi-factor weighted score:

```
risk_score = clamp(0, 100,
    w1 * deviation_score +      # 0-100 from measurement deviation
    w2 * verification_penalty + # 0 or 25 based on failure
    w3 * frequency_score +      # 0-100 based on repeat frequency
    w4 * anomaly_score +        # 0-100 from z-score magnitude
    w5 * hash_mismatch_penalty  # 0 or 20
)

Default weights: w1=0.30, w2=0.25, w3=0.15, w4=0.20, w5=0.10
```

Every risk score stores its breakdown in `threats.evidence`.

#### [NEW] `backend/app/engine/severity.py`

Configurable thresholds (from `system_settings`):
- 0–24 → Low
- 25–49 → Medium
- 50–74 → High
- 75–100 → Critical

#### [NEW] `backend/app/engine/detection.py`

Main pipeline orchestrator:
1. Receive event
2. Calculate measurement deviation
3. Query historical events for statistical context
4. Run all enabled rules
5. If any rule triggers → compute risk score → derive severity → create threat
6. Write to audit ledger
7. Broadcast via WebSocket

---

### Phase 3: Quantum Simulator

#### [NEW] `backend/app/quantum/simulator.py`

Qiskit-based QDS simulation:

- **Normal event**: Create Bell state circuit → measure → expect correlated outcomes → verification passes
- **Replay scenario**: Reuse same signature_hash from previous event
- **MITM scenario**: Inject measurement noise (rotation gate) → deviation > threshold
- **Forgery scenario**: Tamper with signature hash
- **Anomaly scenario**: Apply random unitary → unusual measurement distribution

Each scenario produces a `SecurityEvent` that enters the standard detection pipeline.

Simulation modes:
- `normal` — mostly legitimate events with occasional natural variance
- `attack_mix` — blend of normal + attack scenarios
- `specific` — generate a specific attack type
- `continuous` — generate events at intervals (for demo)

---

### Phase 4: Blockchain Audit Ledger

#### [NEW] `backend/app/blockchain/ledger.py`

```python
class AuditLedger:
    async def add_block(event_id, payload) -> AuditBlock:
        # 1. Serialize payload canonically (sorted JSON)
        # 2. payload_hash = SHA-256(canonical_payload)
        # 3. Get previous block's block_hash (or genesis "0"*64)
        # 4. event_hash = SHA-256(event_id + timestamp)
        # 5. block_hash = SHA-256(previous_hash + payload_hash + event_hash + timestamp)
        # 6. Store in audit_ledger table

    async def verify_chain() -> VerificationResult:
        # Walk entire chain, recalculate each block_hash
        # Return: valid (bool), total_blocks, first_invalid_block (if any)

    async def verify_block(block_index) -> bool:
        # Verify single block integrity
```

---

### Phase 5: API Layer

#### [NEW] `backend/app/api/dashboard.py`
- `GET /api/dashboard/summary` → severity counts, total events, total threats, verification rate
- `GET /api/dashboard/timeline` → alerts bucketed by time (1h/6h/1d/7d/30d)
- `GET /api/dashboard/severity-distribution` → percentage breakdown from DB
- `GET /api/dashboard/top-offenses` → `GROUP BY threat_type ORDER BY count DESC`

#### [NEW] `backend/app/api/events.py`
- `GET /api/events` → paginated, filterable, sortable
- `GET /api/events/{id}` → full event detail with related threats and audit block
- `POST /api/events` → manual event ingestion

#### [NEW] `backend/app/api/threats.py`
- `GET /api/threats` → paginated, filterable (severity, status, type)
- `GET /api/threats/{id}` → full threat detail with quantum analysis, evidence, audit
- `PATCH /api/threats/{id}/status` → update status (open → investigating → resolved)

#### [NEW] `backend/app/api/simulator.py`
- `POST /api/simulator/run` → trigger simulation (mode, count, interval)
- `GET /api/simulator/status` → current simulator state

#### [NEW] `backend/app/api/ledger.py`
- `POST /api/ledger/verify` → full chain verification
- `GET /api/ledger/status` → chain length, last block, integrity status

#### [NEW] `backend/app/api/reports.py`
- `GET /api/reports/summary` → comprehensive statistics
- `GET /api/reports/export?format=csv` → CSV export

#### [NEW] `backend/app/api/settings.py`
- `GET /api/settings` → all configurable settings
- `PUT /api/settings` → update settings (affects detection engine at runtime)

#### [NEW] `backend/app/main.py`
FastAPI app with:
- CORS middleware
- WebSocket endpoint `/ws`
- Router registration
- Startup: create tables, seed default rules and settings
- No hardcoded data anywhere

#### [NEW] `backend/app/websocket/manager.py`
Connection manager: broadcast new events/threats to all connected clients.

---

### Phase 6: Frontend — Next.js

#### [NEW] `frontend/` — Next.js project
Initialized with: `npx -y create-next-app@latest ./ --typescript --tailwind --eslint --app --src-dir --no-import-alias`

Tailwind v3 will be configured automatically by create-next-app.

#### [NEW] `frontend/src/lib/types.ts`
TypeScript interfaces matching backend schemas.

#### [NEW] `frontend/src/lib/api.ts`
Fetch wrapper with base URL from env, error handling, typed responses.

#### [NEW] `frontend/src/hooks/useWebSocket.ts`
WebSocket hook: auto-reconnect, parse incoming events/threats, trigger re-fetches.

#### [NEW] `frontend/src/app/layout.tsx`
Dark theme root layout with Inter font, navigation bar.

---

### Phase 7: Frontend — Dashboard Page

#### [NEW] `frontend/src/app/page.tsx` — Dashboard
Grid layout matching SIEM reference:
- Top row: 4 severity cards (Critical/High/Medium/Low)
- Middle: Active Alerts table + Alerts Over Time chart
- Bottom: Severity Distribution + Top Offenses + Recent Incidents + Log Timeline

All data fetched from `/api/dashboard/*` endpoints. Empty states shown when no data.

#### [NEW] Dashboard components (8 files)
Each component fetches its own data via SWR/fetch, renders with Recharts, shows `<EmptyState>` when no records exist.

---

### Phase 8: Frontend — Logs, Threats, Reports, Settings Pages

#### [NEW] `frontend/src/app/logs/page.tsx`
Full event explorer: search, filter (event_type, severity, session, source, date range), pagination, sorting. Click → detail modal.

#### [NEW] `frontend/src/app/threats/page.tsx`
Threat list with filters (severity, status, type). Click → threat detail page.

#### [NEW] `frontend/src/app/threats/[id]/page.tsx`
Full threat detail: quantum analysis, verification, evidence timeline, audit trail.

#### [NEW] `frontend/src/app/reports/page.tsx`
Statistical reports from `/api/reports/summary`. CSV export button.

#### [NEW] `frontend/src/app/settings/page.tsx`
Settings form: detection thresholds, severity ranges, anomaly sensitivity, replay window. Save → `PUT /api/settings`. System status cards (DB, quantum simulator, ledger).

---

## UI Design System

| Element | Specification |
|---------|--------------|
| Background | `#0a0e1a` (deep navy-black) |
| Card BG | `#111827` with `border border-gray-800` |
| Accent | Cyan `#06b6d4` for quantum theme |
| Critical | `#ef4444` red |
| High | `#f97316` orange |
| Medium | `#eab308` yellow |
| Low | `#22c55e` green |
| Font | Inter (Google Fonts) |
| Charts | Recharts with dark theme, cyan/green/orange/red palette |
| Icons | Lucide React |
| Animations | Subtle pulse on critical cards, smooth chart transitions |

---

## Data Flow (Zero Hardcoded)

```mermaid
sequenceDiagram
    participant U as User/Simulator
    participant API as FastAPI
    participant DE as Detection Engine
    participant DB as PostgreSQL
    participant BL as Audit Ledger
    participant WS as WebSocket
    participant UI as Dashboard

    U->>API: POST /api/simulator/run
    API->>DE: Generate Qiskit events
    DE->>DE: Calculate deviation, stats
    DE->>DE: Run rule engine
    DE->>DE: Compute risk score
    DE->>DB: INSERT security_event
    DE->>DB: INSERT threat (if detected)
    DE->>BL: Add audit block
    BL->>DB: INSERT audit_ledger
    DE->>WS: Broadcast new event/threat
    WS->>UI: Real-time update
    UI->>API: GET /api/dashboard/summary
    API->>DB: SELECT COUNT(*) GROUP BY severity
    DB->>API: {critical: N, high: N, ...}
    API->>UI: JSON response
    UI->>UI: Render (or show "No data")
```

---

## Verification Plan

### Automated Tests
```bash
# Backend
cd backend && python -m pytest tests/ -v

# Frontend
cd frontend && npm run build  # Type-check + build verification
```

### Manual Verification
1. Start backend: `uvicorn app.main:app --reload`
2. Start frontend: `npm run dev`
3. Open dashboard — should show "No security events available"
4. Run simulator via UI → events appear in real-time
5. Verify severity counts match DB queries
6. Verify ledger integrity via `/api/ledger/verify`
7. Change detection thresholds in Settings → verify detection behavior changes
8. Verify no hardcoded data by inspecting empty-state behavior

---

## Open Questions

> [!IMPORTANT]
> **Database creation**: I'll need to create the `qds_siem` database in your PostgreSQL instance. Should I run `CREATE DATABASE qds_siem` automatically on startup, or do you want to create it manually first?

> [!NOTE]
> **Authentication**: The spec mentions authentication for admin functions. For the prototype, I'll implement a simple JWT-based auth with a default admin user. The login page will be minimal — the focus is on the SIEM functionality. Is this acceptable, or should I skip auth entirely for now?

> [!NOTE]
> **Qiskit installation**: Qiskit + Aer can take 5-10 minutes to install. I'll start that early in parallel with other setup. If installation fails on Windows, I have a numpy-based fallback simulator that produces identical event structures.
