from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
from skyfield.api import EarthSatellite, load, wgs84


@dataclass(frozen=True)
class TLERecord:
    name: str
    line1: str
    line2: str


@dataclass(frozen=True)
class RadarLocation:
    name: str
    latitude_deg: float
    longitude_deg: float
    elevation_m: float = 0.0


def load_tle_records(path: str | Path) -> list[TLERecord]:
    """Load standard 2-line or 3-line TLE records from a text file.

    Three-line records contain a name followed by line 1 and line 2. Two-line
    records are accepted as well and receive a NORAD-derived fallback name.
    Blank lines and comment lines beginning with ``#`` are ignored.
    """
    lines = [
        line.strip()
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    records: list[TLERecord] = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("1 "):
            if i + 1 >= len(lines) or not lines[i + 1].startswith("2 "):
                raise ValueError(f"Malformed TLE near line {i + 1}")
            norad = lines[i][2:7].strip() or f"OBJECT_{len(records):03d}"
            records.append(TLERecord(f"NORAD_{norad}", lines[i], lines[i + 1]))
            i += 2
            continue

        if i + 2 >= len(lines):
            raise ValueError(f"Incomplete 3-line TLE record near line {i + 1}")
        name, line1, line2 = lines[i : i + 3]
        if not line1.startswith("1 ") or not line2.startswith("2 "):
            raise ValueError(f"Malformed 3-line TLE record near line {i + 1}")
        records.append(TLERecord(name, line1, line2))
        i += 3

    if not records:
        raise ValueError("No TLE records found")
    return records


class SGP4VisibilityEngine:
    """Topocentric visibility and range computation backed by Skyfield/SGP4."""

    def __init__(self, records: Sequence[TLERecord]) -> None:
        if not records:
            raise ValueError("At least one TLE record is required")
        self.records = list(records)
        self.ts = load.timescale(builtin=True)
        self.satellites = [
            EarthSatellite(record.line1, record.line2, record.name, self.ts)
            for record in self.records
        ]

    @classmethod
    def from_file(cls, path: str | Path) -> "SGP4VisibilityEngine":
        return cls(load_tle_records(path))

    def default_start_time_utc(self) -> datetime:
        """Use the newest epoch in the catalog when no explicit start is supplied."""
        epochs = [sat.epoch.utc_datetime().astimezone(timezone.utc) for sat in self.satellites]
        return max(epochs)

    def compute_geometry(
        self,
        radars: Sequence[RadarLocation],
        start_time_utc: datetime,
        slot_minutes: int,
        time_slots: int,
        min_elevation_deg: float,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Return visibility, elevation (deg), and slant range (km).

        Arrays are indexed ``[radar, object, time_slot]``. Visibility is 1 when
        the propagated object is at or above ``min_elevation_deg``.
        """
        if start_time_utc.tzinfo is None:
            start_time_utc = start_time_utc.replace(tzinfo=timezone.utc)
        else:
            start_time_utc = start_time_utc.astimezone(timezone.utc)

        datetimes = [
            start_time_utc + timedelta(minutes=slot_minutes * slot)
            for slot in range(time_slots)
        ]
        times = self.ts.from_datetimes(datetimes)

        shape = (len(radars), len(self.satellites), time_slots)
        visibility = np.zeros(shape, dtype=np.int8)
        elevation = np.zeros(shape, dtype=float)
        range_km = np.zeros(shape, dtype=float)

        for r, radar in enumerate(radars):
            observer = wgs84.latlon(
                radar.latitude_deg,
                radar.longitude_deg,
                elevation_m=radar.elevation_m,
            )
            for o, satellite in enumerate(self.satellites):
                difference = satellite - observer
                alt, _az, distance = difference.at(times).altaz()
                alt_deg = np.asarray(alt.degrees, dtype=float)
                distance_km = np.asarray(distance.km, dtype=float)
                elevation[r, o, :] = alt_deg
                range_km[r, o, :] = distance_km
                visibility[r, o, :] = (alt_deg >= min_elevation_deg).astype(np.int8)

        return visibility, elevation, range_km
