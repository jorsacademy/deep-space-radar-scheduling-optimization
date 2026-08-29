import numpy as np

from radar_scheduler import DeepSpaceRadarScheduler


def test_configuration_uses_integer_slots():
    scheduler = DeepSpaceRadarScheduler()
    assert scheduler.duration_slots == 4
    assert scheduler.min_separation_slots == 12
    assert scheduler.time_slots == 288


def test_valid_start_requires_full_duration_visibility_and_quality():
    scheduler = DeepSpaceRadarScheduler()
    shape = (len(scheduler.radars), len(scheduler.objects), scheduler.time_slots)
    scheduler.visibility_matrix = np.zeros(shape, dtype=np.int8)
    scheduler.quality_matrix = np.zeros(shape, dtype=float)

    scheduler.visibility_matrix[0, 0, 10:14] = 1
    scheduler.quality_matrix[0, 0, 10:14] = 5.0
    assert (0, 0, 10) in scheduler._valid_starts()

    scheduler.quality_matrix[0, 0, 13] = 0.0
    assert (0, 0, 10) not in scheduler._valid_starts()


def test_solution_metrics_count_full_slot_occupancy():
    scheduler = DeepSpaceRadarScheduler()
    schedule = {r: [] for r in range(len(scheduler.radars))}
    schedule[0] = [
        {
            "object_id": 0,
            "start_slot": 0,
            "start_minute_utc": 0,
            "duration_minutes": 20,
            "quality": 1.0,
        }
    ]
    solution = scheduler._build_solution("Optimal", 1.0, schedule)
    assert solution["radar_utilization"][0] == scheduler.duration_slots / scheduler.time_slots
    assert solution["object_coverage"][0]["observations"] == 1
