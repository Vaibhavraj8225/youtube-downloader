import yt_dlp
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading

class YouTubeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader Pro")
        self.download_thread = None
        self.cancel_flag = False

        self.setup_ui()

    def setup_ui(self):
        # URL input (multi-line)
        tk.Label(self.root, text="YouTube URLs (one per line):").grid(row=0, column=0, sticky="nw")
        self.url_text = tk.Text(self.root, height=5, width=60)
        self.url_text.grid(row=0, column=1, columnspan=2, padx=5, pady=5)

        # Output path
        tk.Label(self.root, text="Save to:").grid(row=1, column=0, sticky="w")
        self.output_entry = tk.Entry(self.root, width=40)
        self.output_entry.grid(row=1, column=1, padx=5, pady=5)
        tk.Button(self.root, text="Browse", command=self.browse_output).grid(row=1, column=2)

        # Quality
        tk.Label(self.root, text="Quality:").grid(row=2, column=0, sticky="w")
        self.quality_var = tk.StringVar(value="best")
        quality_menu = tk.OptionMenu(self.root, self.quality_var, "best", "worst", "1080", "720", "480", "360")
        quality_menu.grid(row=2, column=1, sticky="w", padx=5)

        # Audio only
        self.audio_var = tk.BooleanVar()
        tk.Checkbutton(self.root, text="Audio Only (MP3)", variable=self.audio_var).grid(row=3, column=1, sticky="w", padx=5)

        # Progress bar
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=400, mode="determinate")
        self.progress.grid(row=4, column=1, pady=10, sticky="w")

        # Download and Cancel Buttons
        self.download_btn = tk.Button(self.root, text="Download", command=self.start_download, bg="#4CAF50", fg="white", width=20)
        self.download_btn.grid(row=5, column=1, pady=5)

        self.cancel_btn = tk.Button(self.root, text="Cancel", command=self.cancel_download, bg="#f44336", fg="white", width=10, state=tk.DISABLED)
        self.cancel_btn.grid(row=5, column=2)

    def browse_output(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, folder_selected)

    def start_download(self):
        self.cancel_flag = False
        urls = self.url_text.get("1.0", tk.END).strip().splitlines()
        output_path = self.output_entry.get().strip() or "downloads"
        quality = self.quality_var.get()
        audio_only = self.audio_var.get()

        if not urls or not any(urls):
            messagebox.showwarning("Input Error", "Please enter at least one YouTube URL.")
            return

        # Disable buttons during download
        self.download_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.progress["value"] = 0

        self.download_thread = threading.Thread(
            target=self.download_urls,
            args=(urls, output_path, quality, audio_only)
        )
        self.download_thread.start()

    def download_urls(self, urls, output_path, quality, audio_only):
        for url in urls:
            if self.cancel_flag:
                break
            self.download_video(url, output_path, quality, audio_only)

        self.download_complete()

    def cancel_download(self):
        self.cancel_flag = True
        self.cancel_btn.config(state=tk.DISABLED)
        messagebox.showinfo("Cancelled", "Download has been cancelled.")

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '0.0%').replace('%', '').strip()
            try:
                self.progress["value"] = float(percent)
                self.root.update_idletasks()
            except ValueError:
                pass

    def download_video(self, url, output_path, quality, audio_only):
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        if audio_only:
            format_selector = 'bestaudio'
            postprocessors = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
            merge_output_format = None
        else:
            if quality == 'best':
                format_selector = 'bestvideo+bestaudio/best'
            elif quality == 'worst':
                format_selector = 'worstvideo+worstaudio/worst'
            else:
                format_selector = f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]"

            postprocessors = [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }]
            merge_output_format = 'mp4'

        ydl_opts = {
            'outtmpl': f'{output_path}/%(playlist_title)s/%(title)s.%(ext)s',
            'format': format_selector,
            'merge_output_format': merge_output_format,
            'noplaylist': False,
            'postprocessors': postprocessors,
            'progress_hooks': [self.progress_hook],
            'quiet': True,
        }

        if self.cancel_flag:
            return

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.log_history(url)
        except Exception as e:
            messagebox.showerror("Download Error", f"Failed to download {url}\n\n{e}")

    def download_complete(self):
        self.download_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        if not self.cancel_flag:
            messagebox.showinfo("Complete", "All downloads completed successfully!")

    def log_history(self, url):
        with open("download_history.txt", "a") as f:
            f.write(f"{url}\n")

# Start GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloaderApp(root)
    root.mainloop()
