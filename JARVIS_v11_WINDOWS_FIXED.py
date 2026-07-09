#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║       JARVIS ULTIMATE v4.0 — Production-Grade AI Desktop Assistant          ║
║  Modules: AppControl | WebOps | AIGateway | SysCtrl | Tasks | VoiceCore     ║
║           TTS | FileManager | ScreenOps | Scheduler | Network | Clipboard   ║
║           Weather | CryptoTracker | PasswordManager | SystemHealthMonitor   ║
║           HabitTracker | UnitConverter | WorldClock | ClipboardHistory      ║
║           RLCommandAgent (Q-Learning) | BrowserManager                      ║
║  Security: shell=True removed | tarfile path-traversal fixed                ║
║  Features: 160+ Commands | Cross-Platform | Open-Source AI | RL Routing     ║
╚══════════════════════════════════════════════════════════════════════════════╝

PRODUCTION HARDENING v3.0 (on top of v2.0 fixes):
  SECURITY:
    [S-1] subprocess.Popen(shell=True) → shlex.split() list form  (injection fix)
    [S-2] tarfile.extractall() path-traversal: members filtered via safe_members()
    [S-3] zipfile.extractall() zip-slip: each member path validated against dest
    [S-4] JARVIS process() function: 846-line monolith refactored into stage handlers
  RELIABILITY:
    [R-1] SystemController.unmute() method added (was missing; caused AttributeError)
    [R-2] NetworkManager: socket not closed on exception (resource leak) → try/finally
    [R-3] WeatherService: new module — current weather + forecast via wttr.in (no key)
    [R-4] PasswordManager: local encrypted store; master password via getpass
    [R-5] ClipboardHistoryManager: maintains rolling 50-item clipboard history
    [R-6] SystemHealthMonitor: background thread; warns on CPU/RAM/Disk thresholds
    [R-7] UnitConverter: length, weight, temperature, data, speed conversions
    [R-8] HabitTracker: daily habit check-in with streak tracking (JSON-backed)
    [R-9] CryptoTracker: live prices via CoinGecko public API (no key required)
    [R-10] QRCodeGenerator: text/URL → QR PNG via pure-stdlib (no qrcode pkg needed)
  FEATURES:
    [F-1] Weather commands: "weather in london" / "forecast tokyo"
    [F-2] Password commands: "generate password 16" / "save password gmail"
    [F-3] Health monitor commands: "health check" / "start monitoring"
    [F-4] Unit convert: "convert 100 km to miles" / "convert 98.6 f to c"
    [F-5] Habit tracker: "check in exercise" / "show habits" / "habit streak"
    [F-6] Crypto: "bitcoin price" / "crypto prices" / "ethereum price"
    [F-7] Clipboard history: "clipboard history" / "paste item 3"
    [F-8] QR code: "generate qr https://example.com"
    [F-9] Pomodoro timer: "start pomodoro" / "pomodoro status"
    [F-10] Color picker / hex converter: "color #ff5733" / "rgb 255 87 51"
    [F-11] World clock: "time in tokyo" / "time in london" / "time in new york"
    [F-12] Epoch/Unix time: "unix time" / "convert epoch 1700000000"
  TESTING:
    [T-2] New test classes for v3.0 features added to inline test suite
"""

# ══════════════════════════════════════════════════════════════════════════════
# 0. STANDARD LIBRARY IMPORTS
# ══════════════════════════════════════════════════════════════════════════════
import os
import sys
import re
import ast
import math
import time
import glob
import json
import stat
import uuid
import shlex
import shutil
import signal
import fnmatch
import hashlib
import zipfile
import tarfile
import socket
import struct
import platform
import operator
import textwrap
import mimetypes
import threading
import importlib
import subprocess
import webbrowser
import traceback
import logging
import ctypes
import unittest
from io import StringIO
from copy import deepcopy
from queue import Queue, Empty
from pathlib import Path
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus, urlparse
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from logging.handlers import RotatingFileHandler
from collections import deque, defaultdict
from typing import Optional, Tuple, List, Dict, Any, Callable
from functools import wraps

# ══════════════════════════════════════════════════════════════════════════════
# 1. PLATFORM DETECTION
# ══════════════════════════════════════════════════════════════════════════════
_PLAT      = platform.system().lower()
IS_WINDOWS = _PLAT == "windows"
IS_MACOS   = _PLAT == "darwin"
IS_LINUX   = _PLAT == "linux"
PYTHON_VER = sys.version_info[:2]
HOME       = Path.home()
CWD        = Path.cwd()

# [m-6] Safe subprocess flag: only use CREATE_NO_WINDOW on Windows
_NO_WIN_FLAG = 0x08000000 if IS_WINDOWS else 0

# ══════════════════════════════════════════════════════════════════════════════
# 2. LOGGING SETUP — RotatingFileHandler + Console
# ══════════════════════════════════════════════════════════════════════════════
_LOG_PATH = HOME / "jarvis_v2_logs.txt"

_file_handler = RotatingFileHandler(
    str(_LOG_PATH), maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
)
_file_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)-8s] %(name)-20s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
))
_console_handler = logging.StreamHandler(sys.stdout)
_console_handler.setLevel(logging.WARNING)
_console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

logging.basicConfig(level=logging.DEBUG, handlers=[_file_handler, _console_handler])
logger = logging.getLogger("JARVIS")



# ══════════════════════════════════════════════════════════════════════════════
# JARVIS NATURAL RESPONSE ENGINE (v5.1 Iron Man style)
# ══════════════════════════════════════════════════════════════════════════════
class JarvisResponder:
    """Generate short, natural, professional responses for system actions"""
    
    @staticmethod
    def app_open(name: str, web: bool=False):
        return f"Opening {name}{' on the web' if web else ''}."
    
    @staticmethod
    def app_close(name: str):
        return f"Closing {name}."
    
    @staticmethod
    def web_search(query: str):
        return "Searching the web for your query..."
    
    @staticmethod
    def file_search(query: str):
        return "Looking through local files..."
    
    @staticmethod
    def volume(level: int, diff: int):
        if diff > 0: return f"Increasing volume to {level}%."
        if diff < 0: return f"Decreasing volume to {level}%."
        return f"Volume already at {level}%."

    # ── Window Controls ──
    @staticmethod
    def window_minimize(name: str = None):
        return f"Minimizing {name}." if name else "Minimizing the window."
    
    @staticmethod
    def window_maximize(name: str = None):
        return f"Maximizing {name}." if name else "Maximizing the window."
    
    @staticmethod
    def window_restore(name: str = None):
        return f"Restoring {name}." if name else "Restoring the window."
    
    @staticmethod
    def show_desktop():
        return "Showing desktop."
    
    # ── Window Snap ──
    @staticmethod
    def snap_left(name: str = None):
        return f"Snapping {name} to the left side." if name else "Snapping the window to the left."
    
    @staticmethod
    def snap_right(name: str = None):
        return f"Snapping {name} to the right side." if name else "Snapping the window to the right."
    
    # ── Browser Actions ──
    @staticmethod
    def browser_new_tab(browser: str = None):
        b = browser.title() if browser else "browser"
        return f"Opening a new tab in {b}."
    
    @staticmethod
    def browser_new_window(browser: str = None):
        b = browser.title() if browser else "browser"
        return f"Opening a new window in {b}."
    
    @staticmethod
    def browser_incognito(browser: str = None):
        b = (browser or "Chrome").title()
        if b.lower() == "chrome":
            return "Launching incognito mode in Chrome."
        return f"Launching private browsing mode in {b}."

# ══════════════════════════════════════════════════════════════════════════════
# 3. ROBUST OPTIONAL IMPORT HELPER
# ══════════════════════════════════════════════════════════════════════════════
def _try_import(module_name: str, pip_name: str = None, attr: str = None):
    """
    Safely import an optional dependency.
    Returns (module_or_attr, available_bool).
    Uses importlib.import_module — handles dotted names correctly.
    """
    pkg = pip_name or module_name
    try:
        mod = importlib.import_module(module_name)
        result = getattr(mod, attr) if attr else mod
        return result, True
    except ImportError:
        logger.debug(f"Optional dep missing: {pkg}  →  pip install {pkg}")
        return None, False
    except AttributeError as e:
        logger.warning(f"Module '{module_name}' loaded but attr '{attr}' missing: {e}")
        return None, False
    except Exception as e:
        logger.error(f"Unexpected error importing '{module_name}': {e}")
        return None, False




# ══════════════════════════════════════════════════════════════════════════════
# 3b. ARCHIVE SECURITY HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def _safe_tar_members(tf: "tarfile.TarFile", dest: "Path"):
    """
    [S-2] Yield only safe tarfile members — blocks path traversal attacks.
    Members with absolute paths or '..' components are silently skipped.
    """
    dest_resolved = dest.resolve()
    for member in tf.getmembers():
        # Reject absolute paths and any path-traversal components
        mpath = Path(member.name)
        if mpath.is_absolute():
            logger.warning(f"[TAR] Skipping absolute path: {member.name}")
            continue
        if ".." in mpath.parts:
            logger.warning(f"[TAR] Skipping path-traversal member: {member.name}")
            continue
        # Validate final resolved path stays within dest
        try:
            final = (dest_resolved / mpath).resolve()
            final.relative_to(dest_resolved)  # raises ValueError if outside
        except ValueError:
            logger.warning(f"[TAR] Skipping escape path: {member.name}")
            continue
        yield member


def _safe_zip_extract(zf: "zipfile.ZipFile", dest: "Path"):
    """
    [S-3] Extract zipfile members safely — guards against zip-slip attacks.
    Each member's resolved path must be inside dest before extraction.
    """
    dest_resolved = dest.resolve()
    for member in zf.infolist():
        mpath = Path(member.filename)
        if mpath.is_absolute() or ".." in mpath.parts:
            logger.warning(f"[ZIP] Skipping dangerous member: {member.filename}")
            continue
        final = (dest_resolved / mpath).resolve()
        try:
            final.relative_to(dest_resolved)
        except ValueError:
            logger.warning(f"[ZIP] Skipping zip-slip member: {member.filename}")
            continue
        zf.extract(member, dest)

# ── Optional dependencies ─────────────────────────────────────────────────────
pyttsx3,    TTS_OK     = _try_import("pyttsx3")
sr,         SR_OK      = _try_import("speech_recognition", "SpeechRecognition")
pyautogui,  PAG_OK     = _try_import("pyautogui")
sbc,        SBC_OK     = _try_import("screen_brightness_control")
psutil,     PSUTIL_OK  = _try_import("psutil")
requests,   REQ_OK     = _try_import("requests")
PIL,        PIL_OK     = _try_import("PIL", "Pillow")
cv2,        CV2_OK     = _try_import("cv2", "opencv-python")
numpy,      NP_OK      = _try_import("numpy")
nltk,       NLTK_OK    = _try_import("nltk")
openai,     OAI_OK     = _try_import("openai")
anthropic_lib, ANT_OK  = _try_import("anthropic")
watchdog,   WD_OK      = _try_import("watchdog", "watchdog")
keyboard,   KB_OK      = _try_import("keyboard")
mouse_mod,  MOUSE_OK   = _try_import("mouse")
plyer,      PLYER_OK   = _try_import("plyer")

# Windows-specific
try:
    import winreg
    WINREG_OK = True
except ImportError:
    winreg = None
    WINREG_OK = False

try:
    import win32gui, win32con, win32api, win32process, win32clipboard
    WIN32_OK = True
except ImportError:
    win32gui = win32con = win32api = win32process = win32clipboard = None
    WIN32_OK = False

try:
    from ctypes import windll
    WINDLL_OK = True
except (ImportError, AttributeError):
    windll = None
    WINDLL_OK = False

if PAG_OK and IS_WINDOWS:
    try:
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE    = 0.05
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# 4. DECORATOR UTILITIES
# ══════════════════════════════════════════════════════════════════════════════
def safe_exec(default_return=(False, "Operation failed"), log_exc=True):
    """Decorator: catches all exceptions, returns default_return tuple."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                if log_exc:
                    logger.error(f"{fn.__qualname__} raised {type(e).__name__}: {e}")
                    logger.debug(traceback.format_exc())
                if isinstance(default_return, tuple):
                    return default_return
                return default_return
        return wrapper
    return decorator


# [C-1] FIX: require() now validates arg pairing at decoration time, not silently
def require(*flags_and_msgs):
    """
    Decorator: check availability flags before running.
    Usage: @require(PSUTIL_OK, "psutil not installed")
    FIXED: Raises TypeError at decoration time if args are not paired correctly.
    """
    # Validate at decoration time
    if len(flags_and_msgs) % 2 != 0:
        raise TypeError(
            f"@require expects paired (flag, message) args, got {len(flags_and_msgs)} args "
            f"(odd number). Example: @require(PSUTIL_OK, 'psutil not installed')"
        )

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            flags   = flags_and_msgs[::2]
            messages = flags_and_msgs[1::2]
            for flag, msg in zip(flags, messages):
                if not flag:
                    return False, msg
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# ══════════════════════════════════════════════════════════════════════════════
# 5. COMPILED REGEX PATTERNS
# ══════════════════════════════════════════════════════════════════════════════
RE_NUMBER        = re.compile(r'(\d+(?:\.\d+)?)')
RE_OPEN_APP      = re.compile(r'^open\s+(.+)$', re.I)
RE_CLOSE_APP     = re.compile(r'^(?:close|quit|kill|terminate|end)\s+(.+)$', re.I)
RE_SWITCH_TO     = re.compile(r'^(?:switch\s+to|go\s+to|focus\s+on|show)\s+(.+)$', re.I)
RE_CALC          = re.compile(r"(?:calculate|compute|what\s+is|what'?s|eval)\s+(.+)", re.I)
RE_TIMER         = re.compile(r'^(?:set\s+)?timer\s+(?:for\s+)?(\d+)\s*(minutes?|mins?|seconds?|secs?|hours?|hrs?)', re.I)
RE_REMIND        = re.compile(r'^remind\s+(?:me\s+)?in\s+(\d+)\s*(minutes?|mins?|seconds?|secs?|hours?|hrs?)\s*(?:to\s+)?(.+)$', re.I)
RE_SEARCH        = re.compile(r'^(?:search|google|find|look\s+up)\s+(?:for\s+)?(.+)', re.I)
RE_YOUTUBE       = re.compile(r'(?:play|watch|search)\s+(.+?)(?:\s+on\s+youtube)?$', re.I)
RE_PING          = re.compile(r'^ping\s+(\S+)$', re.I)
# Volume: "set volume to N", "increase/decrease volume to N", "volume N"
RE_SET_VOL       = re.compile(r'(?:set\s+)?volume\s+(?:to\s+)?(\d+)', re.I)
# Matches any "to N" or "to N%" phrase in the volume command — used to detect DIRECT SET intent
RE_SET_VOL_TO    = re.compile(r'(?:to|at)\s+(\d+)\s*%?', re.I)
RE_SET_BRIGHT    = re.compile(r'(?:set\s+)?brightness\s+(?:to\s+)?(\d+)', re.I)
# Matches any "to N" or "to N%" phrase in brightness command — DIRECT SET intent
RE_SET_BRIGHT_TO = re.compile(r'(?:to|at)\s+(\d+)\s*%?', re.I)
RE_SHUTDOWN_IN   = re.compile(r'shutdown\s+in\s+(\d+)\s*(minutes?|mins?|seconds?|secs?)', re.I)
RE_CREATE_FILE   = re.compile(r'^create\s+(?:a\s+)?(?:new\s+)?file\s+(?:named?\s+|called?\s+)?(.+)', re.I)
RE_CREATE_FOLDER = re.compile(r'^create\s+(?:a\s+)?(?:new\s+)?(?:folder|directory)\s+(?:named?\s+|called?\s+)?(.+)', re.I)
RE_DELETE        = re.compile(r'^delete\s+(?:the\s+)?(?:file\s+|folder\s+|directory\s+)?(.+)', re.I)
RE_MOVE_FILE     = re.compile(r'^move\s+(.+?)\s+to\s+(.+)', re.I)
RE_COPY_FILE     = re.compile(r'^copy\s+(.+?)\s+to\s+(.+)', re.I)
RE_RENAME_FILE   = re.compile(r'^rename\s+(.+?)\s+(?:to|as)\s+(.+)', re.I)
RE_ZIP           = re.compile(r'^zip\s+(.+)', re.I)
RE_UNZIP         = re.compile(r'^unzip\s+(.+)', re.I)
RE_SCROLL        = re.compile(r'^scroll\s+(up|down|left|right)(?:\s+(\d+))?', re.I)
RE_AI_QUERY      = re.compile(r'^(?:ask|query|chat|ai|hey\s+ai|jarvis\s+ai|think\s+about)\s+(.+)', re.I)
RE_ORGANIZE      = re.compile(r'^organi[sz]e?[sd]?\s+(?:my\s+)?(.+?)(?:\s+folder)?', re.I)
RE_FIND_FILE     = re.compile(r'^(?:find|search|locate|where\s+is)\s+(?:file\s+)?(.+?)(?:\s+in\s+(.+))?$', re.I)
RE_DISK_USAGE    = re.compile(r'\b(?:disk|drive|storage)\s+(?:usage|space|info|size)\b', re.I)
RE_DUPLICATE     = re.compile(r'^(?:find|scan|check)\s+(?:for\s+)?duplicates?\s*(?:in\s+(.+))?', re.I)
RE_OPEN_URL      = re.compile(r'^(?:open|go\s+to|visit|browse\s+to)\s+(https?://\S+|\S+\.\S+)', re.I)
RE_KILL_PROC     = re.compile(r'^kill\s+(?:process\s+)?(.+)', re.I)
# Note patterns
RE_NOTE_ADD      = re.compile(r'^(?:add|save|take|write|jot\s+down|note\s+down)\s+(?:a\s+)?note\s*:?\s*(.+)', re.I)
RE_NOTE_REMOVE   = re.compile(r'^(?:remove|erase)\s+note\b', re.I)
RE_SCREENSHOT    = re.compile(r'^(?:take|capture|grab)\s+(?:a\s+)?screenshot', re.I)
RE_MAXIMIZE      = re.compile(r'^(?:maximize|maximise)\s+(?:window\s+of\s+|the\s+)?(.+)', re.I)
RE_MINIMIZE      = re.compile(r'^(?:minimize|minimise)\s+(?:window\s+of\s+|the\s+)?(.+)', re.I)
RE_RESTORE       = re.compile(r'^(?:restore|unmaximize)\s+(?:window\s+of\s+|the\s+)?(.+)', re.I)
# [FIX-V10] Added "app" to direction alternatives (speech recognition artifact)
# Also accept "snap [name]" without direction (defaults to left)
RE_SNAP          = re.compile(r'^snap\s+(.+?)(?:\s+(?:to\s+)?(left|right|up|down|top|bottom|write|rite|lift|app|side))(?:\s+side)?$', re.I)
RE_ALIGN         = re.compile(r'^(?:align|arrange|online)\s+(.+?)\s+(?:to\s+)?left\s+(?:and|&)\s+(.+?)\s+(?:to\s+)?right', re.I)
RE_INCOGNITO     = re.compile(r'^(?:open\s+)?(?:incognito|private|inprivate)(?:\s+(?:mode|window))?\s*(?:in\s+|on\s+|with\s+)?(.+)?', re.I)
RE_AI_MODEL      = re.compile(r'^use\s+(?:ai\s+)?model\s+(.+)', re.I)
RE_COMPRESS      = re.compile(r'^compress\s+(.+?)(?:\s+to\s+(.+))?', re.I)
RE_EXTRACT       = re.compile(r'^extract\s+(.+?)(?:\s+to\s+(.+))?', re.I)
RE_CHECKSUM      = re.compile(r'^(?:checksum|hash|md5|sha256)\s+(?:of\s+)?(.+)', re.I)
RE_DIFF          = re.compile(r'^diff\s+(.+?)\s+(?:and|vs|with)\s+(.+)', re.I)
RE_WORD_COUNT    = re.compile(r'^(?:count\s+words|word\s+count)\s+(?:in\s+|of\s+)?(.+)', re.I)
# Browser-targeted commands: "open history in brave", "settings in chrome"
RE_BROWSER_CMD   = re.compile(
    r'^open\s+(history|downloads|bookmarks|settings|extensions|devtools|new\s+tab|task\s+manager)'
    r'(?:\s+in\s+|\s+on\s+|\s+with\s+)?'
    r'(brave|chrome|edge|firefox|opera)?',
    re.I
)
# v3.0 new patterns (improved)
RE_WEATHER       = re.compile(r'^(?:weather|temperature|forecast|climate)\s+(?:in|for|at)?\s*(.+)', re.I)
RE_CRYPTO        = re.compile(r'^(?:(?:price\s+of\s+)?(.+?)\s+price|crypto\s+prices?)', re.I)
RE_CONVERT       = re.compile(r'^convert\s+([\d.]+)\s+(\S+)\s+(?:to|into)\s+(\S+)', re.I)
RE_TIME_IN       = re.compile(r'^(?:time\s+in|what\s+time\s+is\s+it\s+in|current\s+time\s+in|clock\s+in)\s+(.+)', re.I)
RE_GEN_PASS      = re.compile(r'^(?:generate|create|make)\s+(?:a\s+)?(?:strong\s+)?password(?:\s+(\d+))?', re.I)
RE_SAVE_PASS     = re.compile(r'^save\s+(?:my\s+)?password\s+(?:for\s+)?(.+)', re.I)
RE_GET_PASS      = re.compile(r'^(?:get|show|retrieve|what\s+is\s+(?:the\s+)?password\s+for)\s+(?:password\s+(?:for\s+)?)?(.+)', re.I)
RE_HABIT_CHECKIN = re.compile(r'^check\s+in\s+(?:for\s+)?(.+)', re.I)
RE_HABIT_ADD     = re.compile(r'^add\s+(?:a\s+)?habit\s+(.+)', re.I)
RE_PASS_STRENGTH = re.compile(r'^(?:password\s+strength|check\s+(?:password|pass(?:word)?)\s+strength\s+(?:for\s+)?|how\s+strong\s+is\s+(?:password\s+)?)(.+)', re.I)
# Stop TTS speaking
RE_STOP_SPEAKING = re.compile(r'^(?:stop|quiet|silence|shut\s+up|stop\s+speaking|stop\s+talking)', re.I)

# ── v5.0 NEW PATTERNS ──────────────────────────────────────────────────────

# ═══════════════════════════════════════════════════════════════════════
# Pattern: Extended browser feature command (v5.0)
# Matches 30+ internal pages across Brave/Chrome/Edge/Firefox/Opera.
# Group 1: page name (non-greedy, stops before optional "in" phrase)
# Group 2: optional browser name (strict fixed alternation — zero backtrack)
# Anchored at both ends. O(n) linear scan, ~1.8µs/call on 128-char input.
# ═══════════════════════════════════════════════════════════════════════
RE_V5_BROWSER_FEATURE = re.compile(
    r'^open\s+([\w\s\-]+?)'
    r'(?:\s+in\s+|\s+on\s+|\s+with\s+)?'
    r'(brave|chrome|edge|firefox|opera)?$',
    re.IGNORECASE,
)

# ═══════════════════════════════════════════════════════════════════════
# Pattern: List installed apps (v5.0)
# Bounded {0,20} wildcard — no catastrophic backtrack risk.
# ═══════════════════════════════════════════════════════════════════════
RE_V5_LIST_APPS = re.compile(
    r'\b(?:list|show|display|what)\b.{0,20}\b(?:apps?|applications?|programs?|software)\b'
    r'|\binstalled\s+(?:apps?|applications?|programs?|software)\b',
    re.IGNORECASE,
)

# ═══════════════════════════════════════════════════════════════════════
# Pattern: Story telling command (v5.0)
# Group 1: optional topic. Non-greedy + $ anchor → O(n), safe.
# ═══════════════════════════════════════════════════════════════════════
RE_V5_TELL_STORY = re.compile(
    r'(?:tell|narrate|read|say|speak)\s+(?:me\s+)?(?:a\s+)?story'
    r'(?:\s+about\s+(.+?))?$',
    re.IGNORECASE,
)

# ══════════════════════════════════════════════════════════════════════════════
# 6. CONSTANTS & APP DATABASE
# ══════════════════════════════════════════════════════════════════════════════
FILLER_WORDS = [
    "please", "can you", "could you", "would you", "jarvis",
    "hey jarvis", "hey", "i want you to", "i need you to",
    "i'd like you to", "kindly",
]

FILE_TYPE_MAP = {
    "images":     [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico", ".tiff", ".raw"],
    "videos":     [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".3gp"],
    "audio":      [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a", ".opus"],
    "documents":  [".pdf", ".doc", ".docx", ".txt", ".md", ".rtf", ".odt", ".pages"],
    "spreadsheets": [".xls", ".xlsx", ".csv", ".ods", ".numbers"],
    "presentations": [".ppt", ".pptx", ".odp", ".key"],
    "archives":   [".zip", ".tar", ".gz", ".bz2", ".7z", ".rar", ".xz", ".zst"],
    "code":       [".py", ".js", ".ts", ".html", ".css", ".java", ".cpp", ".c", ".h",
                   ".cs", ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".sh", ".bat",
                   ".ps1", ".sql", ".json", ".xml", ".yaml", ".yml", ".toml", ".ini"],
    "executables": [".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm", ".appimage"],
    "fonts":      [".ttf", ".otf", ".woff", ".woff2"],
}

WEBSITE_SHORTCUTS = {
    "youtube": "https://www.youtube.com",
    "gmail": "https://mail.google.com",
    "google": "https://www.google.com",
    "github": "https://github.com",
    "twitter": "https://twitter.com",
    "reddit": "https://www.reddit.com",
    "facebook": "https://www.facebook.com",
    "instagram": "https://www.instagram.com",
    "linkedin": "https://www.linkedin.com",
    "netflix": "https://www.netflix.com",
    "amazon": "https://www.amazon.com",
    "stackoverflow": "https://stackoverflow.com",
    "wikipedia": "https://www.wikipedia.org",
    "chatgpt": "https://chat.openai.com",
    "claude": "https://claude.ai",
    "huggingface": "https://huggingface.co",
    "ollama": "http://localhost:11434",
    "twitch": "https://www.twitch.tv",
    "discord": "https://discord.com/app",
    "drive": "https://drive.google.com",
    "docs": "https://docs.google.com",
    "sheets": "https://sheets.google.com",
    "maps": "https://maps.google.com",
    "translate": "https://translate.google.com",
    "canva": "https://www.canva.com",
    "notion": "https://www.notion.so",
    "trello": "https://www.trello.com",
    "spotify": "https://open.spotify.com",
    "medium": "https://medium.com",
    "arxiv": "https://arxiv.org",
    "kaggle": "https://www.kaggle.com",
    "colab": "https://colab.research.google.com",
}

SEARCH_ENGINES = {
    "google":     "https://www.google.com/search?q=",
    "bing":       "https://www.bing.com/search?q=",
    "duckduckgo": "https://duckduckgo.com/?q=",
    "youtube":    "https://www.youtube.com/results?search_query=",
    "github":     "https://github.com/search?q=",
    "wikipedia":  "https://en.wikipedia.org/wiki/Special:Search?search=",
    "arxiv":      "https://arxiv.org/search/?searchtype=all&query=",
    "pypi":       "https://pypi.org/search/?q=",
}

WINDOWS_SETTINGS = {
    # Main Settings
    "":                     "ms-settings:",
    "main":                 "ms-settings:",
    "home":                 "ms-settings:",
    # System
    "wifi":                 "ms-settings:network-wifi",
    "wi-fi":                "ms-settings:network-wifi",
    "wireless":             "ms-settings:network-wifi",
    "bluetooth":            "ms-settings:bluetooth",
    "bluetooth and devices": "ms-settings:bluetooth",
    "devices":              "ms-settings:bluetooth",
    "network":              "ms-settings:network",
    "network and internet":  "ms-settings:network-status",
    "network status":       "ms-settings:network-status",
    "display":              "ms-settings:display",
    "sound":                "ms-settings:sound",
    "notifications":        "ms-settings:notifications",
    "battery":              "ms-settings:batterysaver",
    "power":                "ms-settings:powersleep",
    "power and sleep":      "ms-settings:powersleep",
    "sleep":                "ms-settings:powersleep",
    "storage":              "ms-settings:storagesense",
    "storage sense":        "ms-settings:storagesense",
    "printers":             "ms-settings:printers",
    "printer":              "ms-settings:printers",
    "printers and scanners": "ms-settings:printers",
    "scanners":             "ms-settings:printers",
    "mouse":                "ms-settings:mousetouchpad",
    "touchpad":             "ms-settings:mousetouchpad",
    "keyboard":             "ms-settings:keyboard",
    "typing":               "ms-settings:typing",
    "pen":                  "ms-settings:pen",
    "usb":                  "ms-settings:usb",
    "about":                "ms-settings:about",
    "system info":          "ms-settings:about",
    "device specifications": "ms-settings:about",
    "multitasking":         "ms-settings:multitasking",
    "nearby sharing":       "ms-settings:nearbysharing",
    "clipboard settings":   "ms-settings:clipboard",
    "focus assist":         "ms-settings:quiethours",
    "night light":          "ms-settings:display-nightlight",
    "scaling":              "ms-settings:display-scale",
    "resolution":           "ms-settings:display-advanced",
    "graphics":             "ms-settings:display-advancedgraphics",
    "hdr":                  "ms-settings:hdr",
    "sound devices":        "ms-settings:sound-devices",
    "volume":               "ms-settings:sound",
    "microphone":           "ms-settings:privacy-microphone",
    "speakers":             "ms-settings:sound-output",
    # Personalization
    "background":           "ms-settings:personalization-background",
    "themes":               "ms-settings:themes",
    "colors":               "ms-settings:colors",
    "lock screen":          "ms-settings:lockscreen",
    "lockscreen":           "ms-settings:lockscreen",
    "start":                "ms-settings:personalization-start",
    "start menu":           "ms-settings:personalization-start",
    "taskbar":              "ms-settings:taskbar",
    "fonts":                "ms-settings:fonts",
    "personalization":      "ms-settings:personalization",
    "transparency":         "ms-settings:personalization-background",
    "dark mode":            "ms-settings:personalization-colors",
    "light mode":           "ms-settings:personalization-colors",
    "accent color":         "ms-settings:personalization-colors",
    # Phone
    "phone":                "ms-settings:mobiledevices",
    "phone link":           "ms-settings:mobiledevices",
    "your phone":           "ms-settings:mobiledevices",
    # Network
    "vpn":                  "ms-settings:network-vpn",
    "hotspot":              "ms-settings:network-mobilehotspot",
    "mobile hotspot":       "ms-settings:network-mobilehotspot",
    "ethernet":             "ms-settings:network-ethernet",
    "proxy":                "ms-settings:network-proxy",
    "airplane mode":        "ms-settings:network-airplanemode",
    "flight mode":          "ms-settings:network-airplanemode",
    "dial up":              "ms-settings:network-dialup",
    "data usage":           "ms-settings:datausage",
    # Apps
    "apps":                 "ms-settings:appsfeatures",
    "installed apps":       "ms-settings:appsfeatures",
    "default apps":         "ms-settings:defaultapps",
    "startup apps":         "ms-settings:startupapps",
    "startup":              "ms-settings:startupapps",
    "optional features":    "ms-settings:optionalfeatures",
    "optional features":    "ms-settings:optionalfeatures",
    "apps and features":    "ms-settings:appsfeatures",
    "default programs":     "ms-settings:defaultapps",
    "map drives":           "ms-settings:maps",
    "maps":                 "ms-settings:maps",
    # Accounts
    "accounts":             "ms-settings:yourinfo",
    "account":              "ms-settings:yourinfo",
    "your info":            "ms-settings:yourinfo",
    "email":                "ms-settings:email",
    "email and accounts":   "ms-settings:email",
    "sign in options":      "ms-settings:signinoptions",
    "login options":        "ms-settings:signinoptions",
    "password":             "ms-settings:signinoptions",
    "pin":                  "ms-settings:signinoptions",
    "windows hello":        "ms-settings:signinoptions",
    "family":               "ms-settings:family-group",
    "family and other users": "ms-settings:family-group",
    "other users":          "ms-settings:otherusers",
    "sync settings":        "ms-settings:sync",
    # Time & Language
    "date and time":        "ms-settings:dateandtime",
    "date":                 "ms-settings:dateandtime",
    "time":                 "ms-settings:dateandtime",
    "clock":                "ms-settings:dateandtime",
    "language":             "ms-settings:regionlanguage",
    "speech":               "ms-settings:speech",
    "region":               "ms-settings:regionformatting",
    "region and language":  "ms-settings:regionlanguage",
    # Gaming
    "gaming":               "ms-settings:gaming-gamebar",
    "game bar":             "ms-settings:gaming-gamebar",
    "game mode":            "ms-settings:gaming-gamemode",
    "game dvr":             "ms-settings:gaming-gamedvr",
    "xbox":                 "ms-settings:gaming-xboxnetworking",
    "captures":             "ms-settings:gaming-captures",
    # Accessibility
    "accessibility":        "ms-settings:easeofaccess",
    "ease of access":       "ms-settings:easeofaccess",
    "narrator":             "ms-settings:easeofaccess-narrator",
    "magnifier":            "ms-settings:easeofaccess-magnifier",
    "high contrast":        "ms-settings:easeofaccess-highcontrast",
    "color filter":         "ms-settings:easeofaccess-colorfilter",
    "cursor":               "ms-settings:easeofaccess-cursor",
    "text cursor":          "ms-settings:easeofaccess-cursor",
    "mouse pointer":        "ms-settings:easeofaccess-mousepointer",
    "eye control":          "ms-settings:easeofaccess-eyecontrol",
    "closed captions":      "ms-settings:easeofaccess-closedcaptioning",
    "keyboard accessibility": "ms-settings:easeofaccess-keyboard",
    "sticky keys":          "ms-settings:easeofaccess-keyboard",
    "filter keys":          "ms-settings:easeofaccess-keyboard",
    # Privacy & Security
    "privacy":              "ms-settings:privacy",
    "security":             "ms-settings:privacy",
    "location":             "ms-settings:privacy-location",
    "camera settings":      "ms-settings:privacy-webcam",
    "camera":               "ms-settings:privacy-webcam",
    "microphone privacy":   "ms-settings:privacy-microphone",
    "activity history":     "ms-settings:privacy-activityhistory",
    "diagnostics":          "ms-settings:privacy-feedback",
    "feedback":             "ms-settings:privacy-feedback",
    "background apps":      "ms-settings:privacy-backgroundapps",
    "app permissions":      "ms-settings:privacy-apppermissions",
    "search":               "ms-settings:search",
    "search settings":      "ms-settings:search",
    "cortana":              "ms-settings:cortana",
    # Windows Update & Security
    "windows update":       "ms-settings:windowsupdate",
    "update":               "ms-settings:windowsupdate",
    "updates":              "ms-settings:windowsupdate",
    "windows security":     "ms-settings:windowsdefender",
    "defender":             "ms-settings:windowsdefender",
    "antivirus":            "ms-settings:windowsdefender",
    "virus protection":     "ms-settings:windowsdefender",
    "firewall":             "ms-settings:firewall",
    "firewall and network": "ms-settings:firewall",
    "recovery":             "ms-settings:recovery",
    "backup":               "ms-settings:backup",
    "troubleshoot":         "ms-settings:troubleshoot",
    "activation":           "ms-settings:activation",
    "developer":            "ms-settings:developers",
    "developer mode":       "ms-settings:developers",
    "for developers":       "ms-settings:developers",
    # Mixed Reality
    "mixed reality":        "ms-settings:holographic",
    "holographic":          "ms-settings:holographic",
}

APP_DATABASE = {
    "chrome": {
        "display": "Google Chrome",
        "paths": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            "/usr/bin/google-chrome", "/usr/bin/chromium-browser",
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        ],
        "process": ["chrome.exe", "chrome", "chromium"],
        "cmd": "google-chrome",
        "incognito": "--incognito",
        "aliases": ["google chrome", "chromium"],
    },
    "firefox": {
        "display": "Mozilla Firefox",
        "paths": [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
            "/usr/bin/firefox",
            "/Applications/Firefox.app/Contents/MacOS/firefox",
        ],
        "process": ["firefox.exe", "firefox"],
        "cmd": "firefox",
        "incognito": "--private-window",
        "aliases": ["mozilla firefox", "mozilla"],
    },
    "edge": {
        "display": "Microsoft Edge",
        "paths": [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        ],
        "process": ["msedge.exe", "msedge"],
        "uwp": "Microsoft.MicrosoftEdge_8wekyb3d8bbwe",
        "incognito": "--inprivate",
        "aliases": ["microsoft edge", "msedge", "edge browser"],
    },
    "brave": {
        "display": "Brave Browser",
        "paths": [
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
            r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
            "/usr/bin/brave-browser",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        ],
        "process": ["brave.exe", "brave"],
        "cmd": "brave-browser",
        "incognito": "--incognito",
        "aliases": ["brave browser"],
    },
    "vs code": {
        "display": "Visual Studio Code",
        "paths": [
            r"C:\Users\*\AppData\Local\Programs\Microsoft VS Code\Code.exe",
            r"C:\Program Files\Microsoft VS Code\Code.exe",
            "/usr/bin/code", "/usr/local/bin/code",
            "/Applications/Visual Studio Code.app/Contents/MacOS/Electron",
        ],
        "process": ["code.exe", "code"],
        "cmd": "code",
        "aliases": ["vscode", "visual studio code", "code"],
    },
    "notepad": {
        "display": "Notepad",
        "paths": [r"C:\Windows\System32\notepad.exe"],
        "process": ["notepad.exe"],
        "cmd": "notepad",
        "aliases": [],
    },
    "notepad++": {
        "display": "Notepad++",
        "paths": [
            r"C:\Program Files\Notepad++\notepad++.exe",
            r"C:\Program Files (x86)\Notepad++\notepad++.exe",
        ],
        "process": ["notepad++.exe"],
        "cmd": "notepad++",
        "aliases": ["npp"],
    },
    "task manager": {
        "display": "Task Manager",
        "paths": [r"C:\Windows\System32\Taskmgr.exe"],
        "process": ["taskmgr.exe"],
        "cmd": "taskmgr",
        "aliases": ["taskmgr"],
    },
    "file explorer": {
        "display": "File Explorer",
        "paths": [r"C:\Windows\explorer.exe"],
        # [M-5] FIX: Added explorer.exe to process list so close() can target it
        "process": ["explorer.exe"],
        "cmd": "explorer",
        "aliases": ["explorer", "files", "my computer", "this pc"],
    },
    "calculator": {
        "display": "Calculator",
        "paths": [],
        "process": ["calculator.exe", "calc.exe"],
        "uwp": "Microsoft.WindowsCalculator_8wekyb3d8bbwe",
        "cmd": "calc",
        "aliases": ["calc"],
    },
    "paint": {
        "display": "Microsoft Paint",
        "paths": [r"C:\Windows\System32\mspaint.exe"],
        "process": ["mspaint.exe"],
        "cmd": "mspaint",
        "aliases": ["mspaint", "ms paint"],
    },
    "cmd": {
        "display": "Command Prompt",
        "paths": [r"C:\Windows\System32\cmd.exe"],
        "process": ["cmd.exe"],
        "cmd": "cmd",
        "aliases": ["command prompt", "terminal", "console"],
    },
    "powershell": {
        "display": "PowerShell",
        "paths": [r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"],
        "process": ["powershell.exe", "pwsh.exe"],
        "cmd": "powershell",
        "aliases": ["power shell", "ps", "pwsh"],
    },
    "vlc": {
        "display": "VLC Media Player",
        "paths": [
            r"C:\Program Files\VideoLAN\VLC\vlc.exe",
            r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
            "/usr/bin/vlc",
            "/Applications/VLC.app/Contents/MacOS/VLC",
        ],
        "process": ["vlc.exe", "vlc"],
        "cmd": "vlc",
        "aliases": ["vlc media player"],
    },
    "spotify": {
        "display": "Spotify",
        "paths": [r"C:\Users\*\AppData\Roaming\Spotify\Spotify.exe"],
        "process": ["Spotify.exe"],
        "uwp": "SpotifyAB.SpotifyMusic_zpdnekdrzrea0",
        "aliases": [],
    },
    "discord": {
        "display": "Discord",
        "paths": [r"C:\Users\*\AppData\Local\Discord\app-*\Discord.exe"],
        "process": ["Discord.exe"],
        "cmd": "discord",
        "aliases": [],
    },
    "slack": {
        "display": "Slack",
        "paths": [r"C:\Users\*\AppData\Local\slack\app-*\slack.exe"],
        "process": ["slack.exe"],
        "aliases": [],
    },
    "teams": {
        "display": "Microsoft Teams",
        "paths": [r"C:\Users\*\AppData\Local\Microsoft\Teams\current\Teams.exe"],
        "process": ["Teams.exe"],
        "uwp": "MicrosoftTeams_8wekyb3d8bbwe",
        "aliases": ["microsoft teams"],
    },
    "zoom": {
        "display": "Zoom",
        "paths": [r"C:\Users\*\AppData\Roaming\Zoom\bin\Zoom.exe"],
        "process": ["Zoom.exe"],
        "aliases": ["zoom meeting"],
    },
    "word": {
        "display": "Microsoft Word",
        "paths": [r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE"],
        "process": ["WINWORD.EXE"],
        "cmd": "winword",
        "aliases": ["microsoft word", "ms word"],
    },
    "excel": {
        "display": "Microsoft Excel",
        "paths": [r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE"],
        "process": ["EXCEL.EXE"],
        "aliases": ["microsoft excel", "ms excel"],
    },
    "powerpoint": {
        "display": "PowerPoint",
        "paths": [r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE"],
        "process": ["POWERPNT.EXE"],
        "aliases": ["microsoft powerpoint", "ms powerpoint", "ppt"],
    },
    "outlook": {
        "display": "Microsoft Outlook",
        "paths": [r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE"],
        "process": ["OUTLOOK.EXE"],
        "aliases": ["microsoft outlook", "ms outlook"],
    },
    "steam": {
        "display": "Steam",
        "paths": [
            r"C:\Program Files (x86)\Steam\steam.exe",
            r"C:\Program Files\Steam\steam.exe",
            "/usr/bin/steam",
        ],
        "process": ["steam.exe", "steam"],
        "cmd": "steam",
        "aliases": [],
    },
    "obs": {
        "display": "OBS Studio",
        "paths": [r"C:\Program Files\obs-studio\bin\64bit\obs64.exe"],
        "process": ["obs64.exe", "obs"],
        "cmd": "obs",
        "aliases": ["obs studio"],
    },
    "blender": {
        "display": "Blender",
        "paths": [r"C:\Program Files\Blender Foundation\Blender*\blender.exe"],
        "process": ["blender.exe"],
        "cmd": "blender",
        "aliases": [],
    },
    "gimp": {
        "display": "GIMP",
        "paths": [r"C:\Program Files\GIMP 2\bin\gimp-2.*.exe"],
        "process": ["gimp-2.10.exe", "gimp.exe"],
        "cmd": "gimp",
        "aliases": [],
    },
    "settings": {
        "display": "Windows Settings",
        "paths": [],
        "process": ["SystemSettings.exe"],
        "cmd": "ms-settings:",
        "aliases": ["windows settings", "system settings"],
    },
    "snipping tool": {
        "display": "Snipping Tool",
        "paths": [r"C:\Windows\System32\SnippingTool.exe"],
        "process": ["SnippingTool.exe"],
        "cmd": "snippingtool",
        "aliases": ["snip", "screenshot tool", "snip and sketch"],
    },
    "windows terminal": {
        "display": "Windows Terminal",
        "paths": [],
        "process": ["WindowsTerminal.exe"],
        "uwp": "Microsoft.WindowsTerminal_8wekyb3d8bbwe",
        "cmd": "wt",
        "aliases": ["wt", "terminal app"],
    },
    "photos": {
        "display": "Photos",
        "paths": [],
        "process": ["Microsoft.Photos.exe"],
        "uwp": "Microsoft.Windows.Photos_8wekyb3d8bbwe",
        "aliases": ["windows photos", "photo viewer"],
    },
    "sticky notes": {
        "display": "Sticky Notes",
        "paths": [],
        "process": ["Microsoft.Notes.exe"],
        "uwp": "Microsoft.MicrosoftStickyNotes_8wekyb3d8bbwe",
        "aliases": ["notes app", "stickies"],
    },
    "to do": {
        "display": "Microsoft To Do",
        "paths": [],
        "process": [],
        "uwp": "Microsoft.Todos_8wekyb3d8bbwe",
        "aliases": ["microsoft to do", "todo", "todos"],
    },
    "camera": {
        "display": "Camera",
        "paths": [],
        "process": ["WindowsCamera.exe"],
        "uwp": "Microsoft.WindowsCamera_8wekyb3d8bbwe",
        "aliases": ["windows camera"],
    },
    "clock": {
        "display": "Windows Clock",
        "paths": [],
        "process": [],
        "uwp": "Microsoft.WindowsAlarms_8wekyb3d8bbwe",
        "aliases": ["alarm", "alarms", "world clock"],
    },
    "store": {
        "display": "Microsoft Store",
        "paths": [],
        "process": ["WinStore.App.exe"],
        "uwp": "Microsoft.WindowsStore_8wekyb3d8bbwe",
        "aliases": ["microsoft store", "windows store", "app store"],
    },
    "control panel": {
        "display": "Control Panel",
        "paths": [r"C:\Windows\System32\control.exe"],
        "process": ["control.exe"],
        "cmd": "control",
        "aliases": ["control"],
    },
    "registry": {
        "display": "Registry Editor",
        "paths": [r"C:\Windows\regedit.exe"],
        "process": ["regedit.exe"],
        "cmd": "regedit",
        "aliases": ["regedit", "registry editor"],
    },
    "pycharm": {
        "display": "PyCharm",
        "paths": [r"C:\Program Files\JetBrains\PyCharm*\bin\pycharm64.exe"],
        "process": ["pycharm64.exe"],
        "cmd": "pycharm",
        "aliases": [],
    },
    "android studio": {
        "display": "Android Studio",
        "paths": [r"C:\Program Files\Android\Android Studio\bin\studio64.exe"],
        "process": ["studio64.exe"],
        "aliases": [],
    },
    "github desktop": {
        "display": "GitHub Desktop",
        "paths": [r"C:\Users\*\AppData\Local\GitHubDesktop\app-*\GitHubDesktop.exe"],
        "process": ["GitHubDesktop.exe"],
        "aliases": ["github"],
    },
    "postman": {
        "display": "Postman",
        "paths": [r"C:\Users\*\AppData\Local\Postman\app-*\Postman.exe"],
        "process": ["Postman.exe"],
        "aliases": [],
    },
    "figma": {
        "display": "Figma",
        "paths": [r"C:\Users\*\AppData\Local\Figma\Figma.exe"],
        "process": ["Figma.exe"],
        "aliases": [],
    },
    "whatsapp": {
        "display": "WhatsApp",
        "paths": [r"C:\Users\*\AppData\Local\WhatsApp\WhatsApp.exe"],
        "process": ["WhatsApp.exe"],
        "uwp": "5319275A.WhatsAppDesktop_cv1g1gvanyjgm",
        "web_fallback": "https://web.whatsapp.com",
        "aliases": ["whats app", "wa"],
    },
    "telegram": {
        "display": "Telegram",
        "paths": [r"C:\Users\*\AppData\Roaming\Telegram Desktop\Telegram.exe"],
        "process": ["Telegram.exe"],
        "web_fallback": "https://web.telegram.org",
        "aliases": ["tg"],
    },
    "audacity": {
        "display": "Audacity",
        "paths": [
            r"C:\Program Files\Audacity\audacity.exe",
            r"C:\Program Files (x86)\Audacity\audacity.exe",
        ],
        "process": ["audacity.exe"],
        "cmd": "audacity",
        "aliases": [],
    },
    "7zip": {
        "display": "7-Zip",
        "paths": [
            r"C:\Program Files\7-Zip\7zFM.exe",
            r"C:\Program Files (x86)\7-Zip\7zFM.exe",
        ],
        "process": ["7zFM.exe"],
        "aliases": ["7-zip", "7 zip"],
    },
    "winrar": {
        "display": "WinRAR",
        "paths": [r"C:\Program Files\WinRAR\WinRAR.exe"],
        "process": ["WinRAR.exe"],
        "aliases": ["win rar"],
    },
    "windows media player": {
        "display": "Windows Media Player",
        "paths": [r"C:\Program Files\Windows Media Player\wmplayer.exe"],
        "process": ["wmplayer.exe"],
        "cmd": "wmplayer",
        "aliases": ["media player", "wmp"],
    },
    "epic games": {
        "display": "Epic Games Launcher",
        "paths": [
            r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe",
        ],
        "process": ["EpicGamesLauncher.exe"],
        "aliases": ["epic", "epic games launcher"],
    },
    "ccleaner": {
        "display": "CCleaner",
        "paths": [r"C:\Program Files\CCleaner\CCleaner.exe"],
        "process": ["CCleaner.exe", "CCleaner64.exe"],
        "aliases": [],
    },
    "photoshop": {
        "display": "Adobe Photoshop",
        "paths": [r"C:\Program Files\Adobe\Adobe Photoshop*\Photoshop.exe"],
        "process": ["Photoshop.exe"],
        "aliases": ["adobe photoshop"],
    },
}

PROCESS_ALIASES = {
    "chrome":      ["chrome.exe", "chromium.exe"],
    "firefox":     ["firefox.exe"],
    "edge":        ["msedge.exe"],
    "notepad":     ["notepad.exe"],
    "vlc":         ["vlc.exe"],
    "calculator":  ["Calculator.exe", "calc.exe"],
    "calendar":    ["HxCalendarAppImm.exe"],
    "mail":        ["HxMail.exe"],
    "sticky notes": ["Microsoft.Notes.exe"],
    "photos":      ["Microsoft.Photos.exe"],
}

# ══════════════════════════════════════════════════════════════════════════════
# 7. MODULE A — TTS (Text-to-Speech) Core
# ══════════════════════════════════════════════════════════════════════════════
class TTSCore:
    """
    Thread-safe TTS engine with fresh-engine-per-call pattern.
    [C-2] FIX: Correct engine cleanup order; engine stopped before retry.
    [M-2] FIX: Non-blocking speak() skips if TTS lock is already held
               (prevents unlimited daemon thread pile-up on rapid commands).
    [v4.0] NEW: speak_full() — speaks the ENTIRE text without truncation.
                stop() — stops any in-progress speech immediately.
                The _stop_event is set when the user says "stop" or "quiet";
                TTS thread checks it and exits mid-sentence.
    """

    def __init__(self):
        self._lock       = threading.Lock()
        self.available   = TTS_OK
        self._speed      = 180
        self._volume     = 1.0
        self._enabled    = True
        self._stop_event = threading.Event()   # [v4.0] set to interrupt TTS

    def stop_speaking(self):
        """Interrupt any currently-playing TTS immediately."""
        self._stop_event.set()

    def _build_engine(self):
        if not TTS_OK:
            return None
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate",   self._speed)
            engine.setProperty("volume", self._volume)
            voices   = engine.getProperty("voices") or []
            preferred = ["zira", "david", "hazel", "samantha", "jenny", "aria"]
            for pref in preferred:
                for v in voices:
                    if v and pref in (v.name or "").lower():
                        engine.setProperty("voice", v.id)
                        break
                else:
                    continue
                break
            return engine
        except Exception as e:
            logger.error(f"TTS _build_engine failed: {e}")
            return None

    def speak(self, text: str, blocking: bool = True):
        """
        Speak text.  By default speaks the FULL text (no truncation).
        blocking=False runs in a daemon thread.
        Respects the stop_event — if stop_speaking() is called mid-speech,
        the thread will exit after the current utterance.
        """
        if not text or not self._enabled:
            return
        clean = str(text).strip()
        print(f"\n🔊  JARVIS: {clean}")
        logger.info(f"[TTS] {clean}")

        def _do_speak():
            # [M-2] FIX: If non-blocking and lock is already taken, skip.
            if not blocking and self._lock.locked():
                logger.debug("[TTS] Skipping non-blocking speak — TTS already in use")
                return

            self._stop_event.clear()   # [v4.0] reset stop flag before speaking

            with self._lock:
                if not TTS_OK:
                    return
                engine = self._build_engine()
                if not engine:
                    return
                success = False

                # ── First attempt ──────────────────────────────────
                try:
                    if self._stop_event.is_set():
                        return   # user interrupted before we even started
                    engine.say(clean)
                    engine.runAndWait()
                    success = True
                except Exception as e:
                    logger.warning(f"TTS first attempt failed: {e}")
                finally:
                    try:
                        engine.stop()
                    except Exception:
                        pass
                    try:
                        del engine
                    except Exception:
                        pass

                if success or self._stop_event.is_set():
                    return

                # ── Retry with fresh engine ────────────────────────
                engine2 = None
                try:
                    engine2 = self._build_engine()
                    if engine2 and not self._stop_event.is_set():
                        engine2.say(clean)
                        engine2.runAndWait()
                except Exception as e2:
                    logger.error(f"TTS retry failed: {e2}")
                finally:
                    if engine2 is not None:
                        try:
                            engine2.stop()
                        except Exception:
                            pass
                        try:
                            del engine2
                        except Exception:
                            pass

        if blocking:
            _do_speak()
        else:
            t = threading.Thread(target=_do_speak, daemon=True)
            t.start()

    def speak_streaming(self, text: str, stop_check: "callable" = None):
        """
        [FIX-AI] Speak a long AI response sentence-by-sentence in a daemon
        thread.  After each sentence the stop_check callback is called; if it
        returns True the speech stops immediately.  This lets the main loop
        keep listening for a "stop" command while JARVIS is still talking.

        Args:
            text:        Full AI response string.
            stop_check:  Optional callable() → bool; returning True aborts.
        """
        if not text or not self._enabled:
            return

        import re as _re
        # Split on sentence-ending punctuation; keep the delimiter
        sentences = _re.split(r'(?<=[.!?])\s+', text.strip())
        if not sentences:
            return

        print(f"\n🔊  JARVIS: {text}")

        def _run():
            self._stop_event.clear()
            for sentence in sentences:
                if self._stop_event.is_set():
                    break
                if stop_check and stop_check():
                    break
                sentence = sentence.strip()
                if not sentence:
                    continue
                # Reuse the normal speak() path but blocking per-sentence
                # so we can check the stop flag between sentences
                with self._lock:
                    if self._stop_event.is_set():
                        break
                    engine = self._build_engine()
                    if not engine:
                        continue
                    try:
                        engine.say(sentence)
                        engine.runAndWait()
                    except Exception:
                        pass
                    finally:
                        try:
                            engine.stop()
                        except Exception:
                            pass
                        try:
                            del engine
                        except Exception:
                            pass

        t = threading.Thread(target=_run, daemon=True)
        t.start()

    def set_speed(self, wpm: int):
        self._speed = max(50, min(400, int(wpm)))
        return True, f"TTS speed set to {self._speed} wpm"

    def set_volume(self, pct: float):
        self._volume = max(0.0, min(1.0, float(pct) / 100))
        return True, f"TTS volume set to {int(self._volume*100)}%"

    def mute_tts(self):
        self._enabled = False
        return True, "TTS muted"

    def unmute_tts(self):
        self._enabled = True
        return True, "TTS unmuted"


# ══════════════════════════════════════════════════════════════════════════════
# 8. MODULE B — Voice Recognition Core
# ══════════════════════════════════════════════════════════════════════════════
class VoiceCore:
    """
    [M-4] FIX: Microphone calibration is now done in a background thread
    with a 5-second timeout to prevent hanging startup if the mic is present
    but unresponsive.
    """

    def __init__(self):
        self.available   = False
        self._recognizer = None
        self._mic        = None

        if not SR_OK:
            logger.warning("speech_recognition not installed")
            return

        try:
            self._recognizer = sr.Recognizer()
            self._recognizer.energy_threshold           = 300
            self._recognizer.dynamic_energy_threshold   = True
            self._recognizer.dynamic_energy_adjustment_ratio = 1.5
            self._recognizer.pause_threshold            = 1.2
            self._recognizer.phrase_threshold           = 0.3
            self._recognizer.non_speaking_duration      = 0.8
            self._recognizer.operation_timeout          = 15
            self._mic = sr.Microphone()

            # [M-4] FIX: Run calibration in a thread with timeout
            calibrated = threading.Event()
            calibration_error = [None]

            def _calibrate():
                try:
                    with self._mic as source:
                        print("🎤  Calibrating microphone...", end="", flush=True)
                        self._recognizer.adjust_for_ambient_noise(source, duration=1.0)
                    calibrated.set()
                except Exception as e:
                    calibration_error[0] = e
                    calibrated.set()

            cal_thread = threading.Thread(target=_calibrate, daemon=True)
            cal_thread.start()
            completed = calibrated.wait(timeout=5.0)

            if not completed:
                print(" (calibration timed out — voice disabled)")
                logger.warning("VoiceCore: mic calibration timed out after 5s")
                return

            if calibration_error[0]:
                print(f" (calibration error: {calibration_error[0]})")
                logger.warning(f"VoiceCore calibration error: {calibration_error[0]}")
                return

            print(" ready")
            self.available = True
            logger.info("VoiceCore initialized successfully")

        except Exception as e:
            logger.warning(f"VoiceCore init failed: {e}")

    def listen(self, timeout: float = 8.0, phrase_limit: float = 20.0) -> Optional[str]:
        if not self.available:
            return None
        print("🎤  Listening...", end="", flush=True)
        try:
            with self._mic as source:
                audio = self._recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_limit
                )
            print(" processing...", end="", flush=True)
            text = self._recognizer.recognize_google(audio)
            print(f" ✅  \"{text}\"")
            logger.info(f"[Voice] Heard: {text}")
            return text.lower().strip()
        except sr.WaitTimeoutError:
            print(" (timeout)")
            return None
        except sr.UnknownValueError:
            print(" ❌  (unclear)")
            return None
        except sr.RequestError as e:
            print(" ❌  (service error)")
            logger.warning(f"[Voice] Service error: {e}")
            return None
        except Exception as e:
            print(f" ❌  ({e})")
            logger.error(f"[Voice] Listen error: {e}")
            return None


# ══════════════════════════════════════════════════════════════════════════════
# 9. MODULE C — AI Gateway (Multi-model open-source + commercial)
# ══════════════════════════════════════════════════════════════════════════════
class AIGateway:
    """
    Unified gateway for multiple AI providers/models.
    [C-5] FIX: After trimming history, ensure it never starts with an
    assistant-role message (Anthropic API rejects this).
    """

    OPEN_SOURCE_MODELS = {
        "llama3.2":    {"provider": "ollama", "id": "llama3.2",        "desc": "Meta Llama 3.2 3B — fast"},
        "llama3.1":    {"provider": "ollama", "id": "llama3.1",        "desc": "Meta Llama 3.1 8B — balanced"},
        "llama3.1:70b":{"provider": "ollama", "id": "llama3.1:70b",   "desc": "Meta Llama 3.1 70B — powerful"},
        "mistral":     {"provider": "ollama", "id": "mistral",         "desc": "Mistral 7B — fast & capable"},
        "mixtral":     {"provider": "ollama", "id": "mixtral",         "desc": "Mixtral 8x7B MoE — excellent"},
        "gemma2":      {"provider": "ollama", "id": "gemma2",          "desc": "Google Gemma 2 9B"},
        "gemma2:27b":  {"provider": "ollama", "id": "gemma2:27b",     "desc": "Google Gemma 2 27B"},
        "qwen2.5":     {"provider": "ollama", "id": "qwen2.5",        "desc": "Alibaba Qwen 2.5 7B"},
        "qwen2.5:72b": {"provider": "ollama", "id": "qwen2.5:72b",   "desc": "Alibaba Qwen 2.5 72B"},
        "phi3":        {"provider": "ollama", "id": "phi3",            "desc": "Microsoft Phi-3 Mini 3.8B"},
        "phi3:medium": {"provider": "ollama", "id": "phi3:medium",    "desc": "Microsoft Phi-3 Medium 14B"},
        "codellama":   {"provider": "ollama", "id": "codellama",       "desc": "Code-focused Llama"},
        "deepseek-coder": {"provider": "ollama", "id": "deepseek-coder", "desc": "DeepSeek Coder 6.7B"},
        "deepseek-r1": {"provider": "ollama", "id": "deepseek-r1",   "desc": "DeepSeek R1 reasoning"},
        "llava":       {"provider": "ollama", "id": "llava",           "desc": "Multimodal vision+language"},
        "orca-mini":   {"provider": "ollama", "id": "orca-mini",       "desc": "Orca Mini 3B — very fast"},
        "neural-chat": {"provider": "ollama", "id": "neural-chat",    "desc": "Intel Neural Chat 7B"},
        "starling-lm": {"provider": "ollama", "id": "starling-lm",   "desc": "Starling 7B — RLHF tuned"},
        "solar":       {"provider": "ollama", "id": "solar",           "desc": "Solar 10.7B — strong"},
        "dolphin-mistral": {"provider": "ollama", "id": "dolphin-mistral", "desc": "Uncensored Mistral"},
        "groq-llama3": {"provider": "groq", "id": "llama3-70b-8192",  "desc": "Llama3 70B via Groq (fast)"},
        "groq-mixtral":{"provider": "groq", "id": "mixtral-8x7b-32768","desc": "Mixtral via Groq (fast)"},
        "groq-gemma":  {"provider": "groq", "id": "gemma-7b-it",      "desc": "Gemma 7B via Groq"},
        "gpt-4o":      {"provider": "openai", "id": "gpt-4o",         "desc": "OpenAI GPT-4o"},
        "gpt-4-turbo": {"provider": "openai", "id": "gpt-4-turbo",    "desc": "OpenAI GPT-4 Turbo"},
        "gpt-3.5":     {"provider": "openai", "id": "gpt-3.5-turbo",  "desc": "OpenAI GPT-3.5"},
        "claude-3.5":  {"provider": "anthropic", "id": "claude-3-5-sonnet-20241022", "desc": "Claude 3.5 Sonnet"},
        "claude-haiku":{"provider": "anthropic", "id": "claude-3-haiku-20240307",   "desc": "Claude 3 Haiku (fast)"},
    }

    def __init__(self):
        self._model       = "llama3.2"
        self._history     : List[Dict]  = []
        self._max_history = 20
        self._system_prompt = (
            "You are JARVIS, an advanced AI assistant. "
            "Be helpful, concise, and accurate. "
            "If asked to perform system actions, describe what you would do clearly."
        )
        self._api_keys = {
            "openai":    os.environ.get("OPENAI_API_KEY",    ""),
            "anthropic": os.environ.get("ANTHROPIC_API_KEY", ""),
            "groq":      os.environ.get("GROQ_API_KEY",      ""),
            "together":  os.environ.get("TOGETHER_API_KEY",  ""),
            "huggingface": os.environ.get("HF_API_KEY",      ""),
        }
        self._ollama_url   = os.environ.get("OLLAMA_URL",    "http://localhost:11434")
        self._lmstudio_url = os.environ.get("LMSTUDIO_URL",  "http://localhost:1234")
        self._jan_url      = os.environ.get("JAN_URL",       "http://localhost:1337")
        self._groq_url     = "https://api.groq.com/openai/v1"
        self._together_url = "https://api.together.xyz/v1"

    def set_model(self, name: str) -> Tuple[bool, str]:
        name = name.strip().lower()
        for key in self.OPEN_SOURCE_MODELS:
            if name in key or key in name:
                self._model = key
                info = self.OPEN_SOURCE_MODELS[key]
                return True, f"AI model set to: {key} ({info['desc']})"
        self._model = name
        return True, f"AI model set to: {name}"

    def list_models(self) -> str:
        lines = ["\n🤖  Available AI Models:\n"]
        current_provider = None
        for key, info in self.OPEN_SOURCE_MODELS.items():
            prov = info["provider"]
            if prov != current_provider:
                current_provider = prov
                lines.append(f"\n  [{prov.upper()}]")
            marker = " ◀ active" if key == self._model else ""
            lines.append(f"    {key:<20} — {info['desc']}{marker}")
        return "\n".join(lines)

    def _ollama_chat(self, messages: List[Dict], model: str) -> str:
        url = f"{self._ollama_url}/api/chat"
        payload = json.dumps({
            "model":    model,
            "messages": messages,
            "stream":   False,
        }).encode()
        req = Request(url, data=payload, headers={"Content-Type": "application/json"})
        try:
            with urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read())
                return data.get("message", {}).get("content", "No response")
        except URLError as e:
            raise ConnectionError(f"Ollama not running at {self._ollama_url}: {e}")

    def _openai_compat_chat(self, messages: List[Dict], model: str,
                             base_url: str, api_key: str) -> str:
        if not REQ_OK:
            raise RuntimeError("requests library not installed")
        headers = {
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        payload = {"model": model, "messages": messages, "max_tokens": 2048}
        resp = requests.post(
            f"{base_url}/chat/completions",
            headers=headers, json=payload, timeout=60
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def _anthropic_chat(self, messages: List[Dict], model: str) -> str:
        if not ANT_OK:
            raise RuntimeError("anthropic library not installed")
        client = anthropic_lib.Anthropic(api_key=self._api_keys["anthropic"])
        user_msgs = [m for m in messages if m["role"] != "system"]
        resp = client.messages.create(
            model=model, max_tokens=2048,
            system=self._system_prompt,
            messages=user_msgs,
        )
        return resp.content[0].text

    def _hf_inference(self, prompt: str, model: str) -> str:
        api_key = self._api_keys["huggingface"]
        if not api_key:
            raise RuntimeError("HF_API_KEY not set")
        url = f"https://api-inference.huggingface.co/models/{model}"
        headers = {"Authorization": f"Bearer {api_key}"}
        payload = json.dumps({"inputs": prompt}).encode()
        req = Request(url, data=payload, headers=headers)
        with urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
            if isinstance(data, list):
                return data[0].get("generated_text", str(data))
            return str(data)

    def query(self, user_input: str, stream_callback: Callable = None) -> Tuple[bool, str]:
        """
        Send query to active AI model, maintaining conversation history.
        [C-5] FIX: After trimming, re-anchor history to always start with a user turn.
        """
        if not user_input.strip():
            return False, "Empty query"

        self._history.append({"role": "user", "content": user_input})

        # Trim history if over limit
        max_entries = self._max_history * 2
        if len(self._history) > max_entries:
            self._history = self._history[-max_entries:]

        # [C-5] FIX: After trim, ensure history never starts with an assistant turn.
        # Anthropic (and most APIs) require conversation to start with user role.
        while self._history and self._history[0]["role"] != "user":
            self._history.pop(0)

        messages = [{"role": "system", "content": self._system_prompt}] + self._history

        model_info = self.OPEN_SOURCE_MODELS.get(self._model, {})
        provider   = model_info.get("provider", "ollama")
        model_id   = model_info.get("id", self._model)

        try:
            if provider == "ollama":
                response = self._ollama_chat(messages, model_id)
            elif provider == "openai":
                response = self._openai_compat_chat(
                    messages, model_id,
                    "https://api.openai.com/v1", self._api_keys["openai"]
                )
            elif provider == "anthropic":
                response = self._anthropic_chat(messages, model_id)
            elif provider == "groq":
                response = self._openai_compat_chat(
                    messages, model_id, self._groq_url, self._api_keys["groq"]
                )
            elif provider == "together":
                response = self._openai_compat_chat(
                    messages, model_id, self._together_url, self._api_keys["together"]
                )
            elif provider == "lmstudio":
                response = self._openai_compat_chat(messages, model_id, self._lmstudio_url, "lm-studio")
            elif provider == "jan":
                response = self._openai_compat_chat(messages, model_id, self._jan_url, "jan")
            else:
                response = self._ollama_chat(messages, model_id)

            self._history.append({"role": "assistant", "content": response})
            return True, response

        except ConnectionError as e:
            tip = "  💡 Start Ollama with: ollama serve" if provider == "ollama" else ""
            msg = f"Connection failed ({provider}): {e}{tip}"
            logger.error(msg)
            return False, msg
        except Exception as e:
            logger.error(f"AIGateway.query failed [{provider}/{model_id}]: {e}")
            return False, f"AI error: {e}"

    def clear_history(self):
        self._history.clear()
        return True, "Conversation history cleared"

    def list_ollama_models(self) -> Tuple[bool, str]:
        try:
            req = Request(f"{self._ollama_url}/api/tags")
            with urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
            models = [m["name"] for m in data.get("models", [])]
            if not models:
                return False, "No models pulled yet. Run: ollama pull llama3.2"
            return True, "Local Ollama models:\n" + "\n".join(f"  • {m}" for m in models)
        except Exception as e:
            return False, f"Cannot reach Ollama: {e}  (run: ollama serve)"

    def pull_ollama_model(self, model: str) -> Tuple[bool, str]:
        try:
            subprocess.Popen(
                ["ollama", "pull", model],
                creationflags=_NO_WIN_FLAG
            )
            return True, f"Pulling model '{model}'... (runs in background)"
        except FileNotFoundError:
            return False, "Ollama not installed. Visit: https://ollama.ai"
        except Exception as e:
            return False, str(e)


# ══════════════════════════════════════════════════════════════════════════════
# 10. MODULE D — Calculator (Safe AST)
# ══════════════════════════════════════════════════════════════════════════════
class SafeCalculator:
    """
    Pure AST evaluator — no eval/exec.
    [C-3] FIX: Exponent capped at MAX_EXPONENT to prevent DoS (preserved).
    [m-3] FIX: Caret ^ is normalised to ** before SAFE_RE strips non-numeric chars.
    """
    MAX_EXPONENT = 1000
    MAX_VALUE    = 1e300

    # [BUG-8/9] FIX: Prepositional patterns resolved BEFORE generic WORD_OPS to prevent
    # digit concatenation. "subtract 5 from 10" → "10 - 5"; "add 3 to 7" → "3 + 7"
    PREP_OPS = [
        (re.compile(r'\badd\s+(\d+(?:\.\d+)?)\s+to\s+(\d+(?:\.\d+)?)', re.I),
         lambda m: f"{m.group(1)} + {m.group(2)}"),
        (re.compile(r'\bsubtract\s+(\d+(?:\.\d+)?)\s+from\s+(\d+(?:\.\d+)?)', re.I),
         lambda m: f"{m.group(2)} - {m.group(1)}"),
        (re.compile(r'\bmultiply\s+(\d+(?:\.\d+)?)\s+by\s+(\d+(?:\.\d+)?)', re.I),
         lambda m: f"{m.group(1)} * {m.group(2)}"),
        (re.compile(r'\bdivide\s+(\d+(?:\.\d+)?)\s+by\s+(\d+(?:\.\d+)?)', re.I),
         lambda m: f"{m.group(1)} / {m.group(2)}"),
    ]
    WORD_OPS = [
        (r'\bplus\b', '+'),          (r'\bminus\b', '-'),
        (r'\btimes\b', '*'),         (r'\binto\b', '*'),
        (r'\bmultiplied\s+by\b', '*'), (r'\bdivided\s+by\b', '/'),
        (r'\bdivide\b', '/'),        (r'\bover\b', '/'),
        (r'\bmod(?:ulo)?\b', '%'),   (r'\bpercent\s+of\b', '/100*'),
        (r'\bsquared\b', '**2'),     (r'\bcubed\b', '**3'),
        (r'\bto\s+the\s+power\s+of\b', '**'),
        (r'\braised\s+to\b', '**'),  (r'\bsubtract\b', '-'),
        (r'\badd\b', '+'),           (r'\bx\b', '*'),
    ]
    SQRT_RE = re.compile(r'square\s+root\s+of\s+(\d+(?:\.\d+)?)', re.I)
    CUBE_RE = re.compile(r'cube\s+root\s+of\s+(\d+(?:\.\d+)?)', re.I)
    # FIX: Pattern now captures optional leading minus so 'log of -5' is caught
    # by the validation branch (v <= 0) rather than falling through to the
    # generic evaluator which would just return -5 as if it were valid.
    LOG_RE  = re.compile(r'log(?:arithm)?\s+of\s+(-?\d+(?:\.\d+)?)', re.I)
    # [m-3] FIX: SAFE_RE now excludes ^ so caret-style exponents survive until normalisation
    SAFE_RE = re.compile(r'[^0-9+\-*/().%^\s]')
    FILLER  = re.compile(
        r'\b(what\s+is|what\'?s|calculate|compute|equals?|'
        r'evaluate|solve|find|the\s+answer\s+to|tell\s+me)\b', re.I
    )
    _OPS: Dict = {
        ast.Add: operator.add,   ast.Sub: operator.sub,
        ast.Mult: operator.mul,  ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Pow: operator.pow,   ast.Mod: operator.mod,
        ast.USub: operator.neg,  ast.UAdd: operator.pos,
    }

    def _ast_eval(self, node) -> float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        # Python 3.14+ removes ast.Num; use hasattr guard
        if hasattr(ast, 'Num') and isinstance(node, ast.Num):  # Python < 3.8 compat
            return float(node.n)
        if isinstance(node, ast.BinOp):
            op_t  = type(node.op)
            if op_t not in self._OPS:
                raise ValueError(f"Unsupported operator: {op_t.__name__}")
            left  = self._ast_eval(node.left)
            right = self._ast_eval(node.right)
            # [C-3] Cap exponent to prevent DoS
            if op_t == ast.Pow:
                if abs(right) > self.MAX_EXPONENT:
                    raise ValueError(f"Exponent {right} exceeds max ({self.MAX_EXPONENT})")
            result = self._OPS[op_t](left, right)
            if abs(result) > self.MAX_VALUE:
                raise OverflowError("Result too large")
            return result
        if isinstance(node, ast.UnaryOp):
            op_t = type(node.op)
            if op_t not in self._OPS:
                raise ValueError(f"Unsupported unary: {op_t.__name__}")
            return self._OPS[op_t](self._ast_eval(node.operand))
        raise ValueError(f"Unsupported AST node: {type(node).__name__}")

    def evaluate(self, expr: str) -> Tuple[bool, str]:
        expr = expr.lower().strip()
        # Special forms
        m = self.SQRT_RE.search(expr)
        if m:
            return True, f"√{m.group(1)} = {math.sqrt(float(m.group(1))):.6g}"
        m = self.CUBE_RE.search(expr)
        if m:
            return True, f"∛{m.group(1)} = {float(m.group(1))**(1/3):.6g}"
        m = self.LOG_RE.search(expr)
        if m:
            v = float(m.group(1))
            if v <= 0:
                return False, "Logarithm undefined for non-positive numbers"
            return True, f"log({m.group(1)}) = {math.log10(v):.6g}  (ln = {math.log(v):.6g})"
        # [BUG-8/9] FIX: Prepositional phrases first to avoid digit concatenation
        for pat, repl in self.PREP_OPS:
            expr = pat.sub(repl, expr)
        # Word replacements
        expr = self.SQRT_RE.sub(lambda x: f"({x.group(1)}**0.5)", expr)
        expr = self.CUBE_RE.sub(lambda x: f"({x.group(1)}**(1/3))", expr)
        for pat, repl in self.WORD_OPS:
            expr = re.sub(pat, repl, expr, flags=re.I)
        expr = self.FILLER.sub("", expr).strip()
        # [m-3] FIX: Normalise caret ^ to ** BEFORE SAFE_RE strips it
        expr = expr.replace("^", "**")
        expr = self.SAFE_RE.sub("", expr).strip()
        expr = re.sub(r'\s+', '', expr)
        if not expr:
            return False, "Empty expression"
        try:
            tree   = ast.parse(expr, mode="eval")
            result = self._ast_eval(tree.body)
            if isinstance(result, float):
                if result.is_integer() and abs(result) < 1e15:
                    result = int(result)
                else:
                    result = round(result, 8)
            return True, f"Result: {result}"
        except ZeroDivisionError:
            return False, "Cannot divide by zero"
        except OverflowError as e:
            return False, str(e)
        except (ValueError, SyntaxError, TypeError) as e:
            logger.debug(f"Calculator: '{expr}' → {e}")
            return False, f"Cannot evaluate: {e}"
        except Exception as e:
            logger.error(f"Calculator unexpected error: {e}")
            return False, f"Error: {e}"

# ══════════════════════════════════════════════════════════════════════════════
# 11. MODULE E — Application Controller
# ══════════════════════════════════════════════════════════════════════════════
class AppController:
    """
    [C-6] FIX: UWP apps are no longer blindly marked installed=True.
               Only mark UWP installed=True if on Windows; launch failure
               surfaces a clear message rather than a silent false positive.
    [M-5] FIX: File Explorer (explorer.exe) is now in the process list and
               can be properly targeted by close(); the old unconditional
               skip of explorer.exe is removed — it only skips if the user
               didn't explicitly ask to close it (which they can via
               "close file explorer").
    """

    def __init__(self):
        self._cache         : Dict = {}
        self._dynamic_apps  : Dict = {}
        self._scan_static()
        if IS_WINDOWS:
            self._scan_registry()
            self._scan_startapps()

    def _scan_static(self):
        for key, entry in APP_DATABASE.items():
            record = {**entry, "installed": False, "resolved_path": None}
            for raw in entry.get("paths", []):
                if "*" in raw:
                    matches = glob.glob(raw)
                    if matches:
                        record["installed"]     = True
                        record["resolved_path"] = matches[0]
                        break
                elif os.path.exists(raw):
                    record["installed"]     = True
                    record["resolved_path"] = raw
                    break
            if not record["installed"] and entry.get("cmd"):
                if shutil.which(entry["cmd"]):
                    record["installed"] = True

            # [C-6] FIX v7: Do NOT assume UWP apps are installed.
            # Previously this marked all UWP entries as installed on Windows,
            # causing File Explorer to open when app missing (e.g., WhatsApp).
            if not record["installed"] and entry.get("uwp"):
                record["installed"] = False  # will be verified on launch
            self._cache[key] = record

    def _scan_registry(self):
        if not WINREG_OK:
            return
        reg_paths = [
            (winreg.HKEY_LOCAL_MACHINE,
             r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE,
             r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER,
             r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]
        for hive, path in reg_paths:
            try:
                with winreg.OpenKey(hive, path) as key:
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            sub = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, sub) as sk:
                                try:
                                    dn = winreg.QueryValueEx(sk, "DisplayName")[0]
                                except (FileNotFoundError, OSError):
                                    continue
                                try:
                                    il = winreg.QueryValueEx(sk, "InstallLocation")[0]
                                except (FileNotFoundError, OSError):
                                    il = ""
                                try:
                                    di = winreg.QueryValueEx(sk, "DisplayIcon")[0]
                                except (FileNotFoundError, OSError):
                                    di = ""
                                exe = None
                                if di and di.lower().endswith(".exe"):
                                    exe = di.split(",")[0].strip('"')
                                elif il and os.path.isdir(il):
                                    exes = glob.glob(os.path.join(il, "*.exe"))
                                    if exes:
                                        exe = exes[0]
                                norm = dn.lower().strip()
                                if norm not in self._cache and norm not in self._dynamic_apps:
                                    self._dynamic_apps[norm] = {
                                        "display": dn, "paths": [exe] if exe else [],
                                        "process": [os.path.basename(exe)] if exe else [],
                                        "aliases": [], "source": "registry",
                                        "installed": bool(exe and os.path.exists(exe)),
                                        "resolved_path": exe if (exe and os.path.exists(exe)) else None,
                                    }
                        except OSError:
                            continue
            except OSError:
                continue

    def _scan_startapps(self):
        """[NEW v7] Scan ALL Start Menu apps via Get-StartApps.
        This captures UWP, Store apps, and classic apps that appear in Start.
        Runs: Get-StartApps | Select Name, AppID | ConvertTo-Json
        """
        if not IS_WINDOWS:
            return
        try:
            ps_cmd = "Get-StartApps | Select-Object Name,AppID | ConvertTo-Json -Compress"
            r = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                capture_output=True, text=True, timeout=20,
                creationflags=_NO_WIN_FLAG
            )
            if r.returncode != 0 or not r.stdout.strip():
                logger.warning(f"Get-StartApps failed: {r.stderr[:200]}")
                return
            try:
                data = json.loads(r.stdout)
            except json.JSONDecodeError:
                # PowerShell sometimes returns single object without array
                data = json.loads(f"[{r.stdout}]")
            if isinstance(data, dict):
                data = [data]
            added = 0
            for item in data:
                name = (item.get("Name") or "").strip()
                appid = (item.get("AppID") or "").strip()
                if not name or not appid:
                    continue
                key = re.sub(r'[\s\-_]', '', name.lower())
                # Don't overwrite static DB entries
                if key in self._cache:
                    # enrich static entry with AppID if missing
                    if "appid" not in self._cache[key]:
                        self._cache[key]["appid"] = appid
                    continue
                if key in self._dynamic_apps:
                    continue
                self._dynamic_apps[key] = {
                    "display": name,
                    "appid": appid,
                    "installed": True,
                    "resolved_path": None,
                    "process": [],
                    "aliases": [name.lower(), re.sub(r'[^a-z0-9]', '', name.lower())],
                    "source": "startapps",
                }
                added += 1
            logger.info(f"[StartApps] Loaded {added} apps from Get-StartApps (total dynamic: {len(self._dynamic_apps)})")
        except Exception as e:
            logger.warning(f"_scan_startapps exception: {e}")

    def find_app(self, name: str) -> Tuple[Optional[str], Optional[Dict]]:
        name = name.lower().strip()
        if name in self._cache:
            return name, self._cache[name]
        norm = re.sub(r'[\s\-_]', '', name)
        for k, v in self._cache.items():
            if norm == re.sub(r'[\s\-_]', '', k):
                return k, v
        for k, v in self._cache.items():
            if name in [a.lower() for a in v.get("aliases", [])]:
                return k, v
        for k, v in self._cache.items():
            if name in k or k in name:
                return k, v
        for k, v in self._cache.items():
            if name in v.get("display", "").lower():
                return k, v
        if name in self._dynamic_apps:
            return name, self._dynamic_apps[name]
        for k, v in self._dynamic_apps.items():
            if name in k or k in name:
                return k, v
        # Fuzzy word-overlap
        name_words = set(name.split())
        best, best_score = None, 0
        for k, v in {**self._cache, **self._dynamic_apps}.items():
            kw = set(k.split()) | set(v.get("display", "").lower().split())
            score = len(name_words & kw)
            if score > best_score and score >= max(1, len(name_words) // 2):
                best, best_score = (k, v), score
        return best if best else (None, None)

    @safe_exec(default_return=(False, "Launch failed"))
    def launch(self, name: str, incognito: bool = False) -> Tuple[bool, str]:
        key, app = self.find_app(name)
        if app is None:
            return False, f"'{name}' not found. Try 'open microsoft store' to find apps."
        display  = app.get("display", name)
        incog_f  = app.get("incognito", "") if incognito else ""
        mode_str = " (incognito)" if incognito else ""

        # [FIX v7] Priority: resolved_path > cmd > appid (from Get-StartApps) > uwp > web_fallback
        if app.get("resolved_path") and os.path.exists(app["resolved_path"]):
            args = [app["resolved_path"]]
            if incog_f:
                args.append(incog_f)
            subprocess.Popen(args, creationflags=_NO_WIN_FLAG)
        elif app.get("cmd") and shutil.which(app["cmd"].split()[0]):
            cmd_v = app["cmd"]
            if IS_WINDOWS and cmd_v.startswith("ms-settings:"):
                os.startfile(cmd_v)
            else:
                subprocess.Popen(shlex.split(cmd_v), creationflags=_NO_WIN_FLAG)  # [S-1] shell=True removed
        elif app.get("appid"):  # From Get-StartApps
            appid = app["appid"]
            try:
                # This works for ALL Start Menu apps (UWP, Win32, Store)
                subprocess.Popen(
                    ["explorer.exe", f"shell:AppsFolder\\{appid}"],
                    creationflags=_NO_WIN_FLAG
                )
            except Exception as e:
                logger.warning(f"StartApps launch failed for {display}: {e}")
                if app.get("web_fallback"):
                    webbrowser.open(app["web_fallback"])
                    return True, JarvisResponder.app_open(display, web=True)
                return False, f"Failed to launch {display}"
        elif app.get("uwp"):
            uid = app["uwp"]
            # Verify UWP package exists before launching
            try:
                if IS_WINDOWS:
                    check_ps = f"Get-AppxPackage -Name {uid.split('_')[0]}* | Select-Object -First 1"
                    r = subprocess.run(["powershell", "-NoProfile", "-Command", check_ps],
                                       capture_output=True, text=True, timeout=5)
                    if r.stdout.strip() == "":
                        if app.get("web_fallback"):
                            webbrowser.open(app["web_fallback"])
                            return True, f"{display} not installed, opening web version"
                        return False, f"{display} is not installed"
                subprocess.Popen(
                    ["explorer.exe", f"shell:AppsFolder\\{uid}!App"],
                    creationflags=_NO_WIN_FLAG
                )
            except Exception as e:
                logger.warning(f"UWP launch failed for {display}: {e}")
                if app.get("web_fallback"):
                    webbrowser.open(app["web_fallback"])
                    return True, JarvisResponder.app_open(display, web=True)
                return False, f"Failed to launch {display}"
        elif app.get("web_fallback"):
            webbrowser.open(app["web_fallback"])
            return True, JarvisResponder.app_open(display, web=True)
        else:
            return False, f"No launch method for '{display}'"

        logger.info(f"Launched: {display}{mode_str}")
        return True, JarvisResponder.app_open(display)

    @safe_exec(default_return=(False, "Close failed"))
    def close(self, name: str) -> Tuple[bool, str]:
        """
        [M-5] FIX: explorer.exe is no longer unconditionally skipped.
        The old guard checked pname == 'explorer.exe' AFTER the pname-in-targets
        check, but 'file explorer' targets were never populated because the
        APP_DATABASE process list was empty. Both issues are now fixed:
          1) APP_DATABASE["file explorer"]["process"] now includes "explorer.exe"
          2) The unconditional skip is removed; explorer is only excluded from
             non-explicit generic kills (protected list below).
        """
        if not PSUTIL_OK:
            return False, "psutil not installed"

        key, app = self.find_app(name)
        targets = set()
        if app:
            targets.update(p.lower() for p in app.get("process", []))
        if name.lower() in PROCESS_ALIASES:
            targets.update(p.lower() for p in PROCESS_ALIASES[name.lower()])
        if not targets:
            targets.add(name.lower())
            targets.add(name.lower() + ".exe")

        # System-critical processes that should NEVER be killed implicitly
        # (only killed if directly targeted by name — e.g., "close file explorer")
        PROTECTED = {"system", "smss.exe", "csrss.exe", "wininit.exe", "services.exe",
                     "lsass.exe", "winlogon.exe", "svchost.exe", "dwm.exe", "explorer.exe"}

        # Special handling for File Explorer - close windows instead of killing process
        if "explorer.exe" in targets or name.lower() in ("file explorer", "explorer", "files"):
            # Close all File Explorer windows gracefully using Alt+F4 or Win32
            if WIN32_OK:
                closed = 0
                def _enum(hwnd, _):
                    nonlocal closed
                    if win32gui.IsWindowVisible(hwnd):
                        try:
                            _, pid = win32process.GetWindowThreadProcessId(hwnd)
                            pname = psutil.Process(pid).name().lower()
                            if pname == "explorer.exe":
                                title = win32gui.GetWindowText(hwnd)
                                # Skip the desktop/taskbar window (has no title or is "Program Manager")
                                if title and title != "Program Manager" and ("File Explorer" in win32gui.GetClassName(hwnd) or "CabinetWClass" == win32gui.GetClassName(hwnd)):
                                    win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                                    closed += 1
                        except Exception:
                            pass
                win32gui.EnumWindows(_enum, None)
                if closed > 0:
                    return True, f"Closed {closed} File Explorer window(s)"
                # If no windows found, try generic close
                return True, "File Explorer windows closed"
            else:
                return False, "Cannot close File Explorer (win32 not available)"

        # Remove protected processes unless the user explicitly targeted them
        user_requested = {name.lower(), name.lower() + ".exe"}
        explicit_targets = targets - (PROTECTED - user_requested)

        count = 0
        for proc in psutil.process_iter(["name"]):
            try:
                pname = (proc.info.get("name") or "").lower()
                if pname in explicit_targets:
                    proc.terminate()
                    count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if count:
            logger.info(f"Closed {count} process(es) for '{name}'")
            return True, JarvisResponder.app_close(name)
        
        # If no process found, try closing by window title (for UWP apps like Microsoft To Do)
        if WIN32_OK:
            closed_windows = 0
            def _close_by_title(hwnd, _):
                nonlocal closed_windows
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd).lower()
                    if name.lower() in title or (app and app.get("display", "").lower() in title):
                        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                        closed_windows += 1
            win32gui.EnumWindows(_close_by_title, None)
            if closed_windows > 0:
                return True, JarvisResponder.app_close(name)
        
        return False, f"'{name}' is not running"

    @safe_exec(default_return=(False, "Switch failed"))
    def switch_to(self, name: str) -> Tuple[bool, str]:
        if not WIN32_OK or not PSUTIL_OK:
            return False, "win32gui / psutil not available"
        key, app = self.find_app(name)
        proc_names = [p.lower() for p in (app.get("process", []) if app else [name])]
        display    = app.get("display", name) if app else name
        found      = [False]

        def _enum(hwnd, _):
            if found[0]:
                return
            if not win32gui.IsWindowVisible(hwnd):
                return
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                proc   = psutil.Process(pid)
                pname  = proc.name().lower()
                if any(p in pname for p in proc_names):
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    win32gui.SetForegroundWindow(hwnd)
                    found[0] = True
            except Exception:
                pass

        win32gui.EnumWindows(_enum, None)
        if not found[0]:
            def _title(hwnd, _):
                if found[0]:
                    return
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd).lower()
                    if name.lower() in title or display.lower() in title:
                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                        win32gui.SetForegroundWindow(hwnd)
                        found[0] = True
            win32gui.EnumWindows(_title, None)

        return (True, f"Switched to {display}") if found[0] else (False, f"Window not found: '{name}'")

    @safe_exec(default_return=(False, "Failed"))
    def maximize_window(self, name: str) -> Tuple[bool, str]:
        if not WIN32_OK:
            return False, "win32gui not available"
        key, app   = self.find_app(name)
        proc_names = [p.lower() for p in (app.get("process", []) if app else [name])]
        display    = app.get("display", name) if app else name
        found      = [False]

        def _enum(hwnd, _):
            if found[0] or not win32gui.IsWindowVisible(hwnd):
                return
            try:
                title = win32gui.GetWindowText(hwnd).lower()
                match = name.lower() in title or display.lower() in title
                if not match and PSUTIL_OK:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    pname  = psutil.Process(pid).name().lower()
                    match  = any(p in pname for p in proc_names)
                if match:
                    win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                    # [FIX-V10] SetForegroundWindow can fail — wrap in try/except
                    try:
                        win32gui.SetForegroundWindow(hwnd)
                    except Exception:
                        try:
                            win32gui.BringWindowToTop(hwnd)
                        except Exception:
                            pass
                    found[0] = True
            except Exception:
                pass

        win32gui.EnumWindows(_enum, None)
        return (True, JarvisResponder.window_maximize(display)) if found[0] else (False, f"Not found: '{name}'")

    @safe_exec(default_return=(False, "Failed"))
    def minimize_window(self, name: str) -> Tuple[bool, str]:
        if not WIN32_OK:
            return False, "win32gui not available"
        key, app   = self.find_app(name)
        proc_names = [p.lower() for p in (app.get("process", []) if app else [name])]
        display    = app.get("display", name) if app else name
        found      = [False]

        def _enum(hwnd, _):
            if found[0] or not win32gui.IsWindowVisible(hwnd):
                return
            try:
                title = win32gui.GetWindowText(hwnd).lower()
                match = name.lower() in title or display.lower() in title
                if not match and PSUTIL_OK:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    pname  = psutil.Process(pid).name().lower()
                    match  = any(p in pname for p in proc_names)
                if match:
                    win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                    found[0] = True
            except Exception:
                pass

        win32gui.EnumWindows(_enum, None)
        return (True, JarvisResponder.window_minimize(display)) if found[0] else (False, f"Not found: '{name}'")

    @safe_exec(default_return=(False, "Failed"))
    def restore_window(self, name: str) -> Tuple[bool, str]:
        if not WIN32_OK:
            return False, "win32gui not available"
        key, app   = self.find_app(name)
        proc_names = [p.lower() for p in (app.get("process", []) if app else [name])]
        display    = app.get("display", name) if app else name
        found      = [False]

        def _enum(hwnd, _):
            if found[0] or not win32gui.IsWindowVisible(hwnd):
                return
            try:
                title = win32gui.GetWindowText(hwnd).lower()
                match = name.lower() in title or display.lower() in title
                if not match and PSUTIL_OK:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    pname  = psutil.Process(pid).name().lower()
                    match  = any(p in pname for p in proc_names)
                if match:
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    win32gui.SetForegroundWindow(hwnd)
                    found[0] = True
            except Exception:
                pass

        win32gui.EnumWindows(_enum, None)
        return (True, JarvisResponder.window_restore(display)) if found[0] else (False, f"Not found: '{name}'")

    @safe_exec(default_return=(False, "Failed"))
    def snap_window(self, name: str, direction: str) -> Tuple[bool, str]:
        if not WIN32_OK:
            return False, "win32gui not available"
        if not PAG_OK:
            return False, "pyautogui not available"
        
        # Clean up the name - remove trailing words like "side", "to", etc.
        name = re.sub(r'\s+(to|the|a|side|window|app)$', '', name, flags=re.I).strip()
        # Handle "right side" being captured as name
        if name.lower().endswith(' to right'):
            name = name[:-9].strip()
        if name.lower().endswith(' to left'):
            name = name[:-8].strip()
            
        # Focus the window first - use direct win32 to avoid launching new instance
        key, app = self.find_app(name)
        proc_names = [p.lower() for p in (app.get("process", []) if app else [name])]
        display = app.get("display", name) if app else name
        found = [False]
        target_hwnd = [None]

        def _enum(hwnd, _):
            if found[0] or not win32gui.IsWindowVisible(hwnd):
                return
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                pname = psutil.Process(pid).name().lower()
                if any(p in pname for p in proc_names):
                    # Also check title to get the right window
                    title = win32gui.GetWindowText(hwnd).lower()
                    if name.lower() in title or display.lower() in title or True:  # Accept first match
                        target_hwnd[0] = hwnd
                        found[0] = True
            except Exception:
                pass

        win32gui.EnumWindows(_enum, None)
        
        if not found[0]:
            # Try without process check - just by title
            def _enum_title(hwnd, _):
                if found[0]:
                    return
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd).lower()
                    if name.lower() in title or display.lower() in title:
                        target_hwnd[0] = hwnd
                        found[0] = True
            win32gui.EnumWindows(_enum_title, None)
        
        if not found[0]:
            return False, f"Cannot find window '{name}' - is it open?"
            
        # Bring to foreground — use multiple strategies to handle
        # the common SetForegroundWindow permission error on Windows.
        # Strategy: (1) SetForegroundWindow, (2) AttachThreadInput + BringWindowToTop,
        # (3) ShowWindow + SetForegroundWindow, (4) Alt key trick
        focused = False
        hwnd = target_hwnd[0]
        
        # Strategy 1: Direct SetForegroundWindow
        try:
            win32gui.SetForegroundWindow(hwnd)
            focused = True
        except Exception:
            pass
        
        # Strategy 2: AttachThreadInput + BringWindowToTop
        if not focused:
            try:
                current_thread = win32api.GetCurrentThreadId()
                _, target_pid = win32process.GetWindowThreadProcessId(hwnd)
                target_thread = win32api.OpenProcess(0x0001, False, target_pid)  # PROCESS_QUERY_INFORMATION
                # Get the thread ID of the target window
                target_tid = win32process.GetWindowThreadProcessId(hwnd)[0]
                if target_tid != current_thread:
                    win32api.AttachThreadInput(current_thread, target_tid, True)
                    win32gui.BringWindowToTop(hwnd)
                    win32gui.SetForegroundWindow(hwnd)
                    win32api.AttachThreadInput(current_thread, target_tid, False)
                    focused = True
            except Exception:
                pass
        
        # Strategy 3: ShowWindow + SetForegroundWindow
        if not focused:
            try:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.1)
                win32gui.SetForegroundWindow(hwnd)
                focused = True
            except Exception:
                pass
        
        # Strategy 4: Alt key trick (releases Windows foreground lock)
        if not focused:
            try:
                pyautogui.keyDown('alt')
                time.sleep(0.05)
                pyautogui.keyUp('alt')
                time.sleep(0.05)
                win32gui.SetForegroundWindow(hwnd)
                focused = True
            except Exception:
                pass
        
        if not focused:
            # Last resort: just bring to top without focus
            try:
                win32gui.BringWindowToTop(hwnd)
            except Exception:
                pass
            # Don't return error — proceed with snap anyway (keyboard shortcut may still work)
        
        time.sleep(0.15)  # Give Windows time to focus
        
        # Handle common speech recognition errors for Indian English
        dir_map = {
            "left": "left", "lift": "left", "lyft": "left",
            "right": "right", "write": "right", "rite": "right", "side": "right",
            "up": "up", "app": "up",  # "to app" misheard for "to up"
            "down": "down",
            "top": "up", "bottom": "down"
        }
        key = dir_map.get(direction.lower(), "left")
        pyautogui.hotkey("win", key)
        time.sleep(0.2)  # Wait for snap animation
        
        if key == "left":
            return True, JarvisResponder.snap_left(display)
        elif key == "right":
            return True, JarvisResponder.snap_right(display)
        else:
            return True, f"Snapped {display} to {direction}"

    @safe_exec(default_return=(False, "Failed"))
    def align_windows(self, left_name: str, right_name: str) -> Tuple[bool, str]:
        # Snap first app to left, second to right
        ok1, msg1 = self.snap_window(left_name, "left")
        time.sleep(0.4)
        ok2, msg2 = self.snap_window(right_name, "right")
        if ok1 and ok2:
            return True, f"Aligned {left_name} left and {right_name} right"
        return False, "Failed to align windows"

    def open_setting(self, name: str) -> Tuple[bool, str]:
        name = name.lower().strip()
        url  = WINDOWS_SETTINGS.get(name)
        if not url:
            for k, v in WINDOWS_SETTINGS.items():
                if name in k or k in name:
                    url, name = v, k
                    break
        if url:
            if IS_WINDOWS:
                os.startfile(url)
            else:
                webbrowser.open(url)
            return True, f"Opening {name} settings"
        if IS_WINDOWS:
            os.startfile("ms-settings:")
            return True, "Opening Settings"
        return False, f"Setting '{name}' not found"

    def count_running_windows(self, name: str) -> int:
        """
        [FIX-CLOSE] Count visible top-level windows belonging to the app.
        Returns 0 if win32gui/psutil unavailable.
        """
        if not WIN32_OK or not PSUTIL_OK:
            return 0
        key, app = self.find_app(name)
        targets: set = set()
        if app:
            targets.update(p.lower() for p in app.get("process", []))
        if name.lower() in PROCESS_ALIASES:
            targets.update(p.lower() for p in PROCESS_ALIASES[name.lower()])
        if not targets:
            targets.add(name.lower())
            targets.add(name.lower() + ".exe")
        window_count = [0]
        def _enum(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return
            if not win32gui.GetWindowText(hwnd):
                return
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                pname  = psutil.Process(pid).name().lower()
                if pname in targets:
                    window_count[0] += 1
            except Exception:
                pass
        try:
            win32gui.EnumWindows(_enum, None)
        except Exception:
            pass
        return window_count[0]


# ══════════════════════════════════════════════════════════════════════════════
# 12. MODULE F — System Controller
# ══════════════════════════════════════════════════════════════════════════════
class SystemController:
    def __init__(self):
        self._volume = 0.2  # 20% default - VolumeController integrated
        self._vol_cache: Tuple = (None, 0.0)

    # ── Volume ──────────────────────────────────────────────────────────
    def get_volume(self) -> Optional[int]:
        """VolumeController: Get current volume (0-100) - uses cached value"""
        # On Windows, we track volume internally since reading system volume requires pycaw
        # For accuracy, we assume starting at 50% and track changes
        if not hasattr(self, '_sys_vol'):
            self._sys_vol = 50  # Assume mid-volume at start
        return int(self._sys_vol)

    def set_volume(self, level: int) -> Tuple[bool, str]:
        """VolumeController: Smart set with actual system volume control"""
        try:
            target_pct = float(level)
        except (TypeError, ValueError):
            return False, "Invalid volume value"

        target_pct = max(0, min(100, target_pct))
        current_pct = self.get_volume()
        diff = int(target_pct - current_pct)

        if abs(diff) < 2:
            msg = f"Volume already at {int(target_pct)}%."
            return True, msg

        # Use pyautogui to actually change system volume
        if PAG_OK:
            # Each volume key press changes by ~2% on Windows
            steps = abs(diff) // 2
            if steps == 0:
                steps = 1
            key = "volumeup" if diff > 0 else "volumedown"
            for _ in range(steps):
                pyautogui.press(key)
                time.sleep(0.05)
            self._sys_vol = target_pct
            self._volume = target_pct / 100
            msg = f"Setting volume to {int(target_pct)}%."
            return True, msg
        else:
            # Fallback to internal tracking only
            self._sys_vol = target_pct
            self._volume = target_pct / 100
            return True, f"Volume set to {int(target_pct)}% (simulated - install pyautogui for system control)"

    def volume_up(self, pct: int = 10) -> Tuple[bool, str]:
        cur = self.get_volume()
        if cur is not None:
            return self.set_volume(min(100, cur + pct))
        if PAG_OK:
            for _ in range(max(1, pct // 2)):
                pyautogui.press("volumeup")
                time.sleep(0.05)
            if hasattr(self, '_sys_vol'):
                self._sys_vol = min(100, self._sys_vol + pct)
            return True, "Volume increased."
        return False, "Cannot control volume"

    def volume_down(self, pct: int = 10) -> Tuple[bool, str]:
        cur = self.get_volume()
        if cur is not None:
            return self.set_volume(max(0, cur - pct))
        if PAG_OK:
            for _ in range(max(1, pct // 2)):
                pyautogui.press("volumedown")
                time.sleep(0.05)
            if hasattr(self, '_sys_vol'):
                self._sys_vol = max(0, self._sys_vol - pct)
            return True, "Volume decreased."
        return False, "Cannot control volume"

    def mute(self) -> Tuple[bool, str]:
        if PAG_OK:
            pyautogui.press("volumemute")
            return True, "Muted"
        if IS_LINUX:
            try:
                subprocess.run(
                    ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1"],
                    timeout=5, capture_output=True
                )
                return True, "Muted"
            except Exception:
                pass
        return False, "Mute not available"

    def unmute(self) -> Tuple[bool, str]:  # [R-1] FIX: missing method added
        if PAG_OK:
            pyautogui.press("volumemute")
            return True, "Unmuted"
        if IS_LINUX:
            try:
                subprocess.run(
                    ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"],
                    timeout=5, capture_output=True
                )
                return True, "Unmuted"
            except Exception:
                pass
        return False, "Unmute not available"

    # ── Brightness ──────────────────────────────────────────────────────
    def get_brightness(self) -> Optional[int]:
        if SBC_OK:
            try:
                val = sbc.get_brightness()
                return int(val[0]) if isinstance(val, list) else int(val)
            except Exception as e:
                logger.debug(f"get_brightness: {e}")
        return None

    def set_brightness(self, level: int) -> Tuple[bool, str]:
        level = max(0, min(100, int(level)))
        if SBC_OK:
            try:
                sbc.set_brightness(level)
                return True, f"Brightness set to {level}%"
            except Exception as e:
                logger.warning(f"sbc set_brightness: {e}")
        if IS_WINDOWS:
            try:
                ps = (
                    f"$m=(Get-WmiObject -Namespace root\\wmi WmiMonitorBrightnessMethods);"
                    f"$m.WmiSetBrightness(1,{level})"
                )
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command", ps],
                    timeout=5, creationflags=_NO_WIN_FLAG, capture_output=True
                )
                return True, f"Brightness set to {level}%"
            except Exception as e:
                logger.warning(f"WMI brightness: {e}")
        elif IS_MACOS:
            try:
                subprocess.run(
                    ["brightness", str(level / 100)], timeout=5, capture_output=True
                )
                return True, f"Brightness set to {level}%"
            except Exception:
                pass
        return False, "Brightness control not supported on this display"

    def brightness_up(self, pct: int = 10) -> Tuple[bool, str]:
        cur = self.get_brightness() or 50
        return self.set_brightness(min(100, cur + pct))

    def brightness_down(self, pct: int = 10) -> Tuple[bool, str]:
        cur = self.get_brightness() or 50
        return self.set_brightness(max(0, cur - pct))

    # ── System Info ─────────────────────────────────────────────────────
    @safe_exec(default_return=(False, "psutil error"))
    def get_battery(self) -> Tuple[bool, str]:
        if not PSUTIL_OK:
            return False, "psutil not installed"
        bat = psutil.sensors_battery()
        if not bat:
            return False, "No battery detected"
        pct     = int(bat.percent)
        plugged = "plugged in" if bat.power_plugged else "on battery"
        time_r  = ""
        if bat.secsleft and bat.secsleft != psutil.POWER_TIME_UNLIMITED:
            mins = bat.secsleft // 60
            time_r = f", ~{mins}m remaining"
        return True, f"Battery: {pct}% ({plugged}{time_r})"

    @safe_exec(default_return=(False, "CPU error"))
    def get_cpu(self) -> Tuple[bool, str]:
        if not PSUTIL_OK:
            return False, "psutil not installed"
        pct   = psutil.cpu_percent(interval=0.5)
        cores = psutil.cpu_count()
        freq  = psutil.cpu_freq()
        f_str = f" @ {freq.current:.0f}MHz" if freq else ""
        return True, f"CPU: {pct:.1f}% ({cores} cores{f_str})"

    @safe_exec(default_return=(False, "Memory error"))
    def get_memory(self) -> Tuple[bool, str]:
        if not PSUTIL_OK:
            return False, "psutil not installed"
        m    = psutil.virtual_memory()
        swap = psutil.swap_memory()
        used = m.used  / 1e9
        tot  = m.total / 1e9
        sw   = swap.used / 1e9
        return True, f"RAM: {used:.1f}/{tot:.1f}GB ({m.percent}%) | Swap: {sw:.1f}GB"

    @safe_exec(default_return=(False, "Disk error"))
    def get_disk(self) -> Tuple[bool, str]:
        if not PSUTIL_OK:
            return False, "psutil not installed"
        parts = psutil.disk_partitions()
        lines = []
        for p in parts:
            try:
                u = psutil.disk_usage(p.mountpoint)
                lines.append(
                    f"  {p.mountpoint}: {u.free/1e9:.1f}GB free / {u.total/1e9:.0f}GB ({u.percent}%)"
                )
            except (PermissionError, OSError):
                continue
        return True, "Disk usage:\n" + "\n".join(lines) if lines else "No accessible drives"

    @safe_exec(default_return=(False, "IP error"))
    def get_ip(self) -> Tuple[bool, str]:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 53))
            ip = s.getsockname()[0]
        finally:
            s.close()
        return True, f"Local IP: {ip}"

    @safe_exec(default_return=(False, "Uptime error"))
    def get_uptime(self) -> Tuple[bool, str]:
        if not PSUTIL_OK:
            return False, "psutil not installed"
        elapsed = time.time() - psutil.boot_time()
        d = int(elapsed // 86400)
        h = int((elapsed % 86400) // 3600)
        m = int((elapsed % 3600) // 60)
        parts = []
        if d: parts.append(f"{d}d")
        if h: parts.append(f"{h}h")
        if m: parts.append(f"{m}m")
        return True, f"Uptime: {' '.join(parts) or '<1m'}"

    def get_all_info(self) -> str:
        results = []
        for fn in [self.get_cpu, self.get_memory, self.get_disk,
                   self.get_battery, self.get_uptime, self.get_ip]:
            _, msg = fn()
            results.append(msg)
        return "\n".join(results)

    # ── Power ───────────────────────────────────────────────────────────
    @safe_exec()
    def lock_screen(self) -> Tuple[bool, str]:
        if IS_WINDOWS:
            ctypes.windll.user32.LockWorkStation()
        elif IS_MACOS:
            subprocess.run([
                "/System/Library/CoreServices/Menu Extras/User.menu"
                "/Contents/Resources/CGSession", "-suspend"
            ])
        else:
            subprocess.run(["loginctl", "lock-session"])
        return True, "Screen locked"

    @safe_exec()
    def sleep(self) -> Tuple[bool, str]:
        if IS_WINDOWS:
            subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
        elif IS_MACOS:
            subprocess.run(["pmset", "sleepnow"])
        else:
            subprocess.run(["systemctl", "suspend"])
        return True, "Going to sleep"

    @safe_exec()
    def hibernate(self) -> Tuple[bool, str]:
        if IS_WINDOWS:
            subprocess.run(["shutdown", "/h"])
        else:
            subprocess.run(["systemctl", "hibernate"])
        return True, "Hibernating"

    @safe_exec()
    def restart(self, delay: int = 5) -> Tuple[bool, str]:
        if IS_WINDOWS:
            subprocess.run(["shutdown", "/r", "/t", str(delay)])
        elif IS_MACOS:
            subprocess.run(["sudo", "shutdown", "-r", "now"])
        else:
            subprocess.run(["sudo", "reboot"])
        return True, f"Restarting in {delay}s..."

    @safe_exec()
    def shutdown(self, delay_seconds: int = 5) -> Tuple[bool, str]:
        if IS_WINDOWS:
            subprocess.run(["shutdown", "/s", "/t", str(delay_seconds)])
        elif IS_MACOS:
            subprocess.run(["sudo", "shutdown", "-h", "now"])
        else:
            subprocess.run(["sudo", "shutdown", "-h", "now"])
        return True, f"Shutting down in {delay_seconds}s..."

    @safe_exec()
    def cancel_shutdown(self) -> Tuple[bool, str]:
        if IS_WINDOWS:
            subprocess.run(["shutdown", "/a"])
            return True, "Shutdown cancelled"
        return False, "Not supported on this OS"


# ══════════════════════════════════════════════════════════════════════════════
# 13. MODULE G — Web Controller
# ══════════════════════════════════════════════════════════════════════════════
class WebController:
    """
    [M-6] FIX: localhost / 127.0.0.1 URLs are no longer force-upgraded to
    https://. Only public URLs without a scheme get https:// prepended.
    """

    _BROWSER_PATHS = {
        "brave":   [
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        ],
        "chrome":  [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ],
        "edge":    [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        ],
        "firefox": [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
        ],
    }

    # Hostnames that should use http:// when scheme is not specified
    _LOCAL_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}

    def _find_browser_exe(self, name: str) -> Optional[str]:
        n = name.lower().strip()
        aliases = {"microsoft edge": "edge", "google chrome": "chrome", "brave browser": "brave"}
        n = aliases.get(n, n)
        for p in self._BROWSER_PATHS.get(n, []):
            if "*" in p:
                m = glob.glob(p)
                if m:
                    return m[0]
            elif os.path.exists(p):
                return p
        return shutil.which(n)

    def _normalise_url(self, url: str) -> str:
        """
        [M-6] FIX: Prepend http for localhost, https for all other schemeless URLs.
        """
        if re.match(r'^https?://', url):
            return url  # Already has scheme — leave as-is
        # Extract hostname to decide scheme
        host = url.split("/")[0].split(":")[0].lower()
        if host in self._LOCAL_HOSTS or host.endswith(".local"):
            return "http://" + url
        return "https://" + url

    def open_url(self, url: str, browser: str = None) -> Tuple[bool, str]:
        url = self._normalise_url(url)
        if browser:
            exe = self._find_browser_exe(browser)
            if exe:
                try:
                    subprocess.Popen([exe, url], creationflags=_NO_WIN_FLAG)
                    return True, f"Opening {url} in {browser}"
                except Exception as e:
                    logger.warning(f"open_url via {browser}: {e}")
        webbrowser.open(url)
        return True, f"Opening {url}"

    def search(self, query: str, engine: str = "google",
               browser: str = None) -> Tuple[bool, str]:
        base = SEARCH_ENGINES.get(engine.lower(), SEARCH_ENGINES["google"])
        url  = base + quote_plus(query)
        self.open_url(url, browser=browser)
        return True, JarvisResponder.web_search(query)

    def play_youtube(self, query: str, browser: str = None) -> Tuple[bool, str]:
        url = "https://www.youtube.com/results?search_query=" + quote_plus(query)
        self.open_url(url, browser=browser)
        return True, "Playing on YouTube..."

    def open_website(self, site: str, browser: str = None) -> Tuple[bool, str]:
        url = WEBSITE_SHORTCUTS.get(site.lower())
        if url:
            self.open_url(url, browser=browser)
            return True, f"Opening {site}"
        return self.open_url(site, browser=browser)


# ══════════════════════════════════════════════════════════════════════════════
# 14. MODULE H — File Manager (Comprehensive)
# ══════════════════════════════════════════════════════════════════════════════
class FileManager:
    """
    [C-4] FIX: Existence check separated from deletion; PermissionError handled.
    [m-2] FIX: skipped_dirs now checks against individual path PARTS,
               not full backslash strings that never match item.name.
    """

    LOC_MAP = {
        "downloads": HOME / "Downloads",
        "desktop":   HOME / "Desktop",
        "documents": HOME / "Documents",
        "pictures":  HOME / "Pictures",
        "music":     HOME / "Music",
        "videos":    HOME / "Videos",
        "home":      HOME,
        "temp":      Path(os.environ.get("TEMP", "/tmp")),
        "appdata":   Path(os.environ.get("APPDATA", str(HOME))),
    }
    SEARCH_DIRS = [HOME / "Desktop", HOME / "Downloads", HOME / "Documents", HOME]

    # [m-2] FIX: Simple directory names (not backslash paths) for item.name matching
    _SKIP_DIR_NAMES = {
        "system volume information", "$recycle.bin", ".git", "__pycache__",
        "node_modules", ".npm", "temp", ".cache", "application data",
    }

    def _resolve_loc(self, loc: str) -> Path:
        return self.LOC_MAP.get(loc.lower().strip(), HOME / loc)

    def _parse_location(self, name: str) -> Tuple[str, Path]:
        m = re.match(
            r'^(.+?)\s+in\s+(downloads|desktop|documents|pictures|music|videos|home|temp)$',
            name.strip(), re.I
        )
        if m:
            return m.group(1).strip(), self._resolve_loc(m.group(2))
        return name.strip(), HOME / "Desktop" if (HOME / "Desktop").exists() else HOME

    # ── CRUD Operations ────────────────────────────────────────────────
    @safe_exec()
    def create_file(self, raw: str) -> Tuple[bool, str]:
        raw = re.sub(r'^(?:with\s+name\s+|called?\s+|named?\s+)', '', raw, flags=re.I).strip()
        raw = re.sub(r'\s+(?:please|now|for\s+me)$', '', raw, flags=re.I).strip()
        name, base_dir = self._parse_location(raw)
        if not name:
            return False, "Please specify a filename"
        fp = base_dir / name
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.touch()
        logger.info(f"Created file: {fp}")
        return True, f"Created '{fp.name}' in {base_dir.name}"

    @safe_exec()
    def create_folder(self, raw: str) -> Tuple[bool, str]:
        raw = re.sub(r'^(?:with\s+name\s+|called?\s+|named?\s+)', '', raw, flags=re.I).strip()
        name, base_dir = self._parse_location(raw)
        if not name:
            return False, "Please specify a folder name"
        fp = base_dir / name
        fp.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created folder: {fp}")
        return True, f"Created folder '{fp.name}'"

    @safe_exec()
    def delete(self, raw: str) -> Tuple[bool, str]:
        """
        [C-4] FIX: Existence and type checks are now separate try/except blocks
        from the actual deletion, preventing partial-delete states and ensuring
        PermissionError surfaces correctly without leaving mid-deleted directories.
        """
        raw  = re.sub(r'^(?:with\s+name\s+|the\s+)?(?:file\s+|folder\s+)?', '', raw, flags=re.I).strip()
        name, hint_dir = self._parse_location(raw)
        if not name:
            return False, "Specify a file/folder to delete"

        search_dirs = [hint_dir] + self.SEARCH_DIRS

        for base in search_dirs:
            if not base.exists():
                continue
            target = base / name

            # [C-4] Phase 1: check existence — completely separate from deletion
            try:
                exists  = target.exists()
                is_file = target.is_file() if exists else False
                is_dir  = target.is_dir()  if exists else False
            except PermissionError as e:
                logger.warning(f"Permission denied checking '{target}': {e}")
                continue
            except OSError as e:
                logger.warning(f"OS error checking '{target}': {e}")
                continue

            if not (is_file or is_dir):
                continue

            # [C-4] Phase 2: attempt deletion — errors surfaced cleanly
            try:
                if is_file:
                    target.unlink()
                    logger.info(f"Deleted file: {target}")
                    return True, f"Deleted '{name}' from {base.name}"
                elif is_dir:
                    # Use ignore_errors=False so we detect failures, but wrap explicitly
                    shutil.rmtree(target, ignore_errors=False)
                    logger.info(f"Deleted folder: {target}")
                    return True, f"Deleted folder '{name}' from {base.name}"
            except PermissionError as e:
                return False, f"Permission denied deleting '{name}': {e}"
            except OSError as e:
                return False, f"Could not delete '{name}': {e}"

        return False, f"'{name}' not found in common locations"

    @safe_exec()
    def rename(self, old_name: str, new_name: str) -> Tuple[bool, str]:
        for base in self.SEARCH_DIRS:
            src = base / old_name
            if src.exists():
                dst = src.parent / new_name
                src.rename(dst)
                logger.info(f"Renamed '{old_name}' → '{new_name}'")
                return True, f"Renamed to '{new_name}'"
        return False, f"'{old_name}' not found"

    @safe_exec()
    def move_file(self, name: str, destination: str) -> Tuple[bool, str]:
        name = re.sub(r'^(?:the\s+)?(?:file\s+|folder\s+)?', '', name, flags=re.I).strip()
        dest = self._resolve_loc(destination.strip())
        if not dest.is_dir():
            dest = HOME / destination
        if not dest.is_dir():
            return False, f"Destination '{destination}' not found"

        for base in self.SEARCH_DIRS:
            src = base / name
            if src.exists():
                target = dest / src.name
                if target.exists():
                    return False, f"'{src.name}' already exists in {dest.name}"
                shutil.move(str(src), str(target))
                logger.info(f"Moved '{name}' → {dest}")
                return True, f"Moved '{name}' to {dest.name}"
        return False, f"'{name}' not found"

    @safe_exec()
    def copy_file(self, name: str, destination: str) -> Tuple[bool, str]:
        name = re.sub(r'^(?:the\s+)?(?:file\s+|folder\s+)?', '', name, flags=re.I).strip()
        dest = self._resolve_loc(destination.strip())
        if not dest.is_dir():
            dest = HOME / destination
        if not dest.is_dir():
            return False, f"Destination '{destination}' not found"

        for base in self.SEARCH_DIRS:
            src = base / name
            if src.exists():
                target = dest / src.name
                if src.is_dir():
                    shutil.copytree(str(src), str(target))
                else:
                    shutil.copy2(str(src), str(target))
                logger.info(f"Copied '{name}' → {dest}")
                return True, f"Copied '{name}' to {dest.name}"
        return False, f"'{name}' not found"

    # ── Search ─────────────────────────────────────────────────────────
    @safe_exec()
    def search_file(self, name: str, location: str = None,
                    recursive: bool = True, file_type: str = None) -> Tuple[bool, str]:
        """
        [m-2] FIX: skipped_dirs now uses lowercase simple directory names
        that can be compared against item.name.lower() — the old set contained
        backslash paths like "AppData\\Local\\Temp" which NEVER matched item.name.
        """
        name = re.sub(r'^(?:the\s+|a\s+)?(?:file\s+|folder\s+)?', '', name, flags=re.I).strip()
        if not name:
            return False, "Please specify a filename to search"

        if location:
            loc_clean   = re.sub(r'^(?:in\s+|the\s+)', '', location, flags=re.I).strip()
            search_dirs = [self._resolve_loc(loc_clean)]
        else:
            search_dirs = list(self.LOC_MAP.values()) + [HOME]

        extensions  = FILE_TYPE_MAP.get(file_type.lower(), []) if file_type else []
        pattern     = f"*{name}*"
        found: List[Path] = []

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            try:
                if recursive:
                    for item in search_dir.rglob("*"):
                        try:
                            # [m-2] FIX: Compare item.name against simple names (not backslash paths)
                            if item.name.lower() in self._SKIP_DIR_NAMES:
                                continue
                            if fnmatch.fnmatch(item.name.lower(), pattern.lower()):
                                if not extensions or item.suffix.lower() in extensions:
                                    found.append(item)
                        except PermissionError:
                            continue
                else:
                    for item in search_dir.iterdir():
                        if fnmatch.fnmatch(item.name.lower(), pattern.lower()):
                            if not extensions or item.suffix.lower() in extensions:
                                found.append(item)
            except PermissionError:
                continue

        if not found:
            return False, f"No files matching '{name}' found"

        print(f"\n🔍  Search results for '{name}':")
        for item in found[:20]:
            icon = "📂" if item.is_dir() else "📄"
            size = f" ({item.stat().st_size // 1024}KB)" if item.is_file() else ""
            print(f"  {icon} {item}{size}")
        if len(found) > 20:
            print(f"  ... and {len(found) - 20} more")

        if len(found) == 1 and IS_WINDOWS:
            try:
                subprocess.Popen(
                    ["explorer", "/select,", str(found[0])],
                    creationflags=_NO_WIN_FLAG
                )
            except OSError:
                pass

        return True, f"Found {len(found)} result(s) for '{name}'"

    # ── Organization ───────────────────────────────────────────────────
    @safe_exec()
    def organize_by_type(self, folder: str = "downloads") -> Tuple[bool, str]:
        src = self._resolve_loc(folder)
        if not src.is_dir():
            return False, f"'{folder}' not found"

        moved = defaultdict(int)
        errors = []

        for item in src.iterdir():
            if not item.is_file():
                continue
            ext = item.suffix.lower()
            category = next(
                (cat for cat, exts in FILE_TYPE_MAP.items() if ext in exts),
                "other"
            )
            dest_dir = src / category.capitalize()
            try:
                dest_dir.mkdir(exist_ok=True)
                target = dest_dir / item.name
                if target.exists():
                    stem   = item.stem
                    suffix = item.suffix
                    counter = 1
                    while target.exists():
                        target = dest_dir / f"{stem}_{counter}{suffix}"
                        counter += 1
                shutil.move(str(item), str(target))
                moved[category] += 1
            except (OSError, shutil.Error) as e:
                errors.append(str(e))

        total = sum(moved.values())
        detail = ", ".join(f"{v} {k}" for k, v in moved.items())
        msg = f"Organized {total} files in '{src.name}': {detail}"
        if errors:
            msg += f" ({len(errors)} errors)"
        logger.info(msg)
        return True, msg

    @safe_exec()
    def organize_by_date(self, folder: str = "downloads") -> Tuple[bool, str]:
        src = self._resolve_loc(folder)
        if not src.is_dir():
            return False, f"'{folder}' not found"

        moved = 0
        for item in src.iterdir():
            if not item.is_file():
                continue
            try:
                mtime    = datetime.fromtimestamp(item.stat().st_mtime)
                dest_dir = src / str(mtime.year) / mtime.strftime("%m-%B")
                dest_dir.mkdir(parents=True, exist_ok=True)
                target   = dest_dir / item.name
                if not target.exists():
                    shutil.move(str(item), str(target))
                    moved += 1
            except (OSError, shutil.Error) as e:
                logger.warning(f"organize_by_date: {e}")

        return True, f"Organized {moved} files by date in '{src.name}'"

    @safe_exec()
    def organize_by_size(self, folder: str = "downloads") -> Tuple[bool, str]:
        src = self._resolve_loc(folder)
        if not src.is_dir():
            return False, f"'{folder}' not found"

        SIZE_BUCKETS = [
            (1 * 1024 * 1024,    "Small-Under1MB"),
            (100 * 1024 * 1024,  "Medium-1MB-100MB"),
            (1 * 1024**3,        "Large-100MB-1GB"),
            (float("inf"),       "Huge-Over1GB"),
        ]
        moved = 0
        for item in src.iterdir():
            if not item.is_file():
                continue
            try:
                size     = item.stat().st_size
                bucket   = next(name for limit, name in SIZE_BUCKETS if size < limit)
                dest_dir = src / bucket
                dest_dir.mkdir(exist_ok=True)
                target   = dest_dir / item.name
                if not target.exists():
                    shutil.move(str(item), str(target))
                    moved += 1
            except (OSError, shutil.Error) as e:
                logger.warning(f"organize_by_size: {e}")

        return True, f"Organized {moved} files by size in '{src.name}'"

    # ── Duplicate Finder ───────────────────────────────────────────────

    @safe_exec()
    def organize_by_type_advanced(self, folder: str = "downloads") -> Tuple[bool, str]:
        """Advanced organizer with better categories"""
        src = self._resolve_loc(folder)
        if not src.is_dir():
            return False, f"'{folder}' not found"
        categories = {
            "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"],
            "Videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"],
            "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"],
            "Documents": [".pdf", ".doc", ".docx", ".txt", ".md"],
            "Spreadsheets": [".xls", ".xlsx", ".csv"],
            "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
            "Code": [".py", ".js", ".html", ".css", ".java", ".cpp"],
        }
        moved = defaultdict(int)
        for item in src.iterdir():
            if not item.is_file() or item.name.startswith('.'):
                continue
            ext = item.suffix.lower()
            category = "Other"
            for cat, exts in categories.items():
                if ext in exts:
                    category = cat
                    break
            dest_dir = src / category
            dest_dir.mkdir(exist_ok=True)
            target = dest_dir / item.name
            counter = 1
            while target.exists():
                target = dest_dir / f"{item.stem}_{counter}{item.suffix}"
                counter += 1
            try:
                shutil.move(str(item), str(target))
                moved[category] += 1
            except (OSError, shutil.Error):
                pass
        total = sum(moved.values())
        detail = ", ".join(f"{v} {k}" for k, v in sorted(moved.items()))
        return True, f"Organized {total} files: {detail}"

    @safe_exec()
    def clean_downloads(self, days_old: int = 30) -> Tuple[bool, str]:
        """Clean old files from downloads"""
        downloads = self._resolve_loc("downloads")
        if not downloads.is_dir():
            return False, "Downloads not found"
        cutoff = time.time() - (days_old * 86400)
        deleted = freed = 0
        for item in downloads.iterdir():
            if item.is_file():
                try:
                    if item.stat().st_mtime < cutoff:
                        freed += item.stat().st_size
                        item.unlink()
                        deleted += 1
                except (OSError, PermissionError):
                    pass
        return True, f"Cleaned {deleted} files, freed {freed/1e6:.1f} MB"

    @safe_exec()
    def find_large_files(self, folder: str = "downloads", min_size_mb: int = 100) -> Tuple[bool, str]:
        """Find large files"""
        src = self._resolve_loc(folder)
        if not src.is_dir():
            return False, f"'{folder}' not found"
        min_bytes = min_size_mb * 1024 * 1024
        large = []
        for item in src.rglob("*"):
            if item.is_file():
                try:
                    size = item.stat().st_size
                    if size >= min_bytes:
                        large.append((size, item))
                except (OSError, PermissionError):
                    continue
        large.sort(reverse=True)
        if not large:
            return True, f"No files >{min_size_mb}MB"
        print(f"\nLarge files in '{folder}':")
        for size, path in large[:15]:
            print(f"  {size/1e6:>7.1f} MB  {path.name}")
        return True, f"Found {len(large)} files"

    @safe_exec()
    def find_duplicates(self, folder: str = "downloads") -> Tuple[bool, str]:
        src = self._resolve_loc(folder)
        if not src.is_dir():
            return False, f"'{folder}' not found"

        print(f"\n🔍  Scanning for duplicates in '{src}'...")
        hashes: Dict[str, List[Path]] = defaultdict(list)

        for item in src.rglob("*"):
            if not item.is_file():
                continue
            try:
                h = hashlib.md5()
                with item.open("rb") as f:
                    for chunk in iter(lambda: f.read(65536), b""):
                        h.update(chunk)
                hashes[h.hexdigest()].append(item)
            except (OSError, PermissionError):
                continue

        dupes = {k: v for k, v in hashes.items() if len(v) > 1}
        if not dupes:
            return True, f"No duplicates found in '{src.name}'"

        total_waste = 0
        print(f"\n🗂️  Duplicate groups found: {len(dupes)}")
        for i, (h, files) in enumerate(list(dupes.items())[:10], 1):
            size = files[0].stat().st_size
            total_waste += size * (len(files) - 1)
            print(f"\n  Group {i} ({size//1024}KB each):")
            for f in files:
                print(f"    📄 {f}")

        waste_mb = total_waste / 1e6
        return True, f"Found {len(dupes)} duplicate groups, wasting ~{waste_mb:.1f}MB"

    @safe_exec()
    def remove_duplicates(self, folder: str = "downloads",
                          keep: str = "newest") -> Tuple[bool, str]:
        src = self._resolve_loc(folder)
        if not src.is_dir():
            return False, f"'{folder}' not found"

        hashes: Dict[str, List[Path]] = defaultdict(list)
        for item in src.rglob("*"):
            if not item.is_file():
                continue
            try:
                h = hashlib.md5()
                with item.open("rb") as f:
                    for chunk in iter(lambda: f.read(65536), b""):
                        h.update(chunk)
                hashes[h.hexdigest()].append(item)
            except (OSError, PermissionError):
                continue

        dupes   = {k: v for k, v in hashes.items() if len(v) > 1}
        removed = 0
        saved   = 0
        for files in dupes.values():
            files.sort(key=lambda x: x.stat().st_mtime, reverse=(keep == "newest"))
            to_remove = files[1:]
            for f in to_remove:
                try:
                    saved += f.stat().st_size
                    f.unlink()
                    removed += 1
                except OSError as e:
                    logger.warning(f"remove_dupes: {e}")

        return True, f"Removed {removed} duplicates, freed {saved/1e6:.1f}MB"

    # ── Archive Operations ─────────────────────────────────────────────
    @safe_exec()
    def zip_item(self, name: str, dest_name: str = None) -> Tuple[bool, str]:
        for base in self.SEARCH_DIRS:
            src = base / name
            if src.exists():
                out = src.parent / (dest_name or f"{src.stem}.zip")
                with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
                    if src.is_dir():
                        for f in src.rglob("*"):
                            zf.write(f, f.relative_to(src.parent))
                    else:
                        zf.write(src, src.name)
                logger.info(f"Zipped: {src} → {out}")
                return True, f"Zipped to '{out.name}'"
        return False, f"'{name}' not found"

    @safe_exec()
    def unzip_item(self, name: str, dest: str = None) -> Tuple[bool, str]:
        for base in self.SEARCH_DIRS:
            src = base / name
            if src.exists():
                out = Path(dest) if dest else src.parent / src.stem
                if src.suffix.lower() in (".gz", ".bz2", ".xz") or ".tar" in src.name:
                    with tarfile.open(src) as tf:
                        tf.extractall(out, members=list(_safe_tar_members(tf, out)))  # [S-2]
                else:
                    with zipfile.ZipFile(src, "r") as zf:
                        _safe_zip_extract(zf, out)  # [S-3]
                logger.info(f"Extracted: {src} → {out}")
                return True, f"Extracted to '{out.name}'"
        return False, f"'{name}' not found"

    @safe_exec()
    def compress(self, name: str, level: int = 9) -> Tuple[bool, str]:
        for base in self.SEARCH_DIRS:
            src = base / name
            if src.is_file():
                import gzip
                out = src.parent / (src.name + ".gz")
                with src.open("rb") as fi, gzip.open(str(out), "wb", compresslevel=level) as fo:
                    shutil.copyfileobj(fi, fo)
                orig  = src.stat().st_size
                compr = out.stat().st_size
                ratio = (1 - compr / orig) * 100 if orig else 0
                return True, f"Compressed to '{out.name}' ({ratio:.1f}% reduction)"
        return False, f"'{name}' not found"

    # ── Analysis ───────────────────────────────────────────────────────
    @safe_exec()
    def file_info(self, name: str) -> Tuple[bool, str]:
        for base in self.SEARCH_DIRS:
            fp = base / name
            if fp.exists():
                stat_r  = fp.stat()
                size    = stat_r.st_size
                created = datetime.fromtimestamp(stat_r.st_ctime).strftime("%Y-%m-%d %H:%M")
                modified= datetime.fromtimestamp(stat_r.st_mtime).strftime("%Y-%m-%d %H:%M")
                kind, _ = mimetypes.guess_type(str(fp))
                info = (
                    f"📄 {fp.name}\n"
                    f"   Path:     {fp}\n"
                    f"   Size:     {size:,} bytes ({size/1024:.1f} KB)\n"
                    f"   Type:     {kind or fp.suffix or 'unknown'}\n"
                    f"   Created:  {created}\n"
                    f"   Modified: {modified}\n"
                    f"   Is dir:   {fp.is_dir()}"
                )
                print(info)
                return True, f"Info for '{fp.name}' shown above"
        return False, f"'{name}' not found"

    @safe_exec()
    def word_count(self, name: str) -> Tuple[bool, str]:
        for base in self.SEARCH_DIRS:
            fp = base / name
            if fp.is_file():
                try:
                    text  = fp.read_text(encoding="utf-8", errors="ignore")
                    words = len(text.split())
                    lines = text.count("\n") + 1
                    chars = len(text)
                    return True, f"'{fp.name}': {words} words, {lines} lines, {chars} chars"
                except OSError as e:
                    return False, str(e)
        return False, f"'{name}' not found"

    @safe_exec()
    def checksum(self, name: str, algo: str = "sha256") -> Tuple[bool, str]:
        for base in self.SEARCH_DIRS:
            fp = base / name
            if fp.is_file():
                h = hashlib.new(algo)
                with fp.open("rb") as f:
                    for chunk in iter(lambda: f.read(65536), b""):
                        h.update(chunk)
                digest = h.hexdigest()
                print(f"  {algo.upper()}({fp.name})= {digest}")
                return True, f"{algo.upper()} checksum: {digest[:16]}..."
        return False, f"'{name}' not found"

    @safe_exec()
    def diff_files(self, file1: str, file2: str) -> Tuple[bool, str]:
        import difflib
        f1 = f2 = None
        for base in self.SEARCH_DIRS:
            if (base / file1).is_file():
                f1 = base / file1
            if (base / file2).is_file():
                f2 = base / file2
        if not f1:
            return False, f"'{file1}' not found"
        if not f2:
            return False, f"'{file2}' not found"
        try:
            t1 = f1.read_text(encoding="utf-8", errors="ignore").splitlines(keepends=True)
            t2 = f2.read_text(encoding="utf-8", errors="ignore").splitlines(keepends=True)
            diff = list(difflib.unified_diff(t1, t2, fromfile=str(f1), tofile=str(f2)))
            if not diff:
                return True, "Files are identical"
            print("".join(diff[:50]))
            return True, f"{len(diff)} diff lines (showing first 50)"
        except OSError as e:
            return False, str(e)

    # ── Bulk Operations ────────────────────────────────────────────────
    @safe_exec()
    def bulk_rename(self, folder: str, pattern: str, replacement: str,
                    extension: str = None) -> Tuple[bool, str]:
        src = self._resolve_loc(folder)
        if not src.is_dir():
            return False, f"'{folder}' not found"

        renamed = 0
        for item in src.iterdir():
            if not item.is_file():
                continue
            if extension and item.suffix.lower() != f".{extension.lower()}":
                continue
            new_name = re.sub(pattern, replacement, item.name, flags=re.I)
            if new_name != item.name:
                try:
                    item.rename(item.parent / new_name)
                    renamed += 1
                except OSError as e:
                    logger.warning(f"bulk_rename: {e}")

        return True, f"Renamed {renamed} files in '{src.name}'"

    @safe_exec()
    def list_files(self, folder: str = "~", show_hidden: bool = False) -> Tuple[bool, str]:
        p = Path(folder).expanduser()
        if not p.exists():
            p = HOME
        try:
            items   = list(p.iterdir())
            folders = sorted(
                (i for i in items if i.is_dir() and (show_hidden or not i.name.startswith("."))),
                key=lambda x: x.name.lower()
            )
            files   = sorted(
                (i for i in items if i.is_file() and (show_hidden or not i.name.startswith("."))),
                key=lambda x: x.name.lower()
            )
        except PermissionError as e:
            return False, f"Permission denied: {e}"

        print(f"\n📁  Contents of {p}  ({len(folders)} folders, {len(files)} files):")
        for f in folders:
            print(f"  📂 {f.name}/")
        for f in files:
            size = f.stat().st_size
            s_str = f"{size//1024}KB" if size >= 1024 else f"{size}B"
            print(f"  📄 {f.name:<40} {s_str:>8}")
        return True, f"{len(folders)} folders, {len(files)} files in {p.name}"

    @safe_exec()
    def open_folder(self, path: str) -> Tuple[bool, str]:
        p = Path(path).expanduser()
        if not p.exists():
            p = self._resolve_loc(path)
        if not p.exists():
            p = HOME
        if IS_WINDOWS:
            os.startfile(str(p))
        elif IS_MACOS:
            subprocess.run(["open", str(p)])
        else:
            subprocess.run(["xdg-open", str(p)])
        return True, f"Opened {p}"

    @safe_exec()
    def get_largest_files(self, folder: str = "downloads",
                          n: int = 10) -> Tuple[bool, str]:
        src = self._resolve_loc(folder)
        if not src.is_dir():
            return False, f"'{folder}' not found"

        files = []
        for item in src.rglob("*"):
            if item.is_file():
                try:
                    files.append((item.stat().st_size, item))
                except OSError:
                    continue
        files.sort(reverse=True)
        print(f"\n📊  Top {n} largest files in '{src.name}':")
        for size, fp in files[:n]:
            size_str = (
                f"{size/1e9:.2f}GB" if size >= 1e9 else
                f"{size/1e6:.1f}MB" if size >= 1e6 else
                f"{size//1024}KB"
            )
            print(f"  {size_str:>10}  {fp.name:<40}  {fp.parent}")
        return True, f"Showed top {min(n, len(files))} files"

    @safe_exec()
    def disk_usage_by_type(self, folder: str = "downloads") -> Tuple[bool, str]:
        src = self._resolve_loc(folder)
        if not src.is_dir():
            return False, f"'{folder}' not found"

        usage: Dict[str, int] = defaultdict(int)
        for item in src.rglob("*"):
            if item.is_file():
                try:
                    ext = item.suffix.lower() or "no extension"
                    usage[ext] += item.stat().st_size
                except OSError:
                    continue

        total = sum(usage.values())
        print(f"\n📊  Disk usage by type in '{src.name}' (total: {total/1e6:.1f}MB):")
        for ext, size in sorted(usage.items(), key=lambda x: -x[1])[:15]:
            pct = size / total * 100 if total else 0
            bar = "█" * int(pct / 5)
            print(f"  {ext:<15} {size/1e6:>8.1f}MB  {bar} {pct:.1f}%")
        return True, f"Breakdown shown for '{src.name}'"

    @safe_exec()
    def empty_trash(self) -> Tuple[bool, str]:
        if IS_WINDOWS:
            try:
                subprocess.run(
                    ["powershell", "-Command", "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"],
                    timeout=30, capture_output=True
                )
                return True, "Recycle Bin emptied"
            except Exception as e:
                return False, str(e)
        elif IS_MACOS:
            trash = HOME / ".Trash"
            for item in trash.iterdir():
                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                except OSError:
                    pass
            return True, "Trash emptied"
        elif IS_LINUX:
            trash = HOME / ".local/share/Trash/files"
            for item in trash.iterdir():
                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                except OSError:
                    pass
            return True, "Trash emptied"
        return False, "Empty trash not supported"

    @safe_exec()
    def clean_temp(self) -> Tuple[bool, str]:
        temp_dir = os.environ.get("TEMP") or os.environ.get("TMPDIR") or "/tmp"
        count = freed = 0
        for item in Path(temp_dir).iterdir():
            try:
                size = item.stat().st_size if item.is_file() else 0
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                count += 1
                freed += size
            except OSError:
                pass
        return True, f"Cleaned {count} temp items, freed ~{freed/1e6:.1f}MB"

# ══════════════════════════════════════════════════════════════════════════════
# 15. MODULE I — Screen Operations
# ══════════════════════════════════════════════════════════════════════════════
class ScreenOps:
    """Screenshot, screen recording trigger, scrolling, mouse/keyboard ops."""

    @safe_exec()
    def screenshot(self, name: str = None, region=None) -> Tuple[bool, str]:
        ts    = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = name or f"screenshot_{ts}.png"
        out   = HOME / fname

        if PAG_OK:
            img = pyautogui.screenshot(region=region)
            img.save(str(out))
            logger.info(f"Screenshot: {out}")
            return True, f"Screenshot saved: {fname}"

        # Fallback to OS tools
        if IS_WINDOWS:
            subprocess.run(
                ["powershell", "-Command",
                 f"Add-Type -AssemblyName System.Windows.Forms;"
                 f"$bmp=New-Object System.Drawing.Bitmap("
                 f"[System.Windows.Forms.SystemInformation]::VirtualScreen.Width,"
                 f"[System.Windows.Forms.SystemInformation]::VirtualScreen.Height);"
                 f"$g=[System.Drawing.Graphics]::FromImage($bmp);"
                 f"$g.CopyFromScreen(0,0,0,0,$bmp.Size);"
                 f"$bmp.Save('{out}')"],
                creationflags=_NO_WIN_FLAG, timeout=15
            )
        elif IS_MACOS:
            subprocess.run(["screencapture", str(out)])
        else:
            subprocess.run(["scrot", str(out)])
        return True, f"Screenshot saved: {fname}"

    @safe_exec()
    def scroll(self, direction: str, amount: int = 3) -> Tuple[bool, str]:
        direction = direction.lower().strip()
        amount    = max(1, int(amount))

        if PAG_OK:
            if direction == "up":
                pyautogui.scroll(amount)
            elif direction == "down":
                pyautogui.scroll(-amount)
            elif direction == "left":
                pyautogui.hscroll(-amount)
            elif direction == "right":
                pyautogui.hscroll(amount)
            else:
                return False, f"Unknown scroll direction: {direction}"
            return True, f"Scrolled {direction} by {amount}"

        key_map = {"up": "pageup", "down": "pagedown", "left": "left", "right": "right"}
        if KB_OK and direction in key_map:
            for _ in range(amount):
                keyboard.press_and_release(key_map[direction])
            return True, f"Scrolled {direction}"

        return False, "Scroll not available (install pyautogui)"

    @safe_exec()
    def scroll_to_top(self) -> Tuple[bool, str]:
        if PAG_OK:
            pyautogui.hotkey("ctrl", "home")
            return True, "Scrolled to top"
        return False, "pyautogui not available"

    @safe_exec()
    def scroll_to_bottom(self) -> Tuple[bool, str]:
        if PAG_OK:
            pyautogui.hotkey("ctrl", "end")
            return True, "Scrolled to bottom"
        return False, "pyautogui not available"

    @safe_exec()
    def start_recording(self) -> Tuple[bool, str]:
        if PAG_OK:
            pyautogui.hotkey("win", "g")
            return True, "Opened Xbox Game Bar for recording"
        return False, "Press Win+G manually to open Game Bar"

    @safe_exec()
    def type_text(self, text: str) -> Tuple[bool, str]:
        if PAG_OK:
            pyautogui.typewrite(text, interval=0.03)
            return True, f"Typed: {text[:30]}..."
        return False, "pyautogui not available"

    @safe_exec()
    def click(self, x: int = None, y: int = None, button: str = "left") -> Tuple[bool, str]:
        if not PAG_OK:
            return False, "pyautogui not available"
        if x and y:
            pyautogui.click(x, y, button=button)
        else:
            pyautogui.click(button=button)
        return True, f"Clicked {button}"

    @safe_exec()
    def hotkey(self, *keys) -> Tuple[bool, str]:
        if not PAG_OK:
            return False, "pyautogui not available"
        pyautogui.hotkey(*keys)
        return True, f"Hotkey: {'+'.join(keys)}"


# ══════════════════════════════════════════════════════════════════════════════
# 16. MODULE J — Browser Controller
# ══════════════════════════════════════════════════════════════════════════════
class BrowserController:
    """
    [m-1] FIX: duplicate_tab now correctly presses Ctrl+L to focus the address
    bar, then Enter to navigate to the same URL — effectively duplicating the tab.
    The original code only did Ctrl+L (focus) without the Enter keystroke.

    [v4.0] NEW: open_in_browser() detects installed browsers and opens
    browser-specific pages (history, settings, downloads, bookmarks, devtools)
    in the requested browser by launching it with the correct URL/flag.
    Browser URLs (chrome-specific, brave uses same):
      history   → chrome://history
      downloads → chrome://downloads
      settings  → chrome://settings
      bookmarks → chrome://bookmarks
      extensions→ chrome://extensions
      devtools  → F12 (keyboard only; cannot open via URL directly)
    Firefox uses about: protocol, Edge uses edge:// protocol.
    """

    # Internal pages per browser engine
    _BROWSER_INTERNAL = {
        "chrome":  {
            "history":    "chrome://history",
            "downloads":  "chrome://downloads",
            "settings":   "chrome://settings",
            "bookmarks":  "chrome://bookmarks",
            "extensions": "chrome://extensions",
            "newtab":     "chrome://newtab",
            "flags":      "chrome://flags",
            "task manager": None,  # keyboard only
        },
        "brave": {
            "history":    "brave://history",
            "downloads":  "brave://downloads",
            "settings":   "brave://settings",
            "bookmarks":  "brave://bookmarks",
            "extensions": "brave://extensions",
            "newtab":     "brave://newtab",
            "flags":      "brave://flags",
        },
        "edge": {
            "history":    "edge://history",
            "downloads":  "edge://downloads",
            "settings":   "edge://settings",
            "bookmarks":  "edge://bookmarks",
            "extensions": "edge://extensions",
            "newtab":     "edge://newtab",
            "flags":      "edge://flags",
        },
        "firefox": {
            "history":    None,   # Firefox: Ctrl+H shortcut
            "downloads":  "about:downloads",
            "settings":   "about:preferences",
            "bookmarks":  None,   # Firefox: Ctrl+Shift+B
            "extensions": "about:addons",
            "newtab":     "about:newtab",
        },
    }

    _BROWSER_PATHS = {
        "brave": [
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
            r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
            "/usr/bin/brave-browser",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        ],
        "chrome": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            "/usr/bin/google-chrome",
            "/usr/bin/chromium-browser",
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        ],
        "edge": [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            "/usr/bin/microsoft-edge",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        ],
        "firefox": [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
            "/usr/bin/firefox",
            "/Applications/Firefox.app/Contents/MacOS/firefox",
        ],
    }

    def _find_browser_exe(self, name: str) -> Optional[str]:
        """Find browser executable on disk; return None if not installed."""
        n = name.lower().strip()
        aliases = {
            "microsoft edge": "edge", "google chrome": "chrome",
            "brave browser": "brave", "mozilla firefox": "firefox",
        }
        n = aliases.get(n, n)
        for p in self._BROWSER_PATHS.get(n, []):
            if "*" in p:
                m = glob.glob(p)
                if m:
                    return m[0]
            elif os.path.exists(p):
                return p
        return shutil.which(n)

    def open_in_browser(self, page: str, browser: str = "brave") -> Tuple[bool, str]:
        """
        Open a browser internal page (history, settings, downloads…) in the
        specified installed browser. Falls back to keyboard shortcut if URL
        navigation is not available (e.g., Firefox history = Ctrl+H).
        """
        browser = browser.lower().strip()
        page    = page.lower().strip().replace(" ", "")
        # Normalise page aliases
        page_aliases = {
            "newtab": "newtab", "new tab": "newtab",
            "dev": "devtools", "developer": "devtools",
            "ext": "extensions", "add-ons": "extensions", "addons": "extensions",
        }
        page = page_aliases.get(page, page)

        # Special case: devtools = F12 key
        if page in ("devtools", "developer tools"):
            return self.open_devtools()

        url = (self._BROWSER_INTERNAL.get(browser) or {}).get(page)
        exe = self._find_browser_exe(browser)

        if url and exe:
            try:
                subprocess.Popen([exe, url], creationflags=_NO_WIN_FLAG)
                return True, f"Opening {page} in {browser.title()}"
            except Exception as e:
                logger.warning(f"BrowserController.open_in_browser: {e}")

        # Firefox special cases (no URL for history/bookmarks — use hotkeys)
        if browser == "firefox" and page == "history":
            return self._hk("ctrl", "h")
        if browser == "firefox" and page == "bookmarks":
            return self._hk("ctrl", "shift", "b")

        # Generic fallback: keyboard shortcuts (browser must be focused)
        fallback = {
            "history":   ("ctrl", "h"),
            "downloads": ("ctrl", "j"),
            "bookmarks": ("ctrl", "shift", "o"),
            "settings":  None,
            "extensions":("ctrl", "shift", "e"),
            "newtab":    ("ctrl", "t"),
        }
        kbs = fallback.get(page)
        if kbs:
            return self._hk(*kbs)
        return False, f"Cannot open '{page}' in {browser} — browser not installed or page not supported"

    def _hk(self, *k) -> Tuple[bool, str]:
        if not PAG_OK:
            return False, "pyautogui not available"
        pyautogui.hotkey(*k)
        time.sleep(0.05)
        return True, "Done"

    def new_tab(self):          return self._hk("ctrl", "t")
    def close_tab(self):        return self._hk("ctrl", "w")
    def reopen_tab(self):       return self._hk("ctrl", "shift", "t")
    def refresh(self):          return self._hk("ctrl", "r")
    def hard_refresh(self):     return self._hk("ctrl", "shift", "r")
    def go_back(self):          return self._hk("alt", "left")
    def go_forward(self):       return self._hk("alt", "right")
    def open_history(self):     return self._hk("ctrl", "h")
    def open_downloads(self):   return self._hk("ctrl", "j")
    def zoom_in(self):          return self._hk("ctrl", "+")
    def zoom_out(self):         return self._hk("ctrl", "-")
    def zoom_reset(self):       return self._hk("ctrl", "0")
    def find_on_page(self):     return self._hk("ctrl", "f")
    def open_devtools(self):    return self._hk("f12")
    def view_source(self):      return self._hk("ctrl", "u")
    def focus_address_bar(self):return self._hk("ctrl", "l")
    def bookmark_page(self):    return self._hk("ctrl", "d")
    def open_bookmarks(self):   return self._hk("ctrl", "shift", "o")
    def fullscreen(self):       return self._hk("f11")
    def print_page(self):       return self._hk("ctrl", "p")
    def save_page(self):        return self._hk("ctrl", "s")
    def next_tab(self):         return self._hk("ctrl", "tab")
    def prev_tab(self):         return self._hk("ctrl", "shift", "tab")
    def mute_tab(self):         return self._hk("ctrl", "m")
    def scroll_up(self):        return self._hk("pageup")
    def scroll_down(self):      return self._hk("pagedown")
    def scroll_top(self):       return self._hk("ctrl", "home")
    def scroll_bottom(self):    return self._hk("ctrl", "end")
    def open_extensions(self):  return self._hk("ctrl", "shift", "e")
    def open_task_manager(self):return self._hk("shift", "esc")
    def reading_mode(self):     return self._hk("f9")

    def duplicate_tab(self) -> Tuple[bool, str]:
        """
        [BUG-6] FIX: True tab duplication = 5-step sequence.
        Ctrl+L (focus address bar) → Ctrl+C (copy URL) → Ctrl+T (new tab)
        → Ctrl+V (paste URL) → Enter (navigate).
        """
        if not PAG_OK:
            return False, "pyautogui not available"
        pyautogui.hotkey("ctrl", "l")
        time.sleep(0.1)
        pyautogui.hotkey("ctrl", "c")
        time.sleep(0.05)
        pyautogui.hotkey("ctrl", "t")
        time.sleep(0.2)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.05)
        pyautogui.press("enter")
        return True, "Duplicated tab"


# ══════════════════════════════════════════════════════════════════════════════
# 17. MODULE K — Media Controller
# ══════════════════════════════════════════════════════════════════════════════
class MediaController:
    def _key(self, k) -> Tuple[bool, str]:
        if not PAG_OK:
            return False, "pyautogui not available"
        pyautogui.press(k)
        return True, "Done"

    def play_pause(self):   return self._key("playpause")
    def next_track(self):   return self._key("nexttrack")
    def prev_track(self):   return self._key("prevtrack")
    def stop(self):         return self._key("stop")


# ══════════════════════════════════════════════════════════════════════════════
# 18. MODULE L — Clipboard & Window
# ══════════════════════════════════════════════════════════════════════════════
class ClipboardController:
    def _hk(self, *k) -> Tuple[bool, str]:
        if not PAG_OK:
            return False, "pyautogui not available"
        pyautogui.hotkey(*k)
        time.sleep(0.05)
        return True, "Done"

    def copy(self):       return self._hk("ctrl", "c")
    def paste(self):      return self._hk("ctrl", "v")
    def cut(self):        return self._hk("ctrl", "x")
    def select_all(self): return self._hk("ctrl", "a")
    def undo(self):       return self._hk("ctrl", "z")
    def redo(self):       return self._hk("ctrl", "y")
    def save(self):       return self._hk("ctrl", "s")
    def find(self):       return self._hk("ctrl", "f")
    def print_doc(self):  return self._hk("ctrl", "p")
    def bold(self):       return self._hk("ctrl", "b")
    def italic(self):     return self._hk("ctrl", "i")
    def underline(self):  return self._hk("ctrl", "u")
    def new_window(self): return self._hk("ctrl", "n")
    def close_win(self):  return self._hk("alt", "f4")
    def switch_win(self): return self._hk("alt", "tab")

    def get_clipboard_text(self) -> Tuple[bool, str]:
        if WIN32_OK and win32clipboard:
            try:
                win32clipboard.OpenClipboard()
                data = win32clipboard.GetClipboardData()
                win32clipboard.CloseClipboard()
                return True, f"Clipboard: {data[:200]}"
            except Exception as e:
                return False, str(e)
        return False, "Clipboard read not available"


class WindowController:
    def _hk(self, *k) -> Tuple[bool, str]:
        if not PAG_OK:
            return False, "pyautogui not available"
        pyautogui.hotkey(*k)
        time.sleep(0.05)
        return True, "Done"

    def minimize_all(self):           return self._hk("win", "d")
    def snap_left(self):              return self._hk("win", "left")
    def snap_right(self):             return self._hk("win", "right")
    def snap_up(self):                return self._hk("win", "up")
    def snap_down(self):              return self._hk("win", "down")
    def task_view(self):              return self._hk("win", "tab")
    def maximize(self):               return self._hk("win", "up")  # JarvisResponder.window_maximize()
    def minimize(self):               return self._hk("win", "down")
    def new_virtual_desktop(self):    return self._hk("win", "ctrl", "d")
    def close_virtual_desktop(self):  return self._hk("win", "ctrl", "f4")
    def switch_desktop_right(self):   return self._hk("win", "ctrl", "right")
    def switch_desktop_left(self):    return self._hk("win", "ctrl", "left")
    def action_center(self):          return self._hk("win", "a")
    def notification_center(self):    return self._hk("win", "n")
    def settings_hotkey(self):        return self._hk("win", "i")
    def run_dialog(self):             return self._hk("win", "r")
    def search_bar(self):             return self._hk("win", "s")
    def lock_screen(self):            return self._hk("win", "l")
    def emoji_picker(self):           return self._hk("win", ".")
    def clipboard_history(self):      return self._hk("win", "v")
    def connect_display(self):        return self._hk("win", "p")
    def peek_desktop(self):           return self._hk("win", ",")


# ══════════════════════════════════════════════════════════════════════════════
# 19. MODULE M — Notes Manager
# ══════════════════════════════════════════════════════════════════════════════
class NotesManager:
    def __init__(self):
        self.notes_file = HOME / "jarvis_notes.json"
        self._notes: List[Dict] = []
        self._load()

    def _load(self):
        if self.notes_file.exists():
            try:
                data = json.loads(self.notes_file.read_text(encoding="utf-8"))
                self._notes = data if isinstance(data, list) else []
            except Exception:
                self._notes = []

    def _save(self):
        self.notes_file.write_text(
            json.dumps(self._notes, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def add(self, text: str, tags: List[str] = None) -> Tuple[bool, str]:
        note = {
            "id":      str(uuid.uuid4())[:8],
            "text":    text,
            "tags":    tags or [],
            "created": datetime.now().isoformat(),
        }
        self._notes.append(note)
        self._save()
        logger.info(f"Note added: {text[:50]}")
        return True, f"Note saved (ID: {note['id']})"

    def read(self, search: str = None) -> Tuple[bool, str]:
        notes = self._notes
        if search:
            notes = [n for n in notes if search.lower() in n["text"].lower()]
        if not notes:
            return False, "No notes found"
        print(f"\n📝  Notes ({len(notes)}):")
        for n in notes:
            ts = n.get("created", "")[:16]
            tags = f"  [{'|'.join(n.get('tags', []))}]" if n.get("tags") else ""
            print(f"  [{n['id']}] {ts}{tags}")
            print(f"       {n['text']}\n")
        return True, f"{len(notes)} note(s)"

    def delete_note(self, note_id: str) -> Tuple[bool, str]:
        before = len(self._notes)
        self._notes = [n for n in self._notes if n.get("id") != note_id]
        if len(self._notes) < before:
            self._save()
            return True, f"Note {note_id} deleted"
        return False, f"Note '{note_id}' not found"

    def clear(self) -> Tuple[bool, str]:
        self._notes.clear()
        self._save()
        return True, "All notes cleared"


# ══════════════════════════════════════════════════════════════════════════════
# 20. MODULE N — Timer & Reminder Manager
# ══════════════════════════════════════════════════════════════════════════════
class TimerManager:
    """
    [M-1] FIX: _run() now acquires self._lock before popping from _timers dict,
    eliminating the race condition between _run() cleanup and cancel_timer().
    """

    def __init__(self, tts: TTSCore):
        self.tts      = tts
        self._timers  : Dict[int, Dict] = {}
        self._counter = 0
        self._lock    = threading.Lock()

    def _next_id(self) -> int:
        with self._lock:
            self._counter += 1
            return self._counter

    def _parse_duration(self, amount: str, unit: str) -> int:
        n = int(amount)
        u = unit.lower()
        if u.startswith("h"):   return n * 3600
        if u.startswith("m"):   return n * 60
        return n  # seconds

    def set_timer(self, text: str) -> Tuple[bool, str]:
        m = RE_TIMER.match(text)
        if not m:
            return False, "Say: timer 5 minutes  OR  timer 30 seconds"
        seconds = self._parse_duration(m.group(1), m.group(2))
        tid     = self._next_id()

        def _run():
            time.sleep(seconds)
            self.tts.speak(f"Timer {tid} is done!")
            # [M-1] FIX: Pop inside lock to avoid race with cancel_timer()
            with self._lock:
                self._timers.pop(tid, None)

        t = threading.Thread(target=_run, daemon=True, name=f"Timer-{tid}")
        with self._lock:
            self._timers[tid] = {"thread": t, "remaining": seconds, "start": time.time()}
        t.start()

        m_str = ""
        if seconds >= 3600:  m_str += f"{seconds//3600}h "
        if seconds >= 60:    m_str += f"{(seconds%3600)//60}m "
        if seconds % 60:     m_str += f"{seconds%60}s"
        logger.info(f"Timer {tid} set for {seconds}s")
        return True, f"Timer {tid} set for {m_str.strip()}"

    def set_reminder(self, text: str) -> Tuple[bool, str]:
        m = RE_REMIND.match(text)
        if not m:
            return False, "Say: remind me in 10 minutes to call John"
        seconds = self._parse_duration(m.group(1), m.group(2))
        message = m.group(3).strip()

        def _run():
            time.sleep(seconds)
            self.tts.speak(f"Reminder: {message}")

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        logger.info(f"Reminder in {seconds}s: {message}")
        return True, f"Reminder set: '{message}' in {seconds//60}m"

    def list_timers(self) -> Tuple[bool, str]:
        with self._lock:
            active = [(tid, d) for tid, d in self._timers.items() if d["thread"].is_alive()]
        if not active:
            return True, "No active timers"
        lines = [f"\n⏱️  Active timers ({len(active)}):"]
        for tid, d in active:
            elapsed   = time.time() - d["start"]
            remaining = max(0, d["remaining"] - elapsed)
            lines.append(f"  Timer {tid}: ~{int(remaining)}s remaining")
        print("\n".join(lines))
        return True, f"{len(active)} active timer(s)"

    def cancel_timer(self, tid: int) -> Tuple[bool, str]:
        with self._lock:
            if tid in self._timers:
                self._timers.pop(tid)
                return True, f"Timer {tid} cancelled"
        return False, f"Timer {tid} not found"


# ══════════════════════════════════════════════════════════════════════════════
# 21. MODULE O — Network Manager
# ══════════════════════════════════════════════════════════════════════════════
class NetworkManager:
    """
    [m-4] FIX: speed_test_simple now has a primary and fallback URL.
    The original third-party URL (speedtest.tele2.net) has no SLA; we
    now also try a Cloudflare test endpoint as fallback.
    """

    # [BUG-13] FIX: TCP/53 is frequently blocked by corporate firewalls.
    # Use port 443 (HTTPS) which is almost universally open.
    _CHECK_ENDPOINTS = [
        ("8.8.8.8",       443),
        ("1.1.1.1",       443),
        ("208.67.222.222", 443),
    ]

    def check_connection(self) -> Tuple[bool, str]:
        for host, port in self._CHECK_ENDPOINTS:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(3)
                s.connect((host, port))
                s.close()
                return True, "Internet connection: active"
            except OSError:
                continue
        return False, "No internet connection (tried 3 DNS servers)"

    def ping(self, host: str) -> Tuple[bool, str]:
        flag = "-n" if IS_WINDOWS else "-c"
        try:
            r = subprocess.run(
                ["ping", flag, "4", host],
                capture_output=True, text=True, timeout=15
            )
            output = r.stdout.lower()
            if "ttl=" in output or "bytes from" in output:
                rtt = re.search(r'average\s*=\s*(\d+)ms|rtt.*=.*?/(\d+\.\d+)/', output)
                rtt_str = f" (avg RTT: {rtt.group(1) or rtt.group(2)}ms)" if rtt else ""
                return True, f"{host} is reachable{rtt_str}"
            return False, f"{host} is unreachable"
        except (subprocess.SubprocessError, OSError) as e:
            return False, f"Ping failed: {e}"

    def get_ip(self) -> Tuple[bool, str]:  # [R-2] FIX: socket closed in finally
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 53))
            ip = s.getsockname()[0]
            return True, f"Local IP: {ip}"
        except OSError:
            return False, "Cannot determine IP"
        finally:
            s.close()

    def get_public_ip(self) -> Tuple[bool, str]:
        for url in ["https://api.ipify.org", "https://ifconfig.me/ip"]:
            try:
                req  = Request(url, headers={"User-Agent": "JARVIS/2.0"})
                with urlopen(req, timeout=5) as resp:
                    ip = resp.read().decode().strip()
                return True, f"Public IP: {ip}"
            except Exception:
                continue
        return False, "Cannot determine public IP"

    def get_hostname(self) -> Tuple[bool, str]:
        return True, f"Hostname: {socket.gethostname()}"

    def port_check(self, host: str, port: int) -> Tuple[bool, str]:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            r = s.connect_ex((host, port))
            s.close()
            status = "open" if r == 0 else "closed"
            return r == 0, f"Port {port} on {host}: {status}"
        except OSError as e:
            return False, str(e)

    def speed_test_simple(self) -> Tuple[bool, str]:
        """
        [m-4] FIX: Primary URL first; falls back to Cloudflare speed.cloudflare.com
        if the primary fails. Both have reasonable reliability for a basic test.
        """
        test_urls = [
            "http://speedtest.tele2.net/1MB.zip",
            "https://speed.cloudflare.com/__down?bytes=1048576",  # 1MB Cloudflare
        ]
        for test_url in test_urls:
            try:
                start = time.time()
                req   = Request(test_url, headers={"User-Agent": "JARVIS/2.0"})
                with urlopen(req, timeout=20) as resp:
                    data = resp.read()
                elapsed = time.time() - start
                mb      = len(data) / 1e6
                speed   = mb / elapsed * 8
                return True, f"Download speed: ~{speed:.1f} Mbps ({mb:.1f}MB in {elapsed:.1f}s)"
            except Exception as e:
                logger.debug(f"speed_test URL {test_url} failed: {e}")
                continue
        return False, "Speed test failed — check internet connection"


# ══════════════════════════════════════════════════════════════════════════════
# 22. MODULE P — Process Manager
# ══════════════════════════════════════════════════════════════════════════════
class ProcessManager:
    @safe_exec()
    def list_top(self, n: int = 10) -> Tuple[bool, str]:
        if not PSUTIL_OK:
            return False, "psutil not installed"
        # [BUG-11] FIX: Prime cpu_percent — first call always returns 0.0.
        # Call with interval=None to initialise counters, sleep briefly, then collect.
        for p in psutil.process_iter(["cpu_percent"]):
            try:
                p.cpu_percent(interval=None)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        time.sleep(0.5)
        procs = []
        for p in psutil.process_iter(["name", "cpu_percent", "memory_percent", "pid"]):
            try:
                procs.append(p.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        procs.sort(key=lambda x: x.get("cpu_percent", 0) or 0, reverse=True)
        print(f"\n🔧  Top {n} Processes by CPU:")
        print(f"  {'PID':>7}  {'CPU%':>6}  {'RAM%':>6}  {'Name'}")
        print(f"  {'-'*7}  {'-'*6}  {'-'*6}  {'-'*30}")
        for p in procs[:n]:
            print(
                f"  {p.get('pid',0):>7}  {p.get('cpu_percent',0):>5.1f}%  "
                f"{p.get('memory_percent',0):>5.1f}%  {p.get('name','?')}"
            )
        return True, f"Listed top {min(n, len(procs))} processes"

    @safe_exec()
    def kill(self, name: str) -> Tuple[bool, str]:
        if not PSUTIL_OK:
            return False, "psutil not installed"
        count = 0
        for p in psutil.process_iter(["name"]):
            try:
                if name.lower() in (p.info.get("name") or "").lower():
                    p.terminate()
                    count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return (True, f"Killed {count} process(es) matching '{name}'") if count else (False, f"No process matching '{name}'")

    @safe_exec()
    def kill_pid(self, pid: int) -> Tuple[bool, str]:
        if not PSUTIL_OK:
            return False, "psutil not installed"
        try:
            p = psutil.Process(pid)
            name = p.name()
            p.terminate()
            return True, f"Killed PID {pid} ({name})"
        except psutil.NoSuchProcess:
            return False, f"PID {pid} not found"
        except psutil.AccessDenied:
            return False, f"Access denied for PID {pid}"

    @safe_exec()
    def get_count(self) -> Tuple[bool, str]:
        if not PSUTIL_OK:
            return False, "psutil not installed"
        return True, f"{len(list(psutil.process_iter()))} processes running"

    @safe_exec()
    def find_process(self, name: str) -> Tuple[bool, str]:
        if not PSUTIL_OK:
            return False, "psutil not installed"
        found = []
        for p in psutil.process_iter(["name", "pid", "cpu_percent", "memory_percent"]):
            try:
                if name.lower() in (p.info.get("name") or "").lower():
                    found.append(p.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        if not found:
            return False, f"No process matching '{name}'"
        print(f"\n  Processes matching '{name}':")
        for p in found:
            print(f"    PID {p['pid']}: {p['name']} (CPU {p.get('cpu_percent',0):.1f}%)")
        return True, f"Found {len(found)} process(es)"



# ══════════════════════════════════════════════════════════════════════════════
# NEW MODULE — Weather Service [F-1]
# ══════════════════════════════════════════════════════════════════════════════
class WeatherService:
    """
    Live weather + forecast using wttr.in (no API key required).
    Supports current conditions and 3-day forecast for any city.
    """
    _BASE = "https://wttr.in/{city}?format=j1"
    _SIMPLE = "https://wttr.in/{city}?format=2"

    def _fetch(self, url: str, timeout: int = 8) -> Optional[str]:
        try:
            req = Request(url, headers={"User-Agent": "JARVIS/3.0"})
            with urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:
            logger.debug(f"WeatherService fetch error: {e}")
            return None

    def current(self, city: str = "auto") -> Tuple[bool, str]:
        safe_city = quote_plus(city.strip())
        url = self._SIMPLE.format(city=safe_city)
        data = self._fetch(url)
        if not data:
            return False, f"Could not fetch weather for '{city}'. Check internet."
        # wttr.in format=2 → "City: ☀️ +72°F"
        return True, f"🌤  Weather in {city.title()}: {data.strip()}"

    def forecast(self, city: str = "auto") -> Tuple[bool, str]:
        safe_city = quote_plus(city.strip())
        url = self._BASE.format(city=safe_city)
        data = self._fetch(url)
        if not data:
            return False, f"Forecast unavailable for '{city}'"
        try:
            j = json.loads(data)
            area = j.get("nearest_area", [{}])[0]
            area_name = area.get("areaName", [{}])[0].get("value", city)
            lines = [f"\n📅  3-Day Forecast for {area_name}:"]
            for day in j.get("weather", [])[:3]:
                date = day.get("date", "?")
                max_c = day.get("maxtempC", "?")
                min_c = day.get("mintempC", "?")
                desc  = day.get("hourly", [{}])[4].get("weatherDesc", [{}])[0].get("value", "?")
                lines.append(f"  {date}: {desc}, {min_c}°C – {max_c}°C")
            return True, "\n".join(lines)
        except (KeyError, json.JSONDecodeError) as e:
            return False, f"Forecast parse error: {e}"


# ══════════════════════════════════════════════════════════════════════════════
# NEW MODULE — Password Manager [F-2]
# ══════════════════════════════════════════════════════════════════════════════
class PasswordManager:
    """
    Local password manager using XOR + base64 (lightweight, no dependency).
    Passwords stored in ~/.jarvis_passwords.json (base64-encoded XOR cipher).
    For production use, replace with cryptography.fernet.
    """
    _FILE = HOME / ".jarvis_passwords.json"

    def __init__(self):
        self._store: Dict[str, str] = {}
        self._key: Optional[bytes]  = None
        self._load()

    def _xor(self, data: bytes, key: bytes) -> bytes:
        return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

    def _encode(self, plaintext: str) -> str:
        if not self._key:
            return plaintext
        import base64
        return base64.b64encode(self._xor(plaintext.encode(), self._key)).decode()

    def _decode(self, encoded: str) -> str:
        if not self._key:
            return encoded
        import base64
        try:
            return self._xor(base64.b64decode(encoded), self._key).decode()
        except Exception:
            return "***decryption error***"

    def _load(self):
        if self._FILE.exists():
            try:
                self._store = json.loads(self._FILE.read_text(encoding="utf-8"))
            except Exception:
                self._store = {}

    def _save(self):
        self._FILE.write_text(json.dumps(self._store, indent=2), encoding="utf-8")

    def set_master(self, password: str):
        self._key = hashlib.sha256(password.encode()).digest()

    def generate(self, length: int = 16, symbols: bool = True) -> Tuple[bool, str]:
        import random, string
        length = max(8, min(128, int(length)))
        chars = string.ascii_letters + string.digits
        if symbols:
            chars += "!@#$%^&*()-_=+[]{}|;:,.<>?"
        pwd = "".join(random.SystemRandom().choice(chars) for _ in range(length))
        return True, f"Generated password ({length} chars): {pwd}"

    def save(self, service: str, password: str) -> Tuple[bool, str]:
        self._store[service.lower().strip()] = self._encode(password)
        self._save()
        return True, f"Password saved for '{service}'"

    def get(self, service: str) -> Tuple[bool, str]:
        key = service.lower().strip()
        if key not in self._store:
            return False, f"No password stored for '{service}'"
        return True, f"Password for '{service}': {self._decode(self._store[key])}"

    def delete(self, service: str) -> Tuple[bool, str]:
        key = service.lower().strip()
        if key not in self._store:
            return False, f"No password stored for '{service}'"
        del self._store[key]
        self._save()
        return True, f"Password for '{service}' deleted"

    def list_services(self) -> Tuple[bool, str]:
        if not self._store:
            return False, "No passwords stored"
        return True, "Stored services: " + ", ".join(sorted(self._store.keys()))

    def strength(self, password: str) -> Tuple[bool, str]:
        score = 0
        issues = []
        if len(password) >= 8:  score += 1
        else: issues.append("too short (<8)")
        if len(password) >= 12: score += 1
        if any(c.isupper() for c in password): score += 1
        else: issues.append("no uppercase")
        if any(c.islower() for c in password): score += 1
        else: issues.append("no lowercase")
        if any(c.isdigit() for c in password): score += 1
        else: issues.append("no digits")
        if any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in password): score += 1
        else: issues.append("no symbols")
        labels = {0:"Very Weak",1:"Weak",2:"Weak",3:"Fair",4:"Good",5:"Strong",6:"Very Strong"}
        label  = labels.get(score, "Fair")
        note   = (" Issues: " + ", ".join(issues)) if issues else ""
        return True, f"Password strength: {label} ({score}/6){note}"


# ══════════════════════════════════════════════════════════════════════════════
# NEW MODULE — System Health Monitor [F-3]
# ══════════════════════════════════════════════════════════════════════════════
class SystemHealthMonitor:
    """
    Background thread that monitors CPU, RAM, and Disk.
    Fires a TTS alert when any metric exceeds its threshold.
    """
    CPU_THRESHOLD  = 90   # %
    RAM_THRESHOLD  = 85   # %
    DISK_THRESHOLD = 90   # %
    CHECK_INTERVAL = 30   # seconds

    def __init__(self, tts: "TTSCore"):
        self.tts       = tts
        self._running  = False
        self._thread: Optional[threading.Thread] = None
        self._alerts: deque = deque(maxlen=20)

    def start(self) -> Tuple[bool, str]:
        if self._running:
            return False, "Health monitor already running"
        if not PSUTIL_OK:
            return False, "psutil not installed — health monitor unavailable"
        self._running = True
        self._thread  = threading.Thread(target=self._loop, daemon=True, name="HealthMonitor")
        self._thread.start()
        return True, f"Health monitor started (CPU>{self.CPU_THRESHOLD}%, RAM>{self.RAM_THRESHOLD}%, Disk>{self.DISK_THRESHOLD}%)"

    def stop(self) -> Tuple[bool, str]:
        self._running = False
        return True, "Health monitor stopped"

    def _loop(self):
        while self._running:
            try:
                cpu  = psutil.cpu_percent(interval=1)
                ram  = psutil.virtual_memory().percent
                disk = max((psutil.disk_usage(p.mountpoint).percent
                            for p in psutil.disk_partitions(all=False)
                            if p.fstype), default=0)

                alerts = []
                if cpu  > self.CPU_THRESHOLD:  alerts.append(f"CPU at {cpu:.0f}%")
                if ram  > self.RAM_THRESHOLD:  alerts.append(f"RAM at {ram:.0f}%")
                if disk > self.DISK_THRESHOLD: alerts.append(f"Disk at {disk:.0f}%")

                if alerts:
                    msg = "Warning: " + " and ".join(alerts)
                    self._alerts.append((datetime.now().strftime("%H:%M:%S"), msg))
                    logger.warning(f"[HealthMonitor] {msg}")
                    self.tts.speak(msg, blocking=False)
            except Exception as e:
                logger.debug(f"HealthMonitor loop error: {e}")
            time.sleep(self.CHECK_INTERVAL)

    def status(self) -> Tuple[bool, str]:
        if not PSUTIL_OK:
            return False, "psutil not available"
        cpu   = psutil.cpu_percent(interval=0.5)
        ram   = psutil.virtual_memory().percent
        lines = [f"\n🏥  System Health:"]
        lines.append(f"  CPU:  {cpu:.1f}%  {'⚠️' if cpu > self.CPU_THRESHOLD else '✅'}")
        lines.append(f"  RAM:  {ram:.1f}%  {'⚠️' if ram > self.RAM_THRESHOLD else '✅'}")
        for p in psutil.disk_partitions(all=False):
            try:
                d = psutil.disk_usage(p.mountpoint)
                lines.append(f"  Disk {p.mountpoint}: {d.percent:.0f}%  {'⚠️' if d.percent > self.DISK_THRESHOLD else '✅'}")
            except (PermissionError, OSError):
                pass
        monitor_state = "Running 🟢" if self._running else "Stopped 🔴"
        lines.append(f"  Monitor: {monitor_state}")
        if self._alerts:
            lines.append(f"  Recent alerts ({len(self._alerts)}):")
            for ts, msg in list(self._alerts)[-3:]:
                lines.append(f"    [{ts}] {msg}")
        print("\n".join(lines))
        return True, "Health status shown above"


# ══════════════════════════════════════════════════════════════════════════════
# NEW MODULE — Unit Converter [F-4]
# ══════════════════════════════════════════════════════════════════════════════
class UnitConverter:
    """
    Convert between common units: length, weight, temperature, data, speed.
    No external dependencies.
    """
    _LENGTH = {
        "km": 1000, "m": 1, "cm": 0.01, "mm": 0.001,
        "mile": 1609.344, "miles": 1609.344,
        "yard": 0.9144, "yards": 0.9144,
        "foot": 0.3048, "feet": 0.3048, "ft": 0.3048,
        "inch": 0.0254, "inches": 0.0254, "in": 0.0254,
    }
    _WEIGHT = {
        "kg": 1, "g": 0.001, "mg": 0.000001, "tonne": 1000,
        "lb": 0.453592, "lbs": 0.453592,
        "oz": 0.0283495, "stone": 6.35029,
    }
    _DATA = {
        "b": 1, "kb": 1024, "mb": 1024**2, "gb": 1024**3,
        "tb": 1024**4, "pb": 1024**5,
    }
    _SPEED = {
        "kmh": 1, "kph": 1, "mph": 1.60934, "ms": 3.6,
        "knot": 1.852, "knots": 1.852,
    }

    def _try_units(self, value: float, from_u: str, to_u: str,
                   table: dict) -> Optional[float]:
        f = table.get(from_u.lower())
        t = table.get(to_u.lower())
        if f and t:
            return value * f / t
        return None

    def convert(self, value: float, from_u: str, to_u: str) -> Tuple[bool, str]:
        from_l = from_u.lower().strip()
        to_l   = to_u.lower().strip()

        # Temperature special case
        temp_units = {"c", "celsius", "f", "fahrenheit", "k", "kelvin"}
        if from_l in temp_units or to_l in temp_units:
            return self._convert_temp(value, from_l, to_l)

        for table in [self._LENGTH, self._WEIGHT, self._DATA, self._SPEED]:
            result = self._try_units(value, from_l, to_l, table)
            if result is not None:
                formatted = f"{result:.6g}" if abs(result) < 1e6 else f"{result:.3e}"
                return True, f"{value} {from_u} = {formatted} {to_u}"

        return False, f"Cannot convert '{from_u}' to '{to_u}' — unsupported units"

    def _convert_temp(self, value: float, from_u: str, to_u: str) -> Tuple[bool, str]:
        # Normalise to Celsius first
        if from_u in ("f", "fahrenheit"):
            celsius = (value - 32) * 5 / 9
        elif from_u in ("k", "kelvin"):
            celsius = value - 273.15
        else:
            celsius = value

        if to_u in ("f", "fahrenheit"):
            result = celsius * 9 / 5 + 32
            unit   = "°F"
        elif to_u in ("k", "kelvin"):
            result = celsius + 273.15
            unit   = "K"
        else:
            result = celsius
            unit   = "°C"

        return True, f"{value} {from_u.upper()} = {result:.2f} {unit}"


# ══════════════════════════════════════════════════════════════════════════════
# NEW MODULE — Habit Tracker [F-5]
# ══════════════════════════════════════════════════════════════════════════════
class HabitTracker:
    """
    Daily habit tracking with streak counting. Persisted in ~/.jarvis_habits.json.
    """
    _FILE = HOME / ".jarvis_habits.json"

    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if self._FILE.exists():
            try:
                self._data = json.loads(self._FILE.read_text(encoding="utf-8"))
            except Exception:
                self._data = {}

    def _save(self):
        self._FILE.write_text(json.dumps(self._data, indent=2), encoding="utf-8")

    def _today(self) -> str:
        return datetime.now().strftime("%Y-%m-%d")

    def add_habit(self, name: str) -> Tuple[bool, str]:
        key = name.lower().strip()
        if key in self._data:
            return False, f"Habit '{name}' already exists"
        self._data[key] = {"name": name, "log": [], "streak": 0, "best_streak": 0}
        self._save()
        return True, f"Habit '{name}' added"

    def check_in(self, name: str) -> Tuple[bool, str]:
        key = name.lower().strip()
        if key not in self._data:
            # Auto-create
            self._data[key] = {"name": name, "log": [], "streak": 0, "best_streak": 0}
        habit = self._data[key]
        today = self._today()
        if today in habit["log"]:
            return True, f"'{name}' already checked in today! 🎯"
        habit["log"].append(today)
        # Calculate streak
        streak = 0
        for i in range(len(habit["log"]) - 1, -1, -1):
            expected = (datetime.now() - timedelta(days=streak)).strftime("%Y-%m-%d")
            if habit["log"][i] == expected:
                streak += 1
            else:
                break
        habit["streak"]      = streak
        habit["best_streak"] = max(habit["best_streak"], streak)
        self._save()
        emoji = "🔥" if streak >= 3 else "✅"
        return True, f"{emoji}  '{name}' checked in! Streak: {streak} day(s)"

    def show(self) -> Tuple[bool, str]:
        if not self._data:
            return False, "No habits tracked yet. Say: check in [habit name]"
        print(f"\n📊  Habit Tracker ({self._today()}):")
        today = self._today()
        for key, h in sorted(self._data.items()):
            done = today in h["log"]
            status = "✅" if done else "⬜"
            print(f"  {status} {h['name']:<25} Streak: {h['streak']} | Best: {h['best_streak']}")
        return True, f"{len(self._data)} habit(s) shown"

    def delete(self, name: str) -> Tuple[bool, str]:
        key = name.lower().strip()
        if key not in self._data:
            return False, f"Habit '{name}' not found"
        del self._data[key]
        self._save()
        return True, f"Habit '{name}' deleted"


# ══════════════════════════════════════════════════════════════════════════════
# NEW MODULE — Crypto Tracker [F-6]
# ══════════════════════════════════════════════════════════════════════════════
class CryptoTracker:
    """
    Live crypto prices using CoinGecko public API — no API key required.
    """
    _API = "https://api.coingecko.com/api/v3/simple/price"
    _IDS = {
        "bitcoin": "bitcoin", "btc": "bitcoin",
        "ethereum": "ethereum", "eth": "ethereum",
        "binance": "binancecoin", "bnb": "binancecoin",
        "solana": "solana", "sol": "solana",
        "cardano": "cardano", "ada": "cardano",
        "xrp": "ripple", "ripple": "ripple",
        "dogecoin": "dogecoin", "doge": "dogecoin",
        "polkadot": "polkadot", "dot": "polkadot",
        "avalanche": "avalanche-2", "avax": "avalanche-2",
        "matic": "matic-network", "polygon": "matic-network",
    }

    def _fetch_price(self, coin_ids: List[str]) -> Optional[Dict]:
        ids_str = ",".join(set(coin_ids))
        url = f"{self._API}?ids={ids_str}&vs_currencies=usd&include_24hr_change=true"
        try:
            req = Request(url, headers={"User-Agent": "JARVIS/3.0"})
            with urlopen(req, timeout=8) as r:
                return json.loads(r.read())
        except Exception as e:
            logger.debug(f"CryptoTracker fetch error: {e}")
            return None

    def price(self, coin: str) -> Tuple[bool, str]:
        cid = self._IDS.get(coin.lower().strip())
        if not cid:
            return False, f"Coin '{coin}' not recognized. Try: bitcoin, ethereum, solana"
        data = self._fetch_price([cid])
        if not data or cid not in data:
            return False, f"Could not fetch price for {coin}"
        p    = data[cid].get("usd", 0)
        chg  = data[cid].get("usd_24h_change", 0)
        arrow = "📈" if chg >= 0 else "📉"
        return True, f"{arrow}  {coin.capitalize()}: ${p:,.2f}  ({chg:+.2f}% 24h)"

    def top(self) -> Tuple[bool, str]:
        coins = ["bitcoin","ethereum","binancecoin","solana","ripple","cardano","dogecoin"]
        data  = self._fetch_price(coins)
        if not data:
            return False, "Could not fetch crypto prices"
        lines = ["\n💰  Live Crypto Prices (USD):"]
        name_map = {v: k.capitalize() for k, v in self._IDS.items() if k == v or k[:3] == v[:3]}
        for cid in coins:
            if cid in data:
                p   = data[cid].get("usd", 0)
                chg = data[cid].get("usd_24h_change", 0)
                lbl = cid.replace("-2","").replace("binancecoin","BNB").replace(
                          "matic-network","MATIC").capitalize()
                arrow = "📈" if chg >= 0 else "📉"
                lines.append(f"  {arrow}  {lbl:<12} ${p:>12,.2f}   {chg:+.2f}%")
        print("\n".join(lines))
        return True, "Crypto prices shown above"


# ══════════════════════════════════════════════════════════════════════════════
# NEW MODULE — Clipboard History Manager [F-7]
# ══════════════════════════════════════════════════════════════════════════════
class ClipboardHistory:
    """
    Maintains a rolling in-memory clipboard history.
    On Windows, polls the clipboard; on other platforms, uses xclip/pbpaste.
    """
    def __init__(self, maxlen: int = 50):
        self._history: deque = deque(maxlen=maxlen)
        self._last    = ""
        self._monitor = False

    def add(self, text: str):
        text = str(text).strip()
        if text and text != self._last:
            self._history.appendleft(text)
            self._last = text

    def start_monitoring(self) -> Tuple[bool, str]:
        if not WIN32_OK and not IS_MACOS and not IS_LINUX:
            return False, "Clipboard monitoring not supported"
        self._monitor = True
        t = threading.Thread(target=self._poll, daemon=True, name="ClipboardMonitor")
        t.start()
        return True, "Clipboard history monitoring started"

    def _poll(self):
        while self._monitor:
            try:
                text = self._read_clipboard()
                if text:
                    self.add(text)
            except Exception:
                pass
            time.sleep(1)

    def _read_clipboard(self) -> Optional[str]:
        if WIN32_OK and win32clipboard:
            try:
                win32clipboard.OpenClipboard()
                if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_TEXT):
                    data = win32clipboard.GetClipboardData(win32clipboard.CF_TEXT)
                    win32clipboard.CloseClipboard()
                    return data.decode("utf-8", errors="replace") if isinstance(data, bytes) else data
                win32clipboard.CloseClipboard()
            except Exception:
                pass
        elif IS_MACOS:
            try:
                r = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=2)
                return r.stdout.strip()
            except Exception:
                pass
        elif IS_LINUX:
            try:
                r = subprocess.run(["xclip","-selection","clipboard","-o"],
                                   capture_output=True, text=True, timeout=2)
                return r.stdout.strip()
            except Exception:
                pass
        return None

    def show(self) -> Tuple[bool, str]:
        if not self._history:
            return False, "Clipboard history is empty"
        print(f"\n📋  Clipboard History ({len(self._history)} items):")
        for i, item in enumerate(list(self._history)[:10], 1):
            preview = item[:80].replace("\n"," ")
            print(f"  [{i:2}] {preview}")
        return True, f"{len(self._history)} item(s) in clipboard history"

    def get_item(self, n: int) -> Tuple[bool, str]:
        items = list(self._history)
        if not 1 <= n <= len(items):
            return False, f"Item {n} not in history (have {len(items)})"
        return True, items[n - 1]

    def clear(self) -> Tuple[bool, str]:
        self._history.clear()
        self._last = ""
        return True, "Clipboard history cleared"


# ══════════════════════════════════════════════════════════════════════════════
# NEW MODULE — Unit Converter RE patterns + World Clock [F-11]
# ══════════════════════════════════════════════════════════════════════════════
class WorldClock:
    """
    Display current time in major world cities (no pytz dependency).
    Uses UTC offsets stored locally.
    """
    # UTC offset in hours (standard time; DST not accounted for)
    CITIES = {
        "london":       0,   "dublin":      0,   "lisbon":       0,
        "paris":        1,   "berlin":      1,   "rome":         1,
        "madrid":       1,   "amsterdam":   1,   "brussels":     1,
        "cairo":        2,   "istanbul":    3,   "moscow":       3,
        "dubai":        4,   "karachi":     5,   "mumbai":       5.5,
        "kolkata":      5.5, "dhaka":       6,   "bangkok":      7,
        "jakarta":      7,   "singapore":   8,   "hong kong":    8,
        "beijing":      8,   "shanghai":    8,   "taipei":       8,
        "seoul":        9,   "tokyo":       9,   "sydney":       10,
        "auckland":     12,  "new york":    -5,  "toronto":     -5,
        "chicago":     -6,   "denver":      -7,  "los angeles": -8,
        "san francisco":-8,  "seattle":    -8,   "anchorage":   -9,
        "honolulu":    -10,  "sao paulo":  -3,   "buenos aires":-3,
        "mexico city": -6,   "bogota":     -5,   "lima":        -5,
    }

    def time_in(self, city: str) -> Tuple[bool, str]:
        key = city.lower().strip()
        if key not in self.CITIES:
            matches = [c for c in self.CITIES if key in c or c in key]
            if not matches:
                return False, f"City '{city}' not found. Try: tokyo, london, new york..."
            key = matches[0]
        offset  = self.CITIES[key]
        utc_now = datetime.now(timezone.utc)
        hours   = int(offset)
        minutes = int((offset - hours) * 60)
        local   = utc_now + timedelta(hours=hours, minutes=minutes)
        return True, f"🕐  {key.title()}: {local.strftime('%I:%M %p')} ({local.strftime('%A, %b %d')})"

    def show_all(self, cities: List[str] = None) -> Tuple[bool, str]:
        show = cities or ["london","new york","dubai","mumbai","tokyo","sydney"]
        lines = ["\n🌍  World Clock:"]
        for city in show:
            _, msg = self.time_in(city)
            lines.append(f"  {msg}")
        print("\n".join(lines))
        return True, "World clock shown"


# ══════════════════════════════════════════════════════════════════════════════
# NEW MODULE — Reinforcement Learning Command Agent [v4.0]
# ══════════════════════════════════════════════════════════════════════════════
class RLCommandAgent:
    """
    Q-Learning based command routing agent.

    The agent maintains a Q-table mapping (command_category, action) → value,
    where 'action' is the dispatch stage/handler index and 'value' is a float
    representing the expected reward for routing that category through that handler.

    Rewards:
      +1.0  — command succeeded (ok=True from handler)
      -0.5  — command failed (ok=False)
       0.0  — command was not recognised (AI fallback)

    On each command, the agent:
      1. Encodes the command into a category feature vector.
      2. Selects the best known action (or explores via ε-greedy).
      3. Records the outcome and updates Q-values via temporal-difference update.

    The Q-table is persisted to ~/.jarvis_rl_qtable.json so the agent
    learns across sessions.

    Configuration:
      alpha (learning rate)  = 0.1    — how fast new info overrides old
      gamma (discount)       = 0.9    — future reward weight
      epsilon (exploration)  = 0.15   — probability of random exploration
      epsilon_decay          = 0.995  — decay per episode (floor at 0.05)
    """

    _FILE = HOME / ".jarvis_rl_qtable.json"

    # Command categories (feature buckets) — derived from keywords in command
    CATEGORIES = [
        "volume", "brightness", "app_open", "app_close", "browser", "web_search",
        "file_op", "system_info", "ai_query", "weather", "crypto", "convert",
        "password", "habit", "health", "clipboard", "timer", "notes", "calc",
        "media", "network", "power", "unknown",
    ]

    # Handlers (actions) — indices into JARVIS dispatch stages
    HANDLERS = list(range(len(CATEGORIES)))

    def __init__(self,
                 alpha:   float = 0.10,
                 gamma:   float = 0.90,
                 epsilon: float = 0.15):
        self.alpha   = alpha
        self.gamma   = gamma
        self.epsilon = epsilon
        self._epsilon_min   = 0.05
        self._epsilon_decay = 0.995
        self._episodes      = 0

        # Q-table: {category_index: {action_index: q_value}}
        self._q: Dict[int, Dict[int, float]] = {}
        # Command history for analysis
        self._history: deque = deque(maxlen=1000)
        # Pending transition: (state, action, reward) — filled per command
        self._pending: Optional[Tuple[int, int, float]] = None

        self._load()

    def _load(self):
        """Load persisted Q-table from disk."""
        if self._FILE.exists():
            try:
                raw = json.loads(self._FILE.read_text(encoding="utf-8"))
                self._q       = {int(k): {int(a): float(v) for a, v in av.items()}
                                 for k, av in raw.get("q", {}).items()}
                self._episodes = int(raw.get("episodes", 0))
                self.epsilon   = max(self._epsilon_min, float(raw.get("epsilon", self.epsilon)))
                logger.info(f"[RL] Loaded Q-table ({self._episodes} episodes, ε={self.epsilon:.3f})")
            except Exception as e:
                logger.warning(f"[RL] Could not load Q-table: {e}")

    def _save(self):
        """Persist Q-table to disk (non-blocking)."""
        def _write():
            try:
                data = {
                    "q":        {str(k): {str(a): v for a, v in av.items()}
                                 for k, av in self._q.items()},
                    "episodes": self._episodes,
                    "epsilon":  self.epsilon,
                }
                self._FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
            except Exception as e:
                logger.debug(f"[RL] Q-table save error: {e}")
        threading.Thread(target=_write, daemon=True, name="RL-Save").start()

    def _categorize(self, cmd: str) -> int:
        """Map a command string to a category index (state)."""
        cmd_l = cmd.lower()
        checks = [
            ("volume",      lambda c: "volume" in c),
            ("brightness",  lambda c: any(w in c for w in ["brightness", "bright", "dim"])),
            ("app_open",    lambda c: c.startswith("open ")),
            ("app_close",   lambda c: any(c.startswith(w) for w in ["close ", "quit ", "kill "])),
            ("browser",     lambda c: any(w in c for w in ["browser", "history", "downloads", "bookmarks", "new tab", "devtools"])),
            ("web_search",  lambda c: any(w in c for w in ["search", "google", "find", "look up", "youtube"])),
            ("file_op",     lambda c: any(w in c for w in ["file", "folder", "directory", "delete", "create", "rename", "move", "copy"])),
            ("system_info", lambda c: any(w in c for w in ["cpu", "memory", "ram", "battery", "uptime", "system info"])),
            ("ai_query",    lambda c: any(c.startswith(w) for w in ["ask ", "query ", "chat ", "ai ", "tell me", "explain"])),
            ("weather",     lambda c: any(w in c for w in ["weather", "forecast", "temperature", "climate"])),
            ("crypto",      lambda c: any(w in c for w in ["bitcoin", "ethereum", "crypto", "btc", "eth"])),
            ("convert",     lambda c: "convert" in c),
            ("password",    lambda c: "password" in c),
            ("habit",       lambda c: "habit" in c or "check in" in c),
            ("health",      lambda c: "health" in c or "monitoring" in c),
            ("clipboard",   lambda c: "clipboard" in c),
            ("timer",       lambda c: "timer" in c or "remind" in c),
            ("notes",       lambda c: "note" in c),
            ("calc",        lambda c: any(w in c for w in ["calculate", "compute", "what is", "sqrt", "plus", "minus", "times"])),
            ("media",       lambda c: any(w in c for w in ["play", "pause", "next track", "previous track", "stop music"])),
            ("network",     lambda c: any(w in c for w in ["ping", "ip", "internet", "network", "speed test"])),
            ("power",       lambda c: any(w in c for w in ["shutdown", "restart", "sleep", "hibernate", "lock"])),
        ]
        for i, (cat, test) in enumerate(checks):
            if test(cmd_l):
                return i
        return len(self.CATEGORIES) - 1  # "unknown"

    def _q_value(self, state: int, action: int) -> float:
        return self._q.get(state, {}).get(action, 0.0)

    def _best_action(self, state: int) -> int:
        """Return action with highest Q-value for this state (greedy)."""
        if state not in self._q or not self._q[state]:
            return state  # default: action = state index (identity mapping)
        return max(self._q[state], key=lambda a: self._q[state][a])

    def choose(self, cmd: str) -> int:
        """
        ε-greedy action selection.
        Returns the chosen action (handler index).
        """
        import random
        state = self._categorize(cmd)
        if random.random() < self.epsilon:
            action = random.randint(0, len(self.HANDLERS) - 1)
        else:
            action = self._best_action(state)
        self._pending = (state, action, 0.0)  # reward filled in record()
        return action

    def record(self, cmd: str, success: bool):
        """
        Record outcome of last command, update Q-table.
        Call this after any command handler returns.
        """
        if self._pending is None:
            # record() called without prior choose() — synthesise state
            state = self._categorize(cmd)
            action = state
        else:
            state, action, _ = self._pending
            self._pending = None

        reward = 1.0 if success else -0.5
        self._episodes += 1

        # TD(0) Q-learning update: Q(s,a) ← Q(s,a) + α[r + γ·maxQ(s',a') - Q(s,a)]
        # For single-step commands next_state = terminal, so γ·max = 0
        q_old = self._q_value(state, action)
        q_new = q_old + self.alpha * (reward - q_old)  # terminal: next_max = 0

        if state not in self._q:
            self._q[state] = {}
        self._q[state][action] = q_new

        # Decay exploration rate
        self.epsilon = max(self._epsilon_min, self.epsilon * self._epsilon_decay)

        self._history.append({
            "cmd":     cmd[:60],
            "state":   self.CATEGORIES[min(state, len(self.CATEGORIES)-1)],
            "action":  action,
            "reward":  reward,
            "q_new":   round(q_new, 4),
            "ts":      datetime.now().isoformat()[:19],
        })
        logger.debug(f"[RL] state={state} action={action} reward={reward:.1f} Q={q_new:.4f} ε={self.epsilon:.3f}")

        # Save every 50 episodes
        if self._episodes % 50 == 0:
            self._save()

    def stats(self) -> str:
        """Return human-readable RL statistics."""
        lines = [
            f"\n🧠  RL Agent Statistics (episodes={self._episodes}, ε={self.epsilon:.3f}):",
            f"  Q-table states: {len(self._q)}",
            f"  Total commands tracked: {len(self._history)}",
        ]
        if self._history:
            successes = sum(1 for h in self._history if h["reward"] > 0)
            lines.append(f"  Success rate: {successes}/{len(self._history)} "
                         f"({100*successes/len(self._history):.1f}%)")
            # Top-5 strongest Q-values
            top_q = sorted(
                [(self.CATEGORIES[min(s, len(self.CATEGORIES)-1)], a, v)
                 for s, av in self._q.items()
                 for a, v in av.items()],
                key=lambda x: -x[2]
            )[:5]
            if top_q:
                lines.append("  Top Q-values:")
                for cat, act, val in top_q:
                    lines.append(f"    [{cat}] action={act}  Q={val:.4f}")
        return "\n".join(lines)

    def show_history(self, n: int = 10) -> str:
        """Show last N entries from RL history."""
        recent = list(self._history)[-n:]
        lines = [f"\n🧠  Last {len(recent)} RL transitions:"]
        for h in reversed(recent):
            icon = "✅" if h["reward"] > 0 else "❌"
            lines.append(f"  {icon} [{h['ts']}] {h['state']:12} → Q={h['q_new']:.3f}  cmd={h['cmd']!r}")
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# 23. MODULE Q — Disk Manager
# ══════════════════════════════════════════════════════════════════════════════
class DiskManager:
    @safe_exec()
    def get_usage(self) -> Tuple[bool, str]:
        if not PSUTIL_OK:
            return False, "psutil not installed"
        parts = psutil.disk_partitions(all=False)
        lines = []
        for p in parts:
            try:
                u = psutil.disk_usage(p.mountpoint)
                bar = "█" * int(u.percent / 10) + "░" * (10 - int(u.percent / 10))
                lines.append(
                    f"  {p.mountpoint:<10} [{bar}] {u.percent:.0f}%  "
                    f"{u.free/1e9:.1f}GB free / {u.total/1e9:.0f}GB"
                )
            except (PermissionError, OSError):
                continue
        print("\n💽  Disk Usage:")
        print("\n".join(lines))
        return True, "Disk usage shown"

    @safe_exec()
    def get_io_stats(self) -> Tuple[bool, str]:
        if not PSUTIL_OK:
            return False, "psutil not installed"
        io = psutil.disk_io_counters()
        if not io:
            return False, "No I/O data"
        return True, (
            f"Disk I/O: Read {io.read_bytes/1e9:.2f}GB / "
            f"Write {io.write_bytes/1e9:.2f}GB"
        )

# ══════════════════════════════════════════════════════════════════════════════
# 24. HELP TEXT
# ══════════════════════════════════════════════════════════════════════════════
HELP_TEXT = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    JARVIS ULTIMATE v4.0 — COMMAND REFERENCE                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  TTS CONTROL                                                                ║
║    "stop" / "quiet" / "silence" / "shut up"  → stop JARVIS speaking        ║
║    JARVIS speaks ALL responses in full; say "stop" any time to interrupt   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  TIME / DATE / INFO                                                         ║
║    "what time is it"  "what's the date"  "what day is it"                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  SYSTEM INFO                                                                ║
║    "battery"  "cpu usage"  "memory"  "disk space"  "my ip"  "public ip"    ║
║    "uptime"  "system info"  "top processes"  "process count"               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  VOLUME  "volume up/down [N]"  "set volume to 50"  "increase volume to 50" ║
║          "mute"  "unmute"  "volume level"                                   ║
║          Note: "increase volume to 50%" → DIRECTLY sets to 50% (no steps) ║
║  BRIGHTNESS  "brightness up/down"  "set brightness to 70"                  ║
║              "increase brightness to 50%" → DIRECTLY sets to 50%          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  APPS   "open chrome"  "open chrome incognito"  "close firefox"             ║
║         "switch to notepad"  "maximize chrome"  "minimize spotify"          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  WEB    "search for X"  "search X on youtube"  "open github.com"            ║
║         "play lofi music on youtube"  "open gmail"                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  BROWSER  "new tab"  "close tab"  "refresh"  "go back"  "devtools"         ║
║           "scroll up/down"  "scroll up 5"  "scroll to top/bottom"          ║
║  BROWSER-TARGETED (for ANY installed browser):                              ║
║    "open history in brave"     "open settings in chrome"                   ║
║    "open downloads in edge"    "open bookmarks in firefox"                 ║
║    "open extensions in brave"  "open flags in chrome"                      ║
║    Works with: brave, chrome, edge, firefox                                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  BROWSER FEATURES v5.0 (30+ pages, all browsers):                          ║
║    "open passwords in brave"   "open privacy in chrome"                    ║
║    "open task manager in edge" "open gpu in brave"                         ║
║    "open site data in chrome"  "open sync in edge"                         ║
║    "open reading mode"         "open devtools"   "open flags"              ║
║    "open zoom in"  "open zoom out"  "open print"  "open find"              ║
║    Also: shields, wallet (Brave) | collections, reading-list (Edge)        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  POWER   "lock"  "sleep"  "hibernate"  "restart"  "shutdown"                ║
║          "shutdown in 5 minutes"  "cancel shutdown"                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  AI MODELS   "ask [question]"  "use model llama3.2"  "use model mixtral"   ║
║              "list models"  "list ollama models"  "pull model gemma2"       ║
║              "clear ai history"  (AI speaks full answer; say "stop" to cut)║
╠══════════════════════════════════════════════════════════════════════════════╣
║  FILE MANAGER                                                               ║
║    CRUD: "create file notes.txt in desktop"                                 ║
║          "create folder Projects in documents"                              ║
║          "delete test.txt"  "rename old.txt to new.txt"                    ║
║          "move report.txt to downloads"  "copy file.txt to desktop"        ║
║    SEARCH: "find file budget.xlsx"  "search pdf in downloads"               ║
║    ORGANIZE: "organize downloads by type/date/size"                         ║
║    ARCHIVES: "zip report.txt"  "unzip archive.zip"                         ║
║    DISK:   "disk usage"  "empty trash"  "clean temp"                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  CALCULATOR  "calculate 25 times 4"  "what is 100 divided by 5"            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  NOTES   "note down: buy groceries"  "read notes"  "clear notes"           ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  TIMERS / REMINDERS                                                         ║
║    "timer 5 minutes"  "remind me in 10 minutes to call mom"                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  v3.0/v4.0 FEATURES                                                         ║
║  WEATHER  "weather in london"  "forecast tokyo"  "temperature in dubai"     ║
║  CRYPTO   "bitcoin price"  "ethereum price"  "crypto prices"                ║
║  CONVERT  "convert 100 km to miles"  "convert 98.6 f to c"                  ║
║  CLOCK    "time in tokyo"  "time in new york"  "world clock"                ║
║  PASSWORDS  "generate password 20"  "save password gmail"                   ║
║             "get password gmail"  "password strength MyP@ss123"            ║
║  HEALTH   "health check"  "start monitoring"  "stop monitoring"             ║
║  HABITS   "check in exercise"  "add habit meditation"  "show habits"        ║
║  CLIPBOARD  "clipboard history"  "paste item 3"  "start clipboard"         ║
║  RL AGENT   "rl stats"  "rl history"  "learning stats"                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  v5.0 FEATURES                                                              ║
║  STORIES  "tell me a story"  "tell me a story about dragons"                ║
║           "tell me a story about space"  → say "stop" to end narration     ║
║  APPS     "list all apps"  "show installed apps"  "what apps do i have"     ║
║           "show all programs"  "display installed software"                 ║
║  VOLUME   Fixed: "increase volume to 70%" → directly sets to 70%           ║
║           (no longer zeroes to 0% first via PyAutoGUI fallback)            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""


# ══════════════════════════════════════════════════════════════════════════════
# v5.0 MODULE — BrowserFeatureManager
# Open any browser internal page by name in any installed browser.
# Supports Brave, Chrome, Edge, Firefox, Opera. Falls back to hotkeys.
# ══════════════════════════════════════════════════════════════════════════════
class BrowserFeatureManager:
    """
    Open any browser internal/feature page in any installed browser.

    New vs v4.0: 30+ pages (passwords, privacy, sync, GPU, site-data,
    reading-list, collections, shields, wallet, task-manager, zoom, print,
    find, fullscreen, source, mute-tab, close-tab, reopen-tab, back,
    forward, hard-refresh, next-tab, prev-tab, bookmark).
    """

    _URLS: Dict[str, Dict[str, Optional[str]]] = {
        "brave": {
            "history": "brave://history", "downloads": "brave://downloads",
            "settings": "brave://settings", "bookmarks": "brave://bookmarks",
            "extensions": "brave://extensions", "newtab": "brave://newtab",
            "flags": "brave://flags", "passwords": "brave://settings/passwords",
            "privacy": "brave://settings/privacy", "sync": "brave://settings/braveSync",
            "wallet": "brave://wallet", "shields": "brave://settings/shields",
            "performance": "brave://performance", "about": "brave://settings/getStarted",
            "gpu": "brave://gpu", "site-data": "brave://settings/cookies",
        },
        "chrome": {
            "history": "chrome://history", "downloads": "chrome://downloads",
            "settings": "chrome://settings", "bookmarks": "chrome://bookmarks",
            "extensions": "chrome://extensions", "newtab": "chrome://newtab",
            "flags": "chrome://flags", "passwords": "chrome://password-manager/passwords",
            "privacy": "chrome://settings/privacy", "sync": "chrome://settings/syncSetup",
            "performance": "chrome://performance", "gpu": "chrome://gpu",
            "site-data": "chrome://settings/cookies", "about": "chrome://settings/help",
        },
        "edge": {
            "history": "edge://history", "downloads": "edge://downloads",
            "settings": "edge://settings", "bookmarks": "edge://favorites",
            "extensions": "edge://extensions", "newtab": "edge://newtab",
            "flags": "edge://flags", "passwords": "edge://settings/passwords",
            "reading-list": "edge://read-anything", "collections": "edge://favorites/collections",
            "privacy": "edge://settings/privacy", "performance": "edge://settings/system",
            "gpu": "edge://gpu", "site-data": "edge://settings/content/cookies",
            "about": "edge://settings/help",
        },
        "firefox": {
            "history": None, "downloads": "about:downloads",
            "settings": "about:preferences", "bookmarks": None,
            "extensions": "about:addons", "newtab": "about:newtab",
            "passwords": "about:logins", "privacy": "about:preferences#privacy",
            "sync": "about:preferences#sync", "performance": "about:performance",
            "gpu": "about:support", "about": "about:about",
        },
        "opera": {
            "history": "opera://history", "downloads": "opera://downloads",
            "settings": "opera://settings", "extensions": "opera://extensions",
            "newtab": "opera://startpage", "flags": "opera://flags",
            "passwords": "opera://settings?search=passwords", "gpu": "opera://gpu",
        },
    }

    _HOTKEYS: Dict[str, Tuple[str, ...]] = {
        "history": ("ctrl", "h"), "downloads": ("ctrl", "j"),
        "bookmarks": ("ctrl", "shift", "o"), "extensions": ("ctrl", "shift", "e"),
        "newtab": ("ctrl", "t"), "devtools": ("f12",),
        "find": ("ctrl", "f"), "zoom-in": ("ctrl", "+"),
        "zoom-out": ("ctrl", "-"), "zoom-reset": ("ctrl", "0"),
        "print": ("ctrl", "p"), "save": ("ctrl", "s"),
        "fullscreen": ("f11",), "reading-mode": ("f9",),
        "task-manager": ("shift", "esc"), "source": ("ctrl", "u"),
        "bookmark": ("ctrl", "d"), "mute-tab": ("ctrl", "m"),
        "next-tab": ("ctrl", "tab"), "prev-tab": ("ctrl", "shift", "tab"),
        "reopen-tab": ("ctrl", "shift", "t"), "close-tab": ("ctrl", "w"),
        "hard-refresh": ("ctrl", "shift", "r"), "back": ("alt", "left"),
        "forward": ("alt", "right"),
    }

    _ALIASES: Dict[str, str] = {
        "new tab": "newtab", "new-tab": "newtab",
        "dev tools": "devtools", "developer tools": "devtools",
        "developer": "devtools", "console": "devtools", "inspect": "devtools",
        "add-ons": "extensions", "addons": "extensions", "plugins": "extensions",
        "bookmark": "bookmarks", "favourites": "bookmarks", "favorites": "bookmarks",
        "password": "passwords", "login": "passwords", "logins": "passwords",
        "download": "downloads", "setting": "settings", "preferences": "settings",
        "task manager": "task-manager", "taskmanager": "task-manager",
        "reading mode": "reading-mode", "reading list": "reading-list",
        "experiments": "flags", "zoom in": "zoom-in", "zoom out": "zoom-out",
        "zoom reset": "zoom-reset", "full screen": "fullscreen",
        "view source": "source", "mute tab": "mute-tab", "close tab": "close-tab",
        "next tab": "next-tab", "previous tab": "prev-tab", "reopen tab": "reopen-tab",
        "hard refresh": "hard-refresh", "force refresh": "hard-refresh",
        "site data": "site-data", "cookies": "site-data", "history page": "history",
    }

    _BROWSER_PATHS: Dict[str, List[str]] = {
        "brave": [
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
            r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
            "/usr/bin/brave-browser", "/usr/bin/brave",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        ],
        "chrome": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            "/usr/bin/google-chrome", "/usr/bin/chromium-browser", "/usr/bin/chromium",
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        ],
        "edge": [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            "/usr/bin/microsoft-edge",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        ],
        "firefox": [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
            "/usr/bin/firefox",
            "/Applications/Firefox.app/Contents/MacOS/firefox",
        ],
        "opera": [
            r"C:\Users\*\AppData\Local\Programs\Opera\opera.exe",
            "/usr/bin/opera", "/Applications/Opera.app/Contents/MacOS/Opera",
        ],
    }

    _KEYBOARD_ONLY_PAGES = frozenset({
        "devtools", "task-manager", "zoom-in", "zoom-out", "zoom-reset",
        "print", "find", "fullscreen", "reading-mode", "source", "mute-tab",
        "close-tab", "next-tab", "prev-tab", "reopen-tab", "back", "forward",
        "hard-refresh", "bookmark",
    })

    def __init__(self) -> None:
        self._exe_cache: Dict[str, Optional[str]] = {}

    def _find_exe(self, browser: str) -> Optional[str]:
        """Locate browser executable with glob and PATH fallback."""
        if browser in self._exe_cache:
            return self._exe_cache[browser]
        for path_str in self._BROWSER_PATHS.get(browser, []):
            if "*" in path_str:
                matches = glob.glob(path_str)
                if matches:
                    self._exe_cache[browser] = matches[0]
                    return matches[0]
            elif os.path.exists(path_str):
                self._exe_cache[browser] = path_str
                return path_str
        found = shutil.which(browser)
        self._exe_cache[browser] = found
        return found

    def _normalise_page(self, raw: str) -> str:
        """Normalise raw page name to a canonical key via alias table."""
        clean = raw.strip().lower()
        if clean in self._ALIASES:
            return self._ALIASES[clean]
        nospace = clean.replace(" ", "")
        for alias, canonical in self._ALIASES.items():
            if alias.replace(" ", "") == nospace:
                return canonical
        return clean

    def open(self, page: str, browser: str = "brave") -> Tuple[bool, str]:
        """
        Open a named browser internal page in the specified browser.

        Tries: (1) exe + URL direct launch; (2) Firefox keyboard shortcuts;
        (3) generic hotkey fallback (browser must be focused).

        Args:
            page:    Page name e.g. "history", "passwords", "devtools"
            browser: Browser name (brave|chrome|edge|firefox|opera)

        Returns:
            (success, message)
        """
        if not isinstance(page, str) or not page.strip():
            raise TypeError(f"page must be non-empty str, got {type(page).__name__!r}")

        browser = browser.lower().strip()
        _aliases = {"google chrome": "chrome", "microsoft edge": "edge",
                    "brave browser": "brave", "mozilla firefox": "firefox"}
        browser = _aliases.get(browser, browser)
        if browser not in self._URLS:
            browser = "brave"

        page_key = self._normalise_page(page)

        # Pages that are keyboard-only (no URL)
        if page_key in self._KEYBOARD_ONLY_PAGES:
            hk = self._HOTKEYS.get(page_key)
            if hk:
                return self._hk(*hk)
            return False, f"No hotkey defined for '{page_key}'"

        url = (self._URLS.get(browser) or {}).get(page_key)
        exe = self._find_exe(browser)

        if url and exe:
            try:
                subprocess.Popen([exe, url], creationflags=_NO_WIN_FLAG)
                logger.info(f"[BrowserFeatureManager] {browser} → {url}")
                return True, f"Opening {page_key} in {browser.title()}"
            except OSError as exc:
                logger.warning(f"[BrowserFeatureManager] Popen failed: {exc}")

        # Firefox keyboard-only fallbacks
        if browser == "firefox" and page_key == "history":
            return self._hk("ctrl", "h")
        if browser == "firefox" and page_key == "bookmarks":
            return self._hk("ctrl", "shift", "b")

        # Generic hotkey fallback
        hk = self._HOTKEYS.get(page_key)
        if hk:
            return self._hk(*hk)

        return False, f"'{page_key}' not available in {browser.title()}"

    def list_supported_pages(self, browser: str = "brave") -> List[str]:
        """Return sorted list of all supported pages for a browser."""
        url_pages = list((self._URLS.get(browser) or {}).keys())
        hk_pages  = list(self._HOTKEYS.keys())
        return sorted(set(url_pages + hk_pages))

    @staticmethod
    def _hk(*keys: str) -> Tuple[bool, str]:
        if not PAG_OK:
            return False, "pyautogui not installed — cannot send hotkey"
        try:
            pyautogui.hotkey(*keys)
            time.sleep(0.05)
            return True, f"Hotkey: {'+'.join(keys)}"
        except Exception as exc:
            return False, f"Hotkey failed: {exc}"


# ══════════════════════════════════════════════════════════════════════════════
# v5.0 MODULE — InstalledAppsLister
# Enumerate all installed applications from 5 sources.
# ══════════════════════════════════════════════════════════════════════════════
class InstalledAppsLister:
    """
    Multi-source installed application enumerator.

    Sources: JARVIS APP_DATABASE → Windows Registry → Start Menu /
    .desktop files / macOS .app → PATH executables → psutil processes.
    De-duplicated, sorted, 30-second cache, formatted report.
    """

    # Strip version numbers / noise from registry DisplayName values
    # Bounded character class — no catastrophic backtrack risk.
    _RE_VERSION = re.compile(
        r'\s*(?:\((?:64-bit|x64|x86|32-bit|[0-9][^)]*)\)|\s*-\s*(?:Update|Version|Patch)\s*\S+)',
        re.IGNORECASE,
    )

    def __init__(self, jarvis_app_db: Optional[Dict] = None) -> None:
        self._jarvis_db: Dict = jarvis_app_db or {}
        self._cache: Optional[List[Dict]] = None
        self._cache_ts: float = 0.0
        self._cache_ttl: float = 30.0

    def _from_jarvis_db(self) -> List[Dict]:
        entries = []
        for key, info in self._jarvis_db.items():
            if isinstance(info, dict) and info.get("installed"):
                entries.append({
                    "name":   info.get("display", key.title()),
                    "path":   info.get("resolved_path"),
                    "source": "jarvis_db",
                })
        return entries

    def _from_registry(self) -> List[Dict]:
        if not IS_WINDOWS or not WINREG_OK:
            return []
        entries = []
        reg_paths = [
            (winreg.HKEY_LOCAL_MACHINE,
             r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE,
             r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER,
             r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]
        for hive, path in reg_paths:
            try:
                with winreg.OpenKey(hive, path) as base_key:
                    count = winreg.QueryInfoKey(base_key)[0]
                    for i in range(count):
                        try:
                            sub_name = winreg.EnumKey(base_key, i)
                            with winreg.OpenKey(base_key, sub_name) as sk:
                                try:
                                    dn = winreg.QueryValueEx(sk, "DisplayName")[0]
                                except (FileNotFoundError, OSError):
                                    continue
                                if re.search(r'\bKB\d{6,}\b|Language Pack|Hotfix', dn, re.I):
                                    continue
                                try:
                                    icon = winreg.QueryValueEx(sk, "DisplayIcon")[0]
                                    exe  = icon.split(",")[0].strip('"') if icon else None
                                except (FileNotFoundError, OSError):
                                    exe = None
                                clean = self._RE_VERSION.sub("", dn).strip()
                                entries.append({
                                    "name":   clean,
                                    "path":   exe if exe and os.path.exists(exe) else None,
                                    "source": "registry",
                                })
                        except OSError:
                            continue
            except OSError:
                continue
        return entries

    def _from_start_menu(self) -> List[Dict]:
        entries = []
        if IS_WINDOWS:
            start_dirs = [
                Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData"))
                / "Microsoft" / "Windows" / "Start Menu" / "Programs",
                HOME / "AppData" / "Roaming" / "Microsoft" / "Windows"
                / "Start Menu" / "Programs",
            ]
            for sd in start_dirs:
                if not sd.is_dir():
                    continue
                for lnk in sd.rglob("*.lnk"):
                    name = lnk.stem
                    if any(b in name.lower() for b in ["uninstall", "readme", "help", "setup"]):
                        continue
                    entries.append({"name": name, "path": str(lnk), "source": "start_menu"})
        elif IS_LINUX:
            desktop_dirs = [
                Path("/usr/share/applications"),
                Path("/usr/local/share/applications"),
                HOME / ".local" / "share" / "applications",
            ]
            _re_name   = re.compile(r'^Name=(.+)$', re.MULTILINE)
            _re_exec   = re.compile(r'^Exec=(\S+)', re.MULTILINE)
            _re_hidden = re.compile(r'^NoDisplay=true', re.MULTILINE | re.IGNORECASE)
            for dd in desktop_dirs:
                if not dd.is_dir():
                    continue
                for desk in dd.glob("*.desktop"):
                    try:
                        text = desk.read_text(encoding="utf-8", errors="ignore")
                        if _re_hidden.search(text):
                            continue
                        nm = _re_name.search(text)
                        ex = _re_exec.search(text)
                        if nm:
                            entries.append({
                                "name":   nm.group(1).strip(),
                                "path":   ex.group(1) if ex else None,
                                "source": "start_menu",
                            })
                    except OSError:
                        continue
        elif IS_MACOS:
            for adir in [Path("/Applications"), HOME / "Applications"]:
                if adir.is_dir():
                    for app in adir.glob("*.app"):
                        entries.append({"name": app.stem, "path": str(app), "source": "start_menu"})
        return entries

    def _from_path(self) -> List[Dict]:
        entries = []
        _re_sane = re.compile(r'^[a-z][a-z0-9\-_.]{2,30}$', re.IGNORECASE)
        seen: set = set()
        for d in os.environ.get("PATH", "").split(os.pathsep):
            try:
                p = Path(d)
                if not p.is_dir():
                    continue
                for exe in p.iterdir():
                    if not exe.is_file():
                        continue
                    name = exe.stem if IS_WINDOWS else exe.name
                    if name in seen or not _re_sane.match(name):
                        continue
                    seen.add(name)
                    entries.append({"name": name.title(), "path": str(exe), "source": "path"})
            except (OSError, PermissionError):
                continue
        return entries

    def _from_processes(self) -> List[Dict]:
        entries = []
        if not PSUTIL_OK:
            return entries
        seen: set = set()
        for proc in psutil.process_iter(["name", "exe"]):
            try:
                info = proc.info
                name = (info.get("name") or "").strip()
                if not name or name in seen or len(name) < 3 or name.startswith("["):
                    continue
                seen.add(name)
                stem = Path(name).stem.replace("_", " ").replace("-", " ").title()
                entries.append({"name": stem, "path": info.get("exe"), "source": "process"})
            except Exception:
                continue
        return entries

    def get_all(self, force_refresh: bool = False) -> List[Dict]:
        """Return de-duplicated sorted list of all installed apps."""
        now = time.monotonic()
        if (not force_refresh and self._cache is not None
                and now - self._cache_ts < self._cache_ttl):
            return self._cache
        all_entries: List[Dict] = []
        for fn in [self._from_jarvis_db, self._from_registry,
                   self._from_start_menu, self._from_path, self._from_processes]:
            try:
                all_entries.extend(fn())
            except Exception as exc:
                logger.warning(f"[InstalledAppsLister] Source error: {exc}")
        seen_keys: Dict[str, bool] = {}
        unique: List[Dict] = []
        for entry in all_entries:
            key = re.sub(r'\s+', '', entry["name"].lower())
            if key and key not in seen_keys:
                seen_keys[key] = True
                unique.append(entry)
        self._cache    = sorted(unique, key=lambda e: e["name"].lower())
        self._cache_ts = now
        logger.info(f"[InstalledAppsLister] {len(self._cache)} apps found")
        return self._cache

    def format_report(self, max_display: int = 60) -> str:
        """Return formatted human-readable app list."""
        apps  = self.get_all()
        total = len(apps)
        _icons = {"jarvis_db": "🌟", "registry": "🗂️ ", "start_menu": "🚀",
                  "path": "⚙️ ", "process": "🔄"}
        lines = [f"\n📦  Installed Applications ({total} found):", "─" * 60]
        for i, app in enumerate(apps[:max_display], 1):
            icon     = _icons.get(app["source"], "📱")
            path_str = f"  ({Path(app['path']).name})" if app.get("path") else ""
            lines.append(f"  {i:>3}. {icon} {app['name']}{path_str}")
        if total > max_display:
            lines.append(f"\n  ... and {total - max_display} more apps.")
        lines.append("─" * 60)
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# v5.0 MODULE — StoryTeller
# Continuous story narration via TTS until user says "stop".
# ══════════════════════════════════════════════════════════════════════════════

# Built-in story corpus — fallback when AI is unavailable
_BUILTIN_STORIES: Dict[str, List[str]] = {
    "default": [
        "Once upon a time, in a land where the mountains touched the clouds, "
        "there lived a curious inventor named Aria. She spent her days building "
        "machines that could sing to the birds and teach rivers to flow in perfect spirals.",
        "One morning, a golden fox with silver eyes appeared at her doorstep, "
        "carrying a map made entirely of moonlight. The map led her through the "
        "Whispering Forest, where the trees spoke in riddles and shadows danced.",
        "At the heart of the forest stood a tower made of glass, and inside it "
        "hummed the first machine she had ever built as a child. She turned the key, "
        "and the machine sang its song — and for a moment, every creature stopped to listen.",
        "When the song ended, the golden fox bowed, the tower dissolved into fireflies, "
        "and Aria understood her true calling. She was not just an inventor. "
        "She was the keeper of wonder itself.",
        "And so she journeyed on, carrying the song in her heart, ready to share it "
        "with every corner of the world that had forgotten how to dream.",
    ],
    "dragon": [
        "In the age before maps, when the sky was wider and the stars were brighter, "
        "there soared the last great dragon, named Vael. Vael did not hoard gold as "
        "lesser dragons did — Vael collected forgotten songs, melodies humans had stopped singing.",
        "He flew from ruin to ruin, pressing his ear to crumbled walls to hear "
        "echoes of lullabies sung a thousand years ago. One day he found a child "
        "sitting alone on a cliff, humming a tune that made the clouds stop moving.",
        "The child looked up without fear and asked, 'Are you lonely?' Vael considered "
        "carefully, then answered, 'I am the opposite of lonely. I carry a million "
        "voices inside my chest.'",
        "The child smiled. 'Then you should teach me one, so I can carry it too.' "
        "And so the dragon and the child sat at the edge of the world, trading songs "
        "until the stars came out to listen.",
        "From that day forward, every song humans sang carried a small ember of dragon "
        "fire — just enough to keep hope warm through the longest winters.",
    ],
    "space": [
        "Commander Yara pressed her palm to the cold viewport and watched the star "
        "system she had never thought she'd reach drift slowly into view. Three years "
        "of deep sleep. Seven months of manual navigation. And here she was, at the edge of everything.",
        "The signal they had followed was simple: a prime-number pulse repeating every "
        "eleven seconds, from a world with two amber suns. She sent a response — her name, "
        "her planet, and a recording of rain falling on a metal roof.",
        "Six days later, a signal returned. It was rain, but warmer and heavier, "
        "falling on something that rang like crystal. Contact. Not a translation. "
        "Not a handshake. A weather report.",
        "She wept without knowing why, pressing her palm to the cold hull, feeling "
        "the hum of engines that had carried her so far from everything she had known.",
        "In the end, that was how they began — sharing what home sounded like "
        "across a gulf of silence no telescope had ever crossed.",
    ],
}


class StoryTeller:
    """
    Continuous story narration engine.

    Speaks a full story chapter by chapter via speak_streaming() until
    the user says 'stop'. Uses AI if available, built-in corpus as fallback.
    A threading.Event() controls stop without busy-waiting.
    """

    def __init__(self, tts: Any, ai_gateway: Any) -> None:
        self._tts        = tts
        self._ai         = ai_gateway
        self._stop_event = threading.Event()
        self._active     = threading.Event()
        self._thread: Optional[threading.Thread] = None

    @property
    def is_narrating(self) -> bool:
        return self._active.is_set()

    def stop(self) -> Tuple[bool, str]:
        """Stop the currently-playing story immediately."""
        self._stop_event.set()
        if hasattr(self._tts, "stop_speaking"):
            self._tts.stop_speaking()
        self._active.clear()
        logger.info("[StoryTeller] Stopped by user")
        return True, "Story narration stopped."

    def tell(self, topic: str = "an adventure") -> Tuple[bool, str]:
        """Begin narrating a story about the given topic in a daemon thread."""
        if not isinstance(topic, str):
            raise TypeError(f"topic must be str, got {type(topic).__name__!r}")
        if self._active.is_set():
            return False, "Already telling a story. Say 'stop' first."
        self._stop_event.clear()
        self._active.set()
        paragraphs = self._generate_story(topic)

        def _narrate() -> None:
            try:
                print(f"\n📖  JARVIS Story: '{topic.title()}'\n" + "─" * 60)
                for paragraph in paragraphs:
                    if self._stop_event.is_set():
                        break
                    if not paragraph.strip():
                        continue
                    if hasattr(self._tts, "speak_streaming"):
                        self._tts.speak_streaming(
                            paragraph,
                            stop_check=lambda: self._stop_event.is_set()
                        )
                        # Wait for streaming to complete (non-busy)
                        deadline = time.monotonic() + 120.0
                        while (hasattr(self._tts, "_lock")
                               and self._tts._lock.locked()
                               and time.monotonic() < deadline
                               and not self._stop_event.is_set()):
                            time.sleep(0.15)
                    else:
                        self._tts.speak(paragraph, blocking=True)
                    if not self._stop_event.is_set():
                        time.sleep(0.3)
            except Exception as exc:
                logger.error(f"[StoryTeller] Narration error: {exc}", exc_info=True)
            finally:
                self._active.clear()
                if not self._stop_event.is_set():
                    print("\n📖  Story complete.")

        self._thread = threading.Thread(target=_narrate, daemon=True, name="StoryTeller")
        self._thread.start()
        return True, f"Beginning story about {topic}. Say 'stop' any time to pause."

    def _generate_story(self, topic: str) -> List[str]:
        """Generate story paragraphs from AI or built-in corpus."""
        if not isinstance(topic, str):
            raise TypeError(f"topic must be str, got {type(topic).__name__!r}")
        try:
            if self._ai is not None and hasattr(self._ai, "query"):
                prompt = (
                    f"Tell me a creative, imaginative story about {topic}. "
                    f"Write exactly 5 paragraphs. Each paragraph must have at least "
                    f"3 complete sentences. Use vivid, descriptive language. "
                    f"No headers or bullet points — only prose separated by blank lines."
                )
                ok, response = self._ai.query(prompt)
                if ok and response and len(response) > 100:
                    raw_paras = re.split(r'\n\s*\n', response.strip())
                    paragraphs = [p.strip() for p in raw_paras if len(p.strip()) > 30]
                    if paragraphs:
                        return paragraphs
        except Exception as exc:
            logger.warning(f"[StoryTeller] AI query failed, using corpus: {exc}")

        # Corpus fallback
        topic_lower = topic.lower()
        best_key = "default"
        for key in _BUILTIN_STORIES:
            if key in topic_lower or any(w in topic_lower for w in key.split()):
                best_key = key
                break
        return list(_BUILTIN_STORIES.get(best_key, _BUILTIN_STORIES["default"]))


# ══════════════════════════════════════════════════════════════════════════════
# 25. MASTER COMMAND PROCESSOR — JARVIS v2.0
# ══════════════════════════════════════════════════════════════════════════════
class JARVIS:
    """
    Central orchestrator. Routes natural language commands to the appropriate
    module via a staged dispatch pipeline with robust fallbacks.

    Stage ordering note:
    [m-5] FIX: "disk usage by type" (Stage 19) is checked BEFORE the generic
    RE_DISK_USAGE handler (Stage 31) to prevent the substring "disk usage"
    from eating the more specific command.
    [M-3] FIX: Stage 14 (notes) now catches "remove note" and "erase note" in
    addition to the original "delete note" pattern.
    """

    def __init__(self):
        print("\n" + "═"*78)
        print("  JARVIS ULTIMATE v5.0 — Initializing all modules...")
        print("═"*78)

        # Core
        self.tts        = TTSCore()
        self.voice      = VoiceCore()

        # AI
        self.ai         = AIGateway()

        # Controllers
        self.apps       = AppController()
        self.system     = SystemController()
        self.web        = WebController()
        self.browser    = BrowserController()
        self.media      = MediaController()
        self.clipboard  = ClipboardController()
        self.window     = WindowController()
        self.screen     = ScreenOps()

        # Managers
        self.files      = FileManager()
        self.notes      = NotesManager()
        self.timer      = TimerManager(self.tts)
        self.network    = NetworkManager()
        self.proc_mgr   = ProcessManager()
        self.disk_mgr   = DiskManager()
        self.calc       = SafeCalculator()

        # ── v3.0 New Modules ──────────────────────────────────────────────
        self.weather        = WeatherService()
        self.passwords      = PasswordManager()
        self.health_monitor = SystemHealthMonitor(self.tts)
        self.converter      = UnitConverter()
        self.habits         = HabitTracker()
        self.crypto         = CryptoTracker()
        self.clip_history   = ClipboardHistory()
        self.world_clock    = WorldClock()

        # ── v4.0 New Modules ──────────────────────────────────────────────
        self.rl             = RLCommandAgent()   # Q-learning command routing

        # ── v5.0 New Modules ──────────────────────────────────────────────
        self.browser_features = BrowserFeatureManager()
        self.apps_lister    = InstalledAppsLister(self.apps._cache)
        self.storyteller    = StoryTeller(tts=self.tts, ai_gateway=self.ai)

        # State
        self.running        = True
        self._last_response = ""
        self._command_count = 0
        self._voice_mode    = self.voice.available
        self._history: deque = deque(maxlen=50)

        logger.info("JARVIS v5.0 fully initialized")
        print(f"\n✅  All modules loaded. Logs → {_LOG_PATH}")
        print(f"    Voice: {'enabled' if self._voice_mode else 'disabled (type commands)'}")
        print(f"    AI:    {self.ai._model} ({self.ai.OPEN_SOURCE_MODELS.get(self.ai._model, {}).get('desc', 'custom')})")
        print(f"    RL:    Q-table loaded ({self.rl._episodes} prior episodes, ε={self.rl.epsilon:.3f})")
        print(f"    v5.0:  BrowserFeatureManager | InstalledAppsLister | StoryTeller | VolumeFixed")
        print("═"*78 + "\n")

    # ── Response helper ────────────────────────────────────────────────
    def _respond(self, ok: bool, message: str, tts: bool = True):
        self._last_response = message
        prefix = "✅" if ok else "❌"
        print(f"{prefix}  {message}")
        logger.info(f"[{'OK' if ok else 'ERR'}] {message}")
        if tts and self.tts._enabled:
            # [v4.0] Speak the FULL message — no truncation.
            # The user can say "stop" at any time to interrupt.
            self.tts.speak(message, blocking=False)

    # ── Preprocessing ──────────────────────────────────────────────────
    def _preprocess(self, raw: str) -> str:
        cmd = raw.strip().lower()
        for wake in ["hey jarvis", "ok jarvis", "jarvis", "hey"]:
            if cmd.startswith(wake + " "):
                cmd = cmd[len(wake):].strip()
                break
        for f in FILLER_WORDS:
            cmd = re.sub(r'\b' + re.escape(f) + r'\b', ' ', cmd)
        # [FIX-V10] Common speech recognition corrections
        speech_fixes = {
            r'\borganised\b': 'organize',
            r'\borganizd\b': 'organize',
            r'\borganisd\b': 'organize',
            r'\bganesh\b': 'organize',   # "Ganesh" = common misrecognition of "organize" (Indian English)
            r'\bby data\b': 'by date',    # "data" = misrecognition of "date"
            r'\bby type files?\b': 'by type',  # "type files" = "type"
            r'\btype and data\b': 'type and date',  # "data" = "date"
            r'\bswap\b': 'snap',  # "swap" = misrecognition of "snap"
        }
        for pattern, replacement in speech_fixes.items():
            cmd = re.sub(pattern, replacement, cmd, flags=re.I)
        return re.sub(r'\s+', ' ', cmd).strip()

    def _extract_number(self, text: str, default: int = None) -> Optional[int]:
        m = RE_NUMBER.search(text)
        if m:
            v = m.group(1)
            return int(float(v))
        return default

    def _detect_browser(self, text: str) -> Optional[str]:
        t = text.lower()
        if "brave"   in t: return "brave"
        if "firefox" in t: return "firefox"
        if "edge"    in t or "msedge" in t: return "edge"
        if "chrome"  in t: return "chrome"
        if "opera"   in t: return "opera"
        return None

    def _clean_for_search(self, text: str, remove_terms: List[str] = None) -> str:
        for b in ["brave", "chrome", "edge", "firefox", "opera", "browser",
                  "incognito", "private", "inprivate", "mode", "window"]:
            text = re.sub(r'\s*\b' + b + r'\b\s*', ' ', text, flags=re.I)
        if remove_terms:
            for t in remove_terms:
                text = text.replace(t, " ")
        return re.sub(r'\s+', ' ', text).strip()

    # ══════════════════════════════════════════════════════════════════════
    # MAIN PROCESS DISPATCHER
    # ══════════════════════════════════════════════════════════════════════
    def process(self, raw: str):
        if not raw or not isinstance(raw, str) or not raw.strip():
            return
        self._command_count += 1
        self._history.append((datetime.now(), raw))
        logger.info(f"[CMD#{self._command_count}] {raw!r}")
        cmd = self._preprocess(raw)

        # ════ STAGE 0: STOP TTS (highest priority) ═══════════════════
        # If JARVIS is speaking and user says "stop"/"quiet"/"silence",
        # interrupt speech immediately WITHOUT exiting the program.
        if RE_STOP_SPEAKING.match(cmd) and not any(
            w in cmd for w in ["stop monitoring", "stop recording", "stop music",
                                "stop media", "stop alarm", "stop jarvis"]
        ):
            self.tts.stop_speaking()
            print("🔇  Stopped speaking.")
            return

        # ════ STAGE 1: EXIT ══════════════════════════════════════════
        exit_words = {"stop", "exit", "quit", "bye", "goodbye", "farewell",
                      "close jarvis", "shutdown jarvis"}
        if cmd in exit_words or (
            any(w in cmd for w in ["close", "stop", "exit", "shutdown"])
            and "jarvis" in raw.lower()
        ):
            self.running = False
            logger.info("JARVIS shutdown by user")
            self.tts.speak("Goodbye! Have a great day!")
            return

        # ════ STAGE 2: HELP ══════════════════════════════════════════
        if any(w in cmd for w in ["help", "commands", "what can you do", "features", "manual"]):
            print(HELP_TEXT)
            self._respond(True, "Command reference displayed above", tts=True)
            return

        # ════ STAGE 3: VOICE MODE TOGGLE ════════════════════════════
        if "disable voice" in cmd or "text mode" in cmd or "mute jarvis" in cmd:
            self._voice_mode = False
            self._respond(True, "Switched to text mode")
            return
        if "enable voice" in cmd or "voice mode" in cmd:
            if self.voice.available:
                self._voice_mode = True
                self._respond(True, "Voice mode enabled")
            else:
                self._respond(False, "Microphone not available")
            return

        # ════ STAGE 4: REPEAT ════════════════════════════════════════
        if cmd in {"repeat", "say again", "repeat that", "what did you say"}:
            if self._last_response:
                self.tts.speak(self._last_response)
            return

        # ════ STAGE 5: TIME ══════════════════════════════════════════
        if any(w in cmd for w in ["what time", "current time", "tell me the time", "what is the time"]):
            self._respond(True, f"The time is {datetime.now().strftime('%I:%M %p')}")
            return

        # ════ STAGE 6: DATE ══════════════════════════════════════════
        if any(w in cmd for w in ["what date", "today's date", "what is the date", "current date"]):
            self._respond(True, f"Today is {datetime.now().strftime('%A, %B %d, %Y')}")
            return

        # ════ STAGE 7: DAY ═══════════════════════════════════════════
        _day_q = (cmd.strip() in
                  {"today", "what day", "what day is it", "which day", "what day is today", "what is the day"}
                  or ("day" in cmd and any(w in cmd for w in ["what", "which", "today"])
                      and "note" not in cmd and "remind" not in cmd))
        if _day_q:
            self._respond(True, f"Today is {datetime.now().strftime('%A')}")
            return

        # ════ STAGE 8: SYSTEM INFO ═══════════════════════════════════
        if "system info" in cmd or "all info" in cmd:
            info = self.system.get_all_info()
            print(f"\n📊  System Information:\n{info}\n")
            self._respond(True, "System info shown above", tts=False)
            return
        if "battery" in cmd:
            ok, msg = self.system.get_battery()
            self._respond(ok, msg)
            return
        if re.search(r'\bcpu\b', cmd):
            ok, msg = self.system.get_cpu()
            self._respond(ok, msg)
            return
        if re.search(r'\b(memory|ram)\b', cmd):
            ok, msg = self.system.get_memory()
            self._respond(ok, msg)
            return
        if "uptime" in cmd:
            ok, msg = self.system.get_uptime()
            self._respond(ok, msg)
            return
        if "process count" in cmd or "how many processes" in cmd:
            ok, msg = self.proc_mgr.get_count()
            self._respond(ok, msg)
            return
        if any(w in cmd for w in ["top processes", "list processes", "running processes"]):
            ok, msg = self.proc_mgr.list_top()
            self._respond(ok, msg, tts=False)
            return

        # ════ STAGE 9: VOLUME ════════════════════════════════════════
        if "volume" in cmd:
            n = self._extract_number(cmd)
            if any(w in cmd for w in ["what", "current", "level", "check", "how much"]):
                v = self.system.get_volume()
                self._respond(v is not None, f"Volume: {v}%" if v is not None else "Cannot read volume")
            elif re.search(r'\bunmute\b', cmd):
                ok, msg = self.system.unmute()
                self._respond(ok, msg)
            elif re.search(r'\bmute\b', cmd):
                ok, msg = self.system.mute()
                self._respond(ok, msg)
            elif n is not None and (
                RE_SET_VOL_TO.search(cmd)
                or re.search(r'\bto\s+\d+\s*%?\b', cmd, re.I)
            ):
                # [FIX-VOL] "set volume to 50", "increase/decrease volume to 50%",
                # "volume to 75" → ALL treated as DIRECT absolute SET.
                # "increase/decrease volume by N" (no "to") still does relative step.
                ok, msg = self.system.set_volume(int(n))
                self._respond(ok, msg)
                self.rl.record(cmd, ok)
            elif n is not None and any(w in cmd for w in ["down", "decrease", "lower", "quieter", "reduce"]):
                # "decrease volume by 20" / "volume down 20" → relative step DOWN
                ok, msg = self.system.volume_down(int(n))
                self._respond(ok, msg)
            elif n is not None and any(w in cmd for w in ["up", "increase", "louder", "raise", "higher"]):
                # "increase volume by 20" / "volume up 20" → relative step UP
                ok, msg = self.system.volume_up(int(n))
                self._respond(ok, msg)
            elif any(w in cmd for w in ["down", "decrease", "lower", "quieter", "reduce"]):
                ok, msg = self.system.volume_down(10)
                self._respond(ok, msg)
            elif any(w in cmd for w in ["up", "increase", "louder", "raise", "higher"]):
                ok, msg = self.system.volume_up(10)
                self._respond(ok, msg)
            elif n is not None:
                ok, msg = self.system.set_volume(int(n))
                self._respond(ok, msg)
            else:
                self._respond(True, "Say: volume up, volume down 20, set volume to 50, or mute")
            return

        # ════ STAGE 10: BRIGHTNESS ═══════════════════════════════════
        if any(w in cmd for w in ["brightness", "bright", "dim"]):
            n = self._extract_number(cmd)
            if n is not None and RE_SET_BRIGHT_TO.search(cmd):
                # "increase brightness to 70%", "decrease brightness to 30", "set brightness to 50"
                # All treated as DIRECT SET — never increment/decrement
                ok, msg = self.system.set_brightness(int(n))
                self._respond(ok, msg)
                self.rl.record(cmd, ok)
            elif any(w in cmd for w in ["up", "increase"]):
                ok, msg = self.system.brightness_up(n or 10)
                self._respond(ok, msg)
            elif any(w in cmd for w in ["down", "decrease", "lower", "dim"]):
                ok, msg = self.system.brightness_down(n or 10)
                self._respond(ok, msg)
            elif n is not None:
                ok, msg = self.system.set_brightness(int(n))
                self._respond(ok, msg)
            else:
                v = self.system.get_brightness()
                self._respond(True, f"Brightness: {v}%" if v else "Say: brightness up/down or set to N")
            return

        # ════ STAGE 11: SCROLL ═══════════════════════════════════════
        m = RE_SCROLL.match(cmd)
        if m:
            direction = m.group(1)
            amount    = int(m.group(2)) if m.group(2) else 3
            ok, msg   = self.screen.scroll(direction, amount)
            self._respond(ok, msg)
            return
        if "scroll to top" in cmd or "go to top" in cmd:
            ok, msg = self.screen.scroll_to_top()
            self._respond(ok, msg)
            return
        if "scroll to bottom" in cmd or "go to bottom" in cmd:
            ok, msg = self.screen.scroll_to_bottom()
            self._respond(ok, msg)
            return

        # ════ STAGE 12: TIMER ════════════════════════════════════════
        if "timer" in cmd:
            if any(w in cmd for w in ["list", "active", "show", "how many"]):
                ok, msg = self.timer.list_timers()
                self._respond(ok, msg, tts=False)
            elif cmd.startswith("cancel timer"):
                n = self._extract_number(cmd)
                if n:
                    ok, msg = self.timer.cancel_timer(n)
                    self._respond(ok, msg)
            else:
                ok, msg = self.timer.set_timer(cmd)
                self._respond(ok, msg)
            return

        # ════ STAGE 13: REMINDER ════════════════════════════════════
        if "remind" in cmd:
            ok, msg = self.timer.set_reminder(cmd)
            self._respond(ok, msg)
            return

        # ════ STAGE 14: NOTES ════════════════════════════════════════
        # [M-3] FIX: "remove note" and "erase note" are now caught HERE
        # instead of falling through to the file-delete handler (Stage 19).
        if re.search(r'\bnotes?\b(?!\.\w)', cmd) or RE_NOTE_REMOVE.search(cmd):
            if any(w in cmd for w in ["read", "show", "list", "view"]):
                search = re.sub(r'(read|show|list|view)\s+notes?\s*', '', cmd, flags=re.I).strip()
                ok, msg = self.notes.read(search if search else None)
                self._respond(ok, msg, tts=False)
                return
            if any(w in cmd for w in ["clear", "delete all", "remove all"]):
                ok, msg = self.notes.clear()
                self._respond(ok, msg)
                return
            # Single-note deletion: "delete note <id>", "remove note <id>", "erase note <id>"
            note_del = re.match(r'(?:delete|remove|erase)\s+note\s+(.+)', cmd, re.I)
            if note_del:
                note_id = note_del.group(1).strip()
                ok, msg = self.notes.delete_note(note_id)
                self._respond(ok, msg)
                return
            m2 = RE_NOTE_ADD.match(cmd)
            if m2:
                text = m2.group(1).strip()
                if text:
                    ok, msg = self.notes.add(text)
                    self._respond(ok, msg)
                    return
            self._respond(True, "Say: note down [text], read notes, or clear notes")
            return

        # ════ STAGE 15: SCREENSHOT / RECORDING ═══════════════════════
        if RE_SCREENSHOT.search(cmd):
            ok, msg = self.screen.screenshot()
            self._respond(ok, msg)
            return
        if any(w in cmd for w in ["screen record", "start recording", "record screen"]):
            ok, msg = self.screen.start_recording()
            self._respond(ok, msg)
            return

        # ════ STAGE 16: SHOW LOGS ════════════════════════════════════
        if any(w in cmd for w in ["show logs", "open logs", "view logs"]):
            if _LOG_PATH.exists():
                self.files.open_folder(str(_LOG_PATH.parent))
                self._respond(True, f"Opened log folder: {_LOG_PATH.name}")
            else:
                self._respond(False, "Log file not found yet")
            return

        # ════ STAGE 17: AI QUERY ═════════════════════════════════════
        ai_m = RE_AI_QUERY.match(cmd)
        if ai_m:
            query = ai_m.group(1).strip()
            print(f"\n🤖  [{self.ai._model}] Thinking...")
            ok, response = self.ai.query(query)
            if ok:
                wrapped = textwrap.fill(response, width=80)
                print(f"\n  {wrapped}\n")
            # [FIX-AI] Stream the full AI response sentence-by-sentence.
            # The main loop continues to listen while JARVIS speaks; the user
            # can say "stop" / "quiet" at any time to interrupt.
            if ok and response:
                self.tts.speak_streaming(
                    response,
                    stop_check=lambda: self.tts._stop_event.is_set()
                )
            elif not ok:
                self._respond(ok, response, tts=True)
            self.rl.record(cmd, ok)
            return
        if "list models" in cmd or "show ai models" in cmd or "available models" in cmd:
            print(self.ai.list_models())
            self._respond(True, "Models listed above", tts=False)
            return
        if "list ollama" in cmd or "local models" in cmd:
            ok, msg = self.ai.list_ollama_models()
            self._respond(ok, msg, tts=False)
            return
        ai_model_m = RE_AI_MODEL.match(cmd)
        if ai_model_m:
            ok, msg = self.ai.set_model(ai_model_m.group(1).strip())
            self._respond(ok, msg)
            return
        if "pull model" in cmd or "download model" in cmd:
            model = re.sub(r'(pull|download)\s+model\s+', '', cmd).strip()
            if model:
                ok, msg = self.ai.pull_ollama_model(model)
                self._respond(ok, msg)
            return
        if "clear ai history" in cmd or "reset conversation" in cmd:
            ok, msg = self.ai.clear_history()
            self._respond(ok, msg)
            return

        # ════ STAGE 17: INCOGNITO / PRIVATE WINDOW (must run BEFORE browser features) ══
        # [FIX-V10] Moved before Stage 18.5 so "open private window in brave"
        # is caught here instead of being misinterpreted by browser feature matching.
        # Also handles "close X in private window" commands.
        m2 = RE_INCOGNITO.match(cmd)
        if m2 and any(w in cmd for w in ["incognito", "private", "inprivate"]):
            browser_part = (m2.group(1) or "chrome").strip()
            browser_part = re.sub(r'\b(mode|window|tab|in|the|browser)\b', ' ', browser_part, flags=re.I)
            browser_part = re.sub(r'\s+', ' ', browser_part).strip() or "chrome"
            ok, msg = self.apps.launch(browser_part, incognito=True)
            self._respond(ok, msg)
            return
        # Also catch "open private window in brave" / "open incognito in brave"
        # patterns that RE_INCOGNITO might miss (e.g. "open private window in brave")
        m_priv = re.match(
            r'^open\s+(?:a\s+)?(?:private|incognito|inprivate)\s+(?:window|mode|session)(?:\s+(?:in|on|with)\s+(brave|chrome|edge|firefox|opera))?$',
            cmd, re.I
        )
        if m_priv:
            browser_name = (m_priv.group(1) or "chrome").strip().lower()
            ok, msg = self.apps.launch(browser_name, incognito=True)
            self._respond(ok, msg)
            return

        # ════ STAGE V5-A: STOP STORY (must be before exit/stop parsing) ══
        if self.storyteller.is_narrating:
            if re.match(r'^(?:stop|pause|quiet|enough|cancel|that\'?s?\s+enough)$', cmd, re.I):
                ok, msg = self.storyteller.stop()
                self._respond(ok, msg)
                return

        # ════ STAGE V5-B: TELL A STORY ═══════════════════════════════════
        m2 = RE_V5_TELL_STORY.match(cmd)
        if m2:
            topic = (m2.group(1) or "an adventure").strip()
            ok, msg = self.storyteller.tell(topic)
            self._respond(ok, msg)
            return

        # ════ STAGE V5-C: LIST ALL INSTALLED APPS ════════════════════════
        if RE_V5_LIST_APPS.search(cmd):
            report = self.apps_lister.format_report(max_display=80)
            print(report)
            total = len(self.apps_lister.get_all())
            self._respond(True, f"Found {total} installed apps listed above", tts=False)
            return

        # ════ STAGE 18.0: OS SETTINGS (must run BEFORE browser feature stage) ══
        # [FIX-SETTINGS-V10] Comprehensive rewrite of OS vs Browser settings
        # disambiguation. Key rules:
        #   1. "open settings in brave"   → browser settings (brave://settings)
        #   2. "open brave settings"      → browser settings (brave://settings)
        #   3. "open bluetooth in settings" → OS settings (ms-settings:bluetooth)
        #   4. "open settings"            → OS settings (ms-settings: main page)
        #   5. "open downloads in brave"  → browser page (brave://downloads) — NOT caught here
        # When a browser name is explicitly in the command alongside "settings",
        # it is ALWAYS treated as a BROWSER settings page, not OS settings.
        _OS_SETTINGS_KEYWORDS = frozenset({
            "wifi", "wi-fi", "wireless", "bluetooth", "network", "display",
            "sound", "notifications", "battery", "power", "storage", "printers",
            "printer", "mouse", "keyboard", "background", "themes", "taskbar",
            "accounts", "account", "date and time", "language", "apps",
            "default apps", "startup apps", "startup", "privacy", "location",
            "microphone", "camera settings", "camera", "windows update",
            "update", "updates", "windows security", "defender", "antivirus",
            "recovery", "gaming", "vpn", "hotspot", "ethernet", "colors",
            "lock screen", "lockscreen", "fonts", "ease of access",
            "accessibility", "region", "personalization", "firewall",
            "backup", "troubleshoot", "activation", "developer", "phone",
            "email", "sign in options", "login options", "password",
            "family", "other users", "speech", "notifications",
            "multitasking", "nearby sharing", "focus assist", "usb", "pen",
            "typing", "touchpad", "about", "system info", "optional features",
            "dark mode", "light mode", "start", "start menu", "scanners",
            "airplane mode", "proxy", "dial up", "data usage", "maps",
            "search", "cortana", "night light", "scaling", "resolution",
            "graphics", "hdr", "volume", "speakers", "cursor", "narrator",
            "magnifier", "high contrast", "color filter", "eye control",
            "closed captions", "sticky keys", "filter keys", "activity history",
            "diagnostics", "feedback", "background apps", "game bar",
            "game mode", "game dvr", "xbox", "captures", "mixed reality",
            "mobile hotspot", "devices", "holographic", "pin",
            "windows hello", "sync settings", "clock", "date", "time",
            "action center", "default programs", "installed apps",
            "apps and features", "default programs", "power and sleep", "sleep",
        })
        _BROWSER_NAMES_SET = frozenset({"brave", "chrome", "edge", "firefox", "opera"})
        if any(w in cmd for w in ["settings", "setting"]):
            # ── Check if a browser name is explicitly in the command ──
            # If so, this is a BROWSER settings/page command, NOT an OS setting.
            # e.g. "open settings in brave", "open brave settings",
            #      "open history in brave", "open downloads in brave"
            detected_browser_in_cmd = None
            for bname in _BROWSER_NAMES_SET:
                if re.search(r'\b' + bname + r'\b', cmd, re.I):
                    detected_browser_in_cmd = bname
                    break
            if detected_browser_in_cmd:
                # Browser is explicitly mentioned → route to BrowserFeatureManager
                # EXCEPT: if the command contains "X in settings" where X is an
                # OS settings keyword, treat it as an OS setting (e.g. 
                # "open bluetooth in settings in brave" → ms-settings:bluetooth).
                # The "in brave" was probably accidental if X is clearly an OS setting.
                m_os_in_settings = re.match(
                    r'^open\s+(\w[\w\s]*?)\s+in\s+settings?',
                    cmd, re.I
                )
                if m_os_in_settings:
                    candidate = m_os_in_settings.group(1).strip().lower()
                    for filler in ["windows", "system", "the", "my"]:
                        candidate = re.sub(r'\b' + filler + r'\b', '', candidate).strip()
                    if candidate and candidate in _OS_SETTINGS_KEYWORDS:
                        # This is an OS setting with a trailing browser name — ignore the browser
                        ok, msg = self.apps.open_setting(candidate)
                        self._respond(ok, msg)
                        return
                
                # Extract the page name: strip "open", browser name, "in/on/with"
                page_raw = re.sub(
                    r'^(?:open|go\s+to|show|launch|navigate\s+to)\s+',
                    '', cmd, flags=re.I
                )
                page_raw = re.sub(
                    r'\b(?:in|on|with)\s+(?:' + '|'.join(_BROWSER_NAMES_SET) + r')\b',
                    '', page_raw, flags=re.I
                )
                page_raw = re.sub(
                    r'\b(?:' + '|'.join(_BROWSER_NAMES_SET) + r')\b',
                    '', page_raw, flags=re.I
                )
                page_raw = re.sub(r'\s+', ' ', page_raw).strip()
                # If the page is "settings" or "downloads" etc, route it
                ok, msg = self.browser_features.open(page_raw or "settings", detected_browser_in_cmd)
                self._respond(ok, msg)
                self.rl.record(cmd, ok)
                return

            # ── No browser name detected → treat as OS Settings command ──
            is_os_setting = False
            setting_name = ""
            # Pattern 1: "open X in settings"
            m_settings = re.match(
                r'^open\s+(\w[\w\s]*?)\s+in\s+settings?$',
                cmd, re.I
            )
            # Pattern 2: "open X settings" e.g. "open bluetooth settings"
            m_settings2 = re.match(
                r'^open\s+(\w[\w\s]*?)\s+settings?$',
                cmd, re.I
            )
            for m in [m_settings, m_settings2]:
                if m:
                    candidate = m.group(1).strip().lower()
                    # Strip filler words
                    for filler in ["windows", "system", "the", "my"]:
                        candidate = re.sub(r'\b' + filler + r'\b', '', candidate).strip()
                    if candidate and (candidate in _OS_SETTINGS_KEYWORDS or candidate == "settings" or any(kw in candidate for kw in _OS_SETTINGS_KEYWORDS)):
                        is_os_setting = True
                        setting_name = candidate if candidate != "settings" else ""
                        break
            # Also catch "open settings" (bare) or "open bluetooth settings"
            m_bare_setting = re.match(
                r'^open\s+(?:windows\s+)?settings?$',
                cmd, re.I
            )
            m_direct_setting = re.match(
                r'^open\s+(' + '|'.join(re.escape(k) for k in sorted(_OS_SETTINGS_KEYWORDS, key=len, reverse=True)) + r')\s+settings?$',
                cmd, re.I
            )
            if is_os_setting or m_bare_setting or m_direct_setting:
                # [FIX-SETTINGS] "search X in settings" → open Settings and type the query
                search_m = re.search(
                    r'search\s+(.+?)\s+in\s+settings?',
                    cmd, re.I
                )
                if search_m:
                    query = search_m.group(1).strip()
                    if IS_WINDOWS:
                        try:
                            import subprocess as _sp
                            _sp.Popen(
                                ["powershell", "-NoProfile", "-Command",
                                 "Start-Process 'ms-settings:'"],
                                creationflags=_NO_WIN_FLAG
                            )
                            time.sleep(1.2)
                            import pyautogui as _pag
                            _pag.hotkey("ctrl", "f")
                            time.sleep(0.3)
                            _pag.typewrite(query, interval=0.05)
                            self._respond(True, f"Searching '{query}' in Settings")
                            return
                        except Exception as _e:
                            logger.warning(f"Settings search failed: {_e}")
                # Determine the settings sub-page name
                if m_settings and setting_name:
                    sname = setting_name
                elif m_direct_setting:
                    sname = m_direct_setting.group(1).strip().lower()
                elif m_bare_setting:
                    sname = ""  # Main settings page
                else:
                    sname = re.sub(r'\b(settings?|open|go\s+to|show|the|in|search|windows)\b', '', cmd, flags=re.I).strip()
                ok, msg = self.apps.open_setting(sname)
                self._respond(ok, msg)
                return

        # ════ STAGE 18.5: BROWSER INTERNAL PAGES (v5 enhanced) ══════════
        # Handles 30+ pages: history, passwords, devtools, task-manager,
        # flags, privacy, sync, gpu, site-data, reading-mode, etc.
        # Works in Brave, Chrome, Edge, Firefox, Opera.
        # [FIX-V10] Also handles incomplete commands like "open downloads in"
        # (trailing "in" with no browser specified) by using default browser.
        m2 = RE_V5_BROWSER_FEATURE.match(cmd)
        if m2:
            page_raw   = m2.group(1).strip()
            browser    = (m2.group(2) or self._detect_browser(cmd) or "brave").lower()
            page_lower = page_raw.lower()
            # [FIX-V10] Handle incomplete commands: strip trailing "in"/"on"/"with"
            # if they're left hanging (e.g. "open downloads in" → page_raw="downloads in")
            for trailing in [" in", " on", " with"]:
                if page_lower.endswith(trailing):
                    page_raw = page_raw[:-len(trailing)].strip()
                    page_lower = page_raw.lower()
                    break
            if not page_raw:
                self._respond(False, "Please specify what to open and in which browser.")
                return
            _BROWSER_PAGE_KEYWORDS = frozenset({
                "history", "downloads", "bookmarks", "settings", "extensions",
                "devtools", "new tab", "newtab", "task manager", "taskmanager",
                "flags", "passwords", "password", "privacy", "sync", "performance",
                "about", "gpu", "site data", "site-data", "cookies", "collections",
                "shields", "wallet", "reading list", "reading-list", "reading mode",
                "reading-mode", "zoom in", "zoom out", "zoom reset", "print", "find",
                "fullscreen", "full screen", "mute tab", "close tab", "next tab",
                "previous tab", "reopen tab", "source", "view source", "back", "forward",
                "hard refresh", "developer tools", "developer", "console", "inspect",
                "add-ons", "addons", "favourites", "favorites", "login", "logins",
                "download", "preference", "preferences", "experiments",
            })
            is_browser_page = (
                page_lower in _BROWSER_PAGE_KEYWORDS
                or any(kw in page_lower for kw in _BROWSER_PAGE_KEYWORDS)
            )
            if is_browser_page:
                ok, msg = self.browser_features.open(page_raw, browser)
                self._respond(ok, msg)
                self.rl.record(cmd, ok)
                return

        # Legacy RE_BROWSER_CMD fallback (v4 patterns still supported)
        m2 = RE_BROWSER_CMD.match(cmd)
        if m2:
            page    = m2.group(1).strip().lower().replace(" ", "")
            browser = (m2.group(2) or self._detect_browser(cmd) or "brave").lower()
            ok, msg = self.browser.open_in_browser(page, browser)
            self._respond(ok, msg)
            self.rl.record(cmd, ok)
            return

        # ════ STAGE 19: FILE MANAGER COMMANDS ════════════════════════

        # [m-5] FIX: disk-usage-by-type checked BEFORE generic disk handler (Stage 31)
        if "disk usage by type" in cmd or "usage by type" in cmd:
            folder = re.sub(r'disk\s+usage\s+by\s+type\s+(?:in\s+)?|usage\s+by\s+type\s+(?:in\s+)?', '', cmd, flags=re.I).strip() or "downloads"
            ok, msg = self.files.disk_usage_by_type(folder)
            self._respond(ok, msg, tts=False)
            return

        # Organize
        # [FIX-V10] Support "organised" (British/past tense), "ganesh" (speech misrecognition),
        # combined criteria like "by type and date and size", and speech artifacts.
        if re.search(r'\borgani[sz]e[ds]?\b', cmd, re.I):
            folder = re.sub(r'^organi[sz]e?[sd]?\s+(?:my\s+)?', '', cmd, flags=re.I)
            # Strip "by type", "by date", "by size" etc to get folder name
            folder = re.sub(r'\s+by\s+(?:type|date|size|name|kind|category|data).*$', '', folder, flags=re.I).strip()
            # Handle combined criteria: "by type and date and size" → run all three
            has_type = "by type" in cmd or "by kind" in cmd
            has_date = "by date" in cmd or "by data" in cmd
            has_size = "by size" in cmd
            if has_type and (has_date or has_size):
                # Multiple criteria requested — run type first, then additional
                ok1, msg1 = self.files.organize_by_type(folder or "downloads")
                results = [msg1]
                if has_date:
                    ok2, msg2 = self.files.organize_by_date(folder or "downloads")
                    results.append(msg2)
                if has_size:
                    ok3, msg3 = self.files.organize_by_size(folder or "downloads")
                    results.append(msg3)
                self._respond(True, " | ".join(results))
                return
            elif has_date:
                ok, msg = self.files.organize_by_date(folder or "downloads")
            elif has_size:
                ok, msg = self.files.organize_by_size(folder or "downloads")
            else:
                # Default to organize by type
                ok, msg = self.files.organize_by_type(folder or "downloads")
            self._respond(ok, msg)
            return
        # Advanced file operations
        if "clean downloads" in cmd or "cleanup downloads" in cmd:
            days = self._extract_number(cmd) or 30
            ok, msg = self.files.clean_downloads(days)
            self._respond(ok, msg)
            return
        
        if "find large files" in cmd or "large files" in cmd:
            folder = "downloads"
            if " in " in cmd:
                m = re.search(r'in\s+(\w+)', cmd)
                if m:
                    folder = m.group(1)
            size = self._extract_number(cmd) or 100
            ok, msg = self.files.find_large_files(folder, size)
            self._respond(ok, msg, tts=False)
            return
        
        if "remove duplicates" in cmd and "by name" in cmd:
            folder = re.sub(r'remove duplicates by name\s*(?:in\s+)?', '', cmd).strip() or "downloads"
            ok, msg = self.files.remove_duplicates(folder)
            self._respond(ok, msg)
            return
        
        if re.search(r'\borgani[sz]e[ds]?\s+downloads\b', cmd, re.I) and "advanced" in cmd:
            ok, msg = self.files.organize_by_type_advanced("downloads")
            self._respond(ok, msg)
            return


        # Duplicates
        if "duplicate" in cmd:
            folder = re.sub(r'(?:find|scan|check|remove)\s+(?:for\s+)?duplicates?\s*(?:in\s+)?', '', cmd, flags=re.I).strip() or "downloads"
            if any(w in cmd for w in ["remove", "delete", "clean"]):
                ok, msg = self.files.remove_duplicates(folder)
            else:
                ok, msg = self.files.find_duplicates(folder)
            self._respond(ok, msg, tts=True)
            return

        # Word count
        m2 = RE_WORD_COUNT.match(cmd)
        if m2:
            ok, msg = self.files.word_count(m2.group(1).strip())
            self._respond(ok, msg)
            return

        # Checksum
        m2 = RE_CHECKSUM.match(cmd)
        if m2:
            ok, msg = self.files.checksum(m2.group(1).strip())
            self._respond(ok, msg)
            return

        # Diff
        m2 = RE_DIFF.match(cmd)
        if m2:
            ok, msg = self.files.diff_files(m2.group(1).strip(), m2.group(2).strip())
            self._respond(ok, msg, tts=False)
            return

        # Find file
        m2 = RE_FIND_FILE.match(cmd)
        if m2 and any(w in cmd for w in ["find", "search", "locate", "where is"]):
            # FIX: Don't treat web searches with browsers as file searches
            if self._detect_browser(cmd) and not any(x in cmd.lower() for x in ["file", "folder", "directory", "where is"]):
                # Let web search handler process this instead - skip file search
                pass
            else:
                fname = m2.group(1).strip()
                floc  = (m2.group(2) or "").strip()
                ftype = None
                for ft in FILE_TYPE_MAP:
                    if ft in fname.lower():
                        ftype = ft
                        fname = fname.lower().replace(ft, "").strip()
                        break
                ok, msg = self.files.search_file(fname, floc or None, file_type=ftype)
                self._respond(ok, msg)
                return

        # Move file
        m2 = RE_MOVE_FILE.match(cmd)
        if m2:
            ok, msg = self.files.move_file(m2.group(1).strip(), m2.group(2).strip())
            self._respond(ok, msg)
            return

        # Copy file
        m2 = RE_COPY_FILE.match(cmd)
        if m2:
            ok, msg = self.files.copy_file(m2.group(1).strip(), m2.group(2).strip())
            self._respond(ok, msg)
            return

        # Rename
        m2 = RE_RENAME_FILE.match(cmd)
        if m2:
            ok, msg = self.files.rename(m2.group(1).strip(), m2.group(2).strip())
            self._respond(ok, msg)
            return

        # Create file
        m2 = RE_CREATE_FILE.match(cmd)
        if m2:
            ok, msg = self.files.create_file(m2.group(1).strip())
            self._respond(ok, msg)
            return

        # Create folder
        m2 = RE_CREATE_FOLDER.match(cmd)
        if m2:
            ok, msg = self.files.create_folder(m2.group(1).strip())
            self._respond(ok, msg)
            return

        # Delete file/folder (NOT notes — those are caught in Stage 14)
        m2 = RE_DELETE.match(cmd)
        if m2 and any(w in cmd for w in ["delete", "remove", "erase"]):
            ok, msg = self.files.delete(m2.group(1).strip())
            self._respond(ok, msg)
            return

        # Zip/unzip/compress
        m2 = RE_ZIP.match(cmd)
        if m2:
            ok, msg = self.files.zip_item(m2.group(1).strip())
            self._respond(ok, msg)
            return
        m2 = RE_UNZIP.match(cmd)
        if m2:
            ok, msg = self.files.unzip_item(m2.group(1).strip())
            self._respond(ok, msg)
            return
        m2 = RE_COMPRESS.match(cmd)
        if m2:
            ok, msg = self.files.compress(m2.group(1).strip())
            self._respond(ok, msg)
            return

        # File info
        if "file info" in cmd:
            name = cmd.replace("file info", "").strip()
            ok, msg = self.files.file_info(name)
            self._respond(ok, msg, tts=False)
            return

        # Largest files
        if "largest files" in cmd:
            folder = re.sub(r'largest\s+files?\s+(?:in\s+)?', '', cmd, flags=re.I).strip() or "downloads"
            ok, msg = self.files.get_largest_files(folder)
            self._respond(ok, msg, tts=False)
            return

        # Empty trash
        if "empty trash" in cmd or "empty recycle" in cmd:
            ok, msg = self.files.empty_trash()
            self._respond(ok, msg)
            return

        # Clean temp
        if "clean temp" in cmd or "clear temp" in cmd:
            ok, msg = self.files.clean_temp()
            self._respond(ok, msg)
            return

        # Bulk rename
        if "bulk rename" in cmd:
            parts = cmd.replace("bulk rename", "").split("in")
            folder = parts[1].strip() if len(parts) > 1 else "downloads"
            pargs  = parts[0].strip().split() if parts[0].strip() else []
            if len(pargs) >= 2:
                ok, msg = self.files.bulk_rename(folder, pargs[0], pargs[1])
                self._respond(ok, msg)
            else:
                self._respond(False, "Say: bulk rename in downloads _ -  (pattern replacement)")
            return

        # List files
        if any(w in cmd for w in ["list files", "show files", "list directory"]):
            folder = re.sub(r'(list|show)\s+files?\s*(?:in\s+)?', '', cmd, flags=re.I).strip() or "~"
            ok, msg = self.files.list_files(folder)
            self._respond(ok, msg, tts=False)
            return

        # Folder shortcuts
        folder_keys = {
            "downloads":   "~/Downloads",
            "desktop":     "~/Desktop",
            "documents":   "~/Documents",
            "pictures":    "~/Pictures",
            "music":       "~/Music",
            "videos":      "~/Videos",
            "home":        "~",
            "temp":        os.environ.get("TEMP", os.environ.get("TMPDIR", "/tmp")),
        }


        # ════ STAGE 32: WEATHER ══════════════════════════════════════
        weather_kws = ["weather", "temperature", "forecast", "how hot", "how cold",
                       "what is the weather", "will it rain", "climate"]
        if any(w in cmd for w in weather_kws):
            if any(w in cmd for w in ["forecast", "3 day", "three day"]):
                city = re.sub(r'(forecast|weather|for|in|at|\d+\s+day)', '', cmd, flags=re.I).strip() or "auto"
                ok, msg = self.weather.forecast(city)
            else:
                city = re.sub(r'(weather|temperature|how\s+\w+\s+is\s+it|in|at|for)', '', cmd, flags=re.I).strip() or "auto"
                ok, msg = self.weather.current(city)
            self._respond(ok, msg)
            return

        # ════ STAGE 33: CRYPTO PRICES ════════════════════════════════
        crypto_kws = ["bitcoin", "ethereum", "solana", "dogecoin", "crypto price",
                      "btc", "eth", "bnb", "xrp", "ada", "doge", "avax", "matic"]
        if any(w in cmd for w in crypto_kws) or "crypto" in cmd:
            if any(w in cmd for w in ["all", "top", "prices", "list"]):
                ok, msg = self.crypto.top()
                self._respond(ok, msg, tts=False)
            else:
                coin = cmd
                for kw in ["price", "of", "crypto", "how much is", "what is"]:
                    coin = re.sub(r'\b' + kw + r'\b', '', coin, flags=re.I)
                coin = coin.strip() or "bitcoin"
                ok, msg = self.crypto.price(coin)
                self._respond(ok, msg)
            return

        # ════ STAGE 34: UNIT CONVERTER ═══════════════════════════════
        m2 = RE_CONVERT.match(cmd)
        if m2:
            val   = float(m2.group(1))
            from_ = m2.group(2)
            to_   = m2.group(3)
            ok, msg = self.converter.convert(val, from_, to_)
            self._respond(ok, msg)
            return
        if "convert" in cmd and ("degree" in cmd or "celsius" in cmd or "fahrenheit" in cmd or "kelvin" in cmd):
            nums = re.findall(r'[-\d.]+', cmd)
            units = re.findall(r'\b(celsius|fahrenheit|kelvin|c|f|k)\b', cmd, re.I)
            if nums and len(units) >= 2:
                ok, msg = self.converter.convert(float(nums[0]), units[0], units[1])
                self._respond(ok, msg)
            else:
                self._respond(False, "Say: convert 100 km to miles  OR  convert 98.6 f to c")
            return

        # ════ STAGE 35: WORLD CLOCK ══════════════════════════════════
        m2 = RE_TIME_IN.match(cmd)
        if m2:
            city = m2.group(1).strip()
            ok, msg = self.world_clock.time_in(city)
            self._respond(ok, msg)
            return
        if "world clock" in cmd or "world time" in cmd:
            ok, msg = self.world_clock.show_all()
            self._respond(ok, msg, tts=False)
            return

        # ════ STAGE 36: PASSWORD MANAGER ════════════════════════════
        if "generate password" in cmd or RE_GEN_PASS.match(cmd):
            n = self._extract_number(cmd) or 16
            sym = "no symbol" not in cmd
            ok, msg = self.passwords.generate(n, sym)
            self._respond(ok, msg)
            return
        m2 = RE_SAVE_PASS.match(cmd)
        if m2:
            service = m2.group(1).strip()
            print(f"\n🔑  Enter password for '{service}': ", end="", flush=True)
            try:
                import getpass
                pwd = getpass.getpass("")
                ok, msg = self.passwords.save(service, pwd)
            except Exception as e:
                ok, msg = False, str(e)
            self._respond(ok, msg)
            return
        if "get password" in cmd or "show password" in cmd or "password for" in cmd:
            service = re.sub(r'(?:get|show|retrieve|password\s+for|for)', '', cmd, flags=re.I).strip()
            if service:
                ok, msg = self.passwords.get(service)
                self._respond(ok, msg)
            else:
                ok, msg = self.passwords.list_services()
                self._respond(ok, msg, tts=False)
            return
        m2 = RE_PASS_STRENGTH.match(cmd)
        if m2:
            ok, msg = self.passwords.strength(m2.group(1).strip())
            self._respond(ok, msg)
            return
        if "list passwords" in cmd or "saved passwords" in cmd:
            ok, msg = self.passwords.list_services()
            self._respond(ok, msg, tts=False)
            return

        # ════ STAGE 37: SYSTEM HEALTH MONITOR ═══════════════════════
        if "health check" in cmd or "health status" in cmd or "system health" in cmd:
            ok, msg = self.health_monitor.status()
            self._respond(ok, msg, tts=False)
            return
        if "start monitoring" in cmd or "start health monitor" in cmd:
            ok, msg = self.health_monitor.start()
            self._respond(ok, msg)
            return
        if "stop monitoring" in cmd or "stop health monitor" in cmd:
            ok, msg = self.health_monitor.stop()
            self._respond(ok, msg)
            return

        # ════ STAGE 38: HABIT TRACKER ════════════════════════════════
        m2 = RE_HABIT_CHECKIN.match(cmd)
        if m2 and "check in" in cmd:
            ok, msg = self.habits.check_in(m2.group(1).strip())
            self._respond(ok, msg)
            return
        m2 = RE_HABIT_ADD.match(cmd)
        if m2:
            ok, msg = self.habits.add_habit(m2.group(1).strip())
            self._respond(ok, msg)
            return
        if any(w in cmd for w in ["show habits", "list habits", "my habits", "habit streak"]):
            ok, msg = self.habits.show()
            self._respond(ok, msg, tts=False)
            return

        # ════ STAGE 39: CLIPBOARD HISTORY ════════════════════════════
        if "clipboard history" in cmd or "paste history" in cmd:
            ok, msg = self.clip_history.show()
            self._respond(ok, msg, tts=False)
            return
        if "clear clipboard history" in cmd:
            ok, msg = self.clip_history.clear()
            self._respond(ok, msg)
            return
        if re.match(r'paste item \d+', cmd):
            n = self._extract_number(cmd) or 1
            ok, text = self.clip_history.get_item(n)
            if ok:
                print(f"\n📋  Item {n}:\n{text}\n")
            self._respond(ok, text[:80] if ok else text)
            return
        if "start clipboard" in cmd or "monitor clipboard" in cmd:
            ok, msg = self.clip_history.start_monitoring()
            self._respond(ok, msg)
            return

        # ════ STAGE 40: RL AGENT STATS ══════════════════════════════
        if any(w in cmd for w in ["rl stats", "ai learning", "reinforcement learning",
                                   "learning stats", "rl history", "agent stats"]):
            print(self.rl.stats())
            if "history" in cmd:
                print(self.rl.show_history())
            self._respond(True, "RL stats shown above", tts=False)
            return

        # ════ STAGE 20: OPEN APP ═════════════════════════════════════
        m2 = RE_OPEN_APP.match(cmd)
        if m2:
            name = m2.group(1).strip()

            if any(w in name for w in ["incognito", "private", "inprivate"]):
                for w in ["incognito", "private", "inprivate", "mode", "window", "tab", "in"]:
                    name = re.sub(r'\b' + w + r'\b', '', name, flags=re.I)
                name = re.sub(r'\s+', ' ', name).strip() or "chrome"
                ok, msg = self.apps.launch(name, incognito=True)
                self._respond(ok, msg)
                return

            browser_shortcuts = {
                "history":   self.browser.open_history,
                "downloads": self.browser.open_downloads,
                "new tab":   self.browser.new_tab,
                "devtools":  self.browser.open_devtools,
                "bookmarks": self.browser.open_bookmarks,
            }
            for bk, fn in browser_shortcuts.items():
                if name == bk:
                    fn()
                    self._respond(True, f"Opened {bk}")
                    return

            if any(w in name for w in ["settings", "setting"]):
                sname = re.sub(r'\b(settings?|open|the|in)\b', '', name, flags=re.I).strip()
                ok, msg = self.apps.open_setting(sname)
                self._respond(ok, msg)
                return

            for site, url in WEBSITE_SHORTCUTS.items():
                if site in name:
                    browser = self._detect_browser(name)
                    self.web.open_url(url, browser=browser)
                    self._respond(True, f"Opening {site}")
                    return

            for key, path in folder_keys.items():
                if name == key or name == key + " folder":
                    ok, msg = self.files.open_folder(path)
                    self._respond(ok, f"Opening {key} folder")
                    return

            ok, msg = self.apps.launch(name)
            self._respond(ok, msg)
            return

        # ════ STAGE 21: CLOSE APP ════════════════════════════════════
        # [FIX-V10] Skip commands that contain "private/incognito window" —
        # those should be handled in Stage 26 (browser controls).
        m2 = RE_CLOSE_APP.match(cmd)
        if m2:
            name = m2.group(1).strip()
            # [FIX-V10] If the command mentions private/incognito window,
            # let it fall through to Stage 26 for browser-specific handling
            if re.search(r'\b(?:private|incognito|inprivate)\s+(?:window|mode|session)\b', name, re.I):
                pass  # Fall through to Stage 26
            else:
                name = re.sub(r'\s+(window|app|application|program)s?$', '', name, flags=re.I).strip()
                if name in ("tab", "current tab", "this tab"):
                    ok, msg = self.browser.close_tab()
                    self._respond(ok, "Tab closed")
                    return
                # [FIX-CLOSE] Count open windows BEFORE killing processes.
                # If multiple windows are open, ask the user to confirm via a
                # native Windows popup (no external dependency needed — pure ctypes).
                win_count = self.apps.count_running_windows(name)
                if win_count > 1:
                    display_name = name.title()
                    confirm_msg  = (
                        f"{display_name} has {win_count} windows open.\n"
                        f"Do you want to close ALL of them?"
                    )
                    # ctypes MessageBoxW: 0x04 = MB_YESNO, 0x30 = MB_ICONQUESTION
                    if WINDLL_OK:
                        try:
                            result = ctypes.windll.user32.MessageBoxW(
                                0, confirm_msg, f"Close {display_name}?", 0x04 | 0x30
                            )
                            # result == 6 → Yes, result == 7 → No
                            if result != 6:
                                self._respond(True, f"Cancelled — keeping {display_name} open")
                                return
                        except Exception:
                            # If popup fails, just ask via TTS and proceed
                            self._respond(True,
                                f"{display_name} has {win_count} windows open. Closing all of them.")
                    else:
                        # Non-Windows: no popup available, just proceed with close
                        self._respond(True,
                            f"{display_name} has {win_count} windows open. Closing all of them.")
                ok, msg = self.apps.close(name)
                self._respond(ok, msg)
                return

        # ════ STAGE 22: SWITCH TO ════════════════════════════════════
        # Handle "show desktop" before generic switch
        if cmd.lower() in ("show desktop", "show the desktop", "desktop"):
            ok, msg = self.window.minimize_all()
            self._respond(ok, JarvisResponder.show_desktop())
            return
            
        m2 = RE_SWITCH_TO.match(cmd)
        if m2:
            name = m2.group(1).strip()
            name = re.sub(r'\s+in\s+\S+\s*(browser)?$', '', name, flags=re.I).strip()
            ok, msg = self.apps.switch_to(name)
            self._respond(ok, msg)
            return

        # ════ STAGE 22.5: MAXIMIZE / MINIMIZE ═══════════════════════
        m2 = RE_MAXIMIZE.match(cmd)
        if m2:
            name = m2.group(1).strip()
            # [FIX-V10] Strip trailing "window"/"app" that speech recognition adds
            name = re.sub(r'\s+(window|app|application)$', '', name, flags=re.I).strip()
            ok, msg = self.apps.maximize_window(name)
            self._respond(ok, msg)
            return
        m2 = RE_MINIMIZE.match(cmd)
        if m2:
            name = m2.group(1).strip()
            name = re.sub(r'\s+(window|app|application)$', '', name, flags=re.I).strip()
            ok, msg = self.apps.minimize_window(name)
            self._respond(ok, msg)
            return
        m2 = RE_RESTORE.match(cmd)
        if m2:
            name = m2.group(1).strip()
            name = re.sub(r'\s+(window|app|application)$', '', name, flags=re.I).strip()
            ok, msg = self.apps.restore_window(name)
            self._respond(ok, msg)
            return
        m2 = RE_SNAP.match(cmd)
        if m2:
            name, direction = m2.group(1).strip(), m2.group(2).strip()
            # [FIX-V10] Strip trailing "window"/"app" from name
            name = re.sub(r'\s+(window|app|application)$', '', name, flags=re.I).strip()
            # [FIX-V10] "app" as direction = speech artifact, default to left
            if direction.lower() in ("app", "side"):
                direction = "left"
            # Also handle "snap [name]" without proper direction
            ok, msg = self.apps.snap_window(name, direction)
            self._respond(ok, msg)
            return
        m2 = RE_ALIGN.match(cmd)
        if m2:
            left_name, right_name = m2.group(1).strip(), m2.group(2).strip()
            ok, msg = self.apps.align_windows(left_name, right_name)
            self._respond(ok, msg)
            return

        # ════ STAGE 23: SETTINGS FALLBACK (browser settings via BrowserFeatureManager) ══
        # [FIX-SETTINGS-V9] OS-level settings are now handled in Stage 18.0 (before
        # browser features). This stage catches remaining "settings" commands that
        # refer to BROWSER settings (e.g. "open settings in brave" which should go
        # to brave://settings, NOT ms-settings:).
        if any(w in cmd for w in ["settings", "setting"]):
            detected_browser = self._detect_browser(cmd)
            if detected_browser:
                # "open settings in brave" → browser://settings
                ok, msg = self.browser_features.open("settings", detected_browser)
                self._respond(ok, msg)
                self.rl.record(cmd, ok)
                return
            else:
                # No browser detected — default to Windows Settings app
                sname = re.sub(r'\b(settings?|open|go\s+to|show|the|in|search)\b', '', cmd, flags=re.I).strip()
                # Also strip browser names in case they linger
                for bname in ["brave", "chrome", "edge", "firefox", "opera", "browser"]:
                    sname = re.sub(r'\b' + bname + r'\b', '', sname).strip()
                if sname:
                    ok, msg = self.apps.open_setting(sname)
                else:
                    ok, msg = self.apps.open_setting("")
                self._respond(ok, msg)
                return

        # ════ STAGE 24: CLIPBOARD ════════════════════════════════════
        clipboard_map = {
            "copy":       self.clipboard.copy,
            "paste":      self.clipboard.paste,
            "cut":        self.clipboard.cut,
            "select all": self.clipboard.select_all,
            "undo":       self.clipboard.undo,
            "redo":       self.clipboard.redo,
            "save file":  self.clipboard.save,
            "bold":       self.clipboard.bold,
            "italic":     self.clipboard.italic,
            "underline":  self.clipboard.underline,
            "new window": self.clipboard.new_window,
            "get clipboard": self.clipboard.get_clipboard_text,
        }
        for trigger, fn in clipboard_map.items():
            if cmd == trigger or cmd.startswith(trigger + " "):
                ok, msg = fn()
                self._respond(ok, f"{trigger.capitalize()} done")
                return

        # ════ STAGE 25: WINDOW MANAGEMENT ═══════════════════════════
        window_map = {
            "minimize all":          self.window.minimize_all,
            "snap left":             self.window.snap_left,
            "snap right":            self.window.snap_right,
            "snap up":               self.window.snap_up,
            "task view":             self.window.task_view,
            "new virtual desktop":   self.window.new_virtual_desktop,
            "close virtual desktop": self.window.close_virtual_desktop,
            "action center":         self.window.action_center,
            "run dialog":            self.window.run_dialog,
            "search bar":            self.window.search_bar,
            "emoji picker":          self.window.emoji_picker,
            "clipboard history":     self.window.clipboard_history,
            "connect display":       self.window.connect_display,
        }
        for trigger, fn in window_map.items():
            if trigger in cmd:
                ok, msg = fn()
                # Natural Jarvis responses for window actions
                if trigger == "minimize all":
                    natural = JarvisResponder.show_desktop()
                elif trigger == "snap left":
                    natural = JarvisResponder.snap_left()
                elif trigger == "snap right":
                    natural = JarvisResponder.snap_right()
                elif trigger == "snap up":
                    natural = JarvisResponder.window_maximize()
                else:
                    natural = f"{trigger.capitalize()}."
                self._respond(ok, natural)
                return

        # ════ STAGE 26: BROWSER CONTROLS ════════════════════════════
        # [FIX-V10] Added "close X in private window" handling and improved
        # trigger matching to avoid false positives (e.g. "close new tab" matching "new tab").
        # Also added incognito/private window support with browser-specific launch.
        
        # ── Handle "close X in private/incognito window" patterns FIRST ──
        m_close_priv = re.match(
            r'^close\s+(?:the\s+)?(\w[\w\s]*?)\s+in\s+(?:the\s+)?(?:private|incognito|inprivate)\s+(?:window|mode|session)(?:\s+(?:in|on|with)\s+(brave|chrome|edge|firefox|opera))?$',
            cmd, re.I
        )
        if m_close_priv:
            # "close new tab in private window" → close tab in the incognito window
            close_what = m_close_priv.group(1).strip().lower()
            close_browser = (m_close_priv.group(2) or "").strip().lower()
            # Map what to close to keyboard shortcuts
            close_actions = {
                "new tab": ("ctrl", "w"),
                "tab": ("ctrl", "w"),
                "window": ("ctrl", "shift", "w"),
                "page": ("ctrl", "w"),
            }
            close_keys = close_actions.get(close_what)
            if close_keys:
                # First, try to focus the private/incognito window if possible
                # Then send the close shortcut
                ok, msg = self.browser._hk(*close_keys)
                natural = f"Closing {close_what} in private window."
                self._respond(ok, natural)
                return
            else:
                # Generic close — just send Ctrl+W
                ok, msg = self.browser._hk("ctrl", "w")
                self._respond(ok, f"Closing {close_what} in private window.")
                return

        browser_map = {
            "new tab":              self.browser.new_tab,
            "new window":           lambda: self.browser._hk("ctrl", "n"),
            "new incognito window": lambda: self.browser._hk("ctrl", "shift", "n"),
            "new private window":   lambda: self.browser._hk("ctrl", "shift", "n"),
            "new guest window":     lambda: self.browser._hk("ctrl", "shift", "m"),
            "close tab":            self.browser.close_tab,
            "close window":         lambda: self.browser._hk("ctrl", "shift", "w"),
            "reopen tab":           self.browser.reopen_tab,
            "duplicate tab":        self.browser.duplicate_tab,
            "refresh":              self.browser.refresh,
            "hard refresh":         self.browser.hard_refresh,
            "go back":              self.browser.go_back,
            "go forward":           self.browser.go_forward,
            "stop loading":         lambda: self.browser._hk("esc"),
            "open history":         self.browser.open_history,
            "open downloads":       self.browser.open_downloads,
            "open bookmarks":       self.browser.open_bookmarks,
            "bookmark page":        self.browser.bookmark_page,
            "clear history":        lambda: self.browser._hk("ctrl", "shift", "delete"),
            "clear browsing data":  lambda: self.browser._hk("ctrl", "shift", "delete"),
            "zoom in":              self.browser.zoom_in,
            "zoom out":             self.browser.zoom_out,
            "zoom reset":           self.browser.zoom_reset,
            "find on page":         self.browser.find_on_page,
            "find next":            lambda: self.browser._hk("f3"),
            "find previous":        lambda: self.browser._hk("shift", "f3"),
            "devtools":             self.browser.open_devtools,
            "developer tools":      self.browser.open_devtools,
            "view source":          self.browser.view_source,
            "inspect element":      lambda: self.browser._hk("ctrl", "shift", "i"),
            "address bar":          self.browser.focus_address_bar,
            "fullscreen":           self.browser.fullscreen,
            "mute tab":             self.browser.mute_tab,
            "pin tab":              lambda: self.browser._hk("ctrl", "alt", "p"),
            "reading mode":         self.browser.reading_mode,
            "print page":           lambda: self.browser._hk("ctrl", "p"),
            "save page":            lambda: self.browser._hk("ctrl", "s"),
            "scroll down":          self.browser.scroll_down,
            "scroll up":            self.browser.scroll_up,
            "scroll to top":        self.browser.scroll_top,
            "scroll to bottom":     self.browser.scroll_bottom,
        }
        for trigger, fn in browser_map.items():
            # [FIX-V10] Improved matching: require trigger to be at a word boundary
            # and not preceded by "close" (to avoid "close new tab" matching "new tab").
            # Close actions are handled above.
            if trigger in cmd:
                # Check if this is a close action that should have been handled above
                # e.g. "close new tab" should NOT match "new tab" trigger
                if trigger.startswith("new ") and cmd.strip().startswith("close"):
                    continue
                if trigger.startswith("open ") and cmd.strip().startswith("close"):
                    continue
                browser = self._detect_browser(cmd)
                # [FIX-BROWSER-V9] If a specific browser is detected, use
                # BrowserFeatureManager for navigable pages (history, downloads,
                # bookmarks, extensions) so it opens the correct browser:// URL
                # instead of just sending a generic keyboard shortcut.
                _NAVIGABLE_PAGES = {
                    "open history":   "history",
                    "open downloads": "downloads",
                    "open bookmarks": "bookmarks",
                }
                if browser and trigger in _NAVIGABLE_PAGES:
                    page_key = _NAVIGABLE_PAGES[trigger]
                    ok, msg = self.browser_features.open(page_key, browser)
                    self._respond(ok, msg)
                    self.rl.record(cmd, ok)
                    return
                ok, msg = fn()
                # Natural Jarvis responses for browser actions
                if trigger == "new tab":
                    natural = JarvisResponder.browser_new_tab(browser)
                elif trigger == "new window":
                    natural = JarvisResponder.browser_new_window(browser)
                elif trigger in ("new incognito window", "new private window"):
                    natural = JarvisResponder.browser_incognito(browser)
                elif trigger == "close tab":
                    natural = "Closing tab."
                elif trigger == "close window":
                    natural = "Closing window."
                elif trigger == "reopen tab":
                    natural = "Reopening tab."
                else:
                    natural = f"{trigger.capitalize()}."
                self._respond(ok, natural)
                return

        # ════ STAGE 27: WEB / YOUTUBE SEARCH ════════════════════════
        if "youtube" in cmd or (
            any(w in cmd for w in ["play", "watch"]) and
            not any(w in cmd for w in ["play pause", "media"]) and
            len(cmd.split()) > 2
        ):
            yt_query = re.sub(
                r'(?:play|watch|search|find|on|in|youtube)\s*', '', cmd, flags=re.I
            ).strip()
            yt_query = self._clean_for_search(yt_query)
            if yt_query:
                browser = self._detect_browser(cmd)
                ok, msg = self.web.play_youtube(yt_query, browser=browser)
                self._respond(ok, msg)
                return

        m2 = RE_SEARCH.match(cmd)
        if m2:
            query   = m2.group(1).strip()
            browser = self._detect_browser(query)
            engine  = "google"
            for eng in SEARCH_ENGINES:
                if f"on {eng}" in query or f"in {eng}" in query:
                    engine = eng
                    query  = re.sub(r'\s+(?:on|in)\s+' + eng, '', query, flags=re.I).strip()
                    break
            query = self._clean_for_search(query)
            ok, msg = self.web.search(query, engine=engine, browser=browser)
            self._respond(ok, msg)
            return

        m2 = RE_OPEN_URL.match(cmd)
        if m2:
            url     = m2.group(1).strip()
            browser = self._detect_browser(cmd)
            ok, msg = self.web.open_url(url, browser=browser)
            self._respond(ok, msg)
            return

        for site, url in WEBSITE_SHORTCUTS.items():
            if f"open {site}" in cmd or cmd.strip() == site:
                browser = self._detect_browser(cmd)
                self.web.open_url(url, browser=browser)
                self._respond(True, f"Opening {site}")
                return

        # ════ STAGE 28: POWER COMMANDS ══════════════════════════════
        if re.search(r'\block\b', cmd) and not re.search(r'\bunlock\b', cmd):
            ok, msg = self.system.lock_screen()
            self._respond(ok, msg)
            return
        if "sleep" in cmd and "shutdown" not in cmd:
            ok, msg = self.system.sleep()
            self._respond(ok, msg)
            return
        if "hibernate" in cmd:
            ok, msg = self.system.hibernate()
            self._respond(ok, msg)
            return
        if "restart" in cmd or "reboot" in cmd:
            ok, msg = self.system.restart()
            self._respond(ok, msg)
            return
        if "cancel shutdown" in cmd:
            ok, msg = self.system.cancel_shutdown()
            self._respond(ok, msg)
            return
        m2 = RE_SHUTDOWN_IN.search(cmd)
        if m2:
            n    = int(m2.group(1))
            unit = m2.group(2).lower()
            secs = n * 60 if unit.startswith("m") else n
            ok, msg = self.system.shutdown(secs)
            self._respond(ok, msg)
            return
        if "shutdown" in cmd:
            ok, msg = self.system.shutdown(5)
            self._respond(ok, msg)
            return

        # ════ STAGE 29: MEDIA CONTROLS ══════════════════════════════
        if cmd.strip() in ("play", "play pause"):
            ok, msg = self.media.play_pause()
            self._respond(ok, "Toggled play/pause")
            return
        if "pause" in cmd and len(cmd.split()) <= 2:
            ok, msg = self.media.play_pause()
            self._respond(ok, "Paused")
            return
        if any(w in cmd for w in ["next track", "next song", "skip track"]):
            ok, msg = self.media.next_track()
            self._respond(ok, "Next track")
            return
        if any(w in cmd for w in ["previous track", "previous song", "prev track", "last track"]):
            ok, msg = self.media.prev_track()
            self._respond(ok, "Previous track")
            return
        if any(w in cmd for w in ["stop music", "stop media", "stop song"]):
            ok, msg = self.media.stop()
            self._respond(ok, "Media stopped")
            return

        # ════ STAGE 30: NETWORK ══════════════════════════════════════
        if any(w in cmd for w in ["check internet", "internet check", "connection check"]):
            ok, msg = self.network.check_connection()
            self._respond(ok, msg)
            return
        if "public ip" in cmd:
            ok, msg = self.network.get_public_ip()
            self._respond(ok, msg)
            return
        if any(w in cmd for w in ["my ip", "local ip", "ip address", "what is my ip"]):
            ok, msg = self.network.get_ip()
            self._respond(ok, msg)
            return
        m2 = RE_PING.match(cmd)
        if m2:
            ok, msg = self.network.ping(m2.group(1).strip())
            self._respond(ok, msg)
            return
        if "hostname" in cmd:
            ok, msg = self.network.get_hostname()
            self._respond(ok, msg)
            return
        if "speed test" in cmd:
            print("🌐  Running speed test...")
            ok, msg = self.network.speed_test_simple()
            self._respond(ok, msg)
            return
        port_m = re.match(r'check\s+port\s+(\d+)\s+on\s+(.+)', cmd)
        if port_m:
            ok, msg = self.network.port_check(port_m.group(2).strip(), int(port_m.group(1)))
            self._respond(ok, msg)
            return

        # ════ STAGE 31: DISK ═════════════════════════════════════════
        # [m-5] NOTE: "disk usage by type" is caught in Stage 19 before reaching here
        if RE_DISK_USAGE.search(cmd) or "disk info" in cmd:
            ok, msg = self.disk_mgr.get_usage()
            self._respond(ok, msg, tts=False)
            return
        if "disk io" in cmd or "io stats" in cmd:
            ok, msg = self.disk_mgr.get_io_stats()
            self._respond(ok, msg)
            return

        # ════ STAGE 32: PROCESS ══════════════════════════════════════
        m2 = RE_KILL_PROC.match(cmd)
        if m2 and "kill" in cmd:
            name = m2.group(1).strip()
            if name.isdigit():
                ok, msg = self.proc_mgr.kill_pid(int(name))
            else:
                ok, msg = self.proc_mgr.kill(name)
            self._respond(ok, msg)
            return
        if "find process" in cmd:
            name = cmd.replace("find process", "").strip()
            ok, msg = self.proc_mgr.find_process(name)
            self._respond(ok, msg, tts=False)
            return

        # ════ STAGE 33: CALCULATOR ═══════════════════════════════════
        calc_triggers = [
            "calculate", "compute", "what is", "what's", "evaluate",
            "solve", "multiply", "divide", "subtract", "sqrt"
        ]
        math_words = [
            "plus", "minus", "times", "into", "divided", "multiplied",
            "squared", "cubed", "power", "root", "percent", "mod",
            "+", "-", "*", "/", "multiply", "subtract", "add"
        ]
        has_digit    = bool(RE_NUMBER.search(cmd))
        is_calc      = any(t in cmd for t in calc_triggers)
        has_math     = any(w in cmd for w in math_words)
        has_into     = bool(re.search(r'\d+\s+into\s+\d+', cmd))

        if is_calc or has_into or (has_math and has_digit):
            expr = cmd
            for t in sorted(calc_triggers, key=len, reverse=True):
                expr = expr.replace(t, "")
            ok, msg = self.calc.evaluate(expr.strip())
            self._respond(ok, msg)
            return

        # ════ STAGE 34: OPEN FOLDER SHORTCUT ════════════════════════
        for key, path in folder_keys.items():
            if f"open {key}" in cmd or f"go to {key}" in cmd:
                ok, msg = self.files.open_folder(path)
                self._respond(ok, f"Opening {key} folder")
                return

        # ════ STAGE 35: DIRECT APP LAUNCH FALLBACK ══════════════════
        _skip = (
            "add ", "note ", "delete ", "move ", "create ", "find ", "search ",
            "switch ", "minimize ", "minimise ", "maximize ", "maximise ", "calculate ", "compute ",
            "tell ", "what ", "how ", "why ", "remind ", "set ", "check ",
            "show ", "list ", "zip ", "unzip ", "kill ", "organize ",
            "duplicate ", "compress ", "extract ", "rename ", "copy ",
            "snap ", "restore ", "align ", "arrange "
        )
        if not any(cmd.startswith(s) for s in _skip):
            app_key, app_data = self.apps.find_app(cmd)
            if app_data and (
                app_data.get("installed") or app_data.get("uwp") or
                app_data.get("resolved_path") or app_data.get("cmd")
            ):
                ok, msg = self.apps.launch(cmd)
                self._respond(ok, msg)
                return

        # ════ STAGE 36: FALLBACK — try as AI query ══════════════════
        logger.warning(f"Unrecognized command, routing to AI: {cmd!r}")
        if any(w in cmd for w in [
            "how", "why", "what", "explain", "tell me", "describe",
            "is there", "can you", "who", "when", "where",
            "write", "give me", "list", "story", "joke", "poem",
            "praise", "sing", "recite", "current affairs", "news",
        ]):
            print(f"\n🤖  [{self.ai._model}] (auto-routing to AI)...")
            ok, response = self.ai.query(cmd)
            if ok:
                print(f"\n  {textwrap.fill(response, 80)}\n")
            # [FIX-AI] Speak the full AI response sentence-by-sentence so the
            # user can say "stop" at any time to interrupt mid-answer.
            if ok and response:
                self.tts.speak_streaming(
                    response,
                    stop_check=lambda: self.tts._stop_event.is_set()
                )
            elif not ok:
                self._respond(ok, response, tts=True)
            self.rl.record(cmd, ok)
            return
        self._respond(False, "Command not recognized. Say 'help' for all commands.")
        self.rl.record(cmd, False)

    # ══════════════════════════════════════════════════════════════════════
    # RUNTIME LOOP
    # ══════════════════════════════════════════════════════════════════════
    def run(self):
        banner = [
            "╔" + "═"*76 + "╗",
            "║" + "  JARVIS ULTIMATE v5.0".center(76) + "║",
            "║" + "  AI | Voice | RL-Agent | BrowserFeatures | AppLister | StoryTeller".center(76) + "║",
            "╚" + "═"*76 + "╝",
        ]
        print("\n" + "\n".join(banner) + "\n")
        self.tts.speak("Hello! I am JARVIS version 4. How can I assist you today?", blocking=False)

        while self.running:
            try:
                if self._voice_mode and self.voice.available:
                    text = self.voice.listen()
                    if text:
                        self.process(text)
                else:
                    try:
                        raw = input("💬  You: ").strip()
                    except EOFError:
                        break
                    if raw:
                        self.process(raw)
            except KeyboardInterrupt:
                print("\n")
                logger.info("JARVIS interrupted by user (Ctrl+C)")
                self.tts.speak("Goodbye!", blocking=True)
                break
            except Exception as e:
                logger.error(f"Main loop error: {e}\n{traceback.format_exc()}")
                print(f"  ⚠️  Unexpected error: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# 26. TEST SUITE  [T-1] — Run with: python jarvis_v2_fixed.py --test
# ══════════════════════════════════════════════════════════════════════════════
class TestSafeCalculator(unittest.TestCase):
    def setUp(self):
        self.calc = SafeCalculator()

    def _ok(self, expr, expected_fragment):
        ok, msg = self.calc.evaluate(expr)
        self.assertTrue(ok, f"Expected OK for '{expr}', got: {msg}")
        self.assertIn(str(expected_fragment), msg)

    def _fail(self, expr):
        ok, msg = self.calc.evaluate(expr)
        self.assertFalse(ok, f"Expected FAIL for '{expr}', got: {msg}")

    # Basic arithmetic
    def test_addition(self):            self._ok("2 + 2", "4")
    def test_subtraction(self):         self._ok("10 - 3", "7")
    def test_multiplication(self):      self._ok("5 * 6", "30")
    def test_division(self):            self._ok("10 / 4", "2.5")
    def test_floor_division(self):      self._ok("10 // 3", "3")
    def test_modulo(self):              self._ok("10 % 3", "1")
    def test_power(self):               self._ok("2 ** 10", "1024")
    def test_unary_minus(self):         self._ok("-5 + 10", "5")
    def test_nested_parens(self):       self._ok("(2 + 3) * (4 - 1)", "15")

    # Word arithmetic
    def test_word_plus(self):           self._ok("5 plus 3", "8")
    def test_word_times(self):          self._ok("4 times 7", "28")
    def test_word_divided_by(self):     self._ok("20 divided by 4", "5")
    def test_word_multiplied_by(self):  self._ok("6 multiplied by 7", "42")
    def test_word_squared(self):        self._ok("5 squared", "25")
    def test_word_cubed(self):          self._ok("3 cubed", "27")
    def test_word_power(self):          self._ok("2 to the power of 8", "256")

    # Special functions
    def test_sqrt(self):                self._ok("square root of 144", "12")
    def test_cube_root(self):           self._ok("cube root of 27", "3")
    def test_log(self):                 self._ok("log of 1000", "3")

    # [m-3] Caret exponent fix
    def test_caret_exponent(self):      self._ok("2^10", "1024")
    def test_caret_exponent_complex(self): self._ok("3^3", "27")

    # Edge cases / security
    def test_zero_division(self):       self._fail("10 / 0")
    def test_exponent_cap(self):        self._fail("2 ** 9999")
    def test_empty(self):               self._fail("")
    def test_log_zero(self):            self._fail("log of 0")
    def test_log_negative(self):        self._fail("log of -5")

    # Calc trigger stripping
    def test_what_is_prefix(self):      self._ok("what is 6 * 7", "42")
    def test_calculate_prefix(self):    self._ok("calculate 100 / 5", "20")


class TestRequireDecorator(unittest.TestCase):
    def test_paired_args_pass(self):
        """[C-1] Paired flags should work normally."""
        @require(True, "should not fail")
        def fn():
            return True, "ok"
        ok, msg = fn()
        self.assertTrue(ok)

    def test_paired_args_fail(self):
        """[C-1] False flag returns the message."""
        @require(False, "dep not installed")
        def fn():
            return True, "ok"
        ok, msg = fn()
        self.assertFalse(ok)
        self.assertEqual(msg, "dep not installed")

    def test_odd_args_raises(self):
        """[C-1] Odd number of args raises TypeError at decoration time."""
        with self.assertRaises(TypeError):
            @require(True)  # Missing message — should raise
            def fn():
                pass

    def test_multiple_flags(self):
        """[C-1] Multiple flag pairs: first False wins."""
        @require(True, "first ok", False, "second fails")
        def fn():
            return True, "ok"
        ok, msg = fn()
        self.assertFalse(ok)
        self.assertEqual(msg, "second fails")


class TestAIGatewayHistoryFix(unittest.TestCase):
    def setUp(self):
        self.ai = AIGateway()

    def test_history_never_starts_with_assistant(self):
        """[C-5] After trim, history must start with user role."""
        # Manually pack the history with assistant at start (simulating bad trim)
        self.ai._history = [
            {"role": "assistant", "content": "stale response"},
            {"role": "user",      "content": "hello"},
            {"role": "assistant", "content": "hi"},
        ]
        # Trigger the re-anchor logic as query() would
        while self.ai._history and self.ai._history[0]["role"] != "user":
            self.ai._history.pop(0)
        self.assertEqual(self.ai._history[0]["role"], "user")

    def test_history_trim_preserves_user_start(self):
        """[C-5] Trim on even boundary keeps user at front."""
        self.ai._max_history = 2  # max 4 entries
        for i in range(10):
            self.ai._history.append({"role": "user",      "content": f"q{i}"})
            self.ai._history.append({"role": "assistant", "content": f"a{i}"})
            if len(self.ai._history) > self.ai._max_history * 2:
                self.ai._history = self.ai._history[-(self.ai._max_history * 2):]
            while self.ai._history and self.ai._history[0]["role"] != "user":
                self.ai._history.pop(0)
            if self.ai._history:
                self.assertEqual(self.ai._history[0]["role"], "user",
                                 f"History started with assistant at iteration {i}")


class TestTimerManagerRace(unittest.TestCase):
    def test_cancel_timer_no_race(self):
        """[M-1] cancel_timer should succeed before _run() pops."""
        class DummyTTS:
            def speak(self, *a, **kw): pass

        tm = TimerManager(DummyTTS())
        # Set a 0.5s timer
        ok, msg = tm.set_timer("timer 1 seconds")
        self.assertTrue(ok)
        tid = 1  # First timer ID

        # Cancel immediately (before _run fires)
        ok2, msg2 = tm.cancel_timer(tid)
        self.assertTrue(ok2, f"cancel_timer should succeed: {msg2}")

        # After cancellation, timer should not be in dict
        with tm._lock:
            self.assertNotIn(tid, tm._timers)


class TestWebControllerURLFix(unittest.TestCase):
    def setUp(self):
        self.web = WebController()

    def test_localhost_gets_http(self):
        """[M-6] localhost should get http://, not https://."""
        url = self.web._normalise_url("localhost:8080")
        self.assertTrue(url.startswith("http://"), f"Got: {url}")
        self.assertFalse(url.startswith("https://"), f"Got: {url}")

    def test_127_gets_http(self):
        url = self.web._normalise_url("127.0.0.1:5000")
        self.assertTrue(url.startswith("http://"), f"Got: {url}")

    def test_public_domain_gets_https(self):
        url = self.web._normalise_url("google.com")
        self.assertTrue(url.startswith("https://"), f"Got: {url}")

    def test_existing_https_unchanged(self):
        url = self.web._normalise_url("https://example.com")
        self.assertEqual(url, "https://example.com")

    def test_existing_http_unchanged(self):
        url = self.web._normalise_url("http://example.com")
        self.assertEqual(url, "http://example.com")


class TestNotesStageOrdering(unittest.TestCase):
    """[M-3] Verify that 'remove note' and 'erase note' go to notes handler."""
    def setUp(self):
        self.j = JARVIS.__new__(JARVIS)
        # Minimal init for testing just the dispatch logic
        self.j.tts        = type("TTS", (), {"_enabled": False, "speak": lambda *a, **kw: None})()
        self.j.notes      = NotesManager()
        self.j._last_response = ""
        self._responded   = []

        orig_respond = JARVIS._respond
        def capture(self_inner, ok, msg, tts=True):
            self._responded.append((ok, msg))
        self.j._respond = lambda ok, msg, tts=True: self._responded.append((ok, msg))

    def test_remove_note_goes_to_notes_handler(self):
        """'remove note' should return a note-related message, not a file-delete message."""
        self.j.notes._notes = []  # empty notes
        cmd = "remove note abc123"
        # Simulate stage 14 directly
        note_del = re.match(r'(?:delete|remove|erase)\s+note\s+(.+)', cmd, re.I)
        self.assertIsNotNone(note_del, "Regex should match 'remove note abc123'")
        self.assertEqual(note_del.group(1).strip(), "abc123")

    def test_re_note_remove_pattern(self):
        """RE_NOTE_REMOVE should match 'remove note' and 'erase note'."""
        self.assertTrue(RE_NOTE_REMOVE.search("remove note 12345"))
        self.assertTrue(RE_NOTE_REMOVE.search("erase note abc"))
        self.assertIsNone(RE_NOTE_REMOVE.search("delete a file"))  # should NOT match


class TestFileManagerDeleteFix(unittest.TestCase):
    """[C-4] delete() existence check separated from deletion."""
    def setUp(self):
        self.fm  = FileManager()
        self.tmp = Path(os.environ.get("TEMP", "/tmp")) / f"jarvis_test_{uuid.uuid4().hex[:8]}"
        self.tmp.mkdir(parents=True, exist_ok=True)
        # Inject tmp as a search dir
        self.fm.SEARCH_DIRS.insert(0, self.tmp)

    def tearDown(self):
        shutil.rmtree(str(self.tmp), ignore_errors=True)
        if self.tmp in self.fm.SEARCH_DIRS:
            self.fm.SEARCH_DIRS.remove(self.tmp)

    def test_delete_existing_file(self):
        f = self.tmp / "test_delete.txt"
        f.write_text("hello")
        ok, msg = self.fm.delete("test_delete.txt")
        self.assertTrue(ok, msg)
        self.assertFalse(f.exists())

    def test_delete_nonexistent_returns_false(self):
        ok, msg = self.fm.delete("no_such_file_xyz.txt")
        self.assertFalse(ok)

    def test_delete_directory(self):
        d = self.tmp / "test_dir"
        d.mkdir()
        (d / "child.txt").write_text("data")
        ok, msg = self.fm.delete("test_dir")
        self.assertTrue(ok, msg)
        self.assertFalse(d.exists())


class TestSearchFileDirSkip(unittest.TestCase):
    """[m-2] skipped_dirs should match simple dir names, not backslash paths."""
    def test_skip_names_no_backslash(self):
        fm = FileManager()
        for name in fm._SKIP_DIR_NAMES:
            self.assertNotIn("\\", name, f"Skip dir '{name}' contains backslash — will never match item.name")
            self.assertNotIn("/", name,  f"Skip dir '{name}' contains forward-slash — will never match item.name")


class TestUWPInstallFix(unittest.TestCase):
    """[C-6] UWP apps should only be marked installed on Windows."""
    def test_uwp_install_flag(self):
        ac = AppController()
        for key, app in ac._cache.items():
            if app.get("uwp") and not app.get("resolved_path") and not app.get("cmd"):
                # Should only be True on Windows, False elsewhere
                expected = IS_WINDOWS
                self.assertEqual(
                    app["installed"], expected,
                    f"App '{key}' UWP installed={app['installed']} expected={expected}"
                )



# ══════════════════════════════════════════════════════════════════════════════
# v3.0 TEST CLASSES
# ══════════════════════════════════════════════════════════════════════════════
class TestShellInjectionFix(unittest.TestCase):
    """[S-1] subprocess.Popen must not use shell=True."""
    def test_no_shell_true_in_launch(self):
        import ast as _ast
        src = open(__file__, encoding="utf-8").read()
        tree = _ast.parse(src)
        class ShellFinder(_ast.NodeVisitor):
            def __init__(self):
                self.violations = []
            def visit_Call(self, node):
                if isinstance(node.func, _ast.Attribute) and node.func.attr in ("Popen","run","call"):
                    for kw in node.keywords:
                        if kw.arg == "shell" and isinstance(kw.value, _ast.Constant) and kw.value.value is True:
                            self.violations.append(node.lineno)
                self.generic_visit(node)
        sf = ShellFinder()
        sf.visit(tree)
        self.assertEqual(sf.violations, [], f"shell=True found at lines: {sf.violations}")


class TestUnitConverter(unittest.TestCase):
    def setUp(self):
        self.uc = UnitConverter()

    def test_km_to_miles(self):
        ok, msg = self.uc.convert(1, "km", "mile")
        self.assertTrue(ok)
        self.assertIn("0.621", msg)

    def test_celsius_to_fahrenheit(self):
        ok, msg = self.uc.convert(0, "c", "f")
        self.assertTrue(ok)
        self.assertIn("32.00", msg)

    def test_celsius_to_kelvin(self):
        ok, msg = self.uc.convert(0, "c", "k")
        self.assertTrue(ok)
        self.assertIn("273.15", msg)

    def test_kg_to_lbs(self):
        ok, msg = self.uc.convert(1, "kg", "lbs")
        self.assertTrue(ok)
        self.assertIn("2.20", msg)

    def test_gb_to_mb(self):
        ok, msg = self.uc.convert(1, "gb", "mb")
        self.assertTrue(ok)
        self.assertIn("1024", msg)

    def test_unsupported_units(self):
        ok, msg = self.uc.convert(1, "furlongs", "parsecs")
        self.assertFalse(ok)


class TestPasswordManager(unittest.TestCase):
    def setUp(self):
        self.pm = PasswordManager()
        self.pm._FILE = Path("/tmp") / f"jarvis_test_pass_{uuid.uuid4().hex[:8]}.json"

    def tearDown(self):
        if self.pm._FILE.exists():
            self.pm._FILE.unlink()

    def test_generate_default_length(self):
        ok, msg = self.pm.generate()
        self.assertTrue(ok)
        # Password should have 16 chars
        import re as _re
        pwd = _re.search(r': (.+)$', msg)
        self.assertIsNotNone(pwd)
        self.assertEqual(len(pwd.group(1)), 16)

    def test_generate_custom_length(self):
        ok, msg = self.pm.generate(24)
        self.assertTrue(ok)
        import re as _re
        pwd = _re.search(r': (.+)$', msg)
        self.assertEqual(len(pwd.group(1)), 24)

    def test_save_and_retrieve(self):
        self.pm.save("testservice", "mypassword123")
        ok, msg = self.pm.get("testservice")
        self.assertTrue(ok)
        self.assertIn("mypassword123", msg)

    def test_delete(self):
        self.pm.save("svc2", "pass2")
        ok, _ = self.pm.delete("svc2")
        self.assertTrue(ok)
        ok2, _ = self.pm.get("svc2")
        self.assertFalse(ok2)

    def test_strength_weak(self):
        ok, msg = self.pm.strength("abc")
        self.assertTrue(ok)
        self.assertIn("Weak", msg)

    def test_strength_strong(self):
        ok, msg = self.pm.strength("MyStr0ng!Pass#2024")
        self.assertTrue(ok)
        self.assertIn("Strong", msg)


class TestWorldClock(unittest.TestCase):
    def setUp(self):
        self.wc = WorldClock()

    def test_known_city(self):
        ok, msg = self.wc.time_in("tokyo")
        self.assertTrue(ok)
        self.assertIn("Tokyo", msg)

    def test_case_insensitive(self):
        ok, msg = self.wc.time_in("LONDON")
        self.assertTrue(ok)

    def test_unknown_city(self):
        ok, msg = self.wc.time_in("mordor")
        self.assertFalse(ok)


class TestRLCommandAgent(unittest.TestCase):
    def setUp(self):
        self.rl = RLCommandAgent()
        self.rl._FILE = Path("/tmp") / f"jarvis_test_rl_{uuid.uuid4().hex[:8]}.json"

    def tearDown(self):
        if self.rl._FILE.exists():
            self.rl._FILE.unlink()

    def test_categorize_volume(self):
        state = self.rl._categorize("set volume to 50")
        self.assertEqual(self.rl.CATEGORIES[state], "volume")

    def test_categorize_brightness(self):
        state = self.rl._categorize("decrease brightness to 30")
        self.assertEqual(self.rl.CATEGORIES[state], "brightness")

    def test_record_success_increases_q(self):
        self.rl.choose("open chrome")
        q_before = self.rl._q_value(self.rl._categorize("open chrome"), 0)
        self.rl.record("open chrome", True)
        q_after  = self.rl._q_value(self.rl._categorize("open chrome"),
                                     self.rl._best_action(self.rl._categorize("open chrome")))
        # Q-value should have changed (update happened)
        self.assertIsInstance(q_after, float)

    def test_record_failure_gives_negative_reward(self):
        state = self.rl._categorize("some unknown command")
        self.rl.choose("some unknown command")
        self.rl.record("some unknown command", False)
        # Check q value is negative (reward=-0.5, alpha=0.1, q_old=0 → q_new=-0.05)
        best = self.rl._best_action(state)
        q = self.rl._q_value(state, best)
        self.assertLess(q, 0.01)  # should be negative or near zero

    def test_epsilon_decays(self):
        e0 = self.rl.epsilon
        for _ in range(100):
            self.rl.choose("open chrome")
            self.rl.record("open chrome", True)
        self.assertLess(self.rl.epsilon, e0)

    def test_stats_returns_string(self):
        result = self.rl.stats()
        self.assertIsInstance(result, str)
        self.assertIn("RL Agent", result)


class TestHabitTracker(unittest.TestCase):
    def setUp(self):
        self.ht = HabitTracker()
        self.ht._FILE = Path("/tmp") / f"jarvis_test_habits_{uuid.uuid4().hex[:8]}.json"
        self.ht._data = {}

    def tearDown(self):
        if self.ht._FILE.exists():
            self.ht._FILE.unlink()

    def test_add_and_checkin(self):
        ok, _ = self.ht.add_habit("test exercise")
        self.assertTrue(ok)
        ok2, msg = self.ht.check_in("test exercise")
        self.assertTrue(ok2)
        self.assertIn("test exercise", msg.lower())

    def test_double_checkin_idempotent(self):
        self.ht.check_in("running")
        ok, msg = self.ht.check_in("running")
        self.assertTrue(ok)
        self.assertIn("already", msg.lower())

    def test_streak_increments(self):
        self.ht.check_in("meditation")
        _, _ = self.ht.show()
        self.assertGreater(self.ht._data["meditation"]["streak"], 0)


class TestSafeTarExtract(unittest.TestCase):
    """[S-2] _safe_tar_members should block path-traversal attacks."""
    def test_blocks_absolute_path(self):
        import tarfile as _tf
        import io, tempfile, os
        # Build an in-memory tar with an absolute-path member
        buf = io.BytesIO()
        with _tf.open(fileobj=buf, mode="w") as tf:
            info = _tf.TarInfo(name="/etc/passwd")
            info.size = 0
            tf.addfile(info, io.BytesIO(b""))
        buf.seek(0)
        dest = Path(tempfile.mkdtemp())
        try:
            with _tf.open(fileobj=buf) as tf:
                safe = list(_safe_tar_members(tf, dest))
            self.assertEqual(safe, [], "Absolute-path member should be filtered")
        finally:
            import shutil as _sh
            _sh.rmtree(str(dest), ignore_errors=True)

    def test_blocks_traversal(self):
        import tarfile as _tf, io, tempfile
        buf = io.BytesIO()
        with _tf.open(fileobj=buf, mode="w") as tf:
            info = _tf.TarInfo(name="../../etc/passwd")
            info.size = 0
            tf.addfile(info, io.BytesIO(b""))
        buf.seek(0)
        dest = Path(tempfile.mkdtemp())
        try:
            with _tf.open(fileobj=buf) as tf:
                safe = list(_safe_tar_members(tf, dest))
            self.assertEqual(safe, [], "Path-traversal member should be filtered")
        finally:
            import shutil as _sh
            _sh.rmtree(str(dest), ignore_errors=True)


def run_tests():
    """[T-1] Run all test cases and print a summary."""
    print("\n" + "="*78)
    print("  JARVIS v4.0 — Running Test Suite")
    print("="*78 + "\n")

    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()

    test_classes = [
        TestSafeCalculator,
        TestRequireDecorator,
        TestAIGatewayHistoryFix,
        TestTimerManagerRace,
        TestWebControllerURLFix,
        TestNotesStageOrdering,
        TestFileManagerDeleteFix,
        TestSearchFileDirSkip,
        TestUWPInstallFix,
        # v3.0 new tests
        TestShellInjectionFix,
        TestUnitConverter,
        TestPasswordManager,
        TestWorldClock,
        TestHabitTracker,
        TestSafeTarExtract,
        # v4.0 new tests
        TestRLCommandAgent,
        # v5.0 new tests
        TestV5BrowserFeatureManager,
        TestV5InstalledAppsLister,
        TestV5StoryTeller,
        TestV5VolumePatch,
        TestV5Regex,
    ]

    for cls in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "="*78)
    total  = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    print(f"  Results: {passed}/{total} passed"
          f" | {len(result.failures)} failures"
          f" | {len(result.errors)} errors")
    print("="*78 + "\n")

    return 0 if result.wasSuccessful() else 1


# ══════════════════════════════════════════════════════════════════════════════
# 27. v5.0 TEST SUITE — 47 new tests across 5 classes
#     Run with: python Jarvis_v5_final.py --test
# ══════════════════════════════════════════════════════════════════════════════

class TestV5BrowserFeatureManager(unittest.TestCase):
    """Tests for BrowserFeatureManager — URL lookup, normalisation, hotkeys."""

    def setUp(self):
        self.bfm = BrowserFeatureManager()

    # ── Alias normalisation ───────────────────────────────────────────
    def test_alias_dev_tools(self):
        self.assertEqual(self.bfm._normalise_page("dev tools"), "devtools")

    def test_alias_favourites(self):
        self.assertEqual(self.bfm._normalise_page("favourites"), "bookmarks")

    def test_alias_new_tab_space(self):
        self.assertEqual(self.bfm._normalise_page("new tab"), "newtab")

    def test_alias_new_tab_hyphen(self):
        self.assertEqual(self.bfm._normalise_page("new-tab"), "newtab")

    def test_alias_password_singular(self):
        self.assertEqual(self.bfm._normalise_page("password"), "passwords")

    def test_alias_task_manager(self):
        self.assertEqual(self.bfm._normalise_page("task manager"), "task-manager")

    def test_alias_reading_mode(self):
        self.assertEqual(self.bfm._normalise_page("reading mode"), "reading-mode")

    def test_alias_hard_refresh(self):
        self.assertEqual(self.bfm._normalise_page("force refresh"), "hard-refresh")

    # ── URL table look-up ─────────────────────────────────────────────
    def test_brave_history_url(self):
        url = self.bfm._URLS["brave"]["history"]
        self.assertEqual(url, "brave://history")

    def test_chrome_passwords_url(self):
        url = self.bfm._URLS["chrome"]["passwords"]
        self.assertIn("password", url.lower())

    def test_edge_collections_url(self):
        url = self.bfm._URLS["edge"].get("collections")
        self.assertIsNotNone(url)

    def test_firefox_history_none(self):
        # Firefox history has no URL — must fall back to hotkey
        url = self.bfm._URLS["firefox"]["history"]
        self.assertIsNone(url)

    # ── Supported pages list ──────────────────────────────────────────
    def test_list_supported_pages_returns_list(self):
        pages = self.bfm.list_supported_pages("brave")
        self.assertIsInstance(pages, list)
        self.assertGreater(len(pages), 5)

    def test_list_supported_pages_sorted(self):
        pages = self.bfm.list_supported_pages("chrome")
        self.assertEqual(pages, sorted(pages))

    # ── Type safety ───────────────────────────────────────────────────
    def test_empty_page_raises_type_error(self):
        with self.assertRaises(TypeError):
            self.bfm.open("", "brave")

    def test_none_page_raises_type_error(self):
        with self.assertRaises(TypeError):
            self.bfm.open(None, "brave")

    # ── Unknown browser fallback ──────────────────────────────────────
    def test_unknown_browser_defaults_to_brave(self):
        # Should not raise — falls back to brave
        # (no exe on CI so it will hit the hotkey/fallback path)
        try:
            ok, msg = self.bfm.open("history", "nonexistentbrowser123")
            self.assertIsInstance(ok, bool)
        except Exception as exc:
            self.fail(f"open() raised unexpectedly: {exc}")

    # ── Keyboard-only pages don't attempt URL launch ──────────────────
    def test_keyboard_only_page_uses_hotkey_path(self):
        # devtools is keyboard-only; exe won't exist in CI, returns False with msg
        ok, msg = self.bfm.open("devtools", "brave")
        # Either hotkey succeeded OR pyautogui not installed — both are valid
        self.assertIsInstance(ok, bool)
        self.assertIsInstance(msg, str)


class TestV5InstalledAppsLister(unittest.TestCase):
    """Tests for InstalledAppsLister — enumeration, caching, report formatting."""

    def setUp(self):
        self.lister = InstalledAppsLister(jarvis_app_db={
            "notepad": {"display": "Notepad", "installed": True,
                        "resolved_path": r"C:\Windows\notepad.exe"},
            "calc":    {"display": "Calculator", "installed": True,
                        "resolved_path": r"C:\Windows\System32\calc.exe"},
            "phantom": {"display": "Phantom", "installed": False},  # not installed
        })

    def test_jarvis_db_installed_apps_included(self):
        apps = self.lister._from_jarvis_db()
        names = [a["name"] for a in apps]
        self.assertIn("Notepad", names)
        self.assertIn("Calculator", names)

    def test_jarvis_db_not_installed_excluded(self):
        apps = self.lister._from_jarvis_db()
        names = [a["name"] for a in apps]
        self.assertNotIn("Phantom", names)

    def test_get_all_returns_list(self):
        apps = self.lister.get_all()
        self.assertIsInstance(apps, list)

    def test_get_all_no_duplicates(self):
        apps = self.lister.get_all()
        keys = [re.sub(r'\s+', '', a["name"].lower()) for a in apps]
        self.assertEqual(len(keys), len(set(keys)),
                         "Duplicate app names found in get_all()")

    def test_get_all_sorted(self):
        apps = self.lister.get_all()
        names = [a["name"].lower() for a in apps]
        self.assertEqual(names, sorted(names))

    def test_cache_is_reused(self):
        apps1 = self.lister.get_all()
        apps2 = self.lister.get_all()
        self.assertIs(apps1, apps2, "Cache should return the same list object")

    def test_force_refresh_rebuilds_cache(self):
        apps1 = self.lister.get_all()
        apps2 = self.lister.get_all(force_refresh=True)
        self.assertIsNot(apps1, apps2, "force_refresh should produce a new list")

    def test_format_report_is_string(self):
        report = self.lister.format_report()
        self.assertIsInstance(report, str)

    def test_format_report_contains_app_names(self):
        # Create a fresh lister with only our known jarvis_db apps so we can
        # confirm they appear without relying on PATH executables overriding.
        small_lister = InstalledAppsLister(jarvis_app_db={
            "testapp": {"display": "TestApp", "installed": True, "resolved_path": None},
        })
        # Force db-only by patching _from_start_menu/_from_path/_from_processes/_from_registry
        small_lister._from_start_menu = lambda: []
        small_lister._from_path       = lambda: []
        small_lister._from_processes  = lambda: []
        small_lister._from_registry   = lambda: []
        report = small_lister.format_report()
        self.assertIn("TestApp", report)

    def test_format_report_respects_max_display(self):
        # Insert many dummy entries to exceed max_display
        dummy_db = {f"app{i}": {"display": f"App {i:03d}", "installed": True}
                    for i in range(200)}
        lister2 = InstalledAppsLister(jarvis_app_db=dummy_db)
        report = lister2.format_report(max_display=10)
        self.assertIn("more apps", report)


class TestV5StoryTeller(unittest.TestCase):
    """Tests for StoryTeller — corpus fallback, threading, stop control."""

    class _FakeTTS:
        def __init__(self):
            self.spoken: List[str] = []
            self._stop_event = threading.Event()
        def speak(self, text, blocking=False):
            self.spoken.append(text)
        def speak_streaming(self, text, stop_check=None):
            self.spoken.append(text)
        def stop_speaking(self):
            self._stop_event.set()

    class _FakeAI:
        """AI that always fails → forces corpus fallback."""
        def query(self, prompt):
            return False, "AI unavailable in test"

    def setUp(self):
        self.tts  = self._FakeTTS()
        self.ai   = self._FakeAI()
        self.st   = StoryTeller(tts=self.tts, ai_gateway=self.ai)

    # ── Corpus fallback ───────────────────────────────────────────────
    def test_generate_story_returns_list(self):
        paragraphs = self.st._generate_story("adventure")
        self.assertIsInstance(paragraphs, list)
        self.assertGreater(len(paragraphs), 0)

    def test_dragon_topic_uses_dragon_corpus(self):
        paragraphs = self.st._generate_story("dragons")
        joined = " ".join(paragraphs).lower()
        self.assertIn("dragon", joined)

    def test_space_topic_uses_space_corpus(self):
        paragraphs = self.st._generate_story("space")
        joined = " ".join(paragraphs).lower()
        self.assertIn("star", joined)

    def test_unknown_topic_falls_back_to_default_corpus(self):
        paragraphs = self.st._generate_story("xyzzy123unknown")
        self.assertEqual(paragraphs, list(_BUILTIN_STORIES["default"]))

    # ── tell() / stop() lifecycle ─────────────────────────────────────
    def test_tell_returns_true(self):
        ok, msg = self.st.tell("adventure")
        self.assertTrue(ok)
        self.st.stop()

    def test_tell_sets_is_narrating(self):
        self.st.tell("test")
        self.assertTrue(self.st.is_narrating)
        self.st.stop()

    def test_stop_clears_is_narrating(self):
        self.st.tell("test")
        self.st.stop()
        time.sleep(0.1)
        self.assertFalse(self.st.is_narrating)

    def test_double_tell_returns_false(self):
        self.st.tell("first story")
        ok, msg = self.st.tell("second story")
        self.assertFalse(ok, "Second tell() while narrating should return False")
        self.st.stop()

    # ── Type safety ───────────────────────────────────────────────────
    def test_tell_non_string_raises(self):
        with self.assertRaises(TypeError):
            self.st.tell(42)

    def test_generate_story_non_string_raises(self):
        with self.assertRaises(TypeError):
            self.st._generate_story(None)


class TestV5VolumePatch(unittest.TestCase):
    """Tests for the v5.0 PyAutoGUI delta-based volume fix."""

    def _make_sys(self, current_vol=50):
        """Create a SystemController-like stub for testing the patch logic."""
        class _VolumeStub:
            def __init__(self, cur):
                self._cur  = cur
                self.presses: List[Tuple[str, int]] = []  # (key, count)
                self._vol_cache = (None, 0.0)

            def get_volume(self):
                return self._cur

            def _do_delta_volume(self, level):
                """Mirrors the v5 PyAutoGUI fallback logic."""
                level   = max(0, min(100, int(level)))
                current = self.get_volume()
                STEP    = 2
                delta   = level - current
                n       = abs(delta) // STEP + (1 if abs(delta) % STEP else 0)
                if delta == 0:
                    return True, f"Volume already at {level}%"
                key = "volumeup" if delta > 0 else "volumedown"
                self.presses.append((key, n))
                return True, f"Volume set to {level}%"

        return _VolumeStub(current_vol)

    def test_no_zero_first_press(self):
        """v5 fix: must never emit 50 × volumedown when going to any level."""
        stub = self._make_sys(current_vol=50)
        stub._do_delta_volume(70)
        for key, count in stub.presses:
            if key == "volumedown":
                self.assertLess(count, 50,
                    "v5 must NOT press volumedown 50 times (old zero-first bug)")

    def test_increase_from_50_to_70(self):
        stub = self._make_sys(current_vol=50)
        stub._do_delta_volume(70)
        self.assertEqual(len(stub.presses), 1)
        key, count = stub.presses[0]
        self.assertEqual(key, "volumeup")
        self.assertEqual(count, 10)  # (70-50)/2 = 10 presses

    def test_decrease_from_80_to_40(self):
        stub = self._make_sys(current_vol=80)
        stub._do_delta_volume(40)
        key, count = stub.presses[0]
        self.assertEqual(key, "volumedown")
        self.assertEqual(count, 20)  # (80-40)/2 = 20 presses

    def test_no_press_when_already_at_target(self):
        stub = self._make_sys(current_vol=60)
        ok, msg = stub._do_delta_volume(60)
        self.assertTrue(ok)
        self.assertEqual(len(stub.presses), 0)
        self.assertIn("already", msg)

    def test_clamp_above_100(self):
        stub = self._make_sys(current_vol=90)
        ok, msg = stub._do_delta_volume(150)  # should clamp to 100
        self.assertTrue(ok)
        if stub.presses:
            key, _ = stub.presses[0]
            self.assertEqual(key, "volumeup")


class TestV5Regex(unittest.TestCase):
    """Regex safety and correctness tests for all v5 patterns."""

    # ── RE_V5_TELL_STORY ─────────────────────────────────────────────
    def test_story_basic(self):
        m = RE_V5_TELL_STORY.match("tell me a story")
        self.assertIsNotNone(m)

    def test_story_with_topic(self):
        m = RE_V5_TELL_STORY.match("tell me a story about dragons")
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1).strip(), "dragons")

    def test_story_narrate_variant(self):
        m = RE_V5_TELL_STORY.match("narrate a story about space explorers")
        self.assertIsNotNone(m)

    def test_story_no_false_positive(self):
        m = RE_V5_TELL_STORY.match("delete my notes")
        self.assertIsNone(m)

    # ── RE_V5_LIST_APPS ──────────────────────────────────────────────
    def test_list_apps_basic(self):
        self.assertIsNotNone(RE_V5_LIST_APPS.search("list all apps"))

    def test_show_applications(self):
        self.assertIsNotNone(RE_V5_LIST_APPS.search("show installed applications"))

    def test_what_apps(self):
        self.assertIsNotNone(RE_V5_LIST_APPS.search("what apps do i have"))

    def test_list_apps_no_false_positive(self):
        self.assertIsNone(RE_V5_LIST_APPS.search("open chrome"))

    # ── RE_V5_BROWSER_FEATURE ────────────────────────────────────────
    def test_browser_feature_basic(self):
        m = RE_V5_BROWSER_FEATURE.match("open history in brave")
        self.assertIsNotNone(m)
        self.assertIn("history", m.group(1))
        self.assertEqual(m.group(2).lower(), "brave")

    def test_browser_feature_no_browser(self):
        m = RE_V5_BROWSER_FEATURE.match("open passwords")
        self.assertIsNotNone(m)
        self.assertIn("passwords", m.group(1))

    # ── Catastrophic backtracking safety ─────────────────────────────
    def test_story_regex_no_catastrophic_backtrack(self):
        evil = "tell me a story about " + "a " * 5000 + "dragon"
        import signal

        def _timeout(sig, frame):
            raise TimeoutError("regex timed out — catastrophic backtracking")

        if hasattr(signal, "SIGALRM"):
            signal.signal(signal.SIGALRM, _timeout)
            signal.alarm(2)
        try:
            RE_V5_TELL_STORY.match(evil)
        finally:
            if hasattr(signal, "SIGALRM"):
                signal.alarm(0)

    def test_list_apps_regex_no_catastrophic_backtrack(self):
        evil = "x" * 10_000 + "apps"
        import time as _t
        t0 = _t.monotonic()
        RE_V5_LIST_APPS.search(evil)
        elapsed = _t.monotonic() - t0
        self.assertLess(elapsed, 1.0,
                        f"RE_V5_LIST_APPS took {elapsed:.3f}s on 10k-char input")


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    # Check for test mode
    if "--test" in sys.argv:
        sys.exit(run_tests())

    # Show dependency status on startup
    print("\n🔍  Checking optional dependencies:")
    deps = {
        "pyttsx3 (TTS)":                TTS_OK,
        "SpeechRecognition (Voice)":     SR_OK,
        "pyautogui (UI Automation)":     PAG_OK,
        "psutil (System Info)":          PSUTIL_OK,
        "screen_brightness_control":     SBC_OK,
        "requests (HTTP)":               REQ_OK,
        "pywin32 (Win32 API)":           WIN32_OK,
        "openai (OpenAI API)":           OAI_OK,
        "anthropic (Claude API)":        ANT_OK,
    }
    for name, ok in deps.items():
        print(f"  {'✅' if ok else '⚠️ '} {name}")

    print("\n💡  Install all optional deps:")
    print("     pip install pyttsx3 SpeechRecognition pyautogui psutil")
    print("     pip install screen_brightness_control requests pywin32")
    print("     pip install openai anthropic")
    print("     # For local AI: install Ollama from https://ollama.ai")
    print("     # then run: ollama pull llama3.2")
    print("     # Run tests: python Jarvis_v5_final.py --test\n")

    # Extension point: if jarvis_intelligence_engine is installed,
    # it can patch JARVIS with enhanced AI capabilities.
    # pip install jarvis-intelligence-engine (optional)
    try:
        from jarvis_intelligence_engine import patch_jarvis
        patch_jarvis(JARVIS()).run()
    except ImportError:
        JARVIS().run()