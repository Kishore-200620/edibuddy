import sys
import os
from pathlib import Path
from fastapi.testclient import TestClient
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app as fastapi_app
from app.database.connection import SessionLocal
from app.models.student import Student
from app.models.lesson import Lesson
from app.models.session import TeachingSession
from app.models.concept import Concept
from app.models.attempt import Attempt
from app.models.document import Document

def run_tests():
    # Mock background avatar generation (Phase 23) just in case, though it's removed
    try:
        import app.api.routes.lessons
        import app.api.routes.answers
        async def mock_avatar_runner(job_id, audio_path, filename): pass
        app.api.routes.lessons.generate_avatar_background = mock_avatar_runner
        app.api.routes.answers.generate_avatar_background = mock_avatar_runner
    except AttributeError:
        pass # Expected, since we removed it in Phase 23!

    client = TestClient(fastapi_app)
    db = SessionLocal()
    
    student_id = None
    student2_id = None
    doc_id = None
    session_id = None
    session2_id = None
    
    try:
        print("--- SETUP ---")
        student = Student(name="Phase24_Test_A", preferred_language="English")
        student2 = Student(name="Phase24_Test_B", preferred_language="English")
        db.add_all([student, student2])
        db.flush()
        student_id = student.id
        student2_id = student2.id
        
        doc = Document(student_id=student_id, filename="newton_test.pdf", file_type="pdf", file_path="/fake/path.pdf")
        db.add(doc)
        db.commit()
        doc_id = doc.id
        
        print("--- STEP 4: REAL HTTP START-LESSON TEST ---")
        start_res = client.post("/lessons/start", json={
            "student_id": student_id,
            "topic": "Newton's Laws",
        })
        assert start_res.status_code == 200, f"Failed to start lesson: {start_res.text}"
        state_data = start_res.json()
        session_id = state_data["session_id"]
        
        print("START TEACHING EVENT CONTRACT:")
        print(json.dumps(state_data, indent=2))
        
        # Verify required fields
        assert "teaching" in state_data
        assert "question" in state_data
        assert "concept" in state_data
        assert "state" in state_data
        assert "audio_url" in state_data
        assert "visual" in state_data
        
        current_concept = state_data["concept"]
        print(f"Current concept: {current_concept}")
        
        print("--- STEP 6A: PATH A (STRUGGLING STUDENT) ---")
        ans_incorrect_res = client.post("/lessons/answer", json={
            "session_id": session_id,
            "answer": "It is when gravity pulls things down.",
            "state": state_data["state"]
        })
        assert ans_incorrect_res.status_code == 200, f"Failed: {ans_incorrect_res.text}"
        state_data_reteach = ans_incorrect_res.json()
        
        assert state_data_reteach["concept"] == current_concept, "Should not advance on incorrect answer"
        assert state_data_reteach["state"]["needs_reteaching"] == True, "needs_reteaching should be True"
        print(f"Evaluation (Incorrect): Mastery = {state_data_reteach['state']['mastery_score']}")
        print(f"Strategy: {state_data_reteach['state']['teaching_strategy']}")
        
        print("--- STEP 6B: PATH B (MASTERED STUDENT) ---")
        # Give a perfect answer to force progression
        ans_correct_res = client.post("/lessons/answer", json={
            "session_id": session_id,
            "answer": "A force is a push or a pull acting upon an object as a result of its interaction with another object. It is measured in Newtons and causes objects to accelerate, stop, or change direction.",
            "state": state_data_reteach["state"]
        })
        assert ans_correct_res.status_code == 200, f"Failed: {ans_correct_res.text}"
        state_data_next = ans_correct_res.json()
        
        new_concept = state_data_next["concept"]
        print(f"Evaluation (Correct): Mastery = {state_data_next['state']['mastery_score']}")
        print(f"New concept: {new_concept}")
        assert new_concept != current_concept, "Should advance to next concept on correct answer"
        assert state_data_next["state"]["needs_reteaching"] == False, "needs_reteaching should be reset"
        assert current_concept in state_data_next["state"]["concepts_completed"], f"{current_concept} must be completed"
        
        print("--- STEP 7: MULTI-CONCEPT CONTINUITY ---")
        # Give a perfect answer to the new concept (Newton's First Law)
        ans_correct_res2 = client.post("/lessons/answer", json={
            "session_id": session_id,
            "answer": "An object at rest stays at rest and an object in motion stays in motion with the same speed and in the same direction unless acted upon by an unbalanced force. This is inertia.",
            "state": state_data_next["state"]
        })
        assert ans_correct_res2.status_code == 200
        state_data_third = ans_correct_res2.json()
        
        third_concept = state_data_third["concept"]
        print(f"Third concept: {third_concept}")
        assert third_concept != new_concept
        assert third_concept != current_concept
        assert new_concept in state_data_third["state"]["concepts_completed"]
        
        print("--- STEP 11 & 14: RECOVERY REGRESSION & REPEATABILITY ---")
        # Track generation calls
        import app.teacher.engine
        import app.voice.tts
        import app.visuals.router
        
        call_counts = {"tts": 0, "generate": 0, "visual": 0}
        
        original_tts = app.voice.tts.TTSService.generate_speech
        original_gen = app.teacher.engine.TeachingEngine.generate
        original_vis = app.visuals.router.VisualRouter.generate
        
        async def mock_tts(*args, **kwargs):
            call_counts["tts"] += 1
            return await original_tts(*args, **kwargs)
        def mock_gen(*args, **kwargs):
            call_counts["generate"] += 1
            return original_gen(*args, **kwargs)
        def mock_vis(*args, **kwargs):
            call_counts["visual"] += 1
            return original_vis(*args, **kwargs)
            
        app.voice.tts.TTSService.generate_speech = mock_tts
        app.teacher.engine.TeachingEngine.generate = mock_gen
        app.visuals.router.VisualRouter.generate = mock_vis
        
        # Call GET /lessons/session/{session_id} twice to verify repeatability
        rec_res1 = client.get(f"/lessons/session/{session_id}")
        rec_res2 = client.get(f"/lessons/session/{session_id}")
        
        assert rec_res1.status_code == 200
        assert rec_res2.status_code == 200
        
        rec_data = rec_res1.json()
        assert rec_data["concept"] == third_concept
        assert rec_data["state"]["concepts_completed"] == state_data_third["state"]["concepts_completed"]
        assert rec_data["audio_url"] == state_data_third["audio_url"]
        
        print(f"Generation counts during recovery: {call_counts}")
        assert call_counts["tts"] == 0, "TTS was generated during recovery!"
        assert call_counts["generate"] == 0, "Teaching was generated during recovery!"
        assert call_counts["visual"] == 0, "Visuals were generated during recovery!"
        
        print("--- STEP 12: DATABASE VERIFICATION ---")
        db_sess = db.get(TeachingSession, session_id)
        assert db_sess is not None
        assert db_sess.student_id == student_id
        db_state = db_sess.state_data
        assert db_state["mastery_score"] == rec_data["state"]["mastery_score"]
        concept_obj = db.get(Concept, db_sess.current_concept_id)
        assert concept_obj.title == third_concept
        print("DB State strictly matches HTTP State")
        
        print("--- STEP 13: SESSION ISOLATION ---")
        start_res2 = client.post("/lessons/start", json={
            "student_id": student2_id,
            "topic": "Newton's Laws",
        })
        assert start_res2.status_code == 200
        session2_id = start_res2.json()["session_id"]
        
        sess2_data = start_res2.json()
        assert sess2_data["concept"] == current_concept, "Session B must start at the beginning!"
        assert sess2_data["state"]["concepts_completed"] == []
        assert sess2_data["state"]["mastery_score"] == 0.0
        
        db_sess2 = db.get(TeachingSession, session2_id)
        assert db_sess2.state_data["concepts_completed"] == []
        
        print("Session B is perfectly isolated from Session A")
        
        print("--- STEP 10: AVATAR INTEGRATION ---")
        avatar_res = client.post("/avatar/session")
        assert avatar_res.status_code == 200
        avatar_data = avatar_res.json()
        assert "session_token" in avatar_data
        assert "ice_servers" in avatar_data
        print("Avatar integration contract passes")
        
        print("ALL TESTS PASSED: PHASE 24 END-TO-END COMPLETION")

    finally:
        print("--- STEP 16: CLEANUP ---")
        try:
            for s_id in [session_id, session2_id]:
                if not s_id: continue
                sess = db.get(TeachingSession, s_id)
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
            
            for st_id in [student_id, student2_id]:
                if st_id:
                    lessons = db.query(Lesson).filter(Lesson.student_id == st_id).all()
                    for l in lessons:
                        db.query(Concept).filter(Concept.lesson_id == l.id).delete()
                    db.query(Lesson).filter(Lesson.student_id == st_id).delete()
                    db.query(Student).filter(Student.id == st_id).delete()
            db.commit()
        except Exception as e:
            print(f"Cleanup error: {e}")
        finally:
            db.close()

if __name__ == "__main__":
    run_tests()
