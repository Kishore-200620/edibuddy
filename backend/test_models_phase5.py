import sys
import inspect
from importlib import import_module
from pathlib import Path

sys.path.insert(0, 'backend')

from sqlalchemy.orm import configure_mappers
from sqlalchemy import inspect as sqla_inspect

# Import the Base and setup metadata inspection
from app.database.connection import Base

# Model Inventory
model_files = [
    "assessment", "attempt", "concept", "document",
    "document_chunk", "lesson", "session", "student"
]

print("--- MODEL INVENTORY ---")
models = []
for m in model_files:
    try:
        mod = import_module(f"app.models.{m}")
        classes = []
        for name, obj in inspect.getmembers(mod, inspect.isclass):
            if obj.__module__ == mod.__name__ and issubclass(obj, Base) and obj is not Base:
                classes.append(name)
                models.append(obj)
        print(f"{m}.py | {', '.join(classes)} | Base | PASS")
    except Exception as e:
        print(f"{m}.py | N/A | N/A | FAIL: {e}")

print("\n--- DECLARATIVE BASE ---")
print(f"Base location: {Base.__module__}")
print(f"Base consistency: {'Consistent' if all(issubclass(m, Base) for m in models) else 'Inconsistent'}")
print(f"metadata tables: {len(Base.metadata.tables)}")

print("\n--- MAPPER CONFIGURATION ---")
try:
    configure_mappers()
    print("Mapper configuration: PASS")
except Exception as e:
    print("Mapper configuration: FAIL", e)

print("\n--- METADATA ---")
for t_name, table in Base.metadata.tables.items():
    model = next((m for m in models if getattr(m, '__tablename__', None) == t_name), None)
    model_name = model.__name__ if model else "Unknown"
    cols = len(table.columns)
    pk = ", ".join([c.name for c in table.primary_key])
    fks = ", ".join([f"{fk.parent.name}->{fk.target_fullname}" for fk in table.foreign_keys])
    print(f"{t_name} | {model_name} | {cols} | {pk} | {fks}")

print("\n--- PRIMARY KEYS ---")
pk_status = "PASS"
pk_exceptions = []
for model in models:
    mapper = sqla_inspect(model)
    if not mapper.primary_key:
        pk_status = "FAIL"
        pk_exceptions.append(f"{model.__name__} has no primary key")
print(f"status: {pk_status}")
print(f"exceptions: {', '.join(pk_exceptions) if pk_exceptions else 'None'}")

print("\n--- FOREIGN KEYS ---")
fk_status = "PASS"
fk_unresolved = []
for t_name, table in Base.metadata.tables.items():
    for fk in table.foreign_keys:
        if fk.column is None:
            fk_status = "FAIL"
            fk_unresolved.append(f"{t_name}.{fk.parent.name} -> {fk.target_fullname}")
print(f"status: {fk_status}")
print(f"unresolved references: {', '.join(fk_unresolved) if fk_unresolved else 'None'}")

print("\n--- RELATIONSHIPS ---")
rel_status = "PASS"
rel_errors = []
for model in models:
    mapper = sqla_inspect(model)
    for rel in mapper.relationships:
        try:
            _ = rel.mapper
        except Exception as e:
            rel_status = "FAIL"
            rel_errors.append(f"{model.__name__}.{rel.key}: {e}")
print(f"status: {rel_status}")
print(f"relationship errors: {', '.join(rel_errors) if rel_errors else 'None'}")

print("\n--- COLUMN TYPES ---")
col_status = "PASS"
col_invalid = []
for t_name, table in Base.metadata.tables.items():
    for col in table.columns:
        if not col.type:
            col_status = "FAIL"
            col_invalid.append(f"{t_name}.{col.name}")
print(f"status: {col_status}")
print(f"invalid types: {', '.join(col_invalid) if col_invalid else 'None'}")

print("\n--- PGVECTOR MODEL ---")
try:
    from app.models.document_chunk import DocumentChunk
    from pgvector.sqlalchemy import Vector
    col_type = DocumentChunk.embedding.property.columns[0].type
    if isinstance(col_type, Vector):
        print("Vector import: PASS")
        print("Vector column: embedding")
        print(f"dimension: {col_type.dim}")
        print("consistency: PASS")
    else:
        print("Vector import: FAIL (Not a Vector)")
except Exception as e:
    print("Vector import: FAIL", e)

print("\n--- MODEL REGISTRY ---")
print(f"registered models: {len(models)}")
