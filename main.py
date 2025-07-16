import asyncio
import http.server
import os
import shutil
import threading
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import sass
import markdown
import websockets

# --- Config ---
CONTENT_DIR = Path("content")
TEMPLATE_DIR = Path("templates")
STATIC_DIR = Path("static")
BUILD_DIR = Path("build")
PORT = 8000
RELOAD_PORT = 8765

# --- Jinja ---
env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))

def build_site():
    print("🛠 Rebuilding site...")
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True)

    if STATIC_DIR.exists():
        shutil.copytree(STATIC_DIR, BUILD_DIR / "static")

    for path in CONTENT_DIR.rglob("*"):
        rel_path = path.relative_to(CONTENT_DIR)
        output_path = BUILD_DIR / rel_path

        if path.suffix == ".md":
            with open(path, "r", encoding="utf-8") as f:
                html = markdown.markdown(f.read())
            rendered = env.get_template("base.html").render(content=html)
            output_path = output_path.with_suffix(".html")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(rendered + LIVE_RELOAD_SCRIPT, encoding="utf-8")

        elif path.suffix == ".html":
            template = env.get_template(str(rel_path))
            rendered = template.render()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(rendered + LIVE_RELOAD_SCRIPT, encoding="utf-8")

        elif path.suffix == ".scss":
            css = sass.compile(filename=str(path))
            output_path = output_path.with_suffix(".css")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(css, encoding="utf-8")

        elif path.is_file():
            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, output_path)

    print("✅ Site built.")

# --- Live Reload Script ---
LIVE_RELOAD_SCRIPT = """
<script>
  const ws = new WebSocket('ws://localhost:8765');
  ws.onmessage = (event) => {
    if (event.data === 'reload') {
      console.log("🔁 Reloading...");
      location.reload();
    }
  };
</script>
"""

# --- WebSocket Server for Reload ---
clients = set()

async def reload_server():
    async def handler(websocket, path):
        clients.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            clients.remove(websocket)

    async with websockets.serve(handler, "localhost", RELOAD_PORT):
        await asyncio.Future()  # run forever

def trigger_reload():
    print("🔁 Triggering reload...")
    asyncio.run(send_reload())

async def send_reload():
    to_remove = set()
    for ws in clients:
        try:
            await ws.send("reload")
        except:
            to_remove.add(ws)
    clients.difference_update(to_remove)

# --- File Watcher ---
class ChangeHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        if not event.is_directory:
            build_site()
            asyncio.run(send_reload())

def watch_files():
    build_site()
    observer = Observer()
    observer.schedule(ChangeHandler(), str(CONTENT_DIR), recursive=True)
    observer.start()
    print("👀 Watching for changes...")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# --- HTTP Server ---
def start_http_server():
    os.chdir(BUILD_DIR)
    handler = http.server.SimpleHTTPRequestHandler
    httpd = http.server.ThreadingHTTPServer(("localhost", PORT), handler)
    print(f"🌍 Serving at http://localhost:{PORT}")
    httpd.serve_forever()

# --- Main ---
def main():
    threading.Thread(target=start_http_server, daemon=True).start()
    threading.Thread(target=watch_files, daemon=True).start()
    asyncio.run(reload_server())

if __name__ == "__main__":
    main()
