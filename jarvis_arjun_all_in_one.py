#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   JARVIS v11 + ARJUN DASHBOARD — ALL-IN-ONE RUNNER                          ║
║                                                                              ║
║   Just run:  python3 jarvis_arjun_all_in_one.py                              ║
║                                                                              ║
║   This single file does EVERYTHING:                                          ║
║     1. Starts the Next.js web dashboard (port 3000)                          ║
║     2. Opens your browser automatically                                      ║
║     3. Starts the bridge server (port 8765)                                  ║
║     4. Imports and runs JARVIS v11                                           ║
║     5. Links web ↔ JARVIS so commands flow both ways                         ║
║                                                                              ║
║   No .env file needed. No configuration needed. Just run it.                 ║
║                                                                              ║
║   If JARVIS source isn't found, it runs in "bridge-only" mode               ║
║   (web dashboard works, JARVIS commands return a friendly message).          ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import time
import errno
import threading
import subprocess
import socket
import logging
import urllib.request
import urllib.parse
import webbrowser
import traceback
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from typing import Optional, Tuple

# ─── Setup logging ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
)
logger = logging.getLogger("jarvis_arjun")

# ─── Configuration (auto-detected, no .env needed) ───────────────────────────

# Auto-detect the Next.js project path
# Tries common locations in order
def _detect_web_path():
    candidates = [
        os.environ.get("ARJUN_WEB_PATH"),
        os.path.expanduser("~/my-project"),
        os.path.expanduser("~/my-project/src"),
        "/home/z/my-project",
        os.path.dirname(os.path.abspath(__file__)),
        os.getcwd(),
    ]
    for path in candidates:
        if path and os.path.isdir(path) and os.path.isfile(os.path.join(path, "package.json")):
            return path
    # Fallback: assume current working directory
    return os.getcwd()

def _detect_jarvis_source():
    candidates = [
        os.environ.get("JARVIS_SOURCE_PATH"),
        os.path.expanduser("~/my-project/upload"),
        "/home/z/my-project/upload",
        os.path.dirname(os.path.abspath(__file__)),
        os.getcwd(),
    ]
    for path in candidates:
        if path and os.path.isfile(os.path.join(path, "JARVIS_v11_WINDOWS_FIXED.py")):
            return path
    return None  # Not found — bridge-only mode

WEB_PROJECT_PATH = _detect_web_path()
JARVIS_SOURCE_PATH = _detect_jarvis_source()

# Ports
WEB_PORT = int(os.environ.get("ARJUN_WEB_PORT", "3000"))
BRIDGE_PORT = int(os.environ.get("ARJUN_BRIDGE_PORT", "8765"))

# Auth token (auto-generated if not set, so no .env needed)
BRIDGE_TOKEN = os.environ.get("ARJUN_BRIDGE_TOKEN", "arjun-jarvis-bridge-2026")

# Security limits
MAX_BODY_BYTES = 10 * 1024  # 10 KB
MAX_COMMAND_LENGTH = 10_000
ALLOWED_ORIGINS = frozenset({
    f"http://localhost:{WEB_PORT}",
    f"http://127.0.0.1:{WEB_PORT}",
    f"http://localhost:{BRIDGE_PORT}",
    f"http://127.0.0.1:{BRIDGE_PORT}",
})

# Timing constants
HEALTH_TIMEOUT_SECONDS = 30
HEALTH_POLL_INTERVAL = 0.5
HEALTH_REQUEST_TIMEOUT = 2
PORT_CHECK_TIMEOUT = 0.5
SUBPROCESS_TERMINATE_WAIT = 5
BRIDGE_THREAD_JOIN_TIMEOUT = 5

# Next.js dev command — try bun first, fall back to npm
def _detect_dev_command():
    for cmd in [["bun", "run", "dev"], ["npm", "run", "dev"], ["npx", "next", "dev"]]:
        try:
            subprocess.run([cmd[0], "--version"], capture_output=True, timeout=3)
            return cmd
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return ["bun", "run", "dev"]  # Default

NEXT_DEV_CMD = _detect_dev_command()


# ══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def _is_port_open(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a TCP port is already in use."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(PORT_CHECK_TIMEOUT)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False


def _wait_for_server(url: str, timeout: int = HEALTH_TIMEOUT_SECONDS) -> bool:
    """Poll a URL until it responds with HTTP < 500 or timeout."""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        logger.error("Refusing to poll URL with scheme %r", parsed.scheme)
        return False

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "JarvisArjunBridge/1.0"})
            with urllib.request.urlopen(req, timeout=HEALTH_REQUEST_TIMEOUT) as r:  # nosec B310
                if r.status < 500:
                    return True
        except Exception:
            time.sleep(HEALTH_POLL_INTERVAL)
    return False


# ══════════════════════════════════════════════════════════════════════════════
# HTTP BRIDGE HANDLER
# ══════════════════════════════════════════════════════════════════════════════

class BridgeHTTPRequestHandler(BaseHTTPRequestHandler):
    """HTTP handler that receives commands from the web app and forwards
    them to JARVIS.process()."""

    _jarvis = None  # Set by ArjunDashboardBridge

    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass  # Suppress default logging

    def _get_origin(self) -> str:
        return self.headers.get("Origin", "")

    def _check_cors(self) -> bool:
        origin = self._get_origin()
        if not origin:
            return True
        return origin in ALLOWED_ORIGINS

    def _send_json(self, code: int, data: dict):
        """Send a JSON response with CORS headers."""
        body = json.dumps(data).encode("utf-8")

        # 1. Status line
        self.send_response(code)

        # 2. CORS headers
        origin = self._get_origin()
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        elif origin:
            self.send_header("Access-Control-Allow-Origin", "null")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Max-Age", "86400")

        # 3. Content headers
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")

        # 4. Body
        self.end_headers()
        self.wfile.write(body)

    def _check_auth(self) -> bool:
        auth = self.headers.get("Authorization", "")
        return auth == f"Bearer {BRIDGE_TOKEN}"

    def do_OPTIONS(self):
        self._send_json(200, {"ok": True})

    def do_GET(self):
        if not self._check_cors():
            self._send_json(403, {"ok": False, "error": "Origin not allowed"})
            return

        if self.path.startswith("/health"):
            self._send_json(200, {
                "ok": True,
                "service": "jarvis-bridge",
                "version": "1.0",
                "jarvis_connected": self._jarvis is not None,
                "command_count": getattr(self._jarvis, "_command_count", 0) if self._jarvis else 0,
            })
        elif self.path.startswith("/status"):
            if not self._check_auth():
                self._send_json(401, {"ok": False, "error": "Unauthorized"})
                return
            if self._jarvis:
                self._send_json(200, {
                    "ok": True,
                    "voice_mode": getattr(self._jarvis, "_voice_mode", False),
                    "running": getattr(self._jarvis, "running", True),
                    "history_count": len(getattr(self._jarvis, "_history", [])),
                    "last_response": getattr(self._jarvis, "_last_response", ""),
                })
            else:
                self._send_json(503, {"ok": False, "error": "JARVIS not connected"})
        else:
            self._send_json(404, {"ok": False, "error": "Not found"})

    def do_POST(self):
        if not self._check_cors():
            self._send_json(403, {"ok": False, "error": "Origin not allowed"})
            return

        if not self._check_auth():
            self._send_json(401, {"ok": False, "error": "Unauthorized"})
            return

        if not self.path.startswith("/command"):
            self._send_json(404, {"ok": False, "error": "Not found"})
            return

        # Read body with size limit
        try:
            length = int(self.headers.get("Content-Length", 0))
        except (ValueError, TypeError):
            self._send_json(400, {"ok": False, "error": "Invalid Content-Length"})
            return

        if length < 0:
            self._send_json(400, {"ok": False, "error": "Negative Content-Length"})
            return

        if length > MAX_BODY_BYTES:
            self._send_json(413, {"ok": False, "error": f"Body too large (max {MAX_BODY_BYTES} bytes)"})
            return

        try:
            raw = self.rfile.read(length).decode("utf-8")
            payload = json.loads(raw) if raw else {}
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            self._send_json(400, {"ok": False, "error": f"Invalid JSON: {e}"})
            return
        except Exception:
            self._send_json(400, {"ok": False, "error": "Bad request"})
            return

        # Validate command
        command = payload.get("command", "")
        if not isinstance(command, str):
            self._send_json(400, {"ok": False, "error": "'command' must be a string"})
            return

        command = command.strip()
        if not command:
            self._send_json(400, {"ok": False, "error": "Missing 'command' field"})
            return

        if len(command) > MAX_COMMAND_LENGTH:
            self._send_json(400, {"ok": False, "error": f"Command too long (max {MAX_COMMAND_LENGTH} chars)"})
            return

        # Execute in JARVIS
        if not self._jarvis:
            self._send_json(503, {"ok": False, "error": "JARVIS not connected"})
            return

        try:
            captured = self._execute_jarvis_command(command, payload.get("speak", False))
            self._send_json(200, {
                "ok": True,
                "command": command,
                "result": captured["message"],
                "success": captured["ok"],
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            })
        except Exception as e:
            logger.error("Bridge command error: %s", e, exc_info=True)
            self._send_json(500, {"ok": False, "error": "Internal bridge error"})

    def _execute_jarvis_command(self, command: str, speak: bool) -> dict:
        """Execute a command in JARVIS, capturing the response."""
        captured = {"ok": False, "message": ""}
        jarvis = self._jarvis
        if jarvis is None:
            return captured

        original_respond = getattr(jarvis, "_respond", None)
        if original_respond is None:
            return {"ok": False, "message": "JARVIS _respond method not found"}

        lock = threading.Lock()

        def capture_respond(ok, message, tts=True):
            with lock:
                captured["ok"] = ok
                captured["message"] = message
            if speak:
                original_respond(ok, message, tts=True)
            else:
                jarvis._last_response = message

        jarvis._respond = capture_respond
        try:
            jarvis.process(command)
        finally:
            time.sleep(0.05)
            jarvis._respond = original_respond

        return captured


# ══════════════════════════════════════════════════════════════════════════════
# ARJUN DASHBOARD BRIDGE
# ══════════════════════════════════════════════════════════════════════════════

class ArjunDashboardBridge:
    """Launches the Arjun web dashboard and provides an HTTP bridge
    for bidirectional communication with JARVIS."""

    def __init__(self, jarvis=None, auto_open_browser=True):
        self.jarvis = jarvis
        self.web_port = WEB_PORT
        self.bridge_port = BRIDGE_PORT
        self.web_project_path = WEB_PROJECT_PATH
        self.auto_open_browser = auto_open_browser

        self._web_process = None
        self._web_stdout_thread = None
        self._bridge_server = None
        self._bridge_thread = None
        self._started = False
        self._lock = threading.Lock()

    def start(self) -> Tuple[bool, str]:
        with self._lock:
            if self._started:
                return True, "Already running"

            print("\n" + "═" * 72)
            print("  JARVIS + ARJUN DASHBOARD — Starting...")
            print("═" * 72)
            print(f"  Web project:  {self.web_project_path}")
            print(f"  JARVIS src:   {JARVIS_SOURCE_PATH or '(not found — bridge-only mode)'}")
            print(f"  Dev command:  {' '.join(NEXT_DEV_CMD)}")
            print(f"  Web port:     {self.web_port}")
            print(f"  Bridge port:  {self.bridge_port}")
            print("═" * 72)

            # 1. Start the Next.js dev server
            web_ok, web_msg = self._start_web_server()
            print(f"  {'✅' if web_ok else '⚠️'}  Web server: {web_msg}")

            # 2. Wait for Next.js, then open browser
            if web_ok or _is_port_open(self.web_port):
                url = f"http://localhost:{self.web_port}"
                print(f"  ⏳  Waiting for dashboard at {url}...")
                if _wait_for_server(url, timeout=HEALTH_TIMEOUT_SECONDS):
                    print(f"  ✅  Dashboard ready at {url}")
                    if self.auto_open_browser:
                        try:
                            webbrowser.open(url)
                            print(f"  🌐  Opened browser → {url}")
                        except Exception as e:
                            print(f"  ⚠️  Could not open browser: {e}")
                else:
                    print(f"  ⚠️  Dashboard not responding after {HEALTH_TIMEOUT_SECONDS}s")
                    print(f"      (it may still be compiling — try opening {url} manually)")

            # 3. Start the bridge HTTP server
            bridge_ok, bridge_msg = self._start_bridge_server()
            print(f"  {'✅' if bridge_ok else '❌'}  Bridge server: {bridge_msg}")

            if not bridge_ok:
                self._cleanup_web_process()
                return False, bridge_msg

            self._started = True
            print("═" * 72)
            print(f"  ✅  All systems running!")
            print(f"     Web dashboard: http://localhost:{self.web_port}")
            print(f"     Bridge API:    http://localhost:{self.bridge_port}")
            print(f"     Token:         {BRIDGE_TOKEN}")
            if not JARVIS_SOURCE_PATH:
                print(f"     ⚠️  JARVIS not found — running in bridge-only mode")
                print(f"        Web commands will return 'JARVIS not connected'")
            print("═" * 72)
            print(f"\n  Press Ctrl+C to shut down everything.\n")

            return True, "Started"

    def _start_web_server(self) -> Tuple[bool, str]:
        """Start the Next.js dev server as a subprocess."""
        # Validate project path first
        if not os.path.isdir(self.web_project_path):
            return False, f"Project path not found: {self.web_project_path}"

        package_json = os.path.join(self.web_project_path, "package.json")
        if not os.path.isfile(package_json):
            return False, f"package.json not found in {self.web_project_path}"

        # If port is already open, assume the web server is running
        if _is_port_open(self.web_port):
            return True, f"Already running on port {self.web_port}"

        try:
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0

            self._web_process = subprocess.Popen(  # nosec B603
                NEXT_DEV_CMD,
                cwd=self.web_project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                creationflags=creationflags,
            )

            # Drain stdout to prevent pipe buffer deadlock
            self._web_stdout_thread = threading.Thread(
                target=self._drain_web_stdout,
                name="WebStdoutDrain",
                daemon=True,
            )
            self._web_stdout_thread.start()

            logger.info("Started Next.js dev server (PID %d)", self._web_process.pid)
            return True, f"Started (PID {self._web_process.pid})"
        except FileNotFoundError:
            return False, f"'{NEXT_DEV_CMD[0]}' not found. Install bun or npm."
        except Exception as e:
            logger.error("Failed to start web server: %s", e, exc_info=True)
            return False, f"Failed: {e}"

    def _drain_web_stdout(self):
        """Read web server stdout to prevent pipe buffer deadlock."""
        if not self._web_process or not self._web_process.stdout:
            return
        try:
            for line in self._web_process.stdout:
                line_str = line.decode("utf-8", errors="replace").rstrip()
                if line_str:
                    logger.debug("[web] %s", line_str)
        except Exception as e:
            logger.debug("Web stdout drain ended: %s", e)

    def _start_bridge_server(self) -> Tuple[bool, str]:
        """Start the HTTP bridge server."""
        try:
            BridgeHTTPRequestHandler._jarvis = self.jarvis
            self._bridge_server = ThreadingHTTPServer(
                ("127.0.0.1", self.bridge_port),
                BridgeHTTPRequestHandler,
            )
            self._bridge_thread = threading.Thread(
                target=self._bridge_server.serve_forever,
                name="ArjunBridgeServer",
                daemon=True,
            )
            self._bridge_thread.start()
            self._started = True
            return True, f"Listening on port {self.bridge_port}"
        except OSError as e:
            if e.errno == errno.EADDRINUSE:
                return False, f"Port {self.bridge_port} already in use. Try a different port: ARJUN_BRIDGE_PORT=8766 python3 jarvis_arjun_all_in_one.py"
            return False, f"OSError {e.errno}: {e.strerror}"
        except Exception as e:
            logger.error("Bridge server start failed: %s", e, exc_info=True)
            return False, str(e)

    def _cleanup_web_process(self):
        """Terminate the web subprocess if it's running."""
        if self._web_process:
            try:
                self._web_process.terminate()
                self._web_process.wait(timeout=SUBPROCESS_TERMINATE_WAIT)
            except subprocess.TimeoutExpired:
                try:
                    self._web_process.kill()
                except Exception as kill_err:
                    logger.warning("Failed to kill web process: %s", kill_err)
            except Exception as e:
                logger.warning("Error during web process cleanup: %s", e)
            finally:
                self._web_process = None

    def stop(self):
        """Clean shutdown of web server and bridge."""
        with self._lock:
            if not self._started:
                return

            print("\n  Shutting down...")

            if self._bridge_server:
                try:
                    self._bridge_server.shutdown()
                    self._bridge_server.server_close()
                    if self._bridge_thread and self._bridge_thread.is_alive():
                        self._bridge_thread.join(timeout=BRIDGE_THREAD_JOIN_TIMEOUT)
                    print("  ✅  Bridge server stopped")
                except Exception as e:
                    print(f"  ⚠️  Bridge shutdown error: {e}")
                finally:
                    self._bridge_server = None
                    self._bridge_thread = None

            self._cleanup_web_process()
            self._web_stdout_thread = None

            self._started = False
            print("  ✅  All stopped. Goodbye!")

    def is_running(self) -> bool:
        return self._started and _is_port_open(self.bridge_port)


# ══════════════════════════════════════════════════════════════════════════════
# JARVIS IMPORT (with graceful fallback)
# ══════════════════════════════════════════════════════════════════════════════

def import_jarvis():
    """Try to import JARVIS v11. Returns (JARVIS_class, error_message)."""
    if not JARVIS_SOURCE_PATH:
        return None, "JARVIS source path not found"

    # Add to path
    if JARVIS_SOURCE_PATH not in sys.path:
        sys.path.insert(0, JARVIS_SOURCE_PATH)

    try:
        from JARVIS_v11_WINDOWS_FIXED import JARVIS
        return JARVIS, None
    except ImportError as e:
        return None, f"Could not import JARVIS: {e}\n  Make sure JARVIS_v11_WINDOWS_FIXED.py is in: {JARVIS_SOURCE_PATH}"
    except Exception as e:
        return None, f"JARVIS import error: {e}"


# ══════════════════════════════════════════════════════════════════════════════
# PATCH JARVIS COMMANDS (add dashboard-specific commands)
# ══════════════════════════════════════════════════════════════════════════════

def patch_jarvis_commands(jarvis, bridge):
    """Add dashboard-specific commands to JARVIS."""
    original_process = jarvis.process

    def patched_process(raw):
        raw_lower = raw.lower().strip() if raw else ""

        if "dashboard status" in raw_lower or "link status" in raw_lower:
            running = bridge.is_running()
            msg = (f"Dashboard link: {'ACTIVE' if running else 'INACTIVE'}\n"
                   f"  Web: http://localhost:{bridge.web_port}\n"
                   f"  Bridge: http://localhost:{bridge.bridge_port}\n"
                   f"  Commands: {getattr(jarvis, '_command_count', 0)} processed")
            jarvis._respond(running, msg, tts=False)
            return

        if "open dashboard" in raw_lower or "open arjun" in raw_lower:
            webbrowser.open(f"http://localhost:{bridge.web_port}")
            jarvis._respond(True, "Opening Arjun dashboard in browser", tts=False)
            return

        if "close dashboard" in raw_lower or "close arjun" in raw_lower:
            bridge.stop()
            jarvis._respond(True, "Dashboard bridge stopped", tts=False)
            return

        if "restart dashboard" in raw_lower:
            bridge.stop()
            time.sleep(1)
            bridge.start()
            jarvis._respond(True, "Dashboard restarted", tts=False)
            return

        original_process(raw)

    jarvis.process = patched_process
    logger.info("JARVIS patched with dashboard commands")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def main():
    auto_browser = "--no-browser" not in sys.argv

    print("\n" + "╔" + "═" * 76 + "╗")
    print("║" + "  JARVIS v11 + ARJUN DASHBOARD — ALL-IN-ONE RUNNER".center(76) + "║")
    print("╚" + "═" * 76 + "╝\n")

    # ─── Step 1: Start the bridge + web dashboard ──────────────────────
    print("  [1/3] Starting web dashboard + bridge server...")
    bridge = ArjunDashboardBridge(jarvis=None, auto_open_browser=auto_browser)
    ok, msg = bridge.start()
    if not ok:
        print(f"\n  ❌  Failed to start: {msg}")
        print(f"  Press Enter to exit...")
        input()
        sys.exit(1)

    # ─── Step 2: Try to import JARVIS ──────────────────────────────────
    print("\n  [2/3] Importing JARVIS v11...")
    JARVIS_CLASS, jarvis_error = import_jarvis()

    if JARVIS_CLASS is None:
        print(f"  ⚠️  {jarvis_error}")
        print(f"  Running in bridge-only mode.")
        print(f"  The web dashboard works — JARVIS commands will return 'not connected'.")
        print(f"\n  To enable JARVIS, place JARVIS_v11_WINDOWS_FIXED.py in one of:")
        print(f"    ~/my-project/upload/")
        print(f"    /home/z/my-project/upload/")
        print(f"    (same folder as this script)")

        # Run bridge-only mode — wait for Ctrl+C
        print(f"\n  Bridge running. Press Ctrl+C to stop.")
        try:
            while bridge.is_running():
                time.sleep(1)
        except KeyboardInterrupt:
            bridge.stop()
        return

    # ─── Step 3: Initialize JARVIS ─────────────────────────────────────
    print("  ✅  JARVIS v11 imported successfully")
    print("\n  [3/3] Initializing JARVIS modules...")
    try:
        jarvis = JARVIS_CLASS()
        bridge.jarvis = jarvis
        BridgeHTTPRequestHandler._jarvis = jarvis
        patch_jarvis_commands(jarvis, bridge)
        print("  ✅  JARVIS initialized and linked to dashboard")
    except Exception as e:
        print(f"  ⚠️  JARVIS init failed: {e}")
        traceback.print_exc()
        print(f"\n  Running in bridge-only mode. Press Ctrl+C to stop.")
        try:
            while bridge.is_running():
                time.sleep(1)
        except KeyboardInterrupt:
            bridge.stop()
        return

    # ─── Run JARVIS main loop ──────────────────────────────────────────
    try:
        jarvis.run()
    except KeyboardInterrupt:
        pass
    finally:
        bridge.stop()


# ══════════════════════════════════════════════════════════════════════════════
# RUN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    main()
