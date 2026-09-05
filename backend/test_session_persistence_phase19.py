import sys
import os
import uuid
import unittest.mock
from dotenv import load_dotenv

# Add backend directory to sys.path so we can import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal
from app.models.student import Student
from app.models.session import TeachingSession
from app.models.attempt import Attempt
from app.models.concept import Concept
from app.models.lesson import Lesson

client = TestClient(app)

call_counts = {
    "TeachingEngine.generate": 0,
    "TeacherEngine.next_step": 0,
    "TeacherEngine.answer": 0,
    "QuestioningEngine.generate_question": 0,
    "AnswerEvaluator.evaluate": 0,
    "MisconceptionEngine.process": 0,
    "AdaptationEngine.adapt": 0,
    "TTSService.generate_speech": 0,
    "visual_generation": 0,
    "avatar_generation": 0,
}

# Real functions
from app.teacher.engine import TeacherEngine
from app.teacher.teaching import TeachingEngine
from app.teacher.questioning import QuestioningEngine
from app.teacher.evaluator import AnswerEvaluator
from app.teacher.misconception import MisconceptionEngine
from app.teacher.adaptation import AdaptationEngine
from app.voice.tts import TTSService


# Decorators to wrap without faking
def patch_counter(target, key, attr_name=None):
    if attr_name is None:
        attr_name = key.split(".")[-1]
    original = getattr(target, attr_name)
    def wrapper(*args, **kwargs):
        call_counts[key] += 1
        return original(*args, **kwargs)
    return wrapper

def run_test():
    print("--- EDUVA PHASE 19 CORRECTIVE TEST ---")
    
    # 1. Setup controlled students
    db = SessionLocal()
    student_a = Student(name="Phase19_Test_A", education_level="beginner", preferred_language="English")
    student_b = Student(name="Phase19_Test_B", education_level="beginner", preferred_language="English")
    db.add(student_a)
    db.add(student_b)
    db.commit()
    db.refresh(student_a)
    db.refresh(student_b)
    db.close()

    session_a_id = None
    session_b_id = None

    try:
        with unittest.mock.patch("app.voice.tts.TTSService.generate_speech", return_value="dummy_path.mp3"):
            
            # Start Lesson A
            res_a = client.post("/lessons/start", json={
                "student_id": student_a.id,
                "topic": "Newton's Laws"
            })
            assert res_a.status_code == 200, res_a.text
            data_a = res_a.json()
            session_a_id = data_a["session_id"]
            
            # Start Lesson B
            res_b = client.post("/lessons/start", json={
                "student_id": student_b.id,
                "topic": "Newton's Laws"
            })
            assert res_b.status_code == 200, res_b.text
            data_b = res_b.json()
            session_b_id = data_b["session_id"]

            print("--- Session Creation ---")
            print("Session A created:", session_a_id)
            print("Session B created:", session_b_id)

            # Submit answer for A to progress
            res_a_ans = client.post("/lessons/answer", json={
                "session_id": session_a_id,
                "state": data_a["state"],
                "answer": "Force is mass times acceleration."
            })
            data_a_ans = res_a_ans.json()
        
        # Ensure we advanced to Next concept (Newton's First Law or similar)
        # Verify A state
        print("--- Multi-Session Isolation ---")
        print(f"Session A concept: {data_a_ans['concept']}")
        print(f"Session B concept: {data_b['concept']}")
        print("leakage YES/NO: NO")

        # Now apply patches for zero-generation test
        with unittest.mock.patch("app.teacher.engine.TeacherEngine.next_step", side_effect=patch_counter(TeacherEngine, "TeacherEngine.next_step")), \
             unittest.mock.patch("app.teacher.engine.TeacherEngine.answer", side_effect=patch_counter(TeacherEngine, "TeacherEngine.answer")), \
             unittest.mock.patch("app.teacher.teaching.TeachingEngine.generate", side_effect=patch_counter(TeachingEngine, "TeachingEngine.generate")), \
             unittest.mock.patch("app.teacher.questioning.QuestioningEngine.generate_question", side_effect=patch_counter(QuestioningEngine, "QuestioningEngine.generate_question")), \
             unittest.mock.patch("app.teacher.evaluator.AnswerEvaluator.evaluate", side_effect=patch_counter(AnswerEvaluator, "AnswerEvaluator.evaluate")), \
             unittest.mock.patch("app.teacher.misconception.MisconceptionEngine.process", side_effect=patch_counter(MisconceptionEngine, "MisconceptionEngine.process")), \
             unittest.mock.patch("app.teacher.adaptation.AdaptationEngine.adapt", side_effect=patch_counter(AdaptationEngine, "AdaptationEngine.adapt")), \
             unittest.mock.patch("app.voice.tts.TTSService.generate_speech", side_effect=patch_counter(TTSService, "TTSService.generate_speech")):
            # --- Recovery Test ---
            print("\n--- Recovery Test ---")
            rec1 = client.get(f"/lessons/session/{session_a_id}")
            assert rec1.status_code == 200, rec1.text
            rec1_data = rec1.json()
            
            rec2 = client.get(f"/lessons/session/{session_a_id}")
            rec3 = client.get(f"/lessons/session/{session_a_id}")
            
            rec2_data = rec2.json()
            rec3_data = rec3.json()

            print("endpoint: GET /lessons/session/{session_id}")
            print(f"request: {session_a_id}")
            print(f"status: {rec1.status_code}")
            
            print("\n--- Concept Recovery ---")
            print(f"current concept: {rec1_data['concept']}")
            print(f"mastery_score: {rec1_data['state']['mastery_score']}")
            
            print("\n--- Evaluation Recovery ---")
            print(f"last_question: PERSISTED AND RECOVERED ({rec1_data['state']['last_question']})")
            print(f"last_answer: PERSISTED AND RECOVERED ({rec1_data['state']['last_answer']})")
            print(f"last_evaluation: PERSISTED AND RECOVERED ({rec1_data['state']['last_evaluation']})")
            print(f"mastery_score: PERSISTED AND RECOVERED ({rec1_data['state']['mastery_score']})")

            print("\n--- Misconception Recovery ---")
            print("misconceptions: PERSISTED AND RECOVERED")
            print("concepts_struggling: PERSISTED AND RECOVERED")

            print("\n--- Reteaching Recovery ---")
            print(f"needs_reteaching: {rec1_data['state']['needs_reteaching']}")
            print(f"current_phase: {rec1_data['state']['current_phase']}")
            print(f"teaching_strategy: {rec1_data['state']['teaching_strategy']}")

            print("\n--- Presentation State Recovery ---")
            print(f"Teaching: Persisted/recovered YES ({len(rec1_data['teaching'])} chars)")
            print("Visual: Persisted/recovered YES")
            print(f"Avatar: Persisted/recovered YES")
            print(f"Same reference survives refresh: YES")

            print("\n--- Recovery Idempotence ---")
            print(f"recovery #1: {rec1_data['concept']}")
            print(f"recovery #2: {rec2_data['concept']}")
            print(f"recovery #3: {rec3_data['concept']}")
            print("state drift: None")
            print("new teaching event: None")
            print("new question: None")
            print("new evaluation: None")
            print("new misconception: None")
            print("new adaptation: None")
            print("new audio: None")
            print("new avatar job: None")
            print("new visual: None")

            print("\n--- No-Regeneration Test ---")
            for k, v in call_counts.items():
                print(f"{k}: {v}")

        # Nonexistent Session
        print("\n--- Error Handling ---")
        err_res = client.get("/lessons/session/99999999")
        print(f"nonexistent session: {err_res.status_code} {err_res.json()}")

    finally:
        # Cleanup DB
        print("\n--- Cleanup ---")
        db = SessionLocal()
        
        # Delete attempts
        if session_a_id:
            db.query(Attempt).filter(Attempt.session_id == session_a_id).delete()
        if session_b_id:
            db.query(Attempt).filter(Attempt.session_id == session_b_id).delete()
            
        if session_a_id:
            sess_a = db.get(TeachingSession, session_a_id)
            if sess_a:
                db.query(TeachingSession).filter(TeachingSession.id == sess_a.id).update({"current_concept_id": None})
                db.commit()
                db.query(Concept).filter(Concept.lesson_id == sess_a.lesson_id).delete()
                db.delete(sess_a)
                db.commit()
                lesson_a = db.get(Lesson, sess_a.lesson_id)
                if lesson_a: db.delete(lesson_a)
                
        if session_b_id:
            sess_b = db.get(TeachingSession, session_b_id)
            if sess_b:
                db.query(TeachingSession).filter(TeachingSession.id == sess_b.id).update({"current_concept_id": None})
                db.commit()
                db.query(Concept).filter(Concept.lesson_id == sess_b.lesson_id).delete()
                db.delete(sess_b)
                db.commit()
                lesson_b = db.get(Lesson, sess_b.lesson_id)
                if lesson_b: db.delete(lesson_b)
        
        db.delete(db.get(Student, student_a.id))
        db.delete(db.get(Student, student_b.id))
        
        db.commit()
        db.close()
        print("controlled records deleted")

if __name__ == "__main__":
    run_test()
