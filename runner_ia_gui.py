from __future__ import annotations

import json
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from runner_playlist.analyzer import analyze_music_folder, export_catalog_json
from runner_playlist.integrations import build_deezer_payload, build_spotify_payload
from runner_playlist.models import RunnerProfile, Song
from runner_playlist.planner import PlaylistPlanner


class RunnerIAGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Runner IA - Playlist para Corrida")
        self.geometry("980x740")

        self.songs_file = tk.StringVar(value="")
        self.music_folder = tk.StringVar(value="")
        self.catalog_output = tk.StringVar(value="catalogo_gerado.json")
        self.playlist_name = tk.StringVar(value="Treino de Corrida")

        self.runner_ppm = tk.StringVar(value="172")
        self.step_length = tk.StringVar(value="1.10")
        self.heart_rate = tk.StringVar(value="168")
        self.pace_min_km = tk.StringVar(value="4.55")
        self.lactate_threshold_hr = tk.StringVar(value="170")
        self.lactate_threshold_pace = tk.StringVar(value="4.50")
        self.distance_km = tk.StringVar(value="10")

        self._build_ui()

    def _build_ui(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=12, pady=12)

        config_tab = ttk.Frame(notebook)
        output_tab = ttk.Frame(notebook)

        notebook.add(config_tab, text="Configuração")
        notebook.add(output_tab, text="Resultado")

        self._build_config_tab(config_tab)
        self._build_output_tab(output_tab)

    def _build_config_tab(self, parent: ttk.Frame) -> None:
        source_frame = ttk.LabelFrame(parent, text="Fonte das músicas")
        source_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(source_frame, text="Catálogo JSON (opcional):").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(source_frame, textvariable=self.songs_file, width=90).grid(row=0, column=1, padx=8, pady=6)
        ttk.Button(source_frame, text="Selecionar", command=self._select_songs_file).grid(row=0, column=2, padx=8, pady=6)

        ttk.Label(source_frame, text="Pasta de músicas (opcional):").grid(row=1, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(source_frame, textvariable=self.music_folder, width=90).grid(row=1, column=1, padx=8, pady=6)
        ttk.Button(source_frame, text="Selecionar", command=self._select_music_folder).grid(row=1, column=2, padx=8, pady=6)

        ttk.Label(source_frame, text="Salvar catálogo gerado em:").grid(row=2, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(source_frame, textvariable=self.catalog_output, width=90).grid(row=2, column=1, padx=8, pady=6)

        profile_frame = ttk.LabelFrame(parent, text="Dados do corredor")
        profile_frame.pack(fill="x", padx=10, pady=10)

        fields = [
            ("Nome da playlist", self.playlist_name),
            ("Passos por minuto (PPM)", self.runner_ppm),
            ("Tamanho da passada (m)", self.step_length),
            ("Frequência cardíaca atual", self.heart_rate),
            ("Ritmo atual (min/km)", self.pace_min_km),
            ("Limiar de lactato - FC", self.lactate_threshold_hr),
            ("Limiar de lactato - Ritmo", self.lactate_threshold_pace),
            ("Distância do treino (km)", self.distance_km),
        ]
        for idx, (label, var) in enumerate(fields):
            ttk.Label(profile_frame, text=label).grid(row=idx, column=0, sticky="w", padx=8, pady=4)
            ttk.Entry(profile_frame, textvariable=var, width=30).grid(row=idx, column=1, sticky="w", padx=8, pady=4)

        actions = ttk.Frame(parent)
        actions.pack(fill="x", padx=10, pady=8)
        ttk.Button(actions, text="Gerar Playlist", command=self._start_generate).pack(side="left", padx=6)
        ttk.Button(actions, text="Limpar resultado", command=self._clear_output).pack(side="left", padx=6)

    def _build_output_tab(self, parent: ttk.Frame) -> None:
        self.output_text = tk.Text(parent, wrap="word", font=("Arial", 11))
        self.output_text.pack(fill="both", expand=True, padx=10, pady=10)

    def _select_songs_file(self) -> None:
        path = filedialog.askopenfilename(title="Selecione o catálogo JSON", filetypes=[("JSON", "*.json")])
        if path:
            self.songs_file.set(path)

    def _select_music_folder(self) -> None:
        path = filedialog.askdirectory(title="Selecione a pasta de músicas")
        if path:
            self.music_folder.set(path)

    def _clear_output(self) -> None:
        self.output_text.delete("1.0", tk.END)

    def _append_output(self, text: str) -> None:
        self.output_text.insert(tk.END, text + "\n")
        self.output_text.see(tk.END)

    def _start_generate(self) -> None:
        threading.Thread(target=self._generate_playlist, daemon=True).start()

    def _generate_playlist(self) -> None:
        try:
            self.after(0, self._clear_output)
            songs = self._load_or_analyze_songs()
            profile = RunnerProfile(
                ppm=int(self.runner_ppm.get()),
                step_length_m=float(self.step_length.get()),
                heart_rate_bpm=int(self.heart_rate.get()),
                pace_min_per_km=float(self.pace_min_km.get()),
                lactate_threshold_hr_bpm=int(self.lactate_threshold_hr.get()),
                lactate_threshold_pace_min_per_km=float(self.lactate_threshold_pace.get()),
            )

            desired_count = max(5, round(float(self.distance_km.get()) * profile.pace_min_per_km / 3.5))
            planner = PlaylistPlanner()
            plan = planner.build_plan(
                profile=profile,
                catalog=songs,
                playlist_name=self.playlist_name.get().strip() or "Treino",
                desired_count=desired_count,
            )

            spotify_payload = build_spotify_payload(plan)
            deezer_payload = build_deezer_payload(plan)

            lines = [
                "=== Playlist Gerada ===",
                f"Nome: {plan.name}",
                f"Zona: {plan.training_zone}",
                f"PPM alvo: {plan.target_ppm}",
                f"Velocidade estimada: {plan.estimated_speed_kmh} km/h",
                f"Quantidade de músicas: {len(plan.songs)}",
                "",
                "--- Músicas selecionadas ---",
            ]
            for idx, song in enumerate(plan.songs, start=1):
                lines.append(f"{idx:02d}. {song.title} - {song.artist} ({song.bpm} bpm)")

            lines.extend(
                [
                    "",
                    "--- Payload Spotify ---",
                    json.dumps(spotify_payload, ensure_ascii=False, indent=2),
                    "",
                    "--- Payload Deezer ---",
                    json.dumps(deezer_payload, ensure_ascii=False, indent=2),
                ]
            )

            self.after(0, lambda: self._append_output("\n".join(lines)))
        except Exception as exc:  # interface para usuário final
            self.after(0, lambda: messagebox.showerror("Erro", f"Não foi possível gerar a playlist:\n{exc}"))

    def _load_or_analyze_songs(self):
        songs_file = self.songs_file.get().strip()
        music_folder = self.music_folder.get().strip()

        if songs_file and music_folder:
            raise ValueError("Escolha apenas uma fonte: catálogo JSON OU pasta de músicas.")

        if songs_file:
            payload = json.loads(Path(songs_file).read_text(encoding="utf-8"))
            return [Song(**item) for item in payload]

        if music_folder:
            songs = analyze_music_folder(music_folder)
            output = self.catalog_output.get().strip()
            if output:
                export_catalog_json(songs, output)
            return songs

        raise ValueError("Informe um catálogo JSON ou selecione uma pasta de músicas.")


def main() -> None:
    app = RunnerIAGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
