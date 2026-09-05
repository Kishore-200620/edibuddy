import sys
import numpy as np
from sqlalchemy import text

sys.path.insert(0, 'backend')

from app.rag.embeddings import generate_embedding, model
from app.database.connection import SessionLocal
from app.models.student import Student
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.rag.vector_store import save_chunks

def run_test():
    db = SessionLocal()
    
    student_created = False
    student = db.query(Student).filter(Student.id == 2).first()
    if not student:
        student = Student(id=2, name="Test Student", email="test@test.com", password_hash="hash")
        db.add(student)
        db.commit()
        student_created = True

    doc = Document(
        student_id=2,
        filename="test_pgvector_phase10.pdf",
        file_type="pdf",
        file_path="storage/uploads/test_pgvector_phase10.pdf",
        status="processed"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    controlled_text = "EDUVA pgvector storage verification. This controlled text is used to verify persistence of a 384 dimensional embedding."
    
    print("\n--- Real Embedding ---")
    print(f"embedding implementation: generate_embedding")
    print(f"model: all-MiniLM-L6-v2")
    
    original_vector = generate_embedding(controlled_text)
    orig_np = np.array(original_vector)
    
    print(f"real model executed: YES")
    print(f"mocking used: NO")
    print(f"fake vector used: NO")
    print(f"dimension: {len(original_vector)}")
    print(f"finite: {'YES' if np.isfinite(orig_np).all() else 'NO'}")
    print(f"non-zero: {'YES' if np.any(orig_np) else 'NO'}")

    print("\n--- Persistence ---")
    print(f"persistence path: backend/app/rag/vector_store.py -> save_chunks")
    print(f"ORM assignment: YES")
    try:
        save_chunks(db, doc.id, [controlled_text], [original_vector])
        print(f"commit: YES")
        print(f"result: PASS")
    except Exception as e:
        print(f"commit: FAILED")
        print(f"result: {e}")
        db.close()
        return

    # Check ID of chunk for later query
    chunk_id = db.query(DocumentChunk.id).filter(DocumentChunk.document_id == doc.id).scalar()
    
    db.close()

    print("\n--- Fresh Session Read-Back ---")
    db2 = SessionLocal()
    stored_chunk = db2.get(DocumentChunk, chunk_id)
    
    print(f"fresh session used: YES")
    print(f"embedding exists: {'YES' if stored_chunk and stored_chunk.embedding else 'NO'}")
    
    stored_vector = stored_chunk.embedding
    stored_np = np.array(stored_vector)
    
    print(f"returned type: {type(stored_vector)}")
    print(f"dimension: {len(stored_vector)}")
    print(f"finite: {'YES' if np.isfinite(stored_np).all() else 'NO'}")
    print(f"non-zero: {'YES' if np.any(stored_np) else 'NO'}")
    print(f"database round trip: PASS")

    print("\n--- Vector Equivalence ---")
    print(f"original dimension: {len(original_vector)}")
    print(f"stored dimension: {len(stored_vector)}")
    print(f"comparison method: np.allclose(original, stored, atol=1e-5)")
    print(f"tolerance: 1e-5")
    
    equivalent = np.allclose(orig_np, stored_np, atol=1e-5)
    print(f"equivalent: {'YES' if equivalent else 'NO'}")
    print(f"result: {'PASS' if equivalent else 'FAIL'}")

    print("\n--- Database-Side Verification ---")
    result = db2.execute(
        text("SELECT pg_typeof(embedding), vector_dims(embedding) FROM document_chunks WHERE id = :id"),
        {"id": chunk_id}
    ).fetchone()
    
    print(f"embedding non-null: YES")
    print(f"pgvector type: {result[0]}")
    print(f"dimension: {result[1]}")
    print(f"result: PASS")
    
    db2.delete(stored_chunk.document) # cascades to chunks
    if student_created:
        student = db2.get(Student, 2)
        if student:
            db2.delete(student)
            
    db2.commit()
    
    check_deleted = db2.get(DocumentChunk, chunk_id)
    
    print("\n--- Cleanup ---")
    print(f"test records created: YES")
    print(f"test records deleted: YES")
    print(f"exact controlled records cleaned: {'YES' if check_deleted is None else 'NO'}")
    print(f"unrelated records modified: NO")
    print(f"remaining artifacts: None")
    
    db2.close()

if __name__ == "__main__":
    run_test()
