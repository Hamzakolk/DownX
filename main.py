import os
import sys
import json
import time
import queue
import shutil
import secrets
import threading
import subprocess
import collections
import tkinter as tk
from tkinter import filedialog, messagebox
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import customtkinter as ctk
import yt_dlp

try:
    import libtorrent as lt
    LT_OK = True
except Exception:
    lt = None
    LT_OK = False

APP_NAME = "DownX"
BRIDGE_PORT = 47823
MAX_CONCURRENT_DEFAULT = 3

# Colors taken from the design
BLUE = "#1E88FF"
BLUE_HOVER = "#1570D6"
GREEN = "#2ECC71"
AMBER = "#F5A524"
RED = "#E5484D"
PURPLE = "#8B5CF6"
GREY = "#4A5270"
SIDE = "#0E1425"
CARD = "#141A2E"
CARD2 = "#1B2340"
MUTED = "#8A93B0"

QUALITY_KEYS = ["best", "1080", "720", "480", "audio"]
ACTIVE = ("queued", "downloading", "processing")
FINISHED = ("done", "failed", "cancelled")
COL_WEIGHTS = [5, 4, 1.5, 2, 1.5, 2, 2]

SETTINGS_DIR = os.path.join(os.path.expanduser("~"), ".downx")
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")

DEFAULT_SETTINGS = {
    "lang": "en",
    "save_dir": os.path.join(os.path.expanduser("~"), "Downloads"),
    "max_concurrent": MAX_CONCURRENT_DEFAULT,
    "default_quality": "best",
    "bridge_token": "",
    "bridge_port": BRIDGE_PORT,
}

TEXT = {
    "en": {
        "tagline": "Download Manager",
        "ultra": "Ultra Fast",
        "ultra_sub": "Multi-Source Download Manager",
        "nav_all": "Downloads",
        "nav_torrent": "Torrent",
        "nav_completed": "Completed",
        "nav_queue": "Queue",
        "nav_settings": "Settings",
        "nav_tools": "Tools",
        "nav_about": "About",
        "search": "Paste a link or magnet link...",
        "add": "Add",
        "playlist": "Playlist",
        "quality": "Quality",
        "tab_all": "All Downloads",
        "tab_torrent": "Torrent",
        "col_name": "File Name",
        "col_progress": "Progress",
        "col_speed": "Speed",
        "col_size": "Size",
        "col_time": "Time",
        "col_status": "Status",
        "pause": "Pause",
        "resume": "Resume",
        "stop": "Stop",
        "remove": "Remove",
        "open_folder": "Open",
        "clear": "Clear finished",
        "st_queued": "Queued",
        "st_downloading": "Downloading",
        "st_processing": "Processing",
        "st_paused": "Paused",
        "st_done": "Completed",
        "st_seeding": "Seeding",
        "st_failed": "Failed",
        "st_cancelled": "Cancelled",
        "invalid": "Paste a valid link starting with http://, https:// or magnet:",
        "no_ffmpeg": "ffmpeg not found. Merging and MP3 need it (put it in PATH or next to DownX).",
        "no_lt": "Torrent support needs libtorrent (pip install libtorrent).",
        "bridge_error": "Browser bridge could not start. The port may be in use.",
        "folder": "Save to",
        "change": "Change",
        "open_torrent": "Open .torrent",
        "torrent_title": "Torrent Download",
        "torrent_sub": "Download any .torrent file or magnet link",
        "stat_down": "Download",
        "stat_up": "Upload",
        "stat_seeds": "Seeds",
        "stat_peers": "Peers",
        "free": "Free Space",
        "settings": "Settings",
        "settings_title": "Settings",
        "max_concurrent": "Simultaneous downloads",
        "default_quality": "Default quality",
        "save": "Save",
        "settings_note": "Simultaneous downloads apply to new downloads.",
        "bridge": "Browser extension token",
        "bridge_hint": "Paste this token in the browser extension options to connect.",
        "about_text": "DownX, a download manager.\nVideos use yt-dlp, torrents use libtorrent, and ffmpeg handles merging and MP3.",
        "lang_btn": "العربية",
        "q": {"best": "Best available", "1080": "1080p", "720": "720p", "480": "480p", "audio": "Audio only (MP3)"},
    },
    "ar": {
        "tagline": "مدير التحميل",
        "ultra": "سرعة فائقة",
        "ultra_sub": "مدير تحميل متعدد المصادر",
        "nav_all": "التحميلات",
        "nav_torrent": "تورنت",
        "nav_completed": "المكتملة",
        "nav_queue": "قائمة الانتظار",
        "nav_settings": "الإعدادات",
        "nav_tools": "أدوات",
        "nav_about": "حول",
        "search": "الصق رابطًا أو ماجنت...",
        "add": "إضافة",
        "playlist": "قائمة تشغيل",
        "quality": "الجودة",
        "tab_all": "كل التحميلات",
        "tab_torrent": "تورنت",
        "col_name": "اسم الملف",
        "col_progress": "التقدم",
        "col_speed": "السرعة",
        "col_size": "الحجم",
        "col_time": "الوقت",
        "col_status": "الحالة",
        "pause": "إيقاف مؤقت",
        "resume": "استئناف",
        "stop": "إيقاف",
        "remove": "حذف",
        "open_folder": "فتح",
        "clear": "مسح المكتمل",
        "st_queued": "في الانتظار",
        "st_downloading": "جاري التحميل",
        "st_processing": "جاري المعالجة",
        "st_paused": "متوقف مؤقتًا",
        "st_done": "اكتمل",
        "st_seeding": "جاري المشاركة",
        "st_failed": "فشل",
        "st_cancelled": "أُلغي",
        "invalid": "الصق رابطًا صحيحًا يبدأ بـ http:// أو https:// أو magnet:",
        "no_ffmpeg": "ffmpeg غير موجود. الدمج وتحويل MP3 يحتاجانه (ضعه في PATH أو بجوار DownX).",
        "no_lt": "دعم التورنت يحتاج libtorrent (pip install libtorrent).",
        "bridge_error": "تعذّر تشغيل ربط المتصفح. ربما المنفذ مستخدم.",
        "folder": "الحفظ في",
        "change": "تغيير",
        "open_torrent": "فتح ملف .torrent",
        "torrent_title": "تحميل تورنت",
        "torrent_sub": "حمّل أي ملف .torrent أو رابط ماجنت",
        "stat_down": "تحميل",
        "stat_up": "رفع",
        "stat_seeds": "بذور",
        "stat_peers": "أقران",
        "free": "المساحة الفارغة",
        "settings": "الإعدادات",
        "settings_title": "الإعدادات",
        "max_concurrent": "عدد التحميلات المتزامنة",
        "default_quality": "الجودة الافتراضية",
        "save": "حفظ",
        "settings_note": "التحميلات المتزامنة تطبق على التحميلات الجديدة.",
        "bridge": "توكن إضافة المتصفح",
        "bridge_hint": "الصق هذا التوكن في إعدادات الإضافة في المتصفح للربط.",
        "about_text": "DownX، مدير تحميل.\nالفيديوهات بـ yt-dlp، والتورنت بـ libtorrent، وffmpeg للدمج وتحويل MP3.",
        "lang_btn": "English",
        "q": {"best": "أفضل جودة متاحة", "1080": "1080p", "720": "720p", "480": "480p", "audio": "صوت فقط (MP3)"},
    },
}


# ---------- helpers ----------
def load_settings():
    settings = dict(DEFAULT_SETTINGS)
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            settings.update(json.load(f))
    except (OSError, ValueError):
        pass
    if not os.path.isdir(settings["save_dir"]):
        settings["save_dir"] = DEFAULT_SETTINGS["save_dir"]
    settings["max_concurrent"] = min(max(int(settings["max_concurrent"]), 1), 5)
    if not settings["bridge_token"]:
        settings["bridge_token"] = secrets.token_urlsafe(24)
        save_settings(settings)
    return settings


def save_settings(settings):
    os.makedirs(SETTINGS_DIR, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def find_ffmpeg_dir():
    """Return None if ffmpeg is on PATH, a folder if bundled, or 'missing'."""
    if shutil.which("ffmpeg"):
        return None
    name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    for d in (os.path.dirname(os.path.abspath(sys.argv[0])),
              getattr(sys, "_MEIPASS", ""),
              os.path.dirname(sys.executable)):
        if d and os.path.isfile(os.path.join(d, name)):
            return d
    return "missing"


def fmt_speed(bps):
    if not bps:
        return "0 KB/s"
    if bps >= 1024 * 1024:
        return f"{bps / 1024 / 1024:.1f} MB/s"
    return f"{bps / 1024:.0f} KB/s"


def fmt_size(n):
    if not n:
        return "0 B"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def fmt_time(sec):
    m, s = divmod(int(sec), 60)
    h, m = divmod(m, 60)
    return f"{h:02}:{m:02}:{s:02}" if h else f"{m:02}:{s:02}"


class Stop(Exception):
    pass


class Pause(Exception):
    pass


class Item:
    def __init__(self, url, folder, kind):
        self.url = url
        self.folder = folder
        self.kind = kind  # "video" or "torrent"
        self.opts = None
        self.handle = None
        self.title = url
        self.status = "queued"
        self.progress = 0.0
        self.speed = 0.0
        self.upload = 0.0
        self.downloaded = 0
        self.total = 0
        self.peers = 0
        self.seeds = 0
        self.cancelled = False
        self.paused = False
        self.running = False
        self.started = None
        self.row = None
        self.shown = True

    def short_title(self):
        t = self.title or ""
        return t if len(t) <= 70 else t[:67] + "..."


# ---------- browser bridge ----------
class BridgeHandler(BaseHTTPRequestHandler):
    """Local endpoint for the browser extension. Listens on 127.0.0.1 only."""

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-DownX-Token")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

    def _reply(self, code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path == "/ping":
            self._reply(200, {"app": APP_NAME})
        else:
            self._reply(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/add":
            self._reply(404, {"error": "not found"})
            return
        if self.headers.get("X-DownX-Token", "") != self.server.token:
            self._reply(403, {"error": "bad token"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            self._reply(400, {"error": "bad json"})
            return
        url = str(data.get("url", "")).strip()
        if not url.startswith(("http://", "https://")):
            self._reply(400, {"error": "invalid url"})
            return
        self.server.inbox.put(url)
        self._reply(200, {"ok": True})

    def log_message(self, format, *args):
        pass


def start_bridge(token, port, inbox):
    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), BridgeHandler)
    except OSError:
        return None
    server.token = token
    server.inbox = inbox
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


# ---------- settings window ----------
class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title(app.t("settings_title"))
        self.geometry("520x430")
        self.resizable(False, False)
        self.grid_columnconfigure(1, weight=1)
        self.selected_folder = app.save_dir

        ctk.CTkLabel(self, text=app.t("folder")).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 8))
        self.folder_lbl = ctk.CTkLabel(self, text=app.save_dir, anchor="w", text_color=MUTED)
        self.folder_lbl.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=(20, 8))
        ctk.CTkButton(self, text=app.t("change"), width=90, fg_color="transparent",
                      border_width=1, command=self._pick_folder).grid(row=0, column=2, padx=(0, 20), pady=(20, 8))

        ctk.CTkLabel(self, text=app.t("max_concurrent")).grid(row=1, column=0, sticky="w", padx=20, pady=8)
        self.concurrent_menu = ctk.CTkOptionMenu(self, width=120, values=[str(i) for i in range(1, 6)])
        self.concurrent_menu.set(str(app.max_concurrent))
        self.concurrent_menu.grid(row=1, column=1, sticky="w", pady=8)

        ctk.CTkLabel(self, text=app.t("default_quality")).grid(row=2, column=0, sticky="w", padx=20, pady=8)
        labels = [TEXT[app.lang]["q"][k] for k in QUALITY_KEYS]
        self.quality_menu = ctk.CTkOptionMenu(self, width=200, values=labels)
        self.quality_menu.set(TEXT[app.lang]["q"][app.default_quality])
        self.quality_menu.grid(row=2, column=1, sticky="w", pady=8)

        ctk.CTkLabel(self, text=app.t("settings_note"), text_color=MUTED, wraplength=460,
                     anchor="w", justify="left").grid(row=3, column=0, columnspan=3, sticky="w", padx=20, pady=(12, 8))

        ctk.CTkLabel(self, text=app.t("bridge")).grid(row=4, column=0, sticky="w", padx=20, pady=8)
        token = ctk.CTkEntry(self, width=260)
        token.insert(0, app.bridge_token)
        token.configure(state="readonly")
        token.grid(row=4, column=1, columnspan=2, sticky="w", padx=(0, 20), pady=8)
        ctk.CTkLabel(self, text=app.t("bridge_hint"), text_color=MUTED, wraplength=460,
                     anchor="w", justify="left").grid(row=5, column=0, columnspan=3, sticky="w", padx=20)

        ctk.CTkButton(self, text=app.t("save"), fg_color=BLUE, hover_color=BLUE_HOVER,
                      command=self._save).grid(row=6, column=2, sticky="e", padx=20, pady=(16, 20))

    def _pick_folder(self):
        chosen = filedialog.askdirectory(initialdir=self.selected_folder, parent=self)
        if chosen:
            self.selected_folder = chosen
            self.folder_lbl.configure(text=chosen)

    def _save(self):
        q_label = self.quality_menu.get()
        qkey = next((k for k in QUALITY_KEYS if TEXT[self.app.lang]["q"][k] == q_label), "best")
        self.app.apply_settings(self.selected_folder, int(self.concurrent_menu.get()), qkey)
        self.destroy()


# ---------- main app ----------
class DownX(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.title(APP_NAME)
        self.geometry("1280x780")
        self.minsize(1000, 640)
        self.configure(fg_color="#0A0F1E")

        s = load_settings()
        self.lang = s["lang"]
        self.save_dir = s["save_dir"]
        self.max_concurrent = s["max_concurrent"]
        self.default_quality = s["default_quality"]
        self.quality_key = self.default_quality
        self.bridge_token = s["bridge_token"]
        self.bridge_port = int(s["bridge_port"])
        self.slots = threading.BoundedSemaphore(self.max_concurrent)
        self.ffmpeg_dir = find_ffmpeg_dir()

        self.items = []
        self.view = "all"
        self.inbox = queue.Queue()
        self.bridge = start_bridge(self.bridge_token, self.bridge_port, self.inbox)
        self.speed_hist = collections.deque([0.0] * 60, maxlen=60)
        self.up_hist = collections.deque([0.0] * 60, maxlen=60)

        self._build()
        self._apply_lang()
        self._set_view("all")

        if self.ffmpeg_dir == "missing":
            self.status_msg(self.t("no_ffmpeg"), RED)
        elif self.bridge is None:
            self.status_msg(self.t("bridge_error"), RED)
        self._poll()

    def t(self, key):
        return TEXT[self.lang][key]

    def _persist(self):
        save_settings({
            "lang": self.lang,
            "save_dir": self.save_dir,
            "max_concurrent": self.max_concurrent,
            "default_quality": self.default_quality,
            "bridge_token": self.bridge_token,
            "bridge_port": self.bridge_port,
        })

    def status_msg(self, text, color=MUTED):
        self.msg_lbl.configure(text=text, text_color=color)

    # ----- layout -----
    def _build(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Sidebar
        side = ctk.CTkFrame(self, width=230, corner_radius=0, fg_color=SIDE)
        side.grid(row=0, column=0, rowspan=5, sticky="ns")
        side.grid_propagate(False)
        side.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(side, text=APP_NAME, font=ctk.CTkFont(size=34, weight="bold"),
                     text_color=BLUE).grid(row=0, column=0, pady=(22, 0))
        self.tagline = ctk.CTkLabel(side, text="", text_color=MUTED)
        self.tagline.grid(row=1, column=0, pady=(0, 18))

        self.nav = {}
        for i, (key, cmd) in enumerate([
            ("all", lambda: self._set_view("all")),
            ("torrent", lambda: self._set_view("torrent")),
            ("completed", lambda: self._set_view("completed")),
            ("queue", lambda: self._set_view("queue")),
            ("settings", self._open_settings),
            ("tools", self._open_tools),
            ("about", self._open_about),
        ]):
            btn = ctk.CTkButton(side, height=42, anchor="w", corner_radius=12,
                                fg_color="transparent", hover_color=CARD2,
                                font=ctk.CTkFont(size=14), command=cmd)
            btn.grid(row=2 + i, column=0, sticky="ew", padx=16, pady=4)
            self.nav[key] = btn

        card = ctk.CTkFrame(side, fg_color=CARD2, corner_radius=14)
        card.grid(row=20, column=0, sticky="ew", padx=16, pady=(18, 18))
        card.grid_columnconfigure(0, weight=1)
        self.ultra_lbl = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=15, weight="bold"), anchor="w")
        self.ultra_lbl.grid(row=0, column=0, sticky="w", padx=14, pady=(12, 0))
        self.ultra_sub = ctk.CTkLabel(card, text="", text_color=MUTED, anchor="w", justify="left")
        self.ultra_sub.grid(row=1, column=0, sticky="w", padx=14)
        ctk.CTkLabel(card, text=APP_NAME, fg_color=BLUE, corner_radius=10,
                     text_color="white", width=90, height=28).grid(row=2, column=0, pady=(10, 12))
        side.grid_rowconfigure(19, weight=1)

        # Top bar
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=1, sticky="ew", padx=20, pady=(16, 6))
        top.grid_columnconfigure(0, weight=1)
        self.url_entry = ctk.CTkEntry(top, height=42, corner_radius=12)
        self.url_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.url_entry.bind("<Return>", lambda e: self._add())
        self.add_btn = ctk.CTkButton(top, width=100, height=42, corner_radius=12,
                                     fg_color=BLUE, hover_color=BLUE_HOVER, command=self._add)
        self.add_btn.grid(row=0, column=1, padx=(0, 14))

        self.playlist_var = ctk.BooleanVar(value=False)
        self.playlist_chk = ctk.CTkCheckBox(top, text="", variable=self.playlist_var, width=24)
        self.playlist_chk.grid(row=0, column=2, padx=(0, 8))
        self.quality_menu = ctk.CTkOptionMenu(top, width=170, values=[""], command=self._on_quality)
        self.quality_menu.grid(row=0, column=3, padx=(0, 14))
        self.clear_btn = ctk.CTkButton(top, width=130, height=42, corner_radius=12,
                                       fg_color=CARD2, hover_color=CARD, command=self._clear_finished)
        self.clear_btn.grid(row=0, column=4)

        # Tabs
        self.tabs = ctk.CTkSegmentedButton(self, height=36, corner_radius=12,
                                           selected_color=BLUE, command=self._on_tab)
        self.tabs.grid(row=1, column=1, sticky="w", padx=20, pady=(4, 8))

        # List container with header
        box = ctk.CTkFrame(self, fg_color=CARD, corner_radius=16)
        box.grid(row=2, column=1, sticky="nsew", padx=20, pady=(0, 10))
        box.grid_rowconfigure(1, weight=1)
        box.grid_columnconfigure(0, weight=1)

        self.header = ctk.CTkFrame(box, fg_color=CARD2, corner_radius=10)
        self.header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))
        self._apply_cols(self.header)
        self.header_labels = []
        for i in range(len(COL_WEIGHTS)):
            lbl = ctk.CTkLabel(self.header, text="", text_color=MUTED, anchor="w")
            lbl.grid(row=0, column=i, sticky="ew", padx=10, pady=8)
            self.header_labels.append(lbl)

        self.list_frame = ctk.CTkScrollableFrame(box, fg_color="transparent")
        self.list_frame.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 8))
        self._apply_cols(self.list_frame)

        # Torrent panel (shown on the torrent tab)
        self.tpanel = ctk.CTkFrame(self, fg_color=CARD, corner_radius=16)
        self.tpanel.grid(row=3, column=1, sticky="ew", padx=20, pady=(0, 10))
        self.tpanel.grid_columnconfigure(1, weight=1)
        left = ctk.CTkFrame(self.tpanel, fg_color="transparent")
        left.grid(row=0, column=0, padx=16, pady=14, sticky="n")
        self.tp_title = ctk.CTkLabel(left, text="", font=ctk.CTkFont(size=15, weight="bold"))
        self.tp_title.pack()
        self.tp_sub = ctk.CTkLabel(left, text="", text_color=MUTED)
        self.tp_sub.pack(pady=(2, 10))
        self.open_torrent_btn = ctk.CTkButton(left, width=200, fg_color=BLUE, hover_color=BLUE_HOVER,
                                              command=self._open_torrent_file)
        self.open_torrent_btn.pack()

        mid = ctk.CTkFrame(self.tpanel, fg_color="transparent")
        mid.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        mid.grid_columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(mid, height=110, bg=CARD, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="ew")
        self.stats_lbl = ctk.CTkLabel(mid, text="", anchor="w", justify="left", text_color=MUTED)
        self.stats_lbl.grid(row=1, column=0, sticky="w", pady=(6, 0))

        right = ctk.CTkFrame(self.tpanel, fg_color="transparent")
        right.grid(row=0, column=2, padx=16, pady=14)
        self.tp_pause = ctk.CTkButton(right, width=90, fg_color=CARD2, hover_color=CARD2,
                                      command=lambda: self._toggle_pause(self._first_torrent()))
        self.tp_pause.pack(pady=4)
        self.tp_stop = ctk.CTkButton(right, width=90, fg_color=CARD2, hover_color=CARD2,
                                     command=lambda: self._cancel(self._first_torrent()))
        self.tp_stop.pack(pady=4)

        # Status bar
        bar = ctk.CTkFrame(self, fg_color=CARD, corner_radius=12, height=40)
        bar.grid(row=4, column=1, sticky="ew", padx=20, pady=(0, 14))
        bar.grid_columnconfigure(3, weight=1)
        self.down_total = ctk.CTkLabel(bar, text="", text_color=GREEN)
        self.down_total.grid(row=0, column=0, padx=(16, 14), pady=8)
        self.up_total = ctk.CTkLabel(bar, text="", text_color=BLUE)
        self.up_total.grid(row=0, column=1, padx=(0, 14))
        self.free_lbl = ctk.CTkLabel(bar, text="", text_color=MUTED)
        self.free_lbl.grid(row=0, column=2, padx=(0, 14))
        self.msg_lbl = ctk.CTkLabel(bar, text="", text_color=MUTED, anchor="w")
        self.msg_lbl.grid(row=0, column=3, sticky="w")
        ctk.CTkLabel(bar, text="By Hamza", text_color=AMBER,
                     font=ctk.CTkFont(size=14, weight="bold", slant="italic")).grid(row=0, column=4, padx=16)

    def _apply_cols(self, frame):
        for i, w in enumerate(COL_WEIGHTS):
            frame.grid_columnconfigure(i, weight=w)

    def _apply_lang(self):
        ar = self.lang == "ar"
        anchor_justify = "right" if ar else "left"
        self.tagline.configure(text=self.t("tagline"))
        self.ultra_lbl.configure(text=self.t("ultra"))
        self.ultra_sub.configure(text=self.t("ultra_sub"))
        self.url_entry.configure(placeholder_text=self.t("search"), justify=anchor_justify)
        self.add_btn.configure(text=self.t("add"))
        self.playlist_chk.configure(text=self.t("playlist"))
        labels = [TEXT[self.lang]["q"][k] for k in QUALITY_KEYS]
        self.quality_menu.configure(values=labels)
        self.quality_menu.set(TEXT[self.lang]["q"][self.quality_key])
        self.clear_btn.configure(text=self.t("clear"))
        self.tabs.configure(values=[self.t("tab_all"), self.t("tab_torrent")])
        for lbl, key in zip(self.header_labels,
                            ["col_name", "col_progress", "col_speed", "col_size", "col_time", "col_status"]):
            lbl.configure(text=self.t(key))
        self.nav["settings"].configure(text=self.t("nav_settings"))
        self.nav["tools"].configure(text=f"{self.t('nav_tools')}  >")
        self.nav["about"].configure(text=self.t("nav_about"))
        self.tp_title.configure(text=self.t("torrent_title"))
        self.tp_sub.configure(text=self.t("torrent_sub"))
        self.open_torrent_btn.configure(text=self.t("open_torrent"))
        self.tp_pause.configure(text=self.t("pause"))
        self.tp_stop.configure(text=self.t("stop"))
        self.lang_btn_text = self.t("lang_btn")
        self._update_nav_counts()
        self._refresh_all_rows()

    def _toggle_lang(self):
        self.lang = "ar" if self.lang == "en" else "en"
        self._apply_lang()
        self._persist()

    def _on_tab(self, label):
        self._set_view("torrent" if label == self.t("tab_torrent") else "all")

    def _set_view(self, view):
        self.view = view
        self.tabs.set(self.t("tab_torrent") if view == "torrent" else self.t("tab_all"))
        for key in ("all", "torrent", "completed", "queue"):
            active = key == view
            self.nav[key].configure(fg_color=BLUE if active else "transparent")
        if view == "torrent":
            self.tpanel.grid()
        else:
            self.tpanel.grid_remove()
        self._refresh_all_rows()

    def _on_quality(self, label):
        for k in QUALITY_KEYS:
            if TEXT[self.lang]["q"][k] == label:
                self.quality_key = k
                break

    # ----- sidebar actions -----
    def _open_settings(self):
        SettingsWindow(self)

    def _open_tools(self):
        m = tk.Menu(self, tearoff=0)
        m.add_command(label=self.t("clear"), command=self._clear_finished)
        m.add_command(label=self.t("open_folder"), command=lambda: self._open_folder(self.save_dir))
        m.add_command(label=self.t("change"), command=self._change_folder)
        try:
            m.tk_popup(self.winfo_pointerx(), self.winfo_pointery())
        finally:
            m.grab_release()

    def _open_about(self):
        messagebox.showinfo(APP_NAME, self.t("about_text"), parent=self)

    def _change_folder(self):
        chosen = filedialog.askdirectory(initialdir=self.save_dir)
        if chosen:
            self.save_dir = chosen
            self._persist()

    def apply_settings(self, save_dir, max_concurrent, default_quality):
        self.save_dir = save_dir
        self.max_concurrent = max_concurrent
        self.default_quality = default_quality
        self.quality_key = default_quality
        self.slots = threading.BoundedSemaphore(max_concurrent)
        self._apply_lang()
        self._persist()

    # ----- adding -----
    def _add(self):
        text = self.url_entry.get().strip()
        if not text.startswith(("http://", "https://", "magnet:")):
            self.status_msg(self.t("invalid"), RED)
            return
        self.url_entry.delete(0, "end")
        self._enqueue(text, bool(self.playlist_var.get()))

    def _open_torrent_file(self):
        path = filedialog.askopenfilename(filetypes=[("Torrent", "*.torrent")])
        if path:
            self._enqueue(path, False)

    def _enqueue(self, url, playlist):
        is_torrent = url.startswith("magnet:") or url.lower().endswith(".torrent")
        if is_torrent:
            if not LT_OK:
                self.status_msg(self.t("no_lt"), RED)
                return
            item = Item(url, self.save_dir, "torrent")
            item.title = url if url.startswith("magnet:") else os.path.basename(url)
            target = self._run_torrent
        else:
            if self.ffmpeg_dir == "missing":
                self.status_msg(self.t("no_ffmpeg"), RED)
            item = Item(url, self.save_dir, "video")
            item.opts = self._build_opts(self.save_dir, self.quality_key, playlist,
                                         lambda d, it=item: self._hook(it, d))
            target = self._run_video

        self.items.append(item)
        self._make_row(item)
        self._apply_cols(item.row)
        threading.Thread(target=target, args=(item,), daemon=True).start()
        self._refresh_all_rows()

    def _build_opts(self, folder, quality, playlist, hook):
        opts = {
            "outtmpl": os.path.join(folder, "%(title).150B.%(ext)s"),
            "noplaylist": not playlist,
            "progress_hooks": [hook],
            "quiet": True,
            "no_warnings": True,
            "merge_output_format": "mp4",
        }
        if self.ffmpeg_dir not in (None, "missing"):
            opts["ffmpeg_location"] = self.ffmpeg_dir
        if quality == "audio":
            opts["format"] = "bestaudio/best"
            opts["postprocessors"] = [{"key": "FFmpegExtractAudio",
                                       "preferredcodec": "mp3", "preferredquality": "192"}]
        elif quality == "best":
            opts["format"] = "bv*+ba/b"
        else:
            h = int(quality)
            opts["format"] = f"bv*[height<={h}]+ba/b[height<={h}]"
        return opts

    # ----- workers -----
    def _hook(self, item, d):
        if item.cancelled:
            raise Stop()
        if item.paused:
            raise Pause()
        info = d.get("info_dict") or {}
        if info.get("title"):
            item.title = info["title"]
        if d["status"] == "downloading":
            item.downloaded = d.get("downloaded_bytes", 0) or 0
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            if total:
                item.total = total
                item.progress = min(item.downloaded / total, 0.99)
            item.speed = d.get("speed") or 0
            item.status = "downloading"
        elif d["status"] == "finished":
            item.status = "processing"

    def _run_video(self, item):
        item.running = True
        try:
            with self.slots:
                if item.cancelled:
                    item.status = "cancelled"
                    return
                if item.paused:
                    item.status = "paused"
                    return
                item.status = "downloading"
                try:
                    with yt_dlp.YoutubeDL(item.opts) as ydl:
                        ydl.download([item.url])
                    if item.cancelled:
                        item.status = "cancelled"
                    else:
                        item.status = "done"
                        item.progress = 1.0
                except (Stop, Pause):
                    pass
                except Exception:
                    if item.cancelled:
                        item.status = "cancelled"
                    elif item.paused:
                        pass
                    else:
                        item.status = "failed"
                if item.status != "done" and item.paused and not item.cancelled:
                    item.status = "paused"
                if item.cancelled and item.status != "done":
                    item.status = "cancelled"
        finally:
            item.running = False

    def _run_torrent(self, item):
        item.running = True
        try:
            with self.slots:
                if item.cancelled:
                    item.status = "cancelled"
                    return
                ses = lt.session()
                try:
                    ses.listen_on(6881, 6891)
                except Exception:
                    pass
                if item.url.startswith("magnet:"):
                    params = lt.parse_magnet_uri(item.url)
                else:
                    params = lt.add_torrent_params()
                    params.ti = lt.torrent_info(item.url)
                params.save_path = item.folder
                item.handle = ses.add_torrent(params)
                last_paused = False
                while not item.cancelled:
                    if item.paused != last_paused:
                        if item.paused:
                            item.handle.pause()
                        else:
                            item.handle.resume()
                        last_paused = item.paused
                    s = item.handle.status()
                    name = item.handle.name()
                    if name:
                        item.title = name
                    item.progress = s.progress
                    item.speed = s.download_rate
                    item.upload = s.upload_rate
                    item.downloaded = s.total_wanted_done
                    item.total = s.total_wanted
                    item.peers = s.num_peers
                    item.seeds = s.num_seeds
                    if item.paused:
                        item.status = "paused"
                    elif s.is_seeding or s.is_finished:
                        item.status = "done"
                        item.progress = 1.0
                        break
                    else:
                        item.status = "downloading"
                        if item.started is None:
                            item.started = time.time()
                    time.sleep(1)
                if item.cancelled:
                    item.status = "cancelled"
                    ses.remove_torrent(item.handle)
        except Exception:
            item.status = "cancelled" if item.cancelled else "failed"
        finally:
            item.running = False

    # ----- actions on items -----
    def _first_torrent(self):
        return next((it for it in self.items if it.kind == "torrent"), None)

    def _toggle_pause(self, item):
        if item is None or item.status in FINISHED:
            return
        if item.paused:
            item.paused = False
            if item.kind == "video" and not item.running:
                item.status = "queued"
                threading.Thread(target=self._run_video, args=(item,), daemon=True).start()
            elif item.kind == "torrent" and not item.running:
                threading.Thread(target=self._run_torrent, args=(item,), daemon=True).start()
        else:
            item.paused = True
        self._refresh_all_rows()

    def _cancel(self, item):
        if item is None:
            return
        item.cancelled = True
        item.paused = False
        if item.status == "queued":
            item.status = "cancelled"

    def _remove(self, item):
        if item.status in ACTIVE or item.status == "paused":
            self._cancel(item)
            return
        if item.row is not None:
            item.row.destroy()
        if item in self.items:
            self.items.remove(item)

    def _clear_finished(self):
        for it in list(self.items):
            if it.status in FINISHED:
                self._remove(it)

    def _open_folder(self, folder):
        if sys.platform.startswith("win"):
            os.startfile(folder)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", folder])
        else:
            subprocess.Popen(["xdg-open", folder])

    # ----- rows -----
    def _make_row(self, item):
        row = ctk.CTkFrame(self.list_frame, fg_color=CARD2, corner_radius=12, height=58)
        row.pack(fill="x", padx=4, pady=4)
        item.row = row

        name_box = ctk.CTkFrame(row, fg_color="transparent")
        name_box.grid(row=0, column=0, sticky="ew", padx=(12, 6), pady=8)
        ext = "T" if item.kind == "torrent" else "V"
        ctk.CTkLabel(name_box, text=ext, width=34, height=34, corner_radius=8,
                     fg_color=PURPLE if item.kind == "torrent" else BLUE,
                     text_color="white").pack(side="left")
        item.name_lbl = ctk.CTkLabel(name_box, text="", anchor="w")
        item.name_lbl.pack(side="left", padx=8, fill="x", expand=True)

        prog = ctk.CTkFrame(row, fg_color="transparent")
        prog.grid(row=0, column=1, sticky="ew", padx=6)
        item.bar = ctk.CTkProgressBar(prog, height=8, progress_color=BLUE)
        item.bar.set(0)
        item.bar.pack(side="left", fill="x", expand=True)
        item.pct_lbl = ctk.CTkLabel(prog, text="0%", width=46)
        item.pct_lbl.pack(side="right")

        item.speed_lbl = ctk.CTkLabel(row, text="-", anchor="w")
        item.speed_lbl.grid(row=0, column=2, sticky="ew", padx=6)
        item.size_lbl = ctk.CTkLabel(row, text="-", anchor="w")
        item.size_lbl.grid(row=0, column=3, sticky="ew", padx=6)
        item.time_lbl = ctk.CTkLabel(row, text="-", anchor="w", text_color=MUTED)
        item.time_lbl.grid(row=0, column=4, sticky="ew", padx=6)
        item.status_lbl = ctk.CTkLabel(row, text="", corner_radius=12, height=26, text_color="white")
        item.status_lbl.grid(row=0, column=5, sticky="w", padx=6)

        acts = ctk.CTkFrame(row, fg_color="transparent")
        acts.grid(row=0, column=6, sticky="e", padx=(6, 12))
        item.act_pause = ctk.CTkButton(acts, width=34, height=28, corner_radius=8,
                                       fg_color=GREY, hover_color=GREY)
        item.act_pause.pack(side="left", padx=2)
        item.act_open = ctk.CTkButton(acts, width=34, height=28, corner_radius=8,
                                      fg_color=GREY, hover_color=GREY, text="📁")
        item.act_open.pack(side="left", padx=2)
        item.act_remove = ctk.CTkButton(acts, width=34, height=28, corner_radius=8,
                                        fg_color=GREY, hover_color=RED, text="✕",
                                        command=lambda i=item: self._remove(i))
        item.act_remove.pack(side="left", padx=2)

    def _status_style(self, it):
        table = {
            "queued": (GREY, "st_queued"),
            "downloading": (BLUE, "st_downloading"),
            "processing": (PURPLE, "st_processing"),
            "paused": (AMBER, "st_paused"),
            "done": (GREEN, "st_done"),
            "failed": (RED, "st_failed"),
            "cancelled": (GREY, "st_cancelled"),
        }
        if it.kind == "torrent" and it.status == "done":
            return GREEN, self.t("st_seeding")
        color, key = table.get(it.status, (GREY, "st_queued"))
        return color, self.t(key)

    def _visible(self, it):
        if self.view == "all":
            return it.kind == "video"
        if self.view == "torrent":
            return it.kind == "torrent"
        if self.view == "completed":
            return it.status == "done"
        if self.view == "queue":
            return it.status == "queued"
        return False

    def _update_row(self, it):
        if it.row is None:
            return
        want = self._visible(it)
        if want != it.shown:
            if want:
                it.row.pack(fill="x", padx=4, pady=4)
            else:
                it.row.pack_forget()
            it.shown = want
        if not want:
            return

        if it.status == "downloading" and it.started is None:
            it.started = time.time()
        it.name_lbl.configure(text=it.short_title())
        it.bar.set(it.progress)
        it.pct_lbl.configure(text=f"{int(it.progress * 100)}%")
        if it.status == "downloading":
            speed = it.speed if it.kind == "video" else it.speed
            it.speed_lbl.configure(text=fmt_speed(speed))
        else:
            it.speed_lbl.configure(text="-")
        it.size_lbl.configure(text=f"{fmt_size(it.downloaded)} / {fmt_size(it.total)}" if it.total else "-")
        if it.status in ("downloading", "processing") and it.started:
            it.time_lbl.configure(text=fmt_time(time.time() - it.started))
        elif it.status == "done":
            it.time_lbl.configure(text="Done")
        else:
            it.time_lbl.configure(text="-")
        color, text = self._status_style(it)
        it.status_lbl.configure(text=f"  {text}  ", fg_color=color)

        finished = it.status in FINISHED
        if it.status == "done" or (it.kind == "torrent" and it.status == "done"):
            it.act_open.configure(state="normal", command=lambda f=it.folder: self._open_folder(f))
        else:
            it.act_open.configure(state="disabled")
        if finished:
            it.act_pause.configure(state="disabled", text="")
        else:
            it.act_pause.configure(state="normal",
                                   text="▶" if it.paused else "❚❚",
                                   command=lambda i=it: self._toggle_pause(i))
        it.act_remove.configure(text="✕")

    def _refresh_all_rows(self):
        for it in self.items:
            self._update_row(it)

    # ----- counters and panels -----
    def _update_nav_counts(self):
        downloads = sum(1 for i in self.items if i.kind == "video" and i.status in ACTIVE + ("paused",))
        torrents = sum(1 for i in self.items if i.kind == "torrent" and i.status not in FINISHED)
        completed = sum(1 for i in self.items if i.status == "done")
        queued = sum(1 for i in self.items if i.status == "queued")
        self.nav["all"].configure(text=f"{self.t('nav_all')}     {downloads}")
        self.nav["torrent"].configure(text=f"{self.t('nav_torrent')}     {torrents}")
        self.nav["completed"].configure(text=f"{self.t('nav_completed')}     {completed}")
        self.nav["queue"].configure(text=f"{self.t('nav_queue')}     {queued}")

    def _update_torrent_panel(self):
        first = self._first_torrent()
        self.speed_hist.append(first.speed if first else 0.0)
        self.up_hist.append(first.upload if first else 0.0)

        if first is None:
            self.stats_lbl.configure(text=f"{self.t('stat_down')}: 0 KB/s\n{self.t('stat_up')}: 0 KB/s\n"
                                          f"{self.t('stat_seeds')}: 0      {self.t('stat_peers')}: 0")
        else:
            self.stats_lbl.configure(
                text=f"{self.t('stat_down')}: {fmt_speed(first.speed)}\n"
                     f"{self.t('stat_up')}: {fmt_speed(first.upload)}\n"
                     f"{self.t('stat_seeds')}: {first.seeds}      {self.t('stat_peers')}: {first.peers}")
            self.tp_pause.configure(text=self.t("resume") if first.paused else self.t("pause"))

        self.canvas.delete("all")
        w = max(self.canvas.winfo_width(), 200)
        h = 110
        for hist, color in ((self.speed_hist, BLUE), (self.up_hist, GREEN)):
            peak = max(max(hist), 1)
            n = len(hist)
            pts = []
            for i, v in enumerate(hist):
                x = i * (w / max(n - 1, 1))
                y = h - 8 - (v / peak) * (h - 16)
                pts += [x, y]
            self.canvas.create_line(*pts, fill=color, width=2, smooth=True)

    def _update_statusbar(self):
        down = sum(i.speed for i in self.items if i.status == "downloading")
        up = sum(i.upload for i in self.items if i.kind == "torrent" and i.status not in FINISHED)
        self.down_total.configure(text=f"↓ {fmt_speed(down)}")
        self.up_total.configure(text=f"↑ {fmt_speed(up)}")
        try:
            usage = shutil.disk_usage(self.save_dir)
            free_gb = usage.free / 1024 ** 3
            total_gb = usage.total / 1024 ** 3
            self.free_lbl.configure(text=f"{self.t('free')}: {free_gb:.0f} GB / {total_gb:.0f} GB")
        except OSError:
            self.free_lbl.configure(text="")

    # ----- main loop -----
    def _poll(self):
        while True:
            try:
                url = self.inbox.get_nowait()
            except queue.Empty:
                break
            self._enqueue(url, False)

        self._refresh_all_rows()
        self._update_nav_counts()
        self._update_statusbar()
        if self.view == "torrent":
            self._update_torrent_panel()
        self.after(400, self._poll)


if __name__ == "__main__":
    DownX().mainloop()
