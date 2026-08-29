# AGNI-NETRA — Known Limitations & Future Roadmap

## 1. Known Limitations

1. **Satellite Orbital Simulation Model**: The AGNI-SAT orbit propagation engine implements a simplified deterministic Sun-Synchronous LEO physics approximation for digital twin demonstration, rather than high-order SGP4 / TLE perturbation modeling.
2. **Cloud Occlusion in Optical Band**: Optical RGB channels (Sentinel-2 / AGNI-SAT Optical) are susceptible to heavy monsoon cloud cover; the system gracefully falls back to MWIR (3.9 µm) and SWIR (2.2 µm) which penetrate atmospheric haze and moderate clouds.
3. **Optional External Data Sources**: Sources such as MOSDAC INSAT-3D and SMS gateway require active external credentials; when credentials are not configured in `.env`, these adapters operate in explicit `NOT_CONFIGURED` / `CONSOLE` simulation mode rather than fabricating live data.
4. **Spatial Resolution Constraints**: NASA FIRMS VIIRS 375m pixel footprint limits exact sub-facility spatial localization within tightly packed multi-unit petrochemical complexes; candidate facility boundaries reflect estimated thermal cluster convex hulls.

---

## 2. Future Engineering Roadmap

- [ ] SGP4 / NORAD Two-Line Element (TLE) integration for physical satellite orbital tracks.
- [ ] Direct integration with CDAC Meghdoot emergency SMS gateway for authorized state agencies.
- [ ] Real-time GeoTIFF rendering on MapLibre via dynamic COG (Cloud Optimized GeoTIFF) tile servers.
- [ ] Continuous online active learning pipeline automatically triggering model fine-tuning when human verification threshold ($N \ge 500$ verified samples) is reached.
