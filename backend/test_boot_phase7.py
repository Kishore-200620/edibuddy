import sys
import time
import subprocess
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path

# Fix sys.path for direct imports
sys.path.insert(0, 'backend')
try:
    import fastapi
    import uvicorn
    from app.main import app
    print(f"FASTAPI_IMPORT_SUCCESS: True")
    print(f"APP_TITLE: {app.title}")
    FASTAPI_VERSION = getattr(fastapi, '__version__', 'unknown')
    UVICORN_VERSION = getattr(uvicorn, '__version__', 'unknown')
except Exception as e:
    print(f"FASTAPI_IMPORT_SUCCESS: False (Exception: {e})")
    sys.exit(1)

print(f"PYTHON_EXECUTABLE: {sys.executable}")
print(f"PYTHON_VERSION: {sys.version.split(' ')[0]}")
print(f"FASTAPI_VERSION: {FASTAPI_VERSION}")
print(f"UVICORN_VERSION: {UVICORN_VERSION}")

# Inspect routers
expected_routers = [
    "answers", "assessments", "avatar", "documents", 
    "lessons", "progress", "voice", "health", 
    "sessions", "students", "websocket"
]

routes = app.routes
route_paths = []
router_status = {r: False for r in expected_routers}

for r in routes:
    path = getattr(r, 'path', None)
    if path:
        route_paths.append((getattr(r, 'methods', set()), path, getattr(r, 'name', 'unknown')))
        # naive check of path prefixes
        for expected in expected_routers:
            if f"/{expected}" in path:
                router_status[expected] = True

print("\n--- ROUTER REGISTRATION ---")
for r, status in router_status.items():
    print(f"{r} | {status}")

print("\n--- ROUTE TABLE ---")
health_path = None
for methods, path, name in route_paths:
    print(f"{list(methods)} | {path} | {name}")
    if "health" in path.lower() or path == "/" or path == "/ping":
        # simple heuristic for a safe endpoint
        if not health_path:
            health_path = path

print(f"\nHEALTH_ENDPOINT_CANDIDATE: {health_path}")

print("\n--- UVICORN STARTUP TEST ---")
server_process = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8080", "--host", "127.0.0.1"],
    cwd="backend",
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

# Wait for startup
time.sleep(4)

smoke_url = f"http://127.0.0.1:8080{health_path if health_path else '/docs'}"
print(f"SMOKE_URL: {smoke_url}")
smoke_status = "FAILED"
smoke_response = ""

try:
    req = urllib.request.Request(smoke_url)
    with urllib.request.urlopen(req, timeout=3) as response:
        smoke_status = response.getcode()
        smoke_response = response.read().decode('utf-8')[:100]
        print(f"SMOKE_HTTP_STATUS: {smoke_status}")
        print(f"SMOKE_RESPONSE: {smoke_response}")
except urllib.error.HTTPError as e:
    smoke_status = e.code
    print(f"SMOKE_HTTP_STATUS: {smoke_status}")
    print(f"SMOKE_RESPONSE: {e.read().decode('utf-8')[:100]}")
except Exception as e:
    print(f"SMOKE_ERROR: {e}")

is_alive = server_process.poll() is None
print(f"PROCESS_ALIVE_AFTER_REQUEST: {is_alive}")

server_process.terminate()
server_process.wait(timeout=5)
print(f"SHUTDOWN_COMPLETED: True")

print("\n--- SERVER LOGS ---")
stdout, _ = server_process.communicate()
print(stdout)
