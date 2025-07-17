import asyncio
import http.server
import socketserver
import threading
import websockets
from pathlib import Path
import os

# --- Constants ---
HTTP_PORT = 8000
WS_PORT = 8765
BASE_DIR = Path(__file__).parent.resolve()
BUILD = BASE_DIR / "build"

# --- HTML Page ---
HTML = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <title>WebSocket Test</title>
</head>
<body>
  <h1>WebSocket Test Page</h1>
  <p>Open the browser console to see connection messages.</p>
  <script>
    const ws = new WebSocket("ws://localhost:{WS_PORT}/test");
    ws.onopen = () => console.log("✅ WebSocket connected");
    ws.onmessage = (e) => console.log("📨 Message:", e.data);
    ws.onerror = (e) => console.error("❌ WebSocket error", e);
  </script>
</body>
</html>
"""

# --- Write HTML file ---
BUILD.mkdir(exist_ok=True)
(HTML_FILE := BUILD / "index.html").write_text(HTML, encoding="utf-8")

# ✅ Move this BEFORE starting servers
os.chdir(str(BUILD))

# --- HTTP Server Thread ---
def start_http():
    handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", HTTP_PORT), handler)
    print(f"🌐 Serving HTTP on http://localhost:{HTTP_PORT}")
    httpd.serve_forever()

# --- WebSocket Handler ---
async def websocket_handler(websocket):
    print(f"🔌 WebSocket connected")
    try:
        await websocket.send("Hello from server!")
        await websocket.wait_closed()
    except Exception as e:
        print("WebSocket error:", e)

# --- Main Async Entrypoint ---
async def main():
    # ✅ Now servers start after chdir
    threading.Thread(target=start_http, daemon=True).start()

    print(f"📡 Starting WebSocket server on ws://localhost:{WS_PORT}")
    async with websockets.serve(websocket_handler, "localhost", WS_PORT):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
