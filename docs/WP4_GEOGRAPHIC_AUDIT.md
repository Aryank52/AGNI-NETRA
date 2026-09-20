# AGNI-NETRA — WP4 Geographic Subsystem & Sovereign Domain Audit

**Document ID:** AUDIT-WP4-GEO-001  
**Classification:** Sovereign Engineering Audit / Unclassified  
**Component:** Geographic Domain & Boundary Intelligence Subsystem  
**Target Environment:** PostgreSQL 16 + PostGIS 3.4 / TimescaleDB  
**Audit Baseline:** WP3 Completed (`d7d8cb1`), Phase 26 Frozen (`eb7824e6`)  
**Status:** COMPLETE & VERIFIED  

---

## 1. Executive Summary & Objective

This deep technical audit traces every pathway in the AGNI-NETRA source tree where geographic coordinates (`latitude`, `longitude`, bounding boxes, spatial polygons, place names) enter, mutate, route, or exit the system. 

The audit evaluates whether India-domain enforcement is authoritative, consistent, auditable, and impossible to bypass accidentally across ingestion, event generation, context fusion, machine learning, the JARVIS autonomous observer, GIS APIs, and public interfaces.

Findings are classified according to the empirical taxonomy:
- **`IMPLEMENTED`**: Production-ready, authoritative PostGIS geometry enforcement.
- **`PARTIALLY IMPLEMENTED`**: Functional in specific layers but bypassed or uncoupled in others.
- **`INCORRECT`**: Flawed logic (e.g. bounding box approximation, random state guessing, silent coordinate swapping).
- **`DEGRADED`**: Fallback paths that degrade epistemic certainty without alerting operators.
- **`MISSING`**: Required capability completely absent from the code path.
- **`SIMULATED`**: Synthetic simulation data (AGNI-SAT digital twin) that must be quarantined from sovereign operational alerts.
- **`NOT CONFIGURED`**: Capability coded but missing production database bindings or migrations.
- **`OUT OF SCOPE`**: Features unrelated to sovereign geographic domain enforcement.

---

## 2. Ingress Point Matrix (Tracing Lat/Lon across AGNI-NETRA)

| # | Subsystem Path | Ingress Form | Current Validation Logic | Target Classification |
|---|---|---|---|---|
| **P-01** | `data_pipeline/adapters/firms_adapter.py` | CSV `(latitude, longitude)` | Float conversion; skips non-floats. No sovereign boundary check. | **PARTIALLY IMPLEMENTED** |
| **P-02** | `backend/app/services/ingestion/hardened_ingestion_service.py` | Observation payload dicts | `-90 <= lat <= 90` and `-180 <= lon <= 180`. Passes foreign coordinates to WP1. | **PARTIALLY IMPLEMENTED** |
| **P-03** | `backend/app/services/spatial_engine.py` (`validate_coordinates`) | `(lat, lon)` float | `5.0 <= lat <= 39.0 and 65.0 <= lon <= 100.0`. Coarse bounding box proxy! | **INCORRECT** |
| **P-04** | `backend/app/services/spatial_engine.py` (`lookup_state` / `lookup_district`) | `(lat, lon)` float | `INDIAN_STATES_BOUNDS` dictionary BBOX lookup; returns hardcoded default districts. | **INCORRECT** |
| **P-05** | `backend/app/services/autonomous_intelligence_service.py` | `(lat, lon)` in cluster | `INDIA_LAT_MIN (6.0) <= lat <= INDIA_LAT_MAX (38.0)`. Falls back to `"Gujarat"` and `"Kutch"`. | **INCORRECT** |
| **P-06** | `backend/app/services/clustering_service.py` | Centroid `(lat, lon)` | `lookup_state(centroid_lat, centroid_lon)` with BBOX proxy. | **INCORRECT** |
| **P-07** | `backend/app/services/india_boundary_service.py` (`is_point_inside_india`) | `(lat, lon)` float | PostGIS `ST_Within(point, geom)` on `admin_boundaries` (`admin_level = 1`). Fallback guesses Gujarat/Jharkhand. | **DEGRADED** |
| **P-08** | `backend/app/services/jarvis/jarvis_mission_service.py` | Natural language text | Keyword regex against 17 foreign territories (Lahore, Karachi, etc.). No coordinate geofence check. | **PARTIALLY IMPLEMENTED** |
| **P-09** | `backend/app/services/jarvis/jarvis_agentic_orchestrator.py` | Thermal event coordinates | Relies on upstream event `latitude`/`longitude`. Lacks 5-tier location classification. | **PARTIALLY IMPLEMENTED** |
| **P-10** | `backend/app/api/v1/endpoints/gis.py` (`parse_bbox`) | `min_lon,min_lat,max_lon,max_lat` | Silently swaps min/max if inverted (`if min_lon > max_lon: min_lon, max_lon = max_lon, min_lon`). | **INCORRECT** |
| **P-11** | `backend/app/api/v1/endpoints/portals.py` | Public hazard map API | Filters active events; does not enforce PostGIS sovereign containment at API boundary. | **PARTIALLY IMPLEMENTED** |
| **P-12** | `backend/app/services/report_service.py` | Incident coordinates | Formats lat/lon into PDF/JSON. Does not assert sovereign verification state. | **PARTIALLY IMPLEMENTED** |
| **P-13** | `backend/app/services/satellite_simulator.py` | Digital twin simulation | Simulates orbital overpasses across predefined Indian sites. Strictly simulation. | **SIMULATED** |

---

## 3. Comprehensive Subsystem Audit Findings

### 3.1 Finding F-GEO-01: Bounding-Box Used as Final Country Proxy in Spatial Engine
- **Location:** `backend/app/services/spatial_engine.py` (Lines 22–34, 139–178)
- **Current Behavior:**
  ```python
  def validate_coordinates(lat: float, lon: float) -> bool:
      ...
      return (5.0 <= lat <= 39.0 and 65.0 <= lon <= 100.0)
  ```
  `INDIAN_STATES_BOUNDS` defines crude rectangular envelopes for 15 states with hardcoded default districts (e.g., Gujarat defaulting to Jamnagar, MP defaulting to Singrauli, Chhattisgarh to Korba).
- **Classification:** **`INCORRECT`**
- **Impact:** Foreign territory within the bounding box (Lahore, Karachi, Kathmandu, Dhaka, Sri Lanka, Arabian Sea) passes validation if not checked against polygon geometry. State and district assignments are fabricated based on bounding boxes rather than actual boundary containment.
- **Required Remediation:** Route coordinate validation and administrative lookup through authoritative PostGIS `admin_boundaries` geometry. Deprecate bounding box guessing. Return `UNKNOWN` when assignment cannot be verified.

---

### 3.2 Finding F-GEO-02: Silent State & District Fallbacks in Autonomous Intelligence Core
- **Location:** `backend/app/services/autonomous_intelligence_service.py` (Lines 321–323)
- **Current Behavior:**
  ```python
  state = lookup_state(c_lat, c_lon) or "Gujarat"
  district = lookup_district(c_lat, c_lon) or "Kutch"
  state_code = state[:3].upper() if state else "IND"
  ```
- **Classification:** **`INCORRECT`**
- **Impact:** Any point failing spatial resolution (including international waters or border regions) is silently assigned to `"Gujarat"` / `"Kutch"`. This fabricates administrative ground truth and generates incorrect event codes (`EVT-GUJ-...`).
- **Required Remediation:** If PostGIS containment confirms the point is in India but the district is unresolvable, set `state = state_name`, `district = "UNKNOWN"`. If outside India, reject the observation before event creation.

---

### 3.3 Finding F-GEO-03: Hardcoded State Guessing in Boundary Service Fallback
- **Location:** `backend/app/services/india_boundary_service.py` (Lines 277–293)
- **Current Behavior:**
  ```python
  # Coarse fallback when PostGIS spatial tables are not present
  if 6.0 <= lat <= 38.0 and 68.0 <= lon <= 98.0:
      return {
          "is_inside_india": True,
          "state_name": "Gujarat" if (20.0 <= lat <= 24.5 and 68.0 <= lon <= 74.5) else "Jharkhand",
          "district_name": "Jamnagar" if (20.0 <= lat <= 24.5 and 68.0 <= lon <= 74.5) else "Dhanbad",
          ...
      }
  ```
- **Classification:** **`DEGRADED`**
- **Impact:** When database connections experience transient issues or in non-PostGIS fallback modes, the service fabricates Gujarat/Jamnagar or Jharkhand/Dhanbad identities.
- **Required Remediation:** Remove all fabricated fallbacks. When spatial queries fail, raise a transient error or return `is_inside = False, state = "UNKNOWN", district = "UNKNOWN"`.

---

### 3.4 Finding F-GEO-04: Ingestion Plane Lacks Authoritative Sovereign Containment Gate
- **Location:** `backend/app/services/ingestion/hardened_ingestion_service.py`
- **Current Behavior:**
  `HardenedIngestionService.process_batch()` validates numerical coordinate bounds (`-90 <= lat <= 90`, `-180 <= lon <= 180`), executes SHA-256 deduplication, and forwards valid detections directly to `PipelineService.process_observations()`. It does not verify sovereign India polygon containment before forwarding.
- **Classification:** **`PARTIALLY IMPLEMENTED`**
- **Impact:** Foreign satellite detections (e.g. from regional NASA FIRMS South Asia subscriptions covering Pakistan, Nepal, Bangladesh, or Sri Lanka) pass through ingestion and enter the proactive intelligence pipeline.
- **Required Remediation:** Enforce authoritative `is_within_india(lat, lon)` during the validation phase of `HardenedIngestionService`. Divert foreign observations to `ingestion_quarantine` with category `INVALID_COORDINATES` and reason `SOVEREIGN_OUT_OF_DOMAIN`.

---

### 3.5 Finding F-GEO-05: Silent Coordinate Inversion in GIS Bounding Box Parser
- **Location:** `backend/app/api/v1/endpoints/gis.py` (Lines 82–85)
- **Current Behavior:**
  ```python
  if min_lon > max_lon:
      min_lon, max_lon = max_lon, min_lon
  if min_lat > max_lat:
      min_lat, max_lat = max_lat, min_lat
  ```
- **Classification:** **`INCORRECT`**
- **Impact:** Clients passing malformed, inverted, or reversed coordinates (e.g. lat/lon swapped with lon/lat) have their input silently modified rather than receiving explicit contract feedback (`HTTP 400 Bad Request`).
- **Required Remediation:** Strictly disallow coordinate inversion. Return `HTTP 400 Bad Request` with an explicit diagnostic message if `min_lon > max_lon` or `min_lat > max_lat`.

---

### 3.6 Finding F-GEO-06: JARVIS Location Grounding Relies on Text Heuristics
- **Location:** `backend/app/services/jarvis/jarvis_mission_service.py` (Lines 64–86)
- **Current Behavior:**
  `JarvisObjectiveNormalizer` checks objective text against a static list of 17 foreign place names (`sri lanka`, `colombo`, `pakistan`, `lahore`, `karachi`, `china`, etc.). If an unlisted foreign location is supplied (e.g. "Islamabad", "Kandahar", "Chittagong", or raw coordinates `31.52, 74.35`), it is not caught by the keyword check.
- **Classification:** **`PARTIALLY IMPLEMENTED`**
- **Impact:** Natural language commands with uncataloged foreign places or raw foreign coordinates could trigger contextual queries against Indian facilities.
- **Required Remediation:** Implement 5-tier location classification:
  1. `EXPLICIT_USER_LOCATION`
  2. `RESOLVED_LOCATION`
  3. `AUTHORITATIVE_GIS_LOCATION`
  4. `UNKNOWN_LOCATION`
  5. `OUT_OF_DOMAIN_LOCATION`
  Verify all parsed coordinates and named entities against PostGIS authoritative boundaries. Reject out-of-domain targets with `OUT_OF_DOMAIN_LOCATION`.

---

### 3.7 Finding F-GEO-07: Public Hazard Map Lacks API-Boundary Geographic Sanitization
- **Location:** `backend/app/api/v1/endpoints/portals.py` (Lines 269–340)
- **Current Behavior:**
  `get_public_hazard_map` queries `ThermalEvent` and masks facility names. However, it does not explicitly enforce sovereign India containment at the query level or apply coordinate blurring to sensitive strategic facility centroids.
- **Classification:** **`PARTIALLY IMPLEMENTED`**
- **Impact:** Potential leakage of unblurred coordinates of sensitive sovereign industrial infrastructure to unauthorized public consumers.
- **Required Remediation:** Add explicit sovereign containment filter and coordinate blurring (2 decimal places ~ 1.1 km resolution) for all public portal hazard responses.

---

## 4. Summary Matrix of Findings & Action Plan

| Finding ID | Component | Current State | Required WP4 Action | Target State |
|---|---|---|---|---|
| **F-GEO-01** | `spatial_engine.py` | BBOX proxy (5–39, 65–100) | Enforce PostGIS `is_within_india` | **IMPLEMENTED** |
| **F-GEO-02** | `autonomous_intelligence_service.py` | Silent fallback to "Gujarat"/"Kutch" | Set `UNKNOWN`, preserve epistemic state | **IMPLEMENTED** |
| **F-GEO-03** | `india_boundary_service.py` | Hardcoded state guessing on fallback | Eliminate guessing; return unassigned | **IMPLEMENTED** |
| **F-GEO-04** | `hardened_ingestion_service.py` | Numerical bounds only; no country check | Quarantine foreign observations to DLQ | **IMPLEMENTED** |
| **F-GEO-05** | `gis.py` | Silent coordinate swapping | Reject inverted BBOX with HTTP 400 | **IMPLEMENTED** |
| **F-GEO-06** | `jarvis_mission_service.py` | Keyword list regex only | 5-tier location classification + PostGIS | **IMPLEMENTED** |
| **F-GEO-07** | `portals.py` | Unblurred public coordinates | Enforce sovereign filter + coordinate blurring | **IMPLEMENTED** |
