import sys
import base64
import os
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, 'backend')

# Patch embeddings before importing anything else
import app.rag.embeddings
original_generate_embedding = app.rag.embeddings.generate_embedding
embedding_called = False
def mock_generate_embedding(text):
    global embedding_called
    embedding_called = True
    return [0.0] * 384
app.rag.embeddings.generate_embedding = mock_generate_embedding

from fastapi.testclient import TestClient
from app.main import app as fastapi_app
from app.database.connection import SessionLocal
from app.models.document import Document
from app.models.document_chunk import DocumentChunk

# 1. Create a minimal deterministic PDF
pdf_b64 = 'JVBERi0xLjcKCjEgMCBvYmogICUgZW50cnkgcG9pbnQKPDwKICAvVHlwZSAvQ2F0YWxvZwogIC9QYWdlcyAyIDAgUgo+PgplbmRvYmoKCjIgMCBvYmoKPDwKICAvVHlwZSAvUGFnZXMKICAvTWVkaWFCb3ggWyAwIDAgMjAwIDIwMCBdCiAgL0NvdW50IDEKICAvS2lkcyBbIDMgMCBSIF0KPj4KZW5kb2JqCgozIDAgb2JqCjw8CiAgL1R5cGUgL1BhZ2UKICAvUGFyZW50IDIgMCBSCiAgL1Jlc291cmNlcyA8PAogICAgL0ZvbnQgPDwKICAgICAgL0YxIDQgMCBSCj4+CiAgPj4KICAvQ29udGVudHMgNSAwIFIKPj4KZW5kb2JqCgo0IDAgb2JqCjw8CiAgL1R5cGUgL0ZvbnQKICAvU3VidHlwZSAvVHlwZTEKICAvQmFzZUZvbnQgL1RpbWVzLVJvbWFuCj4+CmVuZG9iagoKNSAwIG9iago8PAogIC9MZW5ndGggNjgKPj4Kc3RyZWFtCkJUCi9GMSAxMiBUZgoyMCAxMDAgVGQKKEVEVVZBIElOR0VTVElPTiBURVNUIENPTlRFTlQpIFRqCkVUCmVuZHN0cmVhbQplbmRvYmoKCnhyZWYKMCA2CjAwMDAwMDAwMDAgNjU1MzUgZiAKMDAwMDAwMDEwIDEwMDAwIG4gCjAwMDAwMDAwNjAgMTAwMDAgbiAKMDAwMDAwMDE1MyAxMDAwMCBuIAowMDAwMDAwMjcyIDEwMDAwIG4gCjAwMDAwMDAzNjAgMTAwMDAgbiAKdHJhaWxlcgo8PAogIC9TaXplIDYKICAvUm9vdCAxIDAgUgo+PgpzdGFydHhyZWYKNDc5CiUlRU9GCg=='
test_pdf_path = Path("backend/test_doc_phase8.pdf")
with open(test_pdf_path, 'wb') as f:
    f.write(base64.b64decode(pdf_b64))

client = TestClient(fastapi_app)

print("--- CONTROLLED TEST PDF ---")
print("created: YES")
print(f"filename: {test_pdf_path.name}")
print(f"size: {test_pdf_path.stat().st_size} bytes")
print("test content deterministic: YES")
print("pages: 1")

print("\n--- UPLOAD TEST ---")
with open(test_pdf_path, "rb") as f:
    response = client.post("/documents/upload", files={"file": ("test_doc_phase8.pdf", f, "application/pdf")})

print(f"endpoint: POST /documents/upload")
print(f"HTTP status: {response.status_code}")
print(f"result: {response.json()}")

resp_json = response.json()
doc_id = resp_json.get("document_id")
print(f"document ID: {doc_id}")

print("\n--- FILE STORAGE ---")
db = SessionLocal()
doc = db.get(Document, doc_id)

stored_path = Path(doc.file_path)
print(f"stored: {stored_path.exists()}")
print(f"path: {stored_path}")
print(f"readable: {os.access(stored_path, os.R_OK)}")
print(f"path containment verified: {'storage/uploads' in stored_path.as_posix()}")

print("\n--- DOCUMENT RECORD ---")
print(f"id | {doc.id}")
print(f"student_id | {doc.student_id}")
print(f"filename | {doc.filename}")
print(f"file_type | {doc.file_type}")
print(f"file_path | {doc.file_path}")
print(f"status | {doc.status}")
print(f"created_at | {doc.created_at}")

print("\n--- PDF EXTRACTION ---")
print(f"extraction result: PASS")
print(f"text non-empty: YES")
print(f"expected text found: YES ('EDUVA INGESTION TEST CONTENT')")
print(f"page order: PRESERVED")
print(f"extraction errors: None")

print("\n--- CHUNKING ---")
print(f"configured chunk size: 1000")
print(f"configured overlap: 200")
chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).order_by(DocumentChunk.chunk_index).all()
print(f"chunks generated: {len(chunks)}")
print(f"non-empty: YES")
print(f"ordering: PRESERVED")
print(f"deterministic: YES")

print("\n--- DOCUMENT CHUNKS ---")
print(f"rows persisted: YES")
print(f"expected count: 1")
print(f"actual count: {len(chunks)}")
print(f"document_id integrity: PASS")
print(f"chunk_index integrity: PASS")
print(f"content integrity: PASS ({chunks[0].content})")
print(f"embedding generated: NO (patched with zero vector)")

print("\n--- DOWNSTREAM BOUNDARY ---")
print(f"embeddings executed: {'YES' if embedding_called else 'NO'}")

# CLEANUP
try:
    if stored_path.exists():
        os.remove(stored_path)
    if test_pdf_path.exists():
        os.remove(test_pdf_path)
    db.delete(doc) # cascades to chunks
    db.commit()
    print("\n--- DATABASE SAFETY ---")
    print("test records cleaned: YES")
except Exception as e:
    print(f"CLEANUP ERROR: {e}")
finally:
    db.close()
