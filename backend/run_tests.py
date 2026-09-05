import sys
sys.path.insert(0, 'backend')

from tests import test_chunker
from tests import test_embeddings
from tests import test_loaders
from tests import test_retrieval

def run_tests():
    print("--- Chunker Test ---")
    try:
        test_chunker.test_chunk_text()
        print("RESULT: PASS")
    except Exception as e:
        print(f"RESULT: FAIL ({e})")

    print("\n--- Embeddings Test ---")
    try:
        if hasattr(test_embeddings, 'test_embedding_generation'):
            test_embeddings.test_embedding_generation()
            print("RESULT: PASS")
    except Exception as e:
        print(f"RESULT: FAIL ({e})")

    print("\n--- Loaders Test ---")
    try:
        if hasattr(test_loaders, 'test_pdf_loader'):
            test_loaders.test_pdf_loader()
            print("RESULT: PASS")
    except Exception as e:
        print(f"RESULT: FAIL ({e})")
        
    print("\n--- Retrieval Test ---")
    print("RESULT: SKIPPED (external dependencies or requires setup)")

if __name__ == "__main__":
    run_tests()
