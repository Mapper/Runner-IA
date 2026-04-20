# Runner IA Playlist Builder

Aplicativo em Python para montar playlists de corrida sincronizadas com a cadência do corredor (PPM), considerando também comprimento de passada e dados de limiar de lactato (FC e ritmo).

## ✅ Versão para pessoas leigas (clicar e rodar)

Esta versão agora possui interface gráfica (`runner_ia_gui.py`) para uso sem terminal.

### Opção 1 — Rodar com duplo clique (sem empacotar)

- **Windows:** clique em `Executar_Runner_IA.bat`.
- **Linux/macOS:** execute `./executar_runner_ia.sh`.

### Opção 2 — Gerar executável para distribuir (Windows)

1. Dê duplo clique em `build_windows_exe.bat`.
2. O arquivo final será criado em `dist/RunnerIA.exe`.
3. Entregue o `RunnerIA.exe` para o usuário final (sem necessidade de abrir terminal).

> Observação: para gerar `.exe`, é necessário ter Python instalado na máquina que fará o build.

---

## Funcionalidades

- Calcula a zona de treino em relação ao limiar de lactato.
- Estima cadência alvo com base em:
  - passos por minuto (PPM)
  - comprimento da passada
  - ritmo atual
  - faixa de frequência cardíaca vs limiar
- Analisa uma pasta de músicas do usuário e classifica as faixas com BPM.
  - Suporta detecção de BPM automática em arquivos `.wav` PCM 16-bit.
  - Para outros formatos (`.mp3`, `.flac`, `.m4a`, `.ogg`), usa BPM no nome do arquivo (ex: `Artista - Faixa 174bpm.mp3`) ou fallback padrão.
- Seleciona músicas sincronizadas com o objetivo da sessão (BPM da música próximo do PPM alvo).
- Gera payloads para criação de playlist no **Spotify** e **Deezer**.
- Opcionalmente cria playlist via API oficial (quando tokens são fornecidos).

## Estrutura

- `runner_ia_gui.py`: interface gráfica para usuário final.
- `runner_playlist/models.py`: modelos de dados.
- `runner_playlist/planner.py`: lógica de cálculo de zona e seleção de músicas.
- `runner_playlist/analyzer.py`: análise de pasta local e classificação de BPM.
- `runner_playlist/integrations.py`: integração com Spotify e Deezer.
- `app.py`: interface CLI (modo técnico).

## Uso com interface gráfica

1. Abra o app por duplo clique (`Executar_Runner_IA.bat`) ou via `python runner_ia_gui.py`.
2. Selecione uma fonte:
   - catálogo JSON (`--songs-file`, equivalente), **ou**
   - pasta de músicas para análise automática de BPM.
3. Preencha os dados do corredor.
4. Clique em **Gerar Playlist**.
5. Copie os payloads gerados para integração com Spotify/Deezer.

## Uso com CLI (técnico)

```bash
python app.py \
  --music-folder ./minhas-musicas \
  --catalog-output catalogo_gerado.json \
  --runner-ppm 172 \
  --step-length 1.1 \
  --heart-rate 168 \
  --pace-min-km 4.55 \
  --lactate-threshold-hr 170 \
  --lactate-threshold-pace 4.50 \
  --distance-km 10 \
  --playlist-name "Treino de Limiar"
```

## Integração com plataformas

### Spotify

- Defina `SPOTIFY_ACCESS_TOKEN` no ambiente.
- Informe `--spotify-user-id`.

### Deezer

- Defina `DEEZER_ACCESS_TOKEN` no ambiente.
- Informe `--deezer-user-id`.

## Observações

- Sem token, o aplicativo apenas gera e exibe os payloads de integração.
- Para produção, recomenda-se implementar fluxo OAuth completo para cada plataforma.
