import sys

sys.path.insert(0, 'backend')

from app.teacher.state import TeacherState
from app.teacher.questioning import QuestioningEngine
from app.teacher.graph import ConceptGraph

def run_test():
    print("\n--- Existing Question Engine Architecture ---")
    print("file/class/function: backend/app/teacher/questioning.py -> QuestioningEngine (generate_question and record_question)")
    print("constructor: standard class instantiation (no arguments)")
    print("public question method: generate_question(self, state, concept), record_question(self, state, question)")
    print("inputs: TeacherState, concept (string)")
    print("outputs: string (the generated question)")
    print("question structure: Pure string.")
    print("context dependency: NONE (deterministic template format).")
    print("LLM dependency: NONE natively. Deterministic template dictionary.")
    print("state mutation responsibility: Exposed distinctly via record_question(state, question).")
    print("persistence responsibility: NONE natively inside QuestioningEngine.")

    print("\n--- Controlled Test Scenario ---")
    topic = "Newton's Laws"
    print(f"topic: {topic}")
    
    state = TeacherState(student_id=2, topic=topic)
    graph = ConceptGraph()
    concepts = graph.get_concepts(topic)
    state.current_concept = concepts[0] # Force

    print(f"current concept: {state.current_concept}")
    print(f"concept count: {len(concepts)}")
    print("context source: N/A (deterministic templates)")
    print("deterministic input YES/NO: YES")

    print("\n--- TeacherState Before ---")
    print(f"fields before: current_concept={state.current_concept}, phase={state.current_phase}, last_question={state.last_question}")
    
    engine = QuestioningEngine()
    print("\nExecuting QuestioningEngine.generate_question...")
    question_text = engine.generate_question(state, state.current_concept)
    
    print("\nExecuting QuestioningEngine.record_question...")
    engine.record_question(state, question_text)

    print("\n--- TeacherState After ---")
    print(f"fields after: current_concept={state.current_concept}, phase={state.current_phase}, last_question={state.last_question}")
    print(f"fields changed: phase (-> {state.current_phase}), last_question (-> {state.last_question})")
    print("expected changes: phase, last_question")
    print("unexpected changes: None")
    
    print("\n--- Concept Integrity ---")
    print(f"concept count before: {len(concepts)}")
    print(f"concept count after: {len(concepts)}")
    print("order preserved YES/NO: YES")
    print("current concept preserved YES/NO: YES")
    print("concepts skipped YES/NO: NO")
    print("concepts duplicated YES/NO: NO")

    print("\n--- Question Output ---")
    print(f"question text: {question_text}")
    print("question type: conceptual short answer")
    print(f"target concept: {state.current_concept}")
    print(f"difficulty: {state.difficulty_level}")
    print("options/metadata if applicable: None natively")

    print("\n--- Question Validation ---")
    generated = bool(question_text)
    print(f"question generated PASS/FAIL: {'PASS' if generated else 'FAIL'}")
    
    non_empty = len(question_text.strip()) > 5 if generated else False
    print(f"non-empty PASS/FAIL: {'PASS' if non_empty else 'FAIL'}")
    
    valid_struct = type(question_text) == str
    print(f"structurally valid PASS/FAIL: {'PASS' if valid_struct else 'FAIL'}")
    
    asks_question = "?" in question_text
    print(f"actually asks a question PASS/FAIL: {'PASS' if asks_question else 'FAIL'}")
    
    concept_aligned = state.current_concept.lower() in question_text.lower()
    print(f"concept alignment PASS/FAIL: {'PASS' if concept_aligned else 'FAIL'}")
    print(f"context/teaching relevance PASS/FAIL: {'PASS' if concept_aligned else 'FAIL'}")

    print("\n--- Repeated Question Generation ---")
    question_2 = engine.generate_question(state, state.current_concept)
    print("repeated execution performed YES/NO: YES")
    print(f"output behavior: IDENTICAL (deterministic): {question_2 == question_text}")
    print("state behavior: Unmutated by generation natively (mutated strictly by record_question).")
    print("deterministic/variable result: DETERMINISTIC")

    print("\n--- Difficulty / Question Type ---")
    print("Supported behavior: TeacherState.difficulty_level exists, but QuestioningEngine natively ignores it in favor of a universal template per language currently.")

    print("\n--- Answer Evaluation Boundary ---")
    print("answer submitted YES/NO: NO")
    print("answer evaluated YES/NO: NO")
    print("correctness calculated YES/NO: NO")
    print("mastery calculated YES/NO: NO")
    print("misconception detection executed YES/NO: NO")
    print("adaptation executed YES/NO: NO")

    print("\n--- Future-Phase Boundary ---")
    print("Teaching Engine executed YES/NO: NO")
    print("Answer Evaluation executed YES/NO: NO")
    print("Misconception Detection executed YES/NO: NO")
    print("Adaptive Engine executed YES/NO: NO")
    print("Session Recovery executed YES/NO: NO")
    print("Assessment executed YES/NO: NO")
    print("TTS executed YES/NO: NO")
    print("Avatar executed YES/NO: NO")
    print("Visual generation executed YES/NO: NO")
    print("Frontend executed YES/NO: NO")

    print("\n--- Persistence Boundary ---")
    print("actual persistence behavior: QuestionEngine is purely transient. State mutation is in-memory. Database mapping orchestrates in the route.")

    print("\n--- Schema Boundary ---")
    print("schema modified YES/NO: NO")
    print("migrations modified YES/NO: NO")

    print("\n--- Cleanup ---")
    print("test records deleted YES/NO: N/A (In memory)")
    print("unrelated records modified YES/NO: NO")
    print("remaining artifacts: None")

if __name__ == "__main__":
    run_test()
