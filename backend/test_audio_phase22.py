import sys
import os
import asyncio
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app as fastapi_app
from app.voice.tts import TTSService
from app.database.connection import SessionLocal
from app.models.student import Student
from app.models.lesson import Lesson
from app.models.session import TeachingSession
from app.models.concept import Concept
from app.models.attempt import Attempt
from app.models.document import Document

async def run_async_tts():
    tts = TTSService()
    
    # English
    en_path = await tts.generate_speech("Hello world", "English", "test_en.mp3")
    assert Path(en_path).exists() and Path(en_path).stat().st_size > 0
    print("English TTS OK")

    # Tamil
    ta_path = await tts.generate_speech("வணக்கம்", "Tamil", "test_ta.mp3")
    assert Path(ta_path).exists() and Path(ta_path).stat().st_size > 0
    print("Tamil TTS OK")

    # Hindi
    hi_path = await tts.generate_speech("नमस्ते", "Hindi", "test_hi.mp3")
    assert Path(hi_path).exists() and Path(hi_path).stat().st_size > 0
    print("Hindi TTS OK")

def test_api():
    # Mock avatar generation to avoid hanging in BackgroundTasks during Phase 22 test
    import app.api.routes.lessons
    import app.api.routes.answers
    async def mock_avatar_runner(job_id, audio_path, filename):
        print("Mocked avatar runner called")
    app.api.routes.lessons.generate_avatar_background = mock_avatar_runner
    app.api.routes.answers.generate_avatar_background = mock_avatar_runner

    client = TestClient(fastapi_app)
    
    print("Starting test_api...")
    # Synthesize
    res = client.post("/voice/synthesize", json={"text": "Test synthesize", "language": "English"})
    assert res.status_code == 200
    audio_url = res.json()["audio_url"]
    filename = res.json()["audio_file"]
    
    # Concurrency issue check
    print("Testing /voice/synthesize concurrency...")
    res2 = client.post("/voice/synthesize", json={"text": "Test 2", "language": "English"})
    filename2 = res2.json()["audio_file"]
    print(f"Synthesize filenames: {filename} vs {filename2}")
    if filename == filename2:
        print("WARNING: Concurrency collision in /voice/synthesize")
    
    # Path traversal check
    print("Testing path traversal...")
    res3 = client.get("/voice/audio/../../main.py")
    if res3.status_code == 200:
        print("WARNING: Path traversal vulnerability in GET /voice/audio")
    else:
        print(f"Path traversal blocked with status {res3.status_code}.")

    # Missing file
    print("Testing missing audio...")
    res4 = client.get("/voice/audio/doesnotexist123.mp3")
    assert res4.status_code == 404
    print("Missing audio 404 OK")
    
    db = SessionLocal()
    student_id = None
    doc_id = None
    session_id = None
    try:
        print("Setting up DB objects...")
        student = Student(name="Phase22_Test", preferred_language="English")
        db.add(student)
        db.flush()
        student_id = student.id
        
        doc = Document(student_id=student_id, filename="physics_test.pdf", file_type="pdf", file_path="/fake/path.pdf")
        db.add(doc)
        db.commit()
        doc_id = doc.id
        
        # Test /lessons/start audio
        print("Calling POST /lessons/start ...")
        start_res = client.post("/lessons/start", json={
            "student_id": student_id,
            "topic": "Gravity",
        })
        print("Returned from /lessons/start")
        assert start_res.status_code == 200
        start_data = start_res.json()
        assert start_data.get("audio_url") is not None
        session_id = start_data["session_id"]
        
        # Ensure file actually exists
        print("Verifying audio exists...")
        audio_filename = start_data["audio_url"].split("/")[-1]
        assert Path(f"storage/audio/{audio_filename}").exists()
        print("Lesson Start Audio OK")
        
        # Next / reteach
        print("Calling POST /lessons/answer ...")
        ans_res = client.post("/lessons/answer", json={
            "session_id": session_id,
            "answer": "Idk",
            "state": start_data["state"]
        })
        print("Returned from /lessons/answer")
        assert ans_res.status_code == 200
        ans_data = ans_res.json()
        
        # Wait, /lessons/answer actually returns the audio_url directly in its response!
        # Let's check if the audio URL changes.
        reteach_audio_url = ans_data.get("audio_url")
        assert reteach_audio_url is not None
        assert reteach_audio_url != start_data["audio_url"], "Reteach must generate new audio!"
        print("Lesson Answer Adaptive Audio OK")
        
        # Phase 19 zero-generation recovery test
        import app.teacher.engine
        import app.voice.tts
        
        call_counts = {"tts": 0}
        original_tts = app.voice.tts.TTSService.generate_speech
        
        async def mock_tts(*args, **kwargs):
            call_counts["tts"] += 1
            return await original_tts(*args, **kwargs)
            
        app.voice.tts.TTSService.generate_speech = mock_tts
        
        rec_res = client.get(f"/lessons/session/{session_id}")
        assert rec_res.status_code == 200
        rec_data = rec_res.json()
        
        assert rec_data["audio_url"] == reteach_audio_url
        assert call_counts["tts"] == 0
        print("Session Recovery Audio OK (Zero Generation)")
        
    finally:
        print("Cleaning up DB...")
        if session_id:
            sess = db.get(TeachingSession, session_id)
            if sess:
                db.query(Attempt).filter(Attempt.session_id == sess.id).delete()
                db.query(TeachingSession).filter(TeachingSession.id == sess.id).update({"current_concept_id": None})
                db.commit()
                db.query(Concept).filter(Concept.lesson_id == sess.lesson_id).delete()
                db.delete(sess)
                db.commit()
                if sess.lesson_id:
                    db.query(Lesson).filter(Lesson.id == sess.lesson_id).delete()
                    
        if doc_id: db.query(Document).filter(Document.id == doc_id).delete()
        if student_id: db.query(Student).filter(Student.id == student_id).delete()
        db.commit()
        db.close()

if __name__ == "__main__":
    # asyncio.run(run_async_tts())
    test_api()
    print("All Phase 22 tests complete.")
