import sys
sys.path.insert(0, 'backend')
from sqlalchemy import text
from app.database.connection import engine
import pgvector
from pgvector.sqlalchemy import Vector

print("PGVECTOR_INSTALLED: True")
print("PGVECTOR_VERSION:", getattr(pgvector, '__version__', 'unknown'))

try:
    v = Vector(384)
    print("SQLALCHEMY_VECTOR_INIT: True (dim 384)")
except Exception as e:
    print("SQLALCHEMY_VECTOR_INIT: False", e)

try:
    with engine.connect() as conn:
        ext_res = conn.execute(text("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector'")).fetchone()
        if ext_res:
            print(f"EXTENSION_PRESENT: True (version {ext_res[1]})")
        else:
            print("EXTENSION_PRESENT: False")
            
        type_res = conn.execute(text("SELECT typname FROM pg_type WHERE typname = 'vector'")).fetchone()
        print("VECTOR_TYPE_EXISTS:", bool(type_res))

        literal_res = conn.execute(text("SELECT '[1,2,3]'::vector")).scalar()
        print("VECTOR_LITERAL_SUCCESS:", bool(literal_res is not None))
        
        dims_res = conn.execute(text("SELECT vector_dims('[1,2,3]'::vector)")).scalar()
        print("VECTOR_DIMS_SUCCESS: True (dims =", dims_res, ")")
        
        dist_res = conn.execute(text("SELECT '[1,2,3]'::vector <-> '[1,2,4]'::vector")).scalar()
        print("VECTOR_DISTANCE_SUCCESS: True (dist =", dist_res, ")")

except Exception as e:
    print("DB_VECTOR_ERROR:", e)
