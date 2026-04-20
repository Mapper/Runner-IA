import tempfile
import unittest
import wave
from pathlib import Path

from runner_playlist.analyzer import analyze_music_folder, detect_bpm_wav


def write_click_track_wav(path: Path, bpm: int, duration_sec: float = 10.0, sample_rate: int = 44100) -> None:
    n_samples = int(duration_sec * sample_rate)
    samples = [0] * n_samples
    interval = int(sample_rate * 60 / bpm)
    click_len = int(sample_rate * 0.01)

    for start in range(0, n_samples, interval):
        for i in range(start, min(start + click_len, n_samples)):
            # click curto em onda quadrada
            samples[i] = 18000 if (i - start) % 2 == 0 else -18000

    with wave.open(str(path), "wb") as wavf:
        wavf.setnchannels(1)
        wavf.setsampwidth(2)
        wavf.setframerate(sample_rate)
        import array

        wavf.writeframes(array.array("h", samples).tobytes())


class AnalyzerTests(unittest.TestCase):
    def test_detect_bpm_wav_click_track(self):
        with tempfile.TemporaryDirectory() as tmp:
            wav_path = Path(tmp) / "Runner - Beat.wav"
            write_click_track_wav(wav_path, bpm=120)

            detected = detect_bpm_wav(wav_path)
            self.assertTrue(115 <= detected <= 125)

    def test_analyze_music_folder_reads_name_bpm_and_wav(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            write_click_track_wav(base / "ArtistA - Warmup.wav", bpm=180)
            (base / "ArtistB - Interval 172bpm.mp3").write_bytes(b"fake")

            songs = analyze_music_folder(base)
            self.assertEqual(2, len(songs))

            by_id = {s.id: s for s in songs}
            self.assertEqual(172, by_id["ArtistB - Interval 172bpm"].bpm)
            self.assertTrue(170 <= by_id["ArtistA - Warmup"].bpm <= 190)


if __name__ == "__main__":
    unittest.main()
