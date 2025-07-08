Objetivo: Automatizar la ruta “YouTube → Audio → Transcripción Markdown limpia” en tu computadora local, usando solo software gratuito.

1. Entorno
   • Python ≥3.9, ffmpeg, yt-dlp, Whisper, PyTorch (CPU o GPU).  
2. Descarga
   • Extraer audio con yt-dlp → ffmpeg.  
3. Transcripción
   • Whisper detecta idioma (ES/EN/DE) y genera texto.  
4. Limpieza
   • Opcional: quitar muletillas y espacios redundantes.  
5. Persistencia
   • Guardar en `transcriptions/` como `Título.md` con encabezado H1.  
6. Extensión futura
   • Procesar playlists, resumir con LLM, publicar en blog/Obsidian, etc.
