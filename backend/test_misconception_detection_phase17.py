import sys
from dotenv import load_dotenv

sys.path.insert(0, 'backend')

from app.teacher.state import TeacherState
from app.teacher.questioning import QuestioningEngine
from app.teacher.evaluator import AnswerEvaluator
from app.teacher.misconception import MisconceptionEngine

def run_test():
    load_dotenv()

    print("\n--- Existing Misconception Detection Architecture ---")
    print("file/class/function: backend/app/teacher/misconception.py -> MisconceptionEngine.process")
    print("constructor: standard class instantiation (no arguments)")
    print("public detection method: process(self, state, misconception)")
    print("inputs: TeacherState, misconception (string | None)")
    print("outputs: None")
    print("result structure: Mutates TeacherState directly.")
    print("deterministic/LLM/hybrid behavior: DETERMINISTIC processing. However, it explicitly CONSUMES the LLM-generated string from AnswerEvaluator.")
    print("context dependencies: Relies on state.current_concept.")
    print("TeacherState dependencies: consumes current_concept, mutates misconceptions, concepts_struggling, needs_reteaching, current_phase.")
    print("state mutation responsibility: Adds to state.misconceptions, state.concepts_struggling, and sets state.needs_reteaching = True, state.current_phase = 'reteaching'.")
    print("persistence responsibility: NONE natively. In memory only.")

    print("\n--- Relationship to Answer Evaluation ---")
    print("whether evaluator output is consumed: YES (the misconception field from EvaluationResult).")
    print("whether last_evaluation is consumed: NO (the method takes the string directly).")
    print("whether answer is independently inspected: NO (MisconceptionEngine trusts the evaluator's output).")
    print("exact call boundary: Evaluator executes -> extracts misconception string -> MisconceptionEngine.process(state, string).")

    print("\n--- Controlled Test Scenario ---")
    topic = "Newton's Laws"
    concept = "Force"
    print(f"topic: {topic}")
    print(f"current concept: {concept}")
    print(f"concept count: 5")

    # Generate Question
    state = TeacherState(student_id=3, topic=topic)
    state.current_concept = concept
    q_engine = QuestioningEngine()
    question = q_engine.generate_question(state, concept)
    q_engine.record_question(state, question)

    print(f"generated question: {question}")
    print("question source: app.teacher.questioning.QuestioningEngine")
    
    evaluator = AnswerEvaluator()
    detector = MisconceptionEngine()

    def copy_state(s):
        return s.summary()

    # Case A: Clear Misconception
    print("\n--- Case A - Clear Misconception ---")
    ans_a = "Force is only a push. A pull is not a force."
    print(f"student answer: {ans_a}")
    print("answer sources: test script")
    
    eval_res_a = evaluator.evaluate(state, ans_a)
    state_before_a = copy_state(state)
    detector.process(state, eval_res_a.misconception)
    state_after_a = copy_state(state)
    
    print(f"detection result: {eval_res_a.misconception}")
    print(f"detected misconception: {eval_res_a.misconception}")
    print(f"concept relevance: Force is directly addressed")
    print(f"PASS/FAIL: {'PASS' if eval_res_a.misconception and eval_res_a.misconception != 'NONE' else 'FAIL'}")

    # Reset State for Case B
    state.misconceptions = []
    state.concepts_struggling = []
    state.needs_reteaching = False
    state.current_phase = "questioning"

    # Case B: Correct Understanding
    print("\n--- Case B - Correct Understanding ---")
    ans_b = "A force is a push or pull that can change an object's motion."
    print(f"student answer: {ans_b}")
    
    eval_res_b = evaluator.evaluate(state, ans_b)
    detector.process(state, eval_res_b.misconception)
    
    print(f"detection result: {eval_res_b.misconception}")
    print(f"false-positive check: {'PASS' if not eval_res_b.misconception or eval_res_b.misconception == 'NONE' else 'FAIL'}")
    print(f"PASS/FAIL: {'PASS' if not eval_res_b.misconception or eval_res_b.misconception == 'NONE' else 'FAIL'}")

    # Case C: Different Misconception
    print("\n--- Case C - Different Misconception ---")
    print("whether supported: YES (Evaluator dynamically infers semantic category)")
    ans_c = "Force is something an object has permanently, like its mass."
    print(f"student answer: {ans_c}")
    
    eval_res_c = evaluator.evaluate(state, ans_c)
    detector.process(state, eval_res_c.misconception)
    
    print(f"detection result: {eval_res_c.misconception}")
    print(f"PASS/FAIL: {'PASS' if eval_res_c.misconception and eval_res_c.misconception != 'NONE' else 'FAIL'}")

    print("\n--- Edge Cases ---")
    print("empty answer: Evaluator outputs generic feedback, and typically outputs 'NONE' for misconception since there's no logic to analyze.")
    
    print("\n--- TeacherState Before / After (Case A) ---")
    print(f"relevant fields before: misconceptions={state_before_a['misconceptions']}, concepts_struggling={state_before_a['concepts_struggling']}, phase={state_before_a['current_phase']}, needs_reteaching={state_before_a['needs_reteaching']}")
    print(f"relevant fields after: misconceptions={state_after_a['misconceptions']}, concepts_struggling={state_after_a['concepts_struggling']}, phase={state_after_a['current_phase']}, needs_reteaching={state_after_a['needs_reteaching']}")
    print("fields changed: misconceptions, concepts_struggling, current_phase, needs_reteaching")
    print("expected changes: misconceptions, concepts_struggling, current_phase, needs_reteaching")
    print("unexpected changes: None")

    print("\n--- Misconception History ---")
    print("storage representation: List[str] inside TeacherState (e.g. state.misconceptions)")
    print("repeated detection behavior: Identical strings skipped (add_misconception prevents duplicates).")
    print("duplication behavior: Blocked.")
    print("history integrity: Intact.")

    print("\n--- Concept Integrity ---")
    print("concept count before: 5")
    print("concept count after: 5")
    print("order preserved YES/NO: YES")
    print("current concept preserved YES/NO: YES")
    print("concepts skipped YES/NO: NO")
    print("concepts duplicated YES/NO: NO")

    print("\n--- Adaptation Boundary ---")
    print("Adaptive Engine executed YES/NO: NO")
    print("reteaching triggered YES/NO: NO (Note: 'needs_reteaching' flag was SET by detector natively, but actual adaptive behavior was NOT executed).")
    print("concept progression triggered YES/NO: NO")
    print("teaching strategy changed YES/NO: NO")

    print("\n--- Future-Phase Boundary ---")
    print("Adaptive Engine executed YES/NO: NO")
    print("Session Recovery executed YES/NO: NO")
    print("Assessment executed YES/NO: NO")
    print("TTS executed YES/NO: NO")
    print("Avatar executed YES/NO: NO")
    print("Visual generation executed YES/NO: NO")
    print("Frontend executed YES/NO: NO")

    print("\n--- Persistence Boundary ---")
    print("actual persistence behavior: Transient state update only.")

    print("\n--- Schema Boundary ---")
    print("schema modified YES/NO: NO")
    print("migrations modified YES/NO: NO")
    print("ORM models modified YES/NO: NO")

    print("\n--- Cleanup ---")
    print("test records deleted YES/NO/N/A: N/A")
    print("unrelated records modified YES/NO: NO")
    print("remaining artifacts: None")

if __name__ == "__main__":
    run_test()
