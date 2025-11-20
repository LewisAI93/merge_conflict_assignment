import os
import threading
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    from yt_dlp import YoutubeDL
except Exception as e:
    # If yt-dlp isn't installed, show a clear message and exit gracefully
    root = tk.Tk(); root.withdraw()
    messagebox.showerror(
        "Missing dependency",
        "yt-dlp is not installed.\n\nInstall it with:\npy -m pip install -U yt-dlp"
    )
    raise SystemExit(1)

def pick_folder():
    path = filedialog.askdirectory()
    if path:
        folder_var.set(path)

def download():
    url = url_var.get().strip()
    outdir = folder_var.get().strip() or os.path.join(os.path.expanduser("~"), "Downloads")

    if not url:
        messagebox.showwarning("Missing URL", "Please paste a Video URL.")
        return

    try:
        os.makedirs(outdir, exist_ok=True)
    except Exception as e:
        messagebox.showerror("Folder Error", f"Cannot use folder:\n{outdir}\n\n{e}")
        return

    progress_var.set(0)
    status_var.set("Starting...")

    def run():
        def hook(d):
            if d.get('status') == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes', 0)
                percent = (downloaded / total * 100) if total else 0
                # update UI from thread
                root.after(0, progress_var.set, percent)
                root.after(0, status_var.set, f"Downloading... {percent:.1f}%")
            elif d.get('status') == 'finished':
                root.after(0, status_var.set, "Processing...")

        has_ffmpeg = shutil.which("ffmpeg") is not None

        # Prefer MP4; if ffmpeg is present, we can merge best video+audio to MP4.
        ydl_opts = {
            "outtmpl": os.path.join(outdir, "%(title)s.%(ext)s"),
            "noplaylist": True,  # download only the single video even if link is from a playlist
            "progress_hooks": [hook],
            "quiet": True,
            "no_warnings": True,
            "concurrent_fragment_downloads": 3,
        }

        if has_ffmpeg:
            ydl_opts["format"] = "bv*[ext=mp4][height<=1080]+ba[ext=m4a]/b[ext=mp4]/b"
            ydl_opts["merge_output_format"] = "mp4"
        else:
            # Fall back to a single MP4 stream when possible (no merging needed)
            ydl_opts["format"] = "b[ext=mp4]/b"

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            root.after(0, progress_var.set, 100)
            root.after(0, status_var.set, "Done!")
            root.after(0, lambda: messagebox.showinfo("Completed", f"Saved to:\n{outdir}"))
        except Exception as e:
            root.after(0, status_var.set, f"Error: {e}")
            root.after(0, lambda: messagebox.showerror("Download Error", str(e)))

    threading.Thread(target=run, daemon=True).start()

# --- Build UI ---
root = tk.Tk()
root.title("AirFun Video Downloader")
root.geometry("560x230")
root.resizable(False, False)

url_var = tk.StringVar()
default_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
folder_var = tk.StringVar(value=default_downloads)
status_var = tk.StringVar(value="Idle")
progress_var = tk.DoubleVar(value=0.0)

ttk.Label(root, text="Videos URL").pack(anchor="w", padx=12, pady=(12, 4))
url_entry = ttk.Entry(root, textvariable=url_var)
url_entry.pack(fill="x", padx=12)

ttk.Label(root, text="Save to").pack(anchor="w", padx=12, pady=(10, 4))
row = ttk.Frame(root); row.pack(fill="x", padx=12)
ttk.Entry(row, textvariable=folder_var).pack(side="left", fill="x", expand=True)
ttk.Button(row, text="Choose...", command=pick_folder).pack(side="left", padx=(8, 0))

ttk.Button(root, text="Download", command=download).pack(pady=12)

ttk.Progressbar(root, variable=progress_var, maximum=100).pack(fill="x", padx=12)
ttk.Label(root, textvariable=status_var).pack(anchor="w", padx=12, pady=(6, 12))

url_entry.focus()
root.mainloop()