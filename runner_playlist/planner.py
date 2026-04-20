from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from runner_playlist.models import PlaylistPlan, RunnerProfile, Song


@dataclass(frozen=True)
class ZonePolicy:
    name: str
    min_hr_ratio: float
    max_hr_ratio: float
    cadence_multiplier: float


ZONE_POLICIES: List[ZonePolicy] = [
    ZonePolicy("recuperacao", 0.0, 0.85, 0.95),
    ZonePolicy("aerobico", 0.85, 0.95, 1.00),
    ZonePolicy("limiar", 0.95, 1.03, 1.03),
    ZonePolicy("vo2max", 1.03, 1.20, 1.06),
]


class PlaylistPlanner:
    def determine_training_zone(self, profile: RunnerProfile) -> ZonePolicy:
        hr_ratio = profile.heart_rate_bpm / profile.lactate_threshold_hr_bpm
        for zone in ZONE_POLICIES:
            if zone.min_hr_ratio <= hr_ratio < zone.max_hr_ratio:
                return zone
        return ZONE_POLICIES[-1]

    def estimate_speed_kmh(self, profile: RunnerProfile) -> float:
        # velocidade via cadência e passada
        speed_m_per_min = profile.ppm * profile.step_length_m
        return speed_m_per_min * 60 / 1000

    def compute_target_ppm(self, profile: RunnerProfile, zone: ZonePolicy) -> int:
        # Ajuste combinando FC e ritmo vs limiar.
        pace_ratio = profile.lactate_threshold_pace_min_per_km / profile.pace_min_per_km
        load_adjustment = (pace_ratio - 1.0) * 0.5
        target = profile.ppm * (zone.cadence_multiplier + load_adjustment)
        return max(140, min(210, round(target)))

    def select_songs(
        self,
        catalog: Iterable[Song],
        target_ppm: int,
        desired_count: int,
        bpm_tolerance: int = 6,
    ) -> List[Song]:
        candidates = sorted(catalog, key=lambda s: abs(s.bpm - target_ppm))
        within = [song for song in candidates if abs(song.bpm - target_ppm) <= bpm_tolerance]

        selected = within[:desired_count]
        if len(selected) < desired_count:
            already_ids = {s.id for s in selected}
            for song in candidates:
                if song.id in already_ids:
                    continue
                selected.append(song)
                if len(selected) == desired_count:
                    break
        return selected

    def build_plan(
        self,
        profile: RunnerProfile,
        catalog: Iterable[Song],
        playlist_name: str,
        desired_count: int,
    ) -> PlaylistPlan:
        zone = self.determine_training_zone(profile)
        target_ppm = self.compute_target_ppm(profile, zone)
        estimated_speed = self.estimate_speed_kmh(profile)
        songs = self.select_songs(catalog, target_ppm=target_ppm, desired_count=desired_count)

        return PlaylistPlan(
            name=playlist_name,
            target_ppm=target_ppm,
            estimated_speed_kmh=round(estimated_speed, 2),
            training_zone=zone.name,
            songs=songs,
        )
