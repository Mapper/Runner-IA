from __future__ import annotations

import math
import re
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from runner_playlist.models import Song

SUPPORTED_EXTENSIONS = {".wav", ".mp3", ".flac", ".m4a", ".ogg"}
BPM_IN_NAME = re.compile(r"(?P<bpm>\d{2,3})\s?bpm", re.IGNORECASE)


@dataclass(frozen=True)
class AnalyzedTrack:
    path: Path
    title: str
    artist: str
    bpm: int


def _extract_bpm_from_name(filename: str) -> int | None:
    match = BPM_IN_NAME.search(filename)
    if not match:
        return None
    return int(match.group("bpm"))


def _slug_to_title(slug: str) -> tuple[str, str]:
    normalized = slug.replace("_", " ").strip()
    if " - " in normalized:
        artist, title = normalized.split(" - ", 1)
        return title.strip(), artist.strip()
    return normalized, "Unknown Artist"


def detect_bpm_wav(path: Path) -> int:
    with wave.open(str(path), "rb") as wav_file:
        n_channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        sample_rate = wav_file.getframerate()
        n_frames = wav_file.getnframes()
        raw_frames = wav_file.readframes(n_frames)

    if sample_width != 2:
        raise ValueError(f"Formato WAV não suportado em {path.name}: use PCM 16 bits")

    import array

    samples = array.array("h", raw_frames)
    if n_channels > 1:
        mono = []
        for i in range(0, len(samples), n_channels):
            channel_values = samples[i : i + n_channels]
            mono.append(sum(channel_values) / n_channels)
    else:
        mono = samples

    frame_size = 1024
    hop_size = 512
    if len(mono) < frame_size:
        raise ValueError(f"Arquivo muito curto para análise: {path.name}")

    envelope = []
    for i in range(0, len(mono) - frame_size, hop_size):
        frame = mono[i : i + frame_size]
        energy = math.sqrt(sum(sample * sample for sample in frame) / frame_size)
        envelope.append(energy)

    mean_energy = sum(envelope) / len(envelope)
    envelope = [max(0.0, e - mean_energy) for e in envelope]

    min_bpm, max_bpm = 70, 210
    min_lag = int((60 * sample_rate) / (max_bpm * hop_size))
    max_lag = int((60 * sample_rate) / (min_bpm * hop_size))

    best_lag = None
    best_score = float("-inf")

    for lag in range(min_lag, max_lag + 1):
        score = 0.0
        limit = len(envelope) - lag
        if limit <= 0:
            break
        for i in range(limit):
            score += envelope[i] * envelope[i + lag]
        if score > best_score:
            best_score = score
            best_lag = lag

    if best_lag is None or best_lag <= 0:
        raise ValueError(f"Não foi possível estimar BPM para: {path.name}")

    bpm = round(60 * sample_rate / (best_lag * hop_size))
    return max(min_bpm, min(max_bpm, bpm))


def analyze_music_folder(folder: str | Path) -> list[Song]:
    base_path = Path(folder)
    if not base_path.exists() or not base_path.is_dir():
        raise ValueError(f"Pasta inválida: {base_path}")

    songs: list[Song] = []
    for file_path in sorted(base_path.iterdir()):
        if not file_path.is_file() or file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        stem = file_path.stem
        title, artist = _slug_to_title(stem)

        bpm = _extract_bpm_from_name(stem)
        if bpm is None and file_path.suffix.lower() == ".wav":
            bpm = detect_bpm_wav(file_path)

        if bpm is None:
            # fallback conservador quando não há metadado legível.
            bpm = 160

        songs.append(
            Song(
                id=file_path.stem,
                title=title,
                artist=artist,
                bpm=bpm,
            )
        )

    return songs


def export_catalog_json(songs: Iterable[Song], output_path: str | Path) -> None:
    import json

    payload = [
        {"id": song.id, "title": song.title, "artist": song.artist, "bpm": song.bpm}
        for song in songs
    ]
    Path(output_path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
