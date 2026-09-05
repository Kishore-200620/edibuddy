import sys
sys.path.insert(0, 'backend')
from sqlalchemy import text
from app.database.connection import engine, SessionLocal
from app.core.config import settings

print("DATABASE_URL_SCHEME:", settings.database_url.split(":")[0] if settings.database_url else "MISSING")
print("DRIVER_CHECK:", "psycopg" in settings.database_url)

# Attempt 1
try:
    with engine.connect() as conn:
        res = conn.execute(text("SELECT 1")).scalar()
        print("ATTEMPT_1:", res)
        version = conn.execute(text("SELECT version()")).scalar()
        print("PG_VERSION:", version.split(",")[0] if version else version)
        current_db = conn.execute(text("SELECT current_database()")).scalar()
        print("CURRENT_DB:", current_db)
        current_user = conn.execute(text("SELECT current_user")).scalar()
        print("CURRENT_USER:", current_user)
except Exception as e:
    print("ATTEMPT_1_ERROR:", type(e).__name__, e)

# Attempt 2
try:
    with engine.connect() as conn:
        res = conn.execute(text("SELECT 1")).scalar()
        print("ATTEMPT_2:", res)
except Exception as e:
    print("ATTEMPT_2_ERROR:", type(e).__name__, e)

# Attempt 3
try:
    with engine.connect() as conn:
        res = conn.execute(text("SELECT 1")).scalar()
        print("ATTEMPT_3:", res)
except Exception as e:
    print("ATTEMPT_3_ERROR:", type(e).__name__, e)

# Session Test
try:
    db = SessionLocal()
    res = db.execute(text("SELECT 1")).scalar()
    print("SESSION_TEST:", res)
except Exception as e:
    print("SESSION_TEST_ERROR:", type(e).__name__, e)
finally:
    db.close()
    print("SESSION_CLOSED: True")
