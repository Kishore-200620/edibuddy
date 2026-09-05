import sys
sys.path.insert(0, 'backend')

from sqlalchemy import text
from app.database.connection import engine
import pkgutil
import importlib
import traceback

def test_db():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            print("DB_CONNECT=PASS")
            
            # Check pgvector
            result = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'")).fetchone()
            if result:
                print("PGVECTOR_EXT=PASS")
            else:
                print("PGVECTOR_EXT=FAIL (extension not found)")
    except Exception as e:
        print(f"DB_CONNECT=FAIL ({e})")
        
def import_submodules(package_name):
    try:
        package = importlib.import_module(package_name)
    except Exception as e:
        print(f"IMPORT_FAIL {package_name}: {e}")
        return

    prefix = package.__name__ + "."
    for _, module_name, is_pkg in pkgutil.walk_packages(package.__path__, prefix):
        try:
            importlib.import_module(module_name)
        except Exception as e:
            print(f"IMPORT_FAIL {module_name}: {e}")

if __name__ == "__main__":
    print("--- DB Test ---")
    test_db()
    
    print("\n--- Model Imports ---")
    import_submodules("app.models")
    print("Models done")
    
    print("\n--- RAG Imports ---")
    import_submodules("app.rag")
    print("RAG done")
    
    print("\n--- Teacher Imports ---")
    import_submodules("app.teacher")
    print("Teacher done")
    
    print("\n--- Voice Imports ---")
    import_submodules("app.voice")
    print("Voice done")
    
    print("\n--- Avatar Imports ---")
    import_submodules("app.avatar")
    print("Avatar done")
    
    print("\n--- Visuals Imports ---")
    import_submodules("app.visuals")
    print("Visuals done")
