import asyncio
from pathlib import Path
import os
import shutil

from fastapi.testclient import TestClient

from app.main import app as fastapi_app
from app.database.connection import engine, Base, SessionLocal
from app.models.student import Student
from app.models.lesson import Lesson
from app.models.session import TeachingSession
from app.models.concept import Concept
from app.models.document import Document

# 1. Inspect AvatarService abstraction and provider setup
def test_forensic_inspection():
    print("--- Forensic Inspection ---")
    from app.avatar.service import AvatarService
    service = AvatarService()
    print(f"Provider: {service.provider.__class__.__name__}")
    print(f"Configured: {service.configured}")
    assert service.configured, "Avatar service is not configured! SIMLI_API_KEY required."
    print("Forensic inspection passed.")

# 2. Mocked Simli Session Creation
async def test_mock_simli_session():
    print("\n--- Mocked Simli WebRTC Session Creation ---")
    from app.avatar.service import AvatarService
    import httpx
    
    service = AvatarService()
    
    # Mock httpx
    class MockResponse:
        def __init__(self, json_data):
            self._json_data = json_data
        def raise_for_status(self): pass
        def json(self): return self._json_data

    class MockAsyncClient:
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc, tb): pass
        def __init__(self, *args, **kwargs): pass
        async def post(self, url, json, headers):
            return MockResponse({"session_token": "mocked_session_token"})
        async def get(self, url, headers):
            return MockResponse([{"urls": ["stun:mocked.stun"]}])

    original_client = httpx.AsyncClient
    httpx.AsyncClient = MockAsyncClient
    
    try:
        session_data = await service.create_session()
        assert session_data["session_token"] == "mocked_session_token"
        assert len(session_data["ice_servers"]) == 1
        print("Mocked session creation passed.")
    finally:
        httpx.AsyncClient = original_client

# 3. Avatar API and Lesson Integration
def test_api():
    print("\n--- Avatar API & Lesson Integration ---")
    Base.metadata.create_all(bind=engine)
    client = TestClient(fastapi_app)
    
    db = SessionLocal()
    
    # 3a. Test /avatar/session endpoint (mocked)
    print("Testing /avatar/session endpoint...")
    import app.avatar.service
    
    async def mock_create_session(*args, **kwargs):
        return {"session_token": "api_mocked_token", "ice_servers": []}
    
    original_create_session = app.avatar.service.AvatarService.create_session
    app.avatar.service.AvatarService.create_session = mock_create_session
    
    res_session = client.post("/avatar/session")
    assert res_session.status_code == 200
    assert res_session.json()["session_token"] == "api_mocked_token"
    
    # Restore mock
    app.avatar.service.AvatarService.create_session = original_create_session
    print("Session endpoint OK.")

    # 3b. Test Lesson Start (Live Mode)
    print("\nTesting /lessons/start (Live Mode)...")
    student = Student(name="Avatar_Student", preferred_language="English")
    db.add(student)
    db.flush()
    student_id = student.id
    doc = Document(student_id=student_id, filename="avatar_test.pdf", file_type="pdf", file_path="/fake/a.pdf")
    db.add(doc)
    db.commit()

    res_start = client.post("/lessons/start", json={
        "student_id": student_id,
        "topic": "Gravity"
    })
    assert res_start.status_code == 200, res_start.text
    data = res_start.json()
    session_id = data["session_id"]
    
    # Assert background jobs are GONE, but audio_url remains
    assert "avatar_job_id" not in data or data.get("avatar_job_id") is None
    assert "audio_url" in data
    assert data["audio_url"] is not None
    print("Lesson Start integration OK (no background jobs).")

    # 3c. Test Lesson Answer (Adaptive/Reteach)
    print("\nTesting /lessons/answer (Reteach)...")
    res_ans1 = client.post("/lessons/answer", json={
        "session_id": session_id,
        "answer": "Idk",
        "state": data["state"]
    })
    assert res_ans1.status_code == 200
    ans1_data = res_ans1.json()
    assert ans1_data["action"] == "reteach"
    assert "avatar_job_id" not in ans1_data or ans1_data.get("avatar_job_id") is None
    assert "audio_url" in ans1_data
    print("Lesson Answer (Reteach) integration OK.")

    # 3d. Test Lesson Answer (Mastery/Next Concept)
    print("\nTesting /lessons/answer (Next Concept)...")
    res_ans2 = client.post("/lessons/answer", json={
        "session_id": session_id,
        "answer": "Gravity is the force of attraction between masses.",
        "state": ans1_data["state"]
    })
    assert res_ans2.status_code == 200
    ans2_data = res_ans2.json()
    assert ans2_data["action"] == "completed"
    assert "avatar_job_id" not in ans2_data or ans2_data.get("avatar_job_id") is None
    print("Lesson Answer (Completed) integration OK.")

    # 3f. Test Session Persistence & Recovery (Zero Generation)
    print("\nTesting /lessons/session/{session_id} (Session Recovery)...")
    res_rec = client.get(f"/lessons/session/{session_id}")
    assert res_rec.status_code == 200
    rec_data = res_rec.json()
    assert "avatar_job_id" not in rec_data or rec_data.get("avatar_job_id") is None
    print("Session recovery zero generation OK.")

    # Cleanup DB
    try:
        from app.models.attempt import Attempt
        db.query(Attempt).filter(
            Attempt.session_id.in_(
                db.query(TeachingSession.id).filter(TeachingSession.student_id == student_id)
            )
        ).delete(synchronize_session=False)
    except Exception:
        pass
        
    db.query(TeachingSession).filter(TeachingSession.student_id == student_id).delete(synchronize_session=False)
    db.query(Concept).filter(Concept.lesson_id.in_(db.query(Lesson.id).filter(Lesson.student_id == student_id))).delete(synchronize_session=False)
    db.query(Lesson).filter(Lesson.student_id == student_id).delete(synchronize_session=False)
    db.query(Document).filter(Document.student_id == student_id).delete(synchronize_session=False)
    db.query(Student).filter(Student.id == student_id).delete(synchronize_session=False)
    db.commit()
    db.close()
    print("Cleanup complete.")

if __name__ == "__main__":
    test_forensic_inspection()
    asyncio.run(test_mock_simli_session())
    test_api()
    print("\nALL PHASE 23 TESTS COMPLETED SUCCESSFULLY.")
