import sys
sys.path.insert(0, 'backend')
from sqlalchemy import text, inspect as sqla_inspect
from sqlalchemy.orm import configure_mappers
from app.database.connection import engine, Base

import app.models.assessment
import app.models.attempt
import app.models.concept
import app.models.document
import app.models.document_chunk
import app.models.lesson
import app.models.session
import app.models.student

configure_mappers()

print("--- DB IDENTITY ---")
with engine.connect() as conn:
    current_db = conn.execute(text("SELECT current_database()")).scalar()
    current_schema = conn.execute(text("SELECT current_schema()")).scalar()
    print(f"DATABASE: {current_db}")
    print(f"SCHEMA: {current_schema}")

print("\n--- TABLE INVENTORY ---")
inspector = sqla_inspect(engine)
db_tables = inspector.get_table_names()
orm_tables = list(Base.metadata.tables.keys())

for t in orm_tables:
    exists = t in db_tables
    print(f"{t} | {exists}")

missing_tables = [t for t in orm_tables if t not in db_tables]
extra_tables = [t for t in db_tables if t not in orm_tables and t != 'alembic_version']

print("\n--- COLUMN COMPARISON ---")
if db_tables:
    for t in orm_tables:
        if t in db_tables:
            db_cols = {c['name']: c for c in inspector.get_columns(t)}
            orm_cols = Base.metadata.tables[t].columns
            for col in orm_cols:
                if col.name in db_cols:
                    db_type = str(db_cols[col.name]['type'])
                    orm_type = str(col.type)
                    nullable = db_cols[col.name]['nullable']
                    print(f"{t} | {col.name} | {orm_type} | {db_type} | {nullable} | match")
                else:
                    print(f"{t} | {col.name} | {str(col.type)} | MISSING | N/A | missing")
else:
    print("NO TABLES IN DATABASE")

print("\n--- PRIMARY KEYS ---")
if db_tables:
    for t in orm_tables:
        if t in db_tables:
            pk = inspector.get_pk_constraint(t)
            print(f"{t} | {pk.get('constrained_columns', [])}")

print("\n--- FOREIGN KEYS ---")
if db_tables:
    for t in orm_tables:
        if t in db_tables:
            fks = inspector.get_foreign_keys(t)
            if fks:
                for fk in fks:
                    print(f"{t} | {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
            else:
                print(f"{t} | None")

print("\n--- INDEXES ---")
if db_tables:
    for t in orm_tables:
        if t in db_tables:
            idxs = inspector.get_indexes(t)
            for idx in idxs:
                print(f"{t} | {idx['name']} | {idx['column_names']}")

print("\n--- CONSTRAINTS ---")
if db_tables:
    for t in orm_tables:
        if t in db_tables:
            uniques = inspector.get_unique_constraints(t)
            for u in uniques:
                print(f"UNIQUE | {t} | {u['name']} | {u['column_names']}")

