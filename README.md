# Deep Space Radar Scheduling Optimization

Educational mixed-integer optimization for scheduling radar observations of resident space objects (RSOs), with both synthetic visibility and TLE/SGP4 propagation.

The project modernizes an older prototype by making fixed observation duration, separation, energy accounting and coverage logic mutually consistent. It also supports real orbital geometry from TLE data and a lightweight data pipeline for refreshing public CelesTrak GP and SATCAT data.

## Features

- MILP scheduling with fixed-duration observation starts.
- Full-slot radar occupancy and sliding-window observation separation.
- Synthetic visibility mode for deterministic experimentation.
- TLE parsing and SGP4/topocentric visibility mode.
- Current CelesTrak GP/TLE download utility.
- SATCAT metadata ingestion including radar cross section (RCS) when published.
- Uncertainty-aware robustness evaluation by perturbing visibility and observation quality.
- Schedule visualization and structural tests.

> This is an educational/research prototype, not an operational space-domain-awareness system. Public catalog data can be stale or incomplete, radar performance is simplified, and many operational effects are not modeled.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

CBC is used through PuLP. Most PuLP installations include a compatible CBC binary; otherwise install CBC separately.

## Synthetic mode

```bash
python radar_scheduler.py
```

## TLE / SGP4 mode

A historical Vanguard 1 TLE is included only as a reproducible propagation example:

```bash
python radar_scheduler.py --tle-file data/vanguard1.tle
```

For meaningful current analysis, refresh the catalog first.

## Refresh current public catalog data

The refresh utility uses CelesTrak's public GP endpoint for orbital elements and SATCAT endpoint for catalog metadata.

Example: current space-station group

```bash
python refresh_catalog.py --group stations --output-dir data/current/stations
```

Example: one NORAD catalog object

```bash
python refresh_catalog.py --catnr 25544 --output-dir data/current/iss
```

It writes:

```text
data/current/.../
├── catalog.tle
└── satcat_metadata.json
```

The metadata file includes fields such as object type, owner, apogee, perigee, inclination and `RCS` when CelesTrak publishes it. RCS is not available for every catalog object, so downstream radar-quality calculations must retain a documented fallback value or uncertainty model.

Important: classic TLE format cannot represent newly assigned catalog numbers above its traditional five-digit catalog-number limit. CelesTrak also provides OMM JSON/CSV/XML formats; migrating the propagator input to OMM is the next compatibility step for full future catalogs.

## Uncertainty-aware scheduling

`uncertainty.py` provides Monte Carlo-style robustness evaluation. It repeatedly re-solves a fresh scheduler after randomly removing a configurable fraction of visibility opportunities and perturbing observation quality.

```python
from radar_scheduler import DeepSpaceRadarScheduler
from uncertainty import evaluate_schedule_uncertainty

summary = evaluate_schedule_uncertainty(
    lambda: DeepSpaceRadarScheduler(seed=42),
    simulations=50,
    visibility_dropout_probability=0.10,
    quality_relative_sigma=0.10,
)
print(summary)
```

This is a robustness diagnostic rather than a full stochastic-programming formulation. A stronger future extension would optimize first-stage scheduling decisions against scenarios directly rather than independently re-solving each perturbed instance.

## Model defaults

| Parameter | Default |
|---|---:|
| Horizon | 24 h |
| Time slot | 5 min |
| Observation duration | 20 min |
| Minimum observations per object | 3 |
| Minimum separation between starts | 60 min |
| Synthetic objects | 25 |
| Radar sites | 3 |

## Tests

```bash
pytest -q
```

## Project structure

```text
.
├── radar_scheduler.py
├── orbital_visibility.py
├── catalog_client.py
├── refresh_catalog.py
├── uncertainty.py
├── requirements.txt
├── data/
│   └── vanguard1.tle
├── tests/
│   └── test_scheduler.py
├── .gitignore
└── README.md
```

## Data-source notes

CelesTrak GP queries can return TLE, OMM XML/KVN, JSON and CSV. SATCAT CSV/JSON records include an RCS field in square meters when available. The downloader deliberately identifies itself with a user agent and performs explicit, user-triggered refreshes rather than background scraping.

## Current limitations

- TLE mode still uses simplified radar SNR/quality physics.
- SATCAT RCS can be missing and is not a measurement uncertainty distribution.
- Slew/setup time, maintenance, calibration, weather correlation, track initiation, handoffs and competing missions are omitted.
- Current robustness analysis perturbs visibility and quality independently and does not model correlated orbital covariance.
- TLE age matters: current operations should use fresh elements and an explicit epoch/staleness policy.

## License

No license has been selected yet. Add one before distributing or reusing the code outside your intended scope.
