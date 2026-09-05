import sys
sys.path.insert(0, 'backend')
from app.main import app

for r in app.routes:
    methods = list(r.methods) if hasattr(r, 'methods') else []
    path = getattr(r, 'path', '')
    print(f"{methods} {path}")
