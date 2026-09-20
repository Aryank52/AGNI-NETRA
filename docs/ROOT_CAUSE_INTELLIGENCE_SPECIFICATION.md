# AGNI-NETRA — Root-Cause Intelligence Specification
**Standard**: 13-Category Deterministic Root-Cause Physical Taxonomy  
**Implementation**: `backend/app/services/intelligence/root_cause_intelligence_service.py`  
**Engine**: Mathematical Scoring & Spatial-Temporal Feature Correlator  
**Guarantees**: Transparent scoring, zero generative hallucinations, explicit epistemic caveats

---

## 1. 13-Category Physical Root-Cause Taxonomy

The system defines 13 mutually distinct physical root-cause categories reflecting the industrial and geographic reality of the Indian subcontinent:

| # | Category Code | Canonical Title | Primary Industrial / Geographic Domain | Key Spatial & Physical Indicators |
|---|---|---|---|---|
| 1 | `CONTINUOUS_FLARING` | Continuous Flaring (Flare Tip / Knockout Drum) | Petroleum Refineries, Petrochemicals, Gas Processing | Proximity &le; 500m to refinery polygon, persistence &gt; 0.60, steady FRP signature |
| 2 | `PETROCHEMICAL_PROCESS_LEAK` | Fugitive Hydrocarbon / Process Unit Leak | Petrochemical Plants, Polymer Complexes, Cracker Units | High FRP anomaly (&gt; 1.5x baseline), industrial landcover, non-flare footprint |
| 3 | `TANK_FARM_STORAGE` | Tank Farm / Hydrocarbon Storage Vapor Ignition | Bulk Fuel Terminals, POL Depots, Strategic Reserves | Overlap with POL storage terminal, elevated intensity, episodic non-continuous spike |
| 4 | `COAL_MINING_SPOIL_BURNING` | Coal Spoil Overburden Spontaneous Combustion | Opencast Coal Mines (CIL, SCCL, Captive Blocks) | Intersects IBM coal concession, high persistence, sub-surface smoldering profile |
| 5 | `THERMAL_POWER_PLANT_EMISSION` | Thermal Power Ash Pond / Coal Stockyard Ignition | Coal-Fired Thermal Power Stations (CEA Registry) | Within 1.5 km of CEA thermal plant, high persistent baseline, stack vicinity |
| 6 | `AGRICULTURAL_STUBBLE_BURNING` | Agricultural Residue Open Burning | Croplands, Rural Agricultural Basins (Punjab, Haryana, etc.) | Cropland LULC, seasonal cluster, rapid dispersion, low persistence (&lt; 0.20) |
| 7 | `LANDFILL_BIOGAS_COMBUSTION` | Municipal Solid Waste Landfill Methane Fire | Urban Dumpsites, Municipal Waste Yards | Urban/waste LULC, sustained localized hotspot, proximity to urban center |
| 8 | `FORESTRY_BIOMASS_FIRE` | Forest Surface / Biomass Fire | Reserved/Protected Forest, Woodland, Hilly Terrain | Tree cover / Forest LULC, spreading convex hull, high FRP variance, non-industrial |
| 9 | `DRY_BULK_CARGO_SELF_HEATING` | Dry Bulk Cargo / Coal Stockyard Self-Heating | Major/Minor Ports, Bulk Mineral Berths | Port / Coastal terminal boundary, bulk coal or mineral storage yard |
| 10 | `ILLEGAL_COAL_DEPOT` | Unregulated Coal Depot / Smuggling Pit Smoldering | Non-Lease Mining Peripheries, Unlicensed Railheads | Unregistered industrial point near coal belt, intermittent nocturnal thermal detections |
| 11 | `DRILLING_RIG_BLOWOUT` | Exploration / Production Well Blowout | Onshore/Offshore Oil & Gas Wells | Upstream wellhead concession, sudden extreme FRP spike, continuous day/night |
| 12 | `ELECTRICAL_SUBSTATION_ARCING` | High-Voltage Substation / Transformer Arcing | 400kV/765kV Grid Substations, Switchyards | CEA Substation node proximity &le; 300m, acute high-temperature brief signature |
| 13 | `CRUDE_OIL_PIPELINE_RUPTURE` | Trunk Pipeline Leak / Rupture Ignition | Cross-Country Pipeline Right-of-Way (ROW) | Linear intersection with pipeline corridor, sudden unheralded thermal detection |

---

## 2. Hypothesis Verification Status State Machine

Each of the 13 hypotheses is assigned one of four definitive verification statuses:
1. **`CONFIRMED`** (`confidence_score >= 0.80`): Spatial boundary intersection verified, multi-sensor radiometric profile matches equipment footprint, historical baseline persistent.
2. **`PLAUSIBLE`** (`0.45 <= confidence_score < 0.80`): Geographic context and sensor signatures are consistent with physical driver; secondary verification recommended.
3. **`UNLIKELY`** (`0.15 <= confidence_score < 0.45`): Key physical indicators absent; category cannot be firmly excluded but lacks direct evidence.
4. **`RULED_OUT`** (`confidence_score < 0.15`): Contradictory evidence established (e.g. Forest Fire hypothesis ruled out when hotspot is inside an active petroleum refinery).

---

## 3. Mathematical Scoring Formulation

For each category $c \in \{1 \dots 13\}$, the confidence score $S_c$ is deterministically calculated as:

$$S_c = \text{clamp}\left( w_{\text{spatial}} \cdot I_{\text{spatial}} + w_{\text{recurrence}} \cdot I_{\text{rec}} + w_{\text{persistence}} \cdot I_{\text{pers}} + w_{\text{anomaly}} \cdot I_{\text{anom}} + w_{\text{lulc}} \cdot I_{\text{lulc}} - P_{\text{contradiction}}, 0.0, 1.0 \right)$$

Where:
- $I_{\text{spatial}} \in [0.0, 1.0]$: Normalized proximity to known infrastructure (e.g., $1.0$ if inside polygon, decaying exponentially with distance $d$: $e^{-d / 1000}$).
- $I_{\text{rec}} \in [0.0, 1.0]$: Longitudinal recurrence factor ($\min(R / 5.0, 1.0)$).
- $I_{\text{pers}} \in [0.0, 1.0]$: Multi-month footprint persistence index.
- $I_{\text{anom}} \in [0.0, 1.0]$: FRP deviation above historical baseline ($\min((F_{\text{peak}} / F_{\text{baseline}}) / 3.0, 1.0)$).
- $I_{\text{lulc}} \in [0.0, 1.0]$: Land-use / land-cover alignment.
- $P_{\text{contradiction}} \ge 0.0$: Penalty applied if direct contradicting indicators exist (e.g., non-industrial LULC for refinery processes).

### Overall Evidence Strength Score
The case-level `evidence_strength_score` measures the empirical completeness of ingested telemetry:
$$E = 0.35 \cdot (\text{Sensor Count} / 3) + 0.35 \cdot (\text{Facility Verified}) + 0.30 \cdot (\text{Baseline Established})$$

---

## 4. Epistemic Transparency Guarantees

1. **No Hallucinated Chemistry**: When stack spectrometry or gas sensors are absent, the hypothesis states:
   > *"Direct flare gas composition telemetry unavailable; classification inferred from spatial-temporal baseline persistence."*
2. **No Invented Agency Conclusions**: When official state or central records are absent, the hypothesis notes:
   > *"No state or central regulatory inspection report currently indexed for this specific episode."*
3. **Transparent Contradicting Evidence**: Every hypothesis card lists what evidence contradicts it or what indicators were searched for and found absent.
