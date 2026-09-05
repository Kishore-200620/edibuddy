from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from uuid import uuid4


from sqlalchemy.orm import Session
from app.rag.retriever import retrieve_relevant_chunks
from app.database.connection import get_db
from app.teacher.engine import TeacherEngine
from app.teacher.state import TeacherState
from app.services.learning_service import LearningService
from app.voice.tts import TTSService
from app.models.student import Student
from app.models.session import TeachingSession
from app.models.lesson import Lesson
router = APIRouter(
    prefix="/lessons",
    tags=["Lessons"],
)


class StartLessonRequest(BaseModel):
    student_id: int
    topic: str
    document_id: int | None = None
    language: str | None = None


class NextStepRequest(BaseModel):
    session_id: int
    state: dict


teacher_engine = TeacherEngine()
learning_service = LearningService()
tts_service = TTSService()


def extract_speech_text(teaching: str) -> str:
    if not teaching:
        return ""

    text = teaching

    if "EXPLANATION:" in text:
        text = text.split("EXPLANATION:", 1)[1]

    if "QUESTION:" in text:
        text = text.split("QUESTION:", 1)[0]

    return text.strip()

@router.post("/start")
async def start_lesson(
    request: StartLessonRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):

    student = db.get(Student, request.student_id)

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found",
        )

    language = request.language or student.preferred_language

    # 1. Create persistent lesson + concepts + session
    lesson, concepts, session = learning_service.create_lesson_session(
    db=db,
    student_id=request.student_id,
    topic=request.topic,
    document_id=request.document_id,
    language=language,
)

    # 2. Start AI Teacher
    teaching_context = None

    if request.document_id is not None:
        teaching_context = retrieve_relevant_chunks(
            db=db,
            question=request.topic,
            document_id=request.document_id,
            limit=5,
        )

    result = teacher_engine.start(
        student_id=request.student_id,
        topic=request.topic,
        teaching_context=teaching_context,
        language=language,
    )
    audio_filename = f"lesson_{session.id}_teacher.mp3"

    speech_text = extract_speech_text(result["teaching"])

    audio_path = await tts_service.generate_speech(
    text=speech_text,
    language=language,
    filename=audio_filename,
    )

    # 3. Keep database session aligned with TeacherState
    if concepts:
        state_data = {
            "current_concept": result["state"].current_concept,
            "mastery_score": result["state"].mastery_score,
            "difficulty_level": result["state"].difficulty_level,
            "teaching_strategy": result["state"].teaching_strategy,
            "current_phase": result["state"].current_phase,
            "last_question": result["state"].last_question,
            "last_answer": result["state"].last_answer,
            "last_evaluation": result["state"].last_evaluation,
            "misconceptions": result["state"].misconceptions,
            "concepts_struggling": result["state"].concepts_struggling,
            "concepts_completed": result["state"].concepts_completed,
            "needs_reteaching": result["state"].needs_reteaching,
            "attempt_count": result["state"].attempt_count,
            "teaching": result["teaching"],
            "visual": result["visual"].model_dump() if hasattr(result["visual"], "model_dump") else (result["visual"].dict() if hasattr(result["visual"], "dict") else result["visual"]),
            "audio_url": f"/voice/audio/{audio_filename}"
        }
        learning_service.update_session(
            db=db,
            session=session,
            concept_id=concepts[0].id,
            step="question",
            state_data=state_data
        )

    return {
        "session_id": session.id,
        "lesson_id": lesson.id,
        "student_id": request.student_id,
        "topic": request.topic,
        "concept": result["state"].current_concept,
        "teaching": result["teaching"],
        "question": result["question"],
        "visual": result["visual"],
        "audio_url": f"/voice/audio/{audio_filename}",
        "state": result["state"].summary(),
    }

@router.post("/next")
def next_step(
    request: NextStepRequest,
    db: Session = Depends(get_db),
):

    state_data = request.state

    state = TeacherState(
        student_id=state_data["student_id"],
        topic=state_data["topic"],
        language=state_data.get("language", "English"),
        current_concept=state_data["current_concept"],
        mastery_score=state_data["mastery_score"],
        difficulty_level=state_data["difficulty_level"],
        teaching_strategy=state_data["teaching_strategy"],
        current_phase=state_data["current_phase"],
        last_question=state_data["last_question"],
        last_answer=state_data.get("last_answer"),
        last_evaluation=state_data.get("last_evaluation"),
        misconceptions=state_data["misconceptions"],
        concepts_completed=state_data["concepts_completed"],
        concepts_struggling=state_data["concepts_struggling"],
        needs_reteaching=state_data["needs_reteaching"],
        attempt_count=state_data["attempt_count"],
    )

    result = teacher_engine.next_step(state)

    session = db.get(TeachingSession, request.session_id)
    if session:
        # Note: next_step doesn't generate audio/avatar in the current route, only answer() and start() do.
        # But we still persist the teaching content so the client can resume correctly.
        persist_state = {
            "current_concept": state.current_concept,
            "mastery_score": state.mastery_score,
            "difficulty_level": state.difficulty_level,
            "teaching_strategy": state.teaching_strategy,
            "current_phase": state.current_phase,
            "last_question": result["question"] or state.last_question,
            "last_answer": state.last_answer,
            "last_evaluation": state.last_evaluation,
            "misconceptions": state.misconceptions,
            "concepts_struggling": state.concepts_struggling,
            "concepts_completed": state.concepts_completed,
            "needs_reteaching": state.needs_reteaching,
            "attempt_count": state.attempt_count,
            "teaching": result["teaching"],
            "visual": result.get("visual").model_dump() if hasattr(result.get("visual"), "model_dump") else (result.get("visual").dict() if hasattr(result.get("visual"), "dict") else result.get("visual")),
            # Preserve existing avatar/audio since next_step does not generate new ones here
            "audio_url": session.state_data.get("audio_url") if session.state_data else None,
        }
        
        # update current concept mapping
        from app.models.concept import Concept
        concept_obj = None
        if result["concept"]:
            concept_obj = db.query(Concept).filter(Concept.lesson_id == session.lesson_id, Concept.title == result["concept"]).first()
            
        learning_service.update_session(
            db=db,
            session=session,
            concept_id=concept_obj.id if concept_obj else None,
            step="completed" if result["action"] == "completed" else "explain",
            status="completed" if result["action"] == "completed" else "active",
            state_data=persist_state
        )

    return {
        "action": result["action"],
        "concept": result["concept"],
        "teaching": result["teaching"],
        "question": result["question"],
        "visual": result.get("visual"),
        "state": state.summary(),
    }


@router.get("/session/{session_id}")
def recover_session(
    session_id: int,
    db: Session = Depends(get_db),
):
    session = db.get(TeachingSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Teaching session not found")
        
    lesson = db.get(Lesson, session.lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")

    state_data = session.state_data or {}
    
    # Reconstruct TeacherState dict as expected by frontend
    recovered_state = {
        "student_id": session.student_id,
        "topic": lesson.topic,
        "language": lesson.language,
        "current_concept": state_data.get("current_concept"),
        "mastery_score": state_data.get("mastery_score", 0.0),
        "difficulty_level": state_data.get("difficulty_level", "beginner"),
        "teaching_strategy": state_data.get("teaching_strategy", "direct_explanation"),
        "current_phase": state_data.get("current_phase", "introduction"),
        "last_question": state_data.get("last_question"),
        "last_answer": state_data.get("last_answer"),
        "last_evaluation": state_data.get("last_evaluation"),
        "misconceptions": state_data.get("misconceptions", []),
        "concepts_completed": state_data.get("concepts_completed", []),
        "concepts_struggling": state_data.get("concepts_struggling", []),
        "needs_reteaching": state_data.get("needs_reteaching", False),
        "attempt_count": state_data.get("attempt_count", 0),
    }

    action = "completed" if session.status == "completed" else "teaching"
    
    return {
        "session_id": session.id,
        "lesson_id": lesson.id,
        "student_id": session.student_id,
        "topic": lesson.topic,
        "action": action,
        "concept": state_data.get("current_concept"),
        "teaching": state_data.get("teaching", ""),
        "question": state_data.get("last_question"),
        "visual": state_data.get("visual"),
        "audio_url": state_data.get("audio_url"),
        "state": recovered_state,
    }