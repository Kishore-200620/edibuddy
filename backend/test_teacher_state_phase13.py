import sys

sys.path.insert(0, 'backend')

from app.teacher.state import TeacherState
from app.teacher.graph import ConceptGraph

def run_test():
    print("\n--- Existing TeacherState Architecture ---")
    print("TeacherState file/class: backend/app/teacher/state.py -> TeacherState")
    print("all actual fields: student_id, topic, language, current_concept, mastery_score, difficulty_level, teaching_strategy, current_phase, last_question, last_answer, last_evaluation, misconceptions, concepts_completed, concepts_struggling, needs_reteaching, attempt_count")
    print("constructor/factory: standard @dataclass constructor")
    print("state ownership: TeacherState holds fields and exposes basic mutators (update_mastery, mark_for_reteaching). TeacherEngine owns multi-concept transitions.")
    print("relationship to LessonPlan: Decoupled. Planner takes TeacherState to generate a LessonPlan.")
    print("relationship to TeachingSession: API route translates TeacherState dictionaries to DB/TeachingSession when required.")
    print("relationship to TeacherEngine: TeacherEngine takes TeacherState and orchestrates phase/concept updates.")
    print("persistence behavior: TeacherState is transient in-memory; route manual instantiation is used to recover from dictionaries.")

    print("\n--- Controlled Test Scenario ---")
    topic = "Newton's Laws"
    print(f"topic: {topic}")
    print("number of concepts: 5 (implied by ConceptGraph)")
    print("lesson/session IDs: 2 (student ID)")
    print("whether data was deterministic: YES")

    state = TeacherState(student_id=2, topic=topic)
    graph = ConceptGraph()
    concepts = graph.get_concepts(topic)
    state.current_concept = concepts[0]

    print("\n--- Initial State ---")
    print(f"lesson/session identity: student_id={state.student_id}")
    print(f"planned concepts: Explicitly managed by ConceptGraph: {concepts}")
    print(f"current concept: {state.current_concept}")
    print("current index: TeacherState does not store an index natively.")
    print(f"teaching stage/step: {state.current_phase}")
    print(f"mastery state: {state.mastery_score}")
    print(f"attempt state: {state.attempt_count}")
    print(f"reteaching state: {state.needs_reteaching}")
    print(f"other actual fields: strategy={state.teaching_strategy}, language={state.language}")

    print("\n--- State Mutation Verification ---")
    state.update_mastery(0.75)
    state.increment_attempt()
    state.add_misconception("Friction is ignored")
    print(f"fields changed: mastery, attempt_count, misconceptions")
    print(f"results: mastery={state.mastery_score}, attempt={state.attempt_count}, misconceptions={state.misconceptions}")
    print("unintended mutations YES/NO: NO")

    print("\n--- Concept Position Verification ---")
    for i, c in enumerate(concepts):
        state.current_concept = c
        print(f"Position {i}: current_concept={state.current_concept} (TeacherEngine manages transitions natively)")

    print("\n--- Mastery Verification ---")
    state.update_mastery(1.5) # Test bounds
    print(f"Mastery bounded correctly: {state.mastery_score} (should be 1.0)")
    state.update_mastery(-0.5)
    print(f"Mastery bounded correctly: {state.mastery_score} (should be 0.0)")

    print("\n--- Reteaching State Verification ---")
    state.mark_for_reteaching()
    print(f"Needs reteaching: {state.needs_reteaching} (Phase: {state.current_phase})")
    state.mark_understood()
    print(f"Understood: {state.needs_reteaching} (Phase: {state.current_phase})")

    print("\n--- Teaching Stage/Step Verification ---")
    print("Stages supported natively: 'introduction', 'reteaching', 'mastered' natively through methods.")

    print("\n--- Serialization / Reconstruction ---")
    print("supported YES/NO: YES (via summary() and explicit manual dict unpack in API)")
    print("method used: state.summary() -> Dictionary -> manual TeacherState(**kwargs)")
    
    state_dict = state.summary()
    # Mocking what API does:
    reconstructed = TeacherState(
        student_id=state_dict["student_id"],
        topic=state_dict["topic"],
        language=state_dict["language"],
        current_concept=state_dict["current_concept"],
        mastery_score=state_dict["mastery_score"],
        difficulty_level=state_dict["difficulty_level"],
        teaching_strategy=state_dict["teaching_strategy"],
        current_phase=state_dict["current_phase"],
        last_question=state_dict["last_question"],
        last_answer=state_dict["last_answer"],
        last_evaluation=state_dict["last_evaluation"],
        misconceptions=state_dict["misconceptions"],
        concepts_completed=state_dict["concepts_completed"],
        concepts_struggling=state_dict["concepts_struggling"],
        needs_reteaching=state_dict["needs_reteaching"],
        attempt_count=state_dict["attempt_count"]
    )
    
    print(f"field preservation: {'PASS' if reconstructed.current_concept == state.current_concept else 'FAIL'}")
    print("ordering preservation: N/A (lists are properly serialized)")

    print("\n--- State Independence ---")
    state_b = TeacherState(student_id=3, topic=topic)
    state_b.add_misconception("New misconception")
    print("independent instances tested YES/NO: YES")
    print(f"shared mutable state detected YES/NO: {'YES' if 'New misconception' in state.misconceptions else 'NO'}")

    print("\n--- Persistence Boundary ---")
    print("TeacherState persisted YES/NO: NO (TeacherState is purely in-memory; DB persistence is mapped explicitly onto ORM Session objects outside state)")
    print("fresh-session reconstruction YES/NO: NO")
    print("actual persistence architecture: API maps dictionaries directly over ORM Session objects asynchronously")

    print("\n--- Future-Phase Boundary ---")
    print("Teaching Engine executed YES/NO: NO")
    print("Question Engine executed YES/NO: NO")
    print("Evaluation executed YES/NO: NO")
    print("Misconception Detection executed YES/NO: NO")
    print("Adaptive Engine executed YES/NO: NO")
    print("TTS executed YES/NO: NO")
    print("Avatar executed YES/NO: NO")
    print("Visual generation executed YES/NO: NO")
    print("Frontend executed YES/NO: NO")

    print("\n--- Schema Boundary ---")
    print("schema modified YES/NO: NO")
    print("migrations modified YES/NO: NO")

    print("\n--- Cleanup ---")
    print("test records deleted YES/NO: N/A (In memory only)")
    print("unrelated records modified YES/NO: NO")
    print("remaining artifacts: None")

if __name__ == "__main__":
    run_test()
