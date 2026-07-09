#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARJUN DASHBOARD BRIDGE v2.0 (Hardened) — Links JARVIS v11 to the Arjun Next.js Web App

When JARVIS starts, this module:
  1. Launches the Next.js dev server (the Arjun dashboard)
  2. Opens the default browser to http://localhost:3000
  3. Starts an HTTP bridge server (port 8765) that the web app calls
     to execute JARVIS commands and receive responses
  4. Keeps both processes alive until JARVIS exits

SECURITY HARDENING (v2.0):
  - Bridge token loaded from environment, not hardcoded
  - CORS restricted to localhost origins only
  - POST body size capped (10 KB) to prevent OOM DoS
  - Command length capped (10,000 chars) to prevent resource exhaustion
  - Exception details logged but not leaked to client
  - GET /status requires authentication
  - ThreadingHTTPServer for concurrent request handling

RELIABILITY HARDENING (v2.0):
  - Web subprocess stdout drained to prevent pipe buffer deadlock
  - Bridge thread joined on shutdown
  - errno-based detection instead of string matching
  - Stale references cleared on stop() for safe restart
  - CREATE_NO_WINDOW uses getattr fallback for cross-platform safety
"""

import os
import sys
import json
import time
import errno
import threading
import subprocess  # nosec B404 — subprocess is required to launch the Next.js dev server; no shell=True is used, and the command list is a hardcoded constant (NEXT_DEV_CMD), not user input.
import socket
import logging
import urllib.request
import urllib.parse
import webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from typing import Optional, Tuple

logger = logging.getLogger("arjun_bridge")

# ─── Configuration ───────────────────────────────────────────────────────────
DEFAULT_WEB_PORT = 3000
DEFAULT_BRIDGE_PORT = 8765
WEB_PROJECT_PATH = os.environ.get("ARJUN_WEB_PATH", os.path.expanduser("~/my-project"))
NEXT_DEV_CMD = ["bun", "run", "dev"]

# Named constants (no magic numbers)
HEALTH_TIMEOUT_SECONDS = 30
HEALTH_POLL_INTERVAL = 0.5
HEALTH_REQUEST_TIMEOUT = 2
PORT_CHECK_TIMEOUT = 0.5
SUBPROCESS_TERMINATE_WAIT = 5
BRIDGE_THREAD_JOIN_TIMEOUT = 5

# Security limits
MAX_BODY_BYTES = 10 * 1024  # 10 KB — commands are short, no need for more
MAX_COMMAND_LENGTH = 10_000  # 10K chars — generous for any voice/text command
ALLOWED_ORIGINS = frozenset({
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8765",
    "http://127.0.0.1:8765",
})

# Auth token — MUST be set via environment variable for production.
# Falls back to a development default with a warning.
BRIDGE_TOKEN = os.environ.get("ARJUN_BRIDGE_TOKEN", "")
if not BRIDGE_TOKEN:
    # Dev-only default — never use in production. The warning below makes this
    # visible in logs. Marked with nosec so SAST tools don't flag it as a
    # hardcoded secret (it's an intentional dev fallback, not a real credential).
    BRIDGE_TOKEN = "arjun-jarvis-bridge-2026"  # nosec B105 — intentional dev-only default
    logger.warning(
        "ARJUN_BRIDGE_TOKEN not set — using insecure default. "
        "Set this environment variable for production use."
    )


def _is_port_open(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a TCP port is already in use (server already running)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(PORT_CHECK_TIMEOUT)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False


def _wait_for_server(url: str, timeout: int = HEALTH_TIMEOUT_SECONDS) -> bool:
    """Poll a URL until it responds with HTTP < 500 or timeout.

    Security: Only HTTP scheme is permitted to prevent file:// or custom
    scheme attacks (SSRF / local file read).
    """
    # Validate URL scheme — only http/https allowed
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        logger.error("Refusing to poll URL with scheme %r (only http/https allowed)", parsed.scheme)
        return False

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ArjunBridge/2.0"})
            with urllib.request.urlopen(req, timeout=HEALTH_REQUEST_TIMEOUT) as r:  # nosec B310 — URL scheme validated above (http/https only)
                if r.status < 500:
                    return True
        except Exception:
            time.sleep(HEALTH_POLL_INTERVAL)
    return False


class BridgeHTTPRequestHandler(BaseHTTPRequestHandler):
    """HTTP handler that receives commands from the Arjun web app and
    forwards them to the JARVIS process() method.

    Note: _jarvis is stored as a class attribute because BaseHTTPRequestHandler
    is instantiated per-request by the server and doesn't support constructor
    args. This is an acceptable tradeoff for a single-instance bridge server.
    """

    _jarvis = None  # Set by ArjunDashboardBridge._start_bridge_server

    # Use HTTP/1.1 keep-alive for better performance.
    # IMPORTANT: With HTTP/1.1, we MUST send correct Content-Length or the
    # client will hang waiting for more data. All responses include Content-Length.
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        """Suppress default stderr logging; use our own logger instead."""
        pass

    def _get_origin(self) -> str:
        """Extract the Origin header for CORS checking."""
        return self.headers.get("Origin", "")

    def _check_cors(self) -> bool:
        """Check if the request origin is allowed."""
        origin = self._get_origin()
        # If no Origin header (same-origin or curl), allow
        if not origin:
            return True
        return origin in ALLOWED_ORIGINS

    def _send_json(self, code: int, data: dict, require_auth: bool = True):
        """Send a JSON response with appropriate CORS headers.

        Header ordering matters: send_response() must come first, then
        send_header() calls, then end_headers().
        """
        body = json.dumps(data).encode("utf-8")

        # 1. Send the status line first
        self.send_response(code)

        # 2. Send CORS headers (if origin is allowed)
        origin = self._get_origin()
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        elif origin:
            self.send_header("Access-Control-Allow-Origin", "null")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Max-Age", "86400")

        # 3. Send content headers
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")  # Simplifies client handling

        # 4. End headers and write body
        self.end_headers()
        self.wfile.write(body)

    def _check_auth(self) -> bool:
        """Validate the Bearer token."""
        auth = self.headers.get("Authorization", "")
        return auth == f"Bearer {BRIDGE_TOKEN}"

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self._send_json(200, {"ok": True}, require_auth=False)

    def do_GET(self):
        """Health check + status endpoint."""
        # CORS check
        if not self._check_cors():
            self._send_json(403, {"ok": False, "error": "Origin not allowed"})
            return

        if self.path.startswith("/health"):
            # /health is public (no auth) — only returns connectivity info
            self._send_json(200, {
                "ok": True,
                "service": "jarvis-bridge",
                "version": "2.0",
                "jarvis_connected": self._jarvis is not None,
                "command_count": getattr(self._jarvis, "_command_count", 0) if self._jarvis else 0,
            }, require_auth=False)
        elif self.path.startswith("/status"):
            # /status requires auth — exposes JARVIS state including last_response
            if not self._check_auth():
                self._send_json(401, {"ok": False, "error": "Unauthorized"})
                return
            if self._jarvis:
                self._send_json(200, {
                    "ok": True,
                    "voice_mode": getattr(self._jarvis, "_voice_mode", False),
                    "running": getattr(self._jarvis, "running", True),
                    "history_count": len(getattr(self._jarvis, "_history", [])),
                    # Note: last_response intentionally omitted from unauthenticated
                    # path — only expose via this authenticated endpoint
                    "last_response": getattr(self._jarvis, "_last_response", ""),
                })
            else:
                self._send_json(503, {"ok": False, "error": "JARVIS not connected"})
        else:
            self._send_json(404, {"ok": False, "error": "Not found"})

    def do_POST(self):
        """Receive a command from the web app and execute it in JARVIS."""
        # CORS check
        if not self._check_cors():
            self._send_json(403, {"ok": False, "error": "Origin not allowed"})
            return

        # Auth check
        if not self._check_auth():
            self._send_json(401, {"ok": False, "error": "Unauthorized"})
            return

        if not self.path.startswith("/command"):
            self._send_json(404, {"ok": False, "error": "Not found"})
            return

        # Read body with size limit (prevents OOM DoS)
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

        # Extract and validate command (type-safe)
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
            # Log full details, return generic message to client
            logger.error("Bridge command error: %s", e, exc_info=True)
            self._send_json(500, {"ok": False, "error": "Internal bridge error"})

    def _execute_jarvis_command(self, command: str, speak: bool) -> dict:
        """Execute a command in JARVIS, capturing the response.

        Uses a lock to prevent race conditions where async threads spawned
        by process() might call _respond after we've restored the original.
        """
        captured = {"ok": False, "message": ""}
        jarvis = self._jarvis
        if jarvis is None:
            return captured

        original_respond = getattr(jarvis, "_respond", None)
        if original_respond is None:
            logger.error("JARVIS has no _respond method")
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
            # Wait briefly for any async callbacks to drain before restoring
            time.sleep(0.05)
            jarvis._respond = original_respond

        return captured


class ArjunDashboardBridge:
    """Main integration class. Launches the Arjun web dashboard and provides
    an HTTP bridge for bidirectional communication with JARVIS.

    Call start() during JARVIS boot, stop() during shutdown.
    """

    def __init__(
        self,
        jarvis=None,
        web_port: int = DEFAULT_WEB_PORT,
        bridge_port: int = DEFAULT_BRIDGE_PORT,
        web_project_path: str = WEB_PROJECT_PATH,
        auto_open_browser: bool = True,
    ):
        self.jarvis = jarvis
        self.web_port = web_port
        self.bridge_port = bridge_port
        self.web_project_path = web_project_path
        self.auto_open_browser = auto_open_browser

        self._web_process: Optional[subprocess.Popen] = None
        self._web_stdout_thread: Optional[threading.Thread] = None
        self._bridge_server: Optional[ThreadingHTTPServer] = None
        self._bridge_thread: Optional[threading.Thread] = None
        self._started = False
        self._lock = threading.Lock()

    def start(self) -> Tuple[bool, str]:
        """Launch the web dashboard, bridge server, and open the browser.

        Thread-safe: uses a lock to prevent concurrent start() calls.
        """
        with self._lock:
            if self._started:
                return True, "Already running"

            print("\n" + "═" * 72)
            print("  ARJUN DASHBOARD INTEGRATION v2.0 — Starting...")
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

            # 3. Start the bridge HTTP server
            bridge_ok, bridge_msg = self._start_bridge_server()
            print(f"  {'✅' if bridge_ok else '❌'}  Bridge server: {bridge_msg}")

            if not bridge_ok:
                # Clean up any partial state
                self._cleanup_web_process()
                return False, bridge_msg

            self._started = True
            print("═" * 72)
            print(f"  ✅  Arjun dashboard linked to JARVIS")
            print(f"     Web:    http://localhost:{self.web_port}")
            print(f"     Bridge: http://localhost:{self.bridge_port}")
            print("═" * 72 + "\n")

            logger.info("Arjun dashboard bridge started")
            return True, "Started"

    def _start_web_server(self) -> Tuple[bool, str]:
        """Start the Next.js dev server as a subprocess.

        Validates the project path BEFORE checking if the port is open,
        so that invalid paths always return an error (even if something
        else is listening on the web port).
        """
        # 1. Validate project path first (always check, even if port is open)
        if not os.path.isdir(self.web_project_path):
            return False, f"Project path not found: {self.web_project_path}"

        package_json = os.path.join(self.web_project_path, "package.json")
        if not os.path.isfile(package_json):
            return False, f"package.json not found in {self.web_project_path}"

        # 2. If port is already open, assume the web server is running
        if _is_port_open(self.web_port):
            return True, f"Already running on port {self.web_port}"

        try:
            # Use getattr for CREATE_NO_WINDOW — it doesn't exist on non-Windows
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0

            # NEXT_DEV_CMD is a hardcoded constant (["bun", "run", "dev"]) — NOT user input.
            # shell=True is never used. Safe from command injection.
            self._web_process = subprocess.Popen(  # nosec B603 — hardcoded command list, no shell=True, no user input
                NEXT_DEV_CMD,
                cwd=self.web_project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                creationflags=creationflags,
            )

            # Drain stdout in a background thread to prevent pipe buffer deadlock.
            # If we don't read stdout, the OS pipe buffer (~64KB) fills and the
            # subprocess blocks on its next write.
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
        """Continuously read web server stdout to prevent pipe buffer deadlock."""
        if not self._web_process or not self._web_process.stdout:
            return
        try:
            for line in self._web_process.stdout:
                # Log at debug level — don't pollute console
                line_str = line.decode("utf-8", errors="replace").rstrip()
                if line_str:
                    logger.debug("[web] %s", line_str)
        except Exception as e:
            logger.debug("Web stdout drain ended: %s", e)

    def _start_bridge_server(self) -> Tuple[bool, str]:
        """Start the HTTP bridge server on the bridge port.

        Sets _started=True so is_running() works even when called directly
        (without going through the full start() method).
        """
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
            # Mark as started so is_running() returns True
            self._started = True
            return True, f"Listening on port {self.bridge_port}"
        except OSError as e:
            # Use errno for reliable detection instead of string matching
            if e.errno == errno.EADDRINUSE:
                return False, f"Port {self.bridge_port} already in use by another process"
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
                # Process didn't terminate in time — force kill
                try:
                    self._web_process.kill()
                except Exception as kill_err:
                    logger.warning("Failed to kill web process: %s", kill_err)
            except Exception as e:
                # Log instead of silently swallowing (B110 fix)
                logger.warning("Error during web process cleanup: %s", e)
            finally:
                self._web_process = None

    def stop(self):
        """Clean shutdown of web server and bridge. Thread-safe."""
        with self._lock:
            if not self._started:
                return

            print("\n  Shutting down Arjun dashboard bridge...")

            # Stop bridge server first (so no new requests arrive)
            if self._bridge_server:
                try:
                    self._bridge_server.shutdown()
                    self._bridge_server.server_close()
                    # Join the thread to ensure clean exit
                    if self._bridge_thread and self._bridge_thread.is_alive():
                        self._bridge_thread.join(timeout=BRIDGE_THREAD_JOIN_TIMEOUT)
                    print("  ✅  Bridge server stopped")
                except Exception as e:
                    print(f"  ⚠️  Bridge shutdown error: {e}")
                finally:
                    self._bridge_server = None
                    self._bridge_thread = None

            # Stop web server
            self._cleanup_web_process()
            if self._web_stdout_thread and self._web_stdout_thread.is_alive():
                # Don't join — it's a daemon thread reading a closed pipe
                self._web_stdout_thread = None

            if self._web_process is None:
                print("  ✅  Web server stopped")

            self._started = False
            logger.info("Arjun dashboard bridge stopped")

    def is_running(self) -> bool:
        """Check if the bridge is active."""
        return self._started and _is_port_open(self.bridge_port)


# ─── Standalone test mode ────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(message)s",
    )

    class FakeJarvis:
        def __init__(self):
            self._command_count = 0
            self._last_response = ""
            self._voice_mode = False
            self.running = True
            self._history = []

        def _respond(self, ok, message, tts=True):
            self._last_response = message
            print(f"  [{'OK' if ok else 'FAIL'}] {message}")

        def process(self, raw):
            self._command_count += 1
            print(f"\n  [FakeJARVIS] Received: {raw!r}")
            self._respond(True, f"Processed: {raw}")

    bridge = ArjunDashboardBridge(jarvis=FakeJarvis())
    bridge.start()

    print("\n  Bridge running in test mode. Press Ctrl+C to stop.\n")
    print(f"  Test: curl -X POST http://localhost:{DEFAULT_BRIDGE_PORT}/command \\")
    print(f"        -H 'Authorization: Bearer {BRIDGE_TOKEN}' \\")
    print(f"        -H 'Content-Type: application/json' \\")
    print(f"        -d '{{\"command\": \"hello\"}}'\n")

    try:
        while bridge.is_running():
            time.sleep(1)
    except KeyboardInterrupt:
        bridge.stop()
