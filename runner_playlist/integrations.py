from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import List

from runner_playlist.models import PlaylistPlan


@dataclass
class IntegrationResult:
    platform: str
    created: bool
    details: str


class SpotifyClient:
    base_url = "https://api.spotify.com/v1"

    def __init__(self, access_token: str):
        self.access_token = access_token

    def _request(self, method: str, path: str, body: dict | None = None) -> dict:
        payload = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=payload,
            method=method,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def create_playlist(self, user_id: str, plan: PlaylistPlan) -> IntegrationResult:
        playlist = self._request(
            "POST",
            f"/users/{user_id}/playlists",
            {
                "name": plan.name,
                "description": f"RunnerIA | Zona {plan.training_zone} | Cadência alvo {plan.target_ppm}",
                "public": False,
            },
        )
        spotify_playlist_id = playlist["id"]

        track_uris = [f"spotify:track:{song.id}" for song in plan.songs]
        self._request(
            "POST",
            f"/playlists/{spotify_playlist_id}/tracks",
            {"uris": track_uris},
        )
        return IntegrationResult(
            platform="spotify",
            created=True,
            details=f"Playlist criada com id {spotify_playlist_id}",
        )


class DeezerClient:
    base_url = "https://api.deezer.com"

    def __init__(self, access_token: str):
        self.access_token = access_token

    def _request(self, method: str, path: str, params: dict[str, str]) -> dict:
        query = urllib.parse.urlencode(params)
        req = urllib.request.Request(f"{self.base_url}{path}?{query}", method=method)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def create_playlist(self, user_id: str, plan: PlaylistPlan) -> IntegrationResult:
        created = self._request(
            "POST",
            f"/user/{user_id}/playlists",
            {
                "access_token": self.access_token,
                "title": plan.name,
            },
        )
        playlist_id = created["id"]

        song_ids = ",".join(song.id for song in plan.songs)
        self._request(
            "POST",
            f"/playlist/{playlist_id}/tracks",
            {
                "access_token": self.access_token,
                "songs": song_ids,
            },
        )
        return IntegrationResult(
            platform="deezer",
            created=True,
            details=f"Playlist criada com id {playlist_id}",
        )


def build_spotify_payload(plan: PlaylistPlan) -> dict:
    return {
        "name": plan.name,
        "description": f"RunnerIA | Zona {plan.training_zone} | Cadência alvo {plan.target_ppm}",
        "tracks": [f"spotify:track:{song.id}" for song in plan.songs],
    }


def build_deezer_payload(plan: PlaylistPlan) -> dict:
    return {
        "title": plan.name,
        "song_ids": [song.id for song in plan.songs],
        "note": f"RunnerIA | Zona {plan.training_zone} | Cadência alvo {plan.target_ppm}",
    }
