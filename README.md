# Deep Space Radar Scheduling Optimization

An educational mixed-integer linear programming (MILP) model for scheduling radar observations of resident space objects (RSOs). The project supports two visibility modes:

1. **Synthetic mode** for lightweight deterministic demonstrations.
2. **TLE/SGP4 mode** for propagating real two-line element sets and computing topocentric visibility from each radar site.

The optimization formulation reserves full observation duration, enforces sliding-window separation across all radars, links coverage variables correctly to observation counts, and uses consistent physical time in the energy model.

## What the model does

- Defines three radar sites: Maui, Millstone Hill, and Goldstone.
- Accepts standard 2-line or 3-line TLE catalogs.
- Propagates TLE objects with SGP4 through Skyfield.
- Converts propagated states into site-relative elevation and slant range.
- Marks an object visible when its elevation is above the configured minimum elevation.
- Computes a simplified radar-quality score from propagated range, elevation, RCS assumptions, and an SNR-style radar equation.
- Creates fixed-duration observation-start decisions.
- Maximizes priority-weighted object coverage with a secondary quality reward.
- Enforces radar capacity, observation duration, inter-observation separation, visibility, and daily energy constraints.
- Produces summary metrics and a schedule plot.

> This remains an educational/research prototype, not an operational space-domain-awareness system. SGP4 visibility is materially more realistic than the original synthetic pass generator, but radar hardware, atmospheric loss, pointing/slew dynamics, uncertainty, covariance, tasking doctrine, and RCS modeling are still simplified.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

CBC is used through PuLP. Most PuLP installations include a compatible CBC binary; otherwise install CBC separately for your platform.

## Run: synthetic mode

```bash
python radar_scheduler.py
```

This preserves the original demonstration workflow and does not require orbital data.

## Run: TLE + SGP4 mode

Pass a TLE catalog with `--tle-file`:

```bash
python radar_scheduler.py \
  --tle-file data/vanguard1.tle \
  --horizon-hours 24 \
  --output radar_schedule_sgp4.png
```

If `--start-utc` is omitted, the scheduler uses the newest epoch in the supplied TLE catalog as the horizon start. This is useful for reproducible historical examples.

For an operational/current catalog, provide an explicit UTC start near the TLE epoch:

```bash
python radar_scheduler.py \
  --tle-file data/current_catalog.tle \
  --start-utc 2026-08-29T00:00:00Z
```

### TLE format

Standard three-line format:

```text
OBJECT NAME
1 NNNNNU ...
2 NNNNN  ...
```

Standard two-line records without a name are also supported; the loader derives a fallback name from the NORAD catalog number.

The repository contains `data/vanguard1.tle`, a **real historical Vanguard 1 TLE used in standard SGP4 verification material**. It is intentionally old and exists only as a reproducible propagation example. Do not treat it as current orbital data. Replace it with a current catalog when analyzing present-day visibility.

## How SGP4 visibility works

For every radar-object-time combination, `orbital_visibility.py`:

1. Parses the TLE into a Skyfield `EarthSatellite` object.
2. Propagates the satellite at every scheduling time slot using SGP4.
3. Builds a topocentric observer at the radar latitude, longitude, and elevation.
4. Computes elevation angle and slant range.
5. Sets visibility to 1 when elevation is at least the configured minimum elevation.

The resulting arrays are indexed as:

```text
[radar, object, time_slot]
```

The scheduler then uses propagated slant range and elevation in its simplified radar-quality calculation.

## Important modeling note: RCS

TLEs do not contain radar cross section. In TLE mode the current implementation assigns a default `10 m²` RCS and priority `1.0` to imported objects. For serious analysis, replace these defaults with object-specific metadata from an appropriate catalog before interpreting SNR/quality values quantitatively.

## Test

```bash
pytest -q
```

Tests cover:

- slot/duration invariants,
- full-duration visibility requirements,
- utilization accounting,
- TLE parsing,
- SGP4 propagation output shapes and finite ranges,
- scheduler initialization in TLE mode.

## Model defaults

| Parameter | Default |
|---|---:|
| Horizon | 24 h |
| Time slot | 5 min |
| Observation duration | 20 min |
| Minimum observations per object | 3 |
| Minimum separation between starts | 60 min |
| Minimum elevation | 5° |
| Synthetic objects | 25 |
| Radar sites | 3 |

## Project structure

```text
.
├── orbital_visibility.py
├── radar_scheduler.py
├── requirements.txt
├── data/
│   └── vanguard1.tle
├── tests/
│   └── test_scheduler.py
├── .gitignore
└── README.md
```

## Key formulation corrections from the original prototype

The original prototype treated a scheduled observation as a one-slot binary decision while charging and plotting it as a multi-slot observation. That allowed temporal overlap. A start decision at slot `t` now occupies every slot in `[t, t + duration)`.

Object separation is enforced using sliding windows rather than disjoint time blocks, preventing boundary violations. Coverage variable `z[o]` is linked in both directions: an object is marked covered if and only if it receives at least the minimum number of observations. Objects with no feasible observation starts are forced to `z[o] = 0`.

## Remaining limitations

SGP4 propagates TLE mean elements and is appropriate for TLE-based orbit prediction, but this repository does not yet model:

- TLE age/error growth or covariance,
- radar field-of-regard beyond minimum elevation,
- antenna slew and settling time,
- transmit/receive duty cycles,
- atmospheric attenuation and ionospheric effects,
- object-specific RCS/aspect dependence,
- maintenance and weather outages,
- simultaneous bistatic/multistatic observations,
- track quality or orbit-determination covariance reduction.

A logical next research step is to attach object metadata and uncertainty to the TLE catalog, then optimize not merely observation count but expected information gain/orbit-determination quality.

## License

No license has been selected yet. Add one before distributing or reusing the code outside your intended scope.
