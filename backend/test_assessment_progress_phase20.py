import sys
import os
import unittest.mock
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app as fastapi_app
from app.database.connection import SessionLocal
from app.models.student import Student
from app.models.lesson import Lesson
from app.models.session import TeachingSession
from app.models.concept import Concept
from app.models.attempt import Attempt
from app.models.assessment import Assessment

# Tracking hooks to verify zero-generation
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

def patch_counter(target, key, attr_name=None):
    if attr_name is None:
        attr_name = key.split(".")[-1]
    original = getattr(target, attr_name)
    def wrapper(*args, **kwargs):
        call_counts[key] += 1
        return original(*args, **kwargs)
    return wrapper

def reset_counts():
    for k in call_counts:
        call_counts[k] = 0

def run_test():
    client = TestClient(fastapi_app)
    db = SessionLocal()
    
    student_a_id = None
    student_b_id = None
    lesson_a_id = None
    lesson_b_id = None
    session_a_id = None
    session_b_id = None
    assessment_a_id = None
    assessment_b_id = None

    try:
        print("\n--- EDUVA PHASE 20 ASSESSMENT + PROGRESS TEST ---")

        # 1. SETUP CONTROLLED FIXTURES
        print("\n--- Controlled Setup ---")
        student_a = Student(name="Phase20_Test_Student_A")
        student_b = Student(name="Phase20_Test_Student_B")
        db.add(student_a)
        db.add(student_b)
        db.commit()
        
        student_a_id = student_a.id
        student_b_id = student_b.id
        print(f"Student A created: {student_a_id}")
        print(f"Student B created: {student_b_id}")

        lesson_a = Lesson(student_id=student_a_id, title="Lesson A", topic="Physics")
        lesson_b = Lesson(student_id=student_b_id, title="Lesson B", topic="Chemistry")
        db.add(lesson_a)
        db.add(lesson_b)
        db.commit()
        lesson_a_id = lesson_a.id
        lesson_b_id = lesson_b.id
        
        # Session A: Completed (for assessment)
        session_a = TeachingSession(
            student_id=student_a_id, 
            lesson_id=lesson_a_id, 
            status="completed"
        )
        # Session B: Completed
        session_b = TeachingSession(
            student_id=student_b_id, 
            lesson_id=lesson_b_id, 
            status="completed"
        )
        db.add(session_a)
        db.add(session_b)
        db.commit()
        session_a_id = session_a.id
        session_b_id = session_b.id

        # Concepts for A: Test boundary values
        c1 = Concept(lesson_id=lesson_a_id, title="C1", order_index=1, mastery_score=0.0)
        c2 = Concept(lesson_id=lesson_a_id, title="C2", order_index=2, mastery_score=0.5)
        c3 = Concept(lesson_id=lesson_a_id, title="C3", order_index=3, mastery_score=0.8)
        c4 = Concept(lesson_id=lesson_a_id, title="C4", order_index=4, mastery_score=1.0)
        db.add_all([c1, c2, c3, c4])
        db.commit()
        c1_id = c1.id

        # Concept for B
        cb = Concept(lesson_id=lesson_b_id, title="CB", order_index=1, mastery_score=0.9)
        db.add(cb)
        db.commit()

        # Attempts for A to prove historical preservation
        a1 = Attempt(session_id=session_a_id, concept_id=c1_id, question="Q1", student_answer="Bad", is_correct=False)
        a2 = Attempt(session_id=session_a_id, concept_id=c1_id, question="Q2", student_answer="Okay", is_correct=False)
        a3 = Attempt(session_id=session_a_id, concept_id=c1_id, question="Q3", student_answer="Good", is_correct=True)
        db.add_all([a1, a2, a3])
        db.commit()
        
        db.close()
        
        # Zero-Generation Patching
        import app.teacher.engine
        from app.teacher.engine import TeacherEngine
        from app.teacher.teaching import TeachingEngine
        from app.teacher.questioning import QuestioningEngine
        from app.teacher.evaluator import AnswerEvaluator
        from app.teacher.misconception import MisconceptionEngine
        from app.teacher.adaptation import AdaptationEngine
        from app.voice.tts import TTSService

        with unittest.mock.patch("app.teacher.teaching.TeachingEngine.generate", side_effect=patch_counter(TeachingEngine, "TeachingEngine.generate")), \
             unittest.mock.patch("app.teacher.engine.TeacherEngine.next_step", side_effect=patch_counter(TeacherEngine, "TeacherEngine.next_step")), \
             unittest.mock.patch("app.teacher.engine.TeacherEngine.answer", side_effect=patch_counter(TeacherEngine, "TeacherEngine.answer")), \
             unittest.mock.patch("app.teacher.questioning.QuestioningEngine.generate_question", side_effect=patch_counter(QuestioningEngine, "QuestioningEngine.generate_question")), \
             unittest.mock.patch("app.teacher.evaluator.AnswerEvaluator.evaluate", side_effect=patch_counter(AnswerEvaluator, "AnswerEvaluator.evaluate")), \
             unittest.mock.patch("app.teacher.misconception.MisconceptionEngine.process", side_effect=patch_counter(MisconceptionEngine, "MisconceptionEngine.process")), \
             unittest.mock.patch("app.teacher.adaptation.AdaptationEngine.adapt", side_effect=patch_counter(AdaptationEngine, "AdaptationEngine.adapt")), \
             unittest.mock.patch("app.voice.tts.TTSService.generate_speech", side_effect=patch_counter(TTSService, "TTSService.generate_speech")):
            
            # 2. ASSESSMENT CREATION (POST)
            print("\n--- Assessment POST Test ---")
            res_a = client.post(f"/assessments/{session_a_id}")
            assert res_a.status_code == 200, res_a.text
            data_a = res_a.json()
            assessment_a_id = data_a["assessment_id"]
            
            res_b = client.post(f"/assessments/{session_b_id}")
            data_b = res_b.json()
            assessment_b_id = data_b["assessment_id"]

            print(f"Assessment A created: {assessment_a_id}")
            print(f"Assessment A Score (Average of 0.0, 0.5, 0.8, 1.0 = 0.575 -> 57): {data_a['score']}")
            assert data_a['score'] == 57, f"Expected score 57, got {data_a['score']}"
            
            # Boundary Concepts
            # Mastery >= 0.8 is strong. So C3 and C4 are strong. C1 and C2 are weak.
            strong = data_a["strong_areas"].split(", ")
            weak = data_a["weak_areas"].split(", ")
            print(f"Strong areas: {strong}")
            print(f"Weak areas: {weak}")
            assert "C3" in strong and "C4" in strong, "C3 and C4 should be strong (>= 0.8)"
            assert "C1" in weak and "C2" in weak, "C1 and C2 should be weak (< 0.8)"

            # 3. FRESH DB VERIFICATION & ATTEMPT HISTORY
            print("\n--- Fresh Database Verification ---")
            db_fresh = SessionLocal()
            ass_a_db = db_fresh.get(Assessment, assessment_a_id)
            print(f"Fresh DB Score: {ass_a_db.score} (matches API: {ass_a_db.score == data_a['score']})")
            assert ass_a_db.score == data_a['score']
            
            attempts_a = db_fresh.query(Attempt).filter(Attempt.session_id == session_a_id).all()
            print(f"Historical attempts preserved: {len(attempts_a)}")
            assert len(attempts_a) == 3, "All 3 attempts should be preserved"
            
            # 4. PROGRESS API (GET) & ISOLATION
            print("\n--- Progress GET & Isolation ---")
            prog_a_res1 = client.get(f"/students/{student_a_id}/progress")
            assert prog_a_res1.status_code == 200
            prog_a_data1 = prog_a_res1.json()
            
            prog_b_res = client.get(f"/students/{student_b_id}/progress")
            prog_b_data = prog_b_res.json()
            
            print(f"Student A total sessions: {prog_a_data1['total_sessions']}")
            print(f"Student B total sessions: {prog_b_data['total_sessions']}")
            assert prog_a_data1['total_sessions'] == 1
            assert prog_b_data['total_sessions'] == 1
            assert prog_a_data1['assessments'][0]['assessment_id'] == assessment_a_id
            assert prog_b_data['assessments'][0]['assessment_id'] == assessment_b_id
            print("Student A sees only A's data: YES")
            print("Student B sees only B's data: YES")
            
            # 5. IDEMPOTENCE
            print("\n--- Progress Idempotence ---")
            prog_a_res2 = client.get(f"/students/{student_a_id}/progress")
            prog_a_res3 = client.get(f"/students/{student_a_id}/progress")
            print(f"GET #1 average score: {prog_a_data1['average_score']}")
            print(f"GET #2 average score: {prog_a_res2.json()['average_score']}")
            print(f"GET #3 average score: {prog_a_res3.json()['average_score']}")
            assert prog_a_data1 == prog_a_res2.json() == prog_a_res3.json()
            
            # 6. ERROR HANDLING
            print("\n--- Error Handling ---")
            err_res = client.get("/students/999999/progress")
            print(f"Nonexistent student: {err_res.status_code} {err_res.json()}")
            assert err_res.status_code == 404
            
            err_res2 = client.post("/assessments/999999")
            print(f"Nonexistent session for assessment: {err_res2.status_code} {err_res2.json()}")
            assert err_res2.status_code == 404

            # 7. ZERO GENERATION
            print("\n--- Zero Generation Verification ---")
            for k, v in call_counts.items():
                print(f"{k}: {v}")
                assert v == 0, f"{k} should not be called"

    finally:
        print("\n--- Cleanup ---")
        db = SessionLocal()
        
        # Assessments
        if assessment_a_id: db.query(Assessment).filter(Assessment.id == assessment_a_id).delete()
        if assessment_b_id: db.query(Assessment).filter(Assessment.id == assessment_b_id).delete()
        
        # Attempts
        if session_a_id: db.query(Attempt).filter(Attempt.session_id == session_a_id).delete()
        if session_b_id: db.query(Attempt).filter(Attempt.session_id == session_b_id).delete()
        
        # Sessions (and current_concept_id clear)
        if session_a_id:
            sess_a = db.get(TeachingSession, session_a_id)
            if sess_a:
                db.query(TeachingSession).filter(TeachingSession.id == sess_a.id).update({"current_concept_id": None})
                db.commit()
                db.query(Concept).filter(Concept.lesson_id == sess_a.lesson_id).delete()
                db.delete(sess_a)
                db.commit()
        if session_b_id:
            sess_b = db.get(TeachingSession, session_b_id)
            if sess_b:
                db.query(TeachingSession).filter(TeachingSession.id == sess_b.id).update({"current_concept_id": None})
                db.commit()
                db.query(Concept).filter(Concept.lesson_id == sess_b.lesson_id).delete()
                db.delete(sess_b)
                db.commit()
                
        # Lessons
        if lesson_a_id: db.query(Lesson).filter(Lesson.id == lesson_a_id).delete()
        if lesson_b_id: db.query(Lesson).filter(Lesson.id == lesson_b_id).delete()
        
        # Students
        if student_a_id: db.query(Student).filter(Student.id == student_a_id).delete()
        if student_b_id: db.query(Student).filter(Student.id == student_b_id).delete()
        
        db.commit()
        db.close()
        print("Controlled records deleted successfully.")

if __name__ == "__main__":
    run_test()
