from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from runner_playlist.analyzer import analyze_music_folder, export_catalog_json
from runner_playlist.integrations import (
    DeezerClient,
    SpotifyClient,
    build_deezer_payload,
    build_spotify_payload,
)
from runner_playlist.models import RunnerProfile, Song
from runner_playlist.planner import PlaylistPlanner


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Runner IA Playlist Builder")
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--songs-file", help="JSON de catálogo de músicas")
    source_group.add_argument("--music-folder", help="Pasta local com arquivos de música para analisar BPM")

    parser.add_argument("--catalog-output", help="Caminho para salvar JSON gerado após análise de pasta")
    parser.add_argument("--runner-ppm", required=True, type=int)
    parser.add_argument("--step-length", required=True, type=float)
    parser.add_argument("--heart-rate", required=True, type=int)
    parser.add_argument("--pace-min-km", required=True, type=float)
    parser.add_argument("--lactate-threshold-hr", required=True, type=int)
    parser.add_argument("--lactate-threshold-pace", required=True, type=float)
    parser.add_argument("--distance-km", required=True, type=float)
    parser.add_argument("--playlist-name", required=True)
    parser.add_argument("--spotify-user-id")
    parser.add_argument("--deezer-user-id")
    return parser.parse_args()


def load_songs(path: str) -> list[Song]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [Song(**item) for item in data]


def estimate_song_count(distance_km: float, pace_min_per_km: float, avg_song_min: float = 3.5) -> int:
    total_minutes = distance_km * pace_min_per_km
    return max(5, round(total_minutes / avg_song_min))


def main() -> None:
    args = parse_args()
    if args.songs_file:
        songs = load_songs(args.songs_file)
    else:
        songs = analyze_music_folder(args.music_folder)
        if args.catalog_output:
            export_catalog_json(songs, args.catalog_output)
            print(f"Catálogo exportado para: {args.catalog_output}")

    profile = RunnerProfile(
        ppm=args.runner_ppm,
        step_length_m=args.step_length,
        heart_rate_bpm=args.heart_rate,
        pace_min_per_km=args.pace_min_km,
        lactate_threshold_hr_bpm=args.lactate_threshold_hr,
        lactate_threshold_pace_min_per_km=args.lactate_threshold_pace,
    )

    planner = PlaylistPlanner()
    desired_count = estimate_song_count(args.distance_km, args.pace_min_km)
    plan = planner.build_plan(
        profile=profile,
        catalog=songs,
        playlist_name=args.playlist_name,
        desired_count=desired_count,
    )

    print("=== Plano de Playlist ===")
    print(f"Nome: {plan.name}")
    print(f"Zona de treino: {plan.training_zone}")
    print(f"PPM alvo: {plan.target_ppm}")
    print(f"Velocidade estimada: {plan.estimated_speed_kmh} km/h")
    print(f"Quantidade de músicas: {len(plan.songs)}")

    for idx, song in enumerate(plan.songs, start=1):
        print(f"{idx:02d}. {song.title} - {song.artist} ({song.bpm} bpm)")

    spotify_payload = build_spotify_payload(plan)
    deezer_payload = build_deezer_payload(plan)
    print("\n=== Payload Spotify ===")
    print(json.dumps(spotify_payload, ensure_ascii=False, indent=2))
    print("\n=== Payload Deezer ===")
    print(json.dumps(deezer_payload, ensure_ascii=False, indent=2))

    spotify_token = os.getenv("SPOTIFY_ACCESS_TOKEN")
    if spotify_token and args.spotify_user_id:
        spotify = SpotifyClient(spotify_token)
        result = spotify.create_playlist(args.spotify_user_id, plan)
        print(f"Spotify: {result.details}")
    else:
        print("Spotify: integração não executada (token/user_id ausente).")

    deezer_token = os.getenv("DEEZER_ACCESS_TOKEN")
    if deezer_token and args.deezer_user_id:
        deezer = DeezerClient(deezer_token)
        result = deezer.create_playlist(args.deezer_user_id, plan)
        print(f"Deezer: {result.details}")
    else:
        print("Deezer: integração não executada (token/user_id ausente).")


if __name__ == "__main__":
    main()
