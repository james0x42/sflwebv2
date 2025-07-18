import asyncio
import os
import threading
import http.server
import socketserver
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import sass
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import websockets
import subprocess
# --- Absolute paths ---
ROOT_DIR = Path(__file__).parent.resolve()
CONTENT_DIR = ROOT_DIR / "content"
BUILD_DIR = ROOT_DIR / "build"
SCSS_FILE = CONTENT_DIR / "styles.scss"
CSS_FILE = BUILD_DIR / "styles.css"
INDEX_TEMPLATE = CONTENT_DIR / "index.html"
OUTPUT_HTML = BUILD_DIR / "index.html"

# --- Server Ports ---
HTTP_PORT = 8000
WS_PORT = 8765

# --- WebSocket clients ---
clients = set()

# -----------------------
# SCSS Compilation
# -----------------------

def compile_scss():
    if SCSS_FILE.exists():
        try:
            subprocess.run([
                "npx", "sass",
                "--no-source-map",
                str(SCSS_FILE),
                str(CSS_FILE)
            ], check=True)
            print(f"✅ Compiled SCSS (Dart Sass) → {CSS_FILE}")
        except subprocess.CalledProcessError as e:
            print(f"❌ SCSS compilation failed: {e}")
    else:
        print(f"⚠️  No SCSS file found at {SCSS_FILE}")
# -----------------------
# Jinja Rendering
# -----------------------
def render_site():
    env = Environment(loader=FileSystemLoader(str(CONTENT_DIR)))
    try:
        template = env.get_template(INDEX_TEMPLATE.name)
        html = template.render()
        OUTPUT_HTML.write_text(html, encoding="utf-8")
        print(f"✅ Rendered HTML → {OUTPUT_HTML}")
    except Exception as e:
        print(f"❌ Jinja render error: {e}")

# -----------------------
# WebSocket Live Reload
# -----------------------
async def ws_handler(websocket, path):
    clients.add(websocket)
    print(f"🔌 WebSocket connected on path: {path}")
    try:
        await websocket.wait_closed()
    finally:
        clients.remove(websocket)

async def start_websocket_server():
    print(f"📡 Starting WebSocket server on ws://localhost:{WS_PORT}")
    async with websockets.serve(ws_handler, "localhost", WS_PORT):
        await asyncio.Future()  # Run forever

def broadcast_reload():
    for ws in list(clients):
        try:
            asyncio.run_coroutine_threadsafe(ws.send("reload"), asyncio.get_event_loop())
        except Exception:
            pass

# -----------------------
# HTTP Server
# -----------------------
def start_http():
    os.chdir(str(BUILD_DIR))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", HTTP_PORT), handler) as httpd:
        print(f"🌐 Serving site at http://localhost:{HTTP_PORT}")
        httpd.serve_forever()

# -----------------------
# Watchdog File Watcher
# -----------------------
class ChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return
        print(f"🔄 Detected change: {event.src_path}")
        compile_scss()
        render_site()
        broadcast_reload()

# -----------------------
# Main Function
# -----------------------
def main():
    # Initial build
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    compile_scss()
    render_site()

    # Start servers
    threading.Thread(target=start_http, daemon=True).start()
    threading.Thread(target=lambda: asyncio.run(start_websocket_server()), daemon=True).start()

    # Start file watcher
    observer = Observer()
    observer.schedule(ChangeHandler(), str(CONTENT_DIR), recursive=True)
    observer.start()
    print(f"👀 Watching for changes in {CONTENT_DIR}")

    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
