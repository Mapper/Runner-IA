from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class RunnerProfile:
    ppm: int
    step_length_m: float
    heart_rate_bpm: int
    pace_min_per_km: float
    lactate_threshold_hr_bpm: int
    lactate_threshold_pace_min_per_km: float


@dataclass(frozen=True)
class Song:
    id: str
    title: str
    artist: str
    bpm: int


@dataclass
class PlaylistPlan:
    name: str
    target_ppm: int
    estimated_speed_kmh: float
    training_zone: str
    songs: List[Song]
