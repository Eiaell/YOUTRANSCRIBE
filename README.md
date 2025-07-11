# YOUTRANSCRIBE

Automatiza la ruta **YouTube → audio → transcripción Markdown** en local y gratis.
Incluye una GUI minimalista en Tkinter y un script CLI.

## Características
- Descarga audio con `yt-dlp` + `ffmpeg`
- Transcribe en ES/EN/DE usando **Whisper** (GPU o CPU)
- Limpia muletillas opcionalmente
- Guarda `.md` en `transcriptions/`
- GUI always-on-top (ventana flotante) + CLI

## Requisitos
```bash
Python ≥3.9
ffmpeg
