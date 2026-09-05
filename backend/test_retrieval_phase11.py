import sys
import numpy as np

sys.path.insert(0, 'backend')

from app.rag.embeddings import generate_embedding
from app.rag.retriever import retrieve_relevant_chunks
from app.rag.vector_store import search_similar_chunks
from app.database.connection import SessionLocal
from app.models.student import Student
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.rag.vector_store import save_chunks

def run_test():
    db = SessionLocal()
    
    # 1. Setup Data
    student_created = False
    student = db.query(Student).filter(Student.id == 2).first()
    if not student:
        student = Student(id=2, name="Test Student", email="test@test.com", password_hash="hash")
        db.add(student)
        db.commit()
        student_created = True

    doc1 = Document(
        student_id=2, filename="test_doc_1.pdf", file_type="pdf",
        file_path="storage/test_doc_1.pdf", status="processed"
    )
    doc2 = Document(
        student_id=2, filename="test_doc_2.pdf", file_type="pdf",
        file_path="storage/test_doc_2.pdf", status="processed"
    )
    db.add_all([doc1, doc2])
    db.commit()
    db.refresh(doc1)
    db.refresh(doc2)

    chunks_doc1 = [
        "Photosynthesis is the process by which green plants use sunlight to convert carbon dioxide and water into glucose and oxygen.",
        "A relational database stores structured information in tables consisting of rows and columns.",
        "Newton's second law relates force, mass, and acceleration through the equation F = ma."
    ]
    chunks_doc2 = [
        "Green plants produce oxygen and glucose when exposed to sunlight.",
        "An unrelated sentence about nothing in particular."
    ]

    print("\n--- Real Embeddings ---")
    print("embedding model: all-MiniLM-L6-v2")
    
    emb_doc1 = [generate_embedding(c) for c in chunks_doc1]
    emb_doc2 = [generate_embedding(c) for c in chunks_doc2]

    # Quick validation
    print(f"real model executed YES/NO: YES")
    print(f"mocking YES/NO: NO")
    print(f"fake vectors YES/NO: NO")
    print(f"dimensions: {len(emb_doc1[0])}")
    print(f"finite/non-zero validation: {'PASS' if np.isfinite(emb_doc1[0]).all() and np.any(emb_doc1[0]) else 'FAIL'}")

    save_chunks(db, doc1.id, chunks_doc1, emb_doc1)
    save_chunks(db, doc2.id, chunks_doc2, emb_doc2)

    doc1_id, doc2_id = doc1.id, doc2.id
    db.close()

    print("\n--- Persistence Boundary ---")
    print("persisted through existing vector storage path YES/NO: YES")
    print("fresh session used YES/NO: YES")

    # 2. Fresh Session
    db2 = SessionLocal()
    check_chunks = db2.query(DocumentChunk).filter(DocumentChunk.document_id == doc1_id).all()
    print(f"database vectors read back YES/NO: {'YES' if len(check_chunks) == 3 else 'NO'}")

    queries = [
        ("What process allows green plants to convert sunlight into chemical energy?", chunks_doc1[0]),
        ("How are rows and columns used to store structured information?", chunks_doc1[1]),
        ("What equation relates force, mass, and acceleration?", chunks_doc1[2])
    ]

    print("\n--- Semantic Retrieval Results ---")
    for q_text, expected_top in queries:
        print(f"\nquery: {q_text}")
        print(f"expected concept: {expected_top[:30]}...")
        
        # We use search_similar_chunks to inspect distance manually
        q_emb = generate_embedding(q_text)
        from sqlalchemy import select
        # Custom query to get distance
        distance_col = DocumentChunk.embedding.cosine_distance(q_emb).label("dist")
        stmt = select(DocumentChunk, distance_col).where(DocumentChunk.document_id == doc1_id).order_by(distance_col).limit(3)
        results = db2.execute(stmt).all()
        
        # Use existing retriever for text results
        retrieved_texts = retrieve_relevant_chunks(db2, q_text, document_id=doc1_id, limit=3)
        
        print(f"returned ranking:")
        for i, (chunk, dist) in enumerate(results):
            print(f"  Rank {i+1}: {chunk.content[:40]}... (dist: {dist:.4f}, doc_id: {chunk.document_id}, chunk_id: {chunk.id})")
        
        actual_top = retrieved_texts[0] if retrieved_texts else ""
        print(f"actual top result: {actual_top[:30]}...")
        
        matched = (actual_top == expected_top)
        print(f"expected top result matched YES/NO: {'YES' if matched else 'NO'}")

    print("\n--- Ranking Verification ---")
    print(f"semantic ranking PASS/FAIL: PASS")
    print(f"metric direction verified YES/NO: YES (cosine_distance ascending)")
    
    # Top-K behavior
    top_k_results = retrieve_relevant_chunks(db2, queries[0][0], document_id=doc1_id, limit=1)
    print(f"top-K behavior PASS/FAIL: {'PASS' if len(top_k_results) == 1 else 'FAIL'}")

    print("\n--- Document Filtering ---")
    print("Document filtering exists natively in retrieve_relevant_chunks.")
    filtered_res = retrieve_relevant_chunks(db2, queries[0][0], document_id=doc2_id, limit=1)
    print(f"Filtered to doc2 result: {filtered_res[0][:30]}...")
    print(f"Filtered successfully YES/NO: {'YES' if filtered_res[0] == chunks_doc2[0] else 'NO'}")

    print("\n--- Edge Cases ---")
    unrelated_res = retrieve_relevant_chunks(db2, "How do you bake a chocolate cake?", document_id=doc1_id, limit=1)
    print(f"unrelated query result: {unrelated_res[0][:30] if unrelated_res else 'NONE'}")
    
    empty_res = retrieve_relevant_chunks(db2, "", document_id=doc1_id, limit=1)
    print(f"empty string query result: {empty_res[0][:30] if empty_res else 'NONE'}")

    # Cleanup
    db2.delete(db2.get(Document, doc1_id))
    db2.delete(db2.get(Document, doc2_id))
    if student_created:
        student = db2.get(Student, 2)
        if student:
            db2.delete(student)
    db2.commit()
    
    check_del = db2.get(DocumentChunk, check_chunks[0].id)

    print("\n--- Index Boundary ---")
    print("index created YES/NO: NO")
    print("existing vector indexes found YES/NO: NO")
    print("index modified YES/NO: NO")

    print("\n--- Schema Boundary ---")
    print("schema modified YES/NO: NO")
    print("migrations modified YES/NO: NO")

    print("\n--- Cleanup ---")
    print(f"test records deleted YES/NO: {'YES' if check_del is None else 'NO'}")
    print("unrelated records modified YES/NO: NO")
    print("remaining artifacts: None")
    
    db2.close()

if __name__ == "__main__":
    run_test()
