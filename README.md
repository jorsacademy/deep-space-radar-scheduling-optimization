# Deep Space Radar Scheduling Optimization

An educational mixed-integer linear programming (MILP) model for scheduling deep-space radar observations of resident space objects (RSOs).

This repository modernizes an older prototype and fixes several formulation inconsistencies: observation decisions now reserve their full duration, separation is enforced with sliding windows across all radars, coverage variables are correctly linked to observation counts, and the energy model uses consistent physical time accounting.

## What the model does

- Simulates synthetic visibility windows for three radar sites and 25 RSOs.
- Computes a simplified radar-quality score from geometry and an SNR-style calculation.
- Creates fixed-duration observation-start decisions.
- Maximizes priority-weighted object coverage with a secondary quality reward.
- Enforces radar capacity, observation duration, inter-observation separation, visibility, and daily energy constraints.
- Produces summary metrics and a schedule plot.

> This is an educational optimization model, not an operational space-domain-awareness system. Orbital visibility and radar physics are intentionally simplified and generated synthetically.

## Key formulation corrections

The original prototype treated a scheduled observation as a one-slot binary decision while charging and plotting it as a multi-slot observation. That allowed temporal overlap. In this version, a start decision at slot `t` occupies every slot in `[t, t + duration)`.

Object separation is enforced using sliding windows rather than disjoint time blocks, preventing boundary violations. Coverage variable `z[o]` is linked in both directions: an object is marked covered if and only if it receives at least the minimum number of observations. Objects with no feasible observation starts are forced to `z[o] = 0`.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

CBC is used through PuLP. Most PuLP installations include a compatible CBC binary; otherwise install CBC separately for your platform.

## Run

```bash
python radar_scheduler.py
```

The script prints solution metrics and writes `radar_schedule.png`.

## Test

```bash
pytest -q
```

The tests focus on structural invariants and do not require a full large optimization run.

## Model defaults

| Parameter | Default |
|---|---:|
| Horizon | 24 h |
| Time slot | 5 min |
| Observation duration | 20 min |
| Minimum observations per object | 3 |
| Minimum separation between starts | 60 min |
| Objects | 25 |
| Radar sites | 3 |

## Project structure

```text
.
├── radar_scheduler.py
├── requirements.txt
├── tests/
│   └── test_scheduler.py
├── .gitignore
└── README.md
```

## Limitations

The visibility calculation is stochastic and is not derived from TLE/ephemeris propagation. Radar gain, SNR, atmospheric effects, track initiation, slew time, calibration, maintenance, weather, and handoff dynamics are simplified or omitted. If this project is extended toward research use, the next major step should be replacing synthetic visibility with a real propagator such as SGP4/Orekit and explicitly modeling slew/setup times.

## License

No license has been selected yet. Add one before distributing or reusing the code outside your intended scope.
