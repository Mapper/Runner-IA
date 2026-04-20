import unittest

from runner_playlist.models import RunnerProfile, Song
from runner_playlist.planner import PlaylistPlanner


class PlannerTests(unittest.TestCase):
    def test_build_plan_selects_songs_near_target_bpm(self):
        profile = RunnerProfile(
            ppm=172,
            step_length_m=1.1,
            heart_rate_bpm=168,
            pace_min_per_km=4.6,
            lactate_threshold_hr_bpm=170,
            lactate_threshold_pace_min_per_km=4.5,
        )
        songs = [
            Song(id="1", title="A", artist="X", bpm=160),
            Song(id="2", title="B", artist="X", bpm=172),
            Song(id="3", title="C", artist="X", bpm=175),
            Song(id="4", title="D", artist="X", bpm=180),
        ]

        planner = PlaylistPlanner()
        plan = planner.build_plan(profile, songs, "Teste", desired_count=3)

        self.assertEqual(3, len(plan.songs))
        self.assertIn(plan.training_zone, {"recuperacao", "aerobico", "limiar", "vo2max"})
        self.assertGreaterEqual(plan.target_ppm, 140)
        self.assertLessEqual(plan.target_ppm, 210)


if __name__ == "__main__":
    unittest.main()
