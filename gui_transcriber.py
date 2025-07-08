#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pequeña interfaz gráfica que envuelve youtube_transcriber.py
· Ventana siempre en primer plano
· Campo para pegar URL de YouTube
· Botón «Transcribir»
· Mensajes de estado sin congelar la UI (threading)
"""

import threading
import tkinter as tk
from youtube_transcriber import transcribe_youtube_video   # debe estar en la misma carpeta

MODEL_DEFAULT = "base"   # tiny | base | small | medium | large

def start_transcription():
    url = url_entry.get().strip()
    if not url:
        status_var.set("❌ Pega primero una URL")
        return

    status_var.set("⏳ Descargando y transcribiendo…")
    transcribe_btn.config(state=tk.DISABLED)

    def worker():
        try:
            transcribe_youtube_video(url, model_name=MODEL_DEFAULT)
            status_var.set("✅ Listo — revisa /transcriptions")
        except Exception as e:
            status_var.set(f"❌ Error: {e}")
        finally:
            transcribe_btn.config(state=tk.NORMAL)

    threading.Thread(target=worker, daemon=True).start()

# ---------- Tkinter ----------
root = tk.Tk()
root.title("YT → Markdown")
root.attributes("-topmost", True)       # siempre delante
root.resizable(False, False)

tk.Label(root, text="Pega el enlace de YouTube:").pack(padx=10, pady=(10, 0))
url_entry = tk.Entry(root, width=45)
url_entry.pack(padx=10, pady=5)
url_entry.focus()

transcribe_btn = tk.Button(root, text="Transcribir", command=start_transcription)
transcribe_btn.pack(pady=5)

status_var = tk.StringVar(value="Esperando URL…")
tk.Label(root, textvariable=status_var, fg="blue").pack(pady=(0, 10))

root.mainloop()