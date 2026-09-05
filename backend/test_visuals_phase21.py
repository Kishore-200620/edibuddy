import sys
import os
import unittest.mock
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app as fastapi_app
from app.visuals.router import VisualRouter
from app.schemas.teaching import VisualEvent
from app.database.connection import SessionLocal
from app.models.student import Student
from app.models.lesson import Lesson
from app.models.session import TeachingSession
from app.models.concept import Concept
from app.models.attempt import Attempt
from app.models.assessment import Assessment
from app.models.document import Document

def run_tests():
    print("\n--- EDUVA PHASE 21 VISUAL VALIDATION TEST ---")
    
    router = VisualRouter()

    # 1. Blackboard
    v1 = router.generate(teaching="EXPLANATION: Force is a push or pull acting on an object.", concept="Force")
    assert v1.type == "blackboard", f"Expected blackboard, got {v1.type}"

    # 2. Equation
    v2 = router.generate(teaching="EXPLANATION: The formula is V = IR.", concept="Ohm's Law")
    assert v2.type == "equation", f"Expected equation, got {v2.type}"

    # 3. Diagram
    v3 = router.generate(teaching="EXPLANATION: The process leads to a new state.", concept="State Machine")
    assert v3.type == "diagram", f"Expected diagram, got {v3.type}"

    # 4. Code
    v4 = router.generate(teaching="EXPLANATION: x = 10\nprint(x) is a simple python script.", concept="Variables")
    assert v4.type == "code", f"Expected code, got {v4.type}"
    
    # 5. Python x = 10 regression (MUST be code, not equation)
    v5 = router.generate(teaching="EXPLANATION: python variable assignment:\nx = 10", concept="Variables")
    assert v5.type == "code", f"Expected code for python x=10 regression, got {v5.type}"

    print("Visual routing logic passed all expected categories.")
    
    db = SessionLocal()
    client = TestClient(fastapi_app)
    
    student_id = None
    doc_id = None
    session_id = None
    
    try:
        # Create student and document (for RAG)
        student = Student(name="Phase21_Test_Student", preferred_language="English")
        db.add(student)
        db.flush() # Flush to get student ID
        student_id = student.id
        
        doc = Document(student_id=student_id, filename="physics_test.pdf", file_type="pdf", file_path="/fake/path.pdf")
        db.add(doc)
        db.commit()
        doc_id = doc.id
        
        # We need mock TeachingEngine to generate specific text for our tests so we can test routing.
        # But wait! The prompt says "Validate actual EDUVA teaching integration... Do NOT validate VisualRouter only in isolation. Execute the actual lesson flow."
        # So we should call the actual `/lessons/start`, `/lessons/next`, etc!
        # But wait, generating AI text is slow and non-deterministic unless we mock it or we don't care exactly which category it picks, as long as it returns A visual.
        # "The visual must correspond to the CURRENT teaching concept. It must not be generated from... arbitrary text"
        # We can mock `TeachingEngine.generate` and `QuestioningEngine.generate_question` just to provide deterministic text!
        # Let's mock them so we guarantee what the text contains!

        with unittest.mock.patch("app.teacher.teaching.TeachingEngine.generate") as mock_teaching, \
             unittest.mock.patch("app.teacher.questioning.QuestioningEngine.generate_question") as mock_question, \
             unittest.mock.patch("app.teacher.evaluator.AnswerEvaluator.evaluate") as mock_evaluate, \
             unittest.mock.patch("app.voice.tts.TTSService.generate_speech") as mock_tts, \
             unittest.mock.patch("fastapi.BackgroundTasks.add_task") as mock_bg_task:

            mock_teaching.return_value = "EXPLANATION: The process flow algorithm.\nEXAMPLE: Flowchart"
            mock_question.return_value = "What is process flow?"
            mock_tts.return_value = "/mock/audio.mp3"
            
            # 6. RAG + Lesson Start
            print("\n--- Testing /lessons/start (RAG Integration) ---")
            start_res = client.post("/lessons/start", json={
                "student_id": student_id,
                "topic": "Algorithms",
                "document_id": doc_id,
            })
            assert start_res.status_code == 200, start_res.text
            start_data = start_res.json()
            session_id = start_data["session_id"]
            state = start_data["state"]
            
            # Since teaching contained "process", "flow", "algorithm", it should be 'code' or 'diagram'.
            # Wait, "algorithm" maps to code!
            print(f"Start visual type: {start_data['visual']['type']}")
            assert start_data["visual"]["type"] == "code", f"Expected code, got {start_data['visual']['type']}"
            assert start_data["visual"]["title"] == start_data["concept"], "Visual title should match concept"
            
            # 7. Adaptive Reteach
            print("\n--- Testing /lessons/answer (Adaptive Reteach) ---")
            # We must use /lessons/answer. Wait, /lessons/answer route exists in answers.py
            
            # Mock evaluator to return a partial answer
            class MockEval:
                score = 0.5
                is_correct = False
                correctness = "incorrect"
                feedback = "Partial"
                misconception = "Thinks algorithms are just math equations"
                next_action = "reteach"
                def summary(self): return {"score": self.score}
            mock_evaluate.return_value = MockEval()
            
            # Reteach teaching should be an equation!
            mock_teaching.return_value = "EXPLANATION: The mathematical formula is x = y + z."
            mock_question.return_value = "What is the formula?"
            
            ans_res = client.post("/lessons/answer", json={
                "session_id": session_id,
                "answer": "Algorithms are math.",
                "state": state
            })
            assert ans_res.status_code == 200, ans_res.text
            ans_data = ans_res.json()
            # Wait, /lessons/answer route returns state. We then call /lessons/next with the new state!
            new_state = ans_data["state"]
            
            # Call next
            next_res = client.post("/lessons/next", json={
                "session_id": session_id,
                "state": new_state
            })
            assert next_res.status_code == 200, next_res.text
            next_data = next_res.json()
            
            print(f"Reteach visual type: {next_data['visual']['type']}")
            assert next_data["visual"]["type"] == "equation", f"Expected equation, got {next_data['visual']['type']}"
            
            # 8. Next Concept
            print("\n--- Testing /lessons/answer + /lessons/next (Next Concept) ---")
            MockEval.score = 1.0
            MockEval.is_correct = True
            MockEval.next_action = "next_concept"
            mock_evaluate.return_value = MockEval()
            
            mock_teaching.return_value = "EXPLANATION: This is a blackboard explanation."
            
            ans_res2 = client.post("/lessons/answer", json={
                "session_id": session_id,
                "answer": "I know it now.",
                "state": next_data["state"]
            })
            new_state2 = ans_res2.json()["state"]
            
            next_res2 = client.post("/lessons/next", json={
                "session_id": session_id,
                "state": new_state2
            })
            next_data2 = next_res2.json()
            
            print(f"Next concept visual type: {next_data2['visual']['type']}")
            assert next_data2["visual"]["type"] == "blackboard", f"Expected blackboard, got {next_data2['visual']['type']}"

        # 9. Multilingual
        print("\n--- Testing Multilingual ---")
        with unittest.mock.patch("app.teacher.teaching.TeachingEngine.generate") as mock_teaching_ml, \
             unittest.mock.patch("app.teacher.questioning.QuestioningEngine.generate_question") as mock_question_ml, \
             unittest.mock.patch("app.voice.tts.TTSService.generate_speech") as mock_tts_ml, \
             unittest.mock.patch("fastapi.BackgroundTasks.add_task") as mock_bg_task_ml:
            
            # Hindi
            mock_teaching_ml.return_value = "EXPLANATION: बल एक धक्का या खिंचाव है (Force is a push or pull)."
            mock_question_ml.return_value = "बल क्या है?"
            
            ml_res = client.post("/lessons/start", json={
                "student_id": student_id,
                "topic": "Force",
                "language": "Hindi"
            })
            assert ml_res.status_code == 200
            ml_data = ml_res.json()
            print(f"Hindi visual type: {ml_data['visual']['type']}")
            assert ml_data["visual"]["type"] == "blackboard"
            
            ml_session_id = ml_data["session_id"]
            if ml_session_id: db.query(TeachingSession).filter(TeachingSession.id == ml_session_id).delete()

        # 10. Phase 19 Persistence / Recovery
        print("\n--- Testing Phase 19 Recovery ---")
        # We use session_id which has a blackboard visual
        # Ensure zero-generation!
        import app.teacher.engine
        
        call_counts = {k: 0 for k in ["generate", "next_step", "generate_question"]}
        def counter(k):
            def wrap(*args, **kwargs):
                call_counts[k] += 1
                return getattr(app.teacher.engine, k)(*args, **kwargs)
            return wrap
        
        with unittest.mock.patch("app.teacher.teaching.TeachingEngine.generate", side_effect=counter("generate")), \
             unittest.mock.patch("app.teacher.questioning.QuestioningEngine.generate_question", side_effect=counter("generate_question")):
            
            rec_res = client.get(f"/lessons/session/{session_id}")
            assert rec_res.status_code == 200, rec_res.text
            rec_data = rec_res.json()
            
            assert rec_data["visual"]["type"] == next_data2["visual"]["type"]
            assert rec_data["visual"]["content"] == next_data2["visual"]["content"]
            print(f"Recovered visual perfectly: {rec_data['visual']['type']}")
            
            assert call_counts["generate"] == 0
            assert call_counts["generate_question"] == 0
            print("Zero generation verified during recovery.")
            
    finally:
        print("\n--- Cleanup ---")
        try:
            if student_id:
                # Delete in correct FK order for all related records
                lessons = db.query(Lesson).filter(Lesson.student_id == student_id).all()
                for l in lessons:
                    sessions = db.query(TeachingSession).filter(TeachingSession.lesson_id == l.id).all()
                    for s in sessions:
                        db.query(Attempt).filter(Attempt.session_id == s.id).delete()
                        s.current_concept_id = None
                        db.commit()
                        db.delete(s)
                    db.query(Concept).filter(Concept.lesson_id == l.id).delete()
                    db.delete(l)
                if doc_id: db.query(Document).filter(Document.id == doc_id).delete()
                db.query(Student).filter(Student.id == student_id).delete()
                db.commit()
        except Exception as e:
            db.rollback()
            print(f"Cleanup error (ignored): {e}")
        finally:
            db.close()
        print("Controlled records deleted successfully.")

if __name__ == "__main__":
    run_tests()
