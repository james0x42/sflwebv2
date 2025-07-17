import os
import asyncio
import threading
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import websockets
import http.server
import shutil

# Paths
ROOT = Path(__file__).parent.resolve()
CONTENT = ROOT / "content"
BUILD = ROOT / "build"
PORT = 8000
WS_PORT = 8765

# Jinja environment
env = Environment(loader=FileSystemLoader(str(CONTENT)))

# Live reload script
RELOAD_SCRIPT = """
<script>
  const ws = new WebSocket('ws://localhost:8765');
  ws.onmessage = (e) => { if (e.data === 'reload') location.reload(); };
</script>
"""

# WebSocket clients
clients = set()

# Correct websocket handler (2 arguments required)
async def websocket_handler(websocket, path):
    clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        clients.remove(websocket)

# Notify clients to reload
async def broadcast_reload():
    if clients:
        await asyncio.wait([client.send("reload") for client in clients])

def trigger_reload(loop):
    asyncio.run_coroutine_threadsafe(broadcast_reload(), loop)

# Build site (including CSS copy)
def build_site():
    print("🔧 Building site...")
    BUILD.mkdir(exist_ok=True)

    try:
        # Render index.html
        template = env.get_template("index.html")
        rendered = template.render()
        (BUILD / "index.html").write_text(rendered + RELOAD_SCRIPT, encoding="utf-8")

        # Copy styles.css if exists
        css_src = CONTENT / "styles.css"
        if css_src.exists():
            shutil.copy2(css_src, BUILD / "styles.css")
            print("🎨 Copied styles.css")

        print("✅ Site built.")
    except Exception as e:
        print("❌ Build error:", e)

# File watcher
class ChangeHandler(FileSystemEventHandler):
    def __init__(self, loop):
        self.loop = loop

    def on_any_event(self, event):
        if not event.is_directory:
            build_site()
            trigger_reload(self.loop)

def start_watcher(loop):
    handler = ChangeHandler(loop)
    observer = Observer()
    observer.schedule(handler, str(CONTENT), recursive=True)
    observer.start()
    print(f"👀 Watching {CONTENT}")
    try:
        observer.join()
    except KeyboardInterrupt:
        observer.stop()
        observer.join()

# HTTP Server
def start_http():
    BUILD.mkdir(exist_ok=True)
    os.chdir(str(BUILD))
    server = http.server.ThreadingHTTPServer(("localhost", PORT), http.server.SimpleHTTPRequestHandler)
    print(f"🌍 Serving at http://localhost:{PORT}")
    server.serve_forever()

# Main asyncio function
async def main():
    build_site()
    loop = asyncio.get_running_loop()

    # Start threads for HTTP server and watcher
    threading.Thread(target=start_http, daemon=True).start()
    threading.Thread(target=start_watcher, args=(loop,), daemon=True).start()

    # Correct WebSocket server setup
    print(f"🔌 WebSocket server on ws://localhost:{WS_PORT}")
    async with websockets.serve(websocket_handler, "localhost", WS_PORT):
        await asyncio.Future()  # Run indefinitely

if __name__ == "__main__":
    asyncio.run(main())
