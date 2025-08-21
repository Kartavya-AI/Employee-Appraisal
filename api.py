import os
import json
import logging
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import uvicorn

from tool import (
    setup_knowledge_base, 
    get_questions_for_role, 
    get_feedback, 
    KNOWLEDGE_BASE
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

vector_store = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global vector_store
    try:
        logger.info("Starting application initialization...")
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.error("GOOGLE_API_KEY environment variable not found")
            raise RuntimeError("GOOGLE_API_KEY environment variable is required")
        
        logger.info("Initializing knowledge base...")
        vector_store = setup_knowledge_base()
        logger.info("Knowledge base initialized successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        raise
    finally:
        logger.info("Application shutdown")

app = FastAPI(
    title="HR Appraisal Assessment API",
    description="A comprehensive API for conducting role-based appraisal assessments",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionModel(BaseModel):
    question: str
    options: List[str]
    answer: str

class AssessmentRequest(BaseModel):
    role: str = Field(..., description="The role for which to generate questions")
    num_questions: int = Field(default=10, ge=1, le=50, description="Number of questions to generate")
    
    @validator('role')
    def validate_role(cls, v):
        if v not in KNOWLEDGE_BASE:
            available_roles = list(KNOWLEDGE_BASE.keys())
            raise ValueError(f"Role '{v}' not found. Available roles: {available_roles}")
        return v

class SubmissionRequest(BaseModel):
    role: str = Field(..., description="The role being assessed")
    answers: List[str] = Field(..., description="List of user answers")
    questions: List[QuestionModel] = Field(..., description="List of questions that were asked")
    
    @validator('role')
    def validate_role(cls, v):
        if v not in KNOWLEDGE_BASE:
            available_roles = list(KNOWLEDGE_BASE.keys())
            raise ValueError(f"Role '{v}' not found. Available roles: {available_roles}")
        return v
    
    @validator('answers')
    def validate_answers_length(cls, v, values):
        if 'questions' in values and len(v) != len(values['questions']):
            raise ValueError("Number of answers must match number of questions")
        return v

class AssessmentResponse(BaseModel):
    role: str
    questions: List[QuestionModel]
    total_questions: int

class ResultResponse(BaseModel):
    role: str
    score: int
    total_questions: int
    percentage: float
    feedback: str

class HealthResponse(BaseModel):
    status: str
    message: str
    available_roles: List[str]
    total_questions_in_db: int

@app.get("/", response_model=Dict[str, str])
async def root():
    return {
        "message": "HR Appraisal Assessment API",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    global vector_store
    try:
        if vector_store is None:
            raise HTTPException(status_code=503, detail="Vector store not initialized")
        total_count = vector_store._collection.count()
        
        return HealthResponse(
            status="healthy",
            message="API is running successfully",
            available_roles=list(KNOWLEDGE_BASE.keys()),
            total_questions_in_db=total_count
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

@app.get("/roles", response_model=List[str])
async def get_available_roles():
    return list(KNOWLEDGE_BASE.keys())

@app.post("/assessment/start", response_model=AssessmentResponse)
async def start_assessment(request: AssessmentRequest):
    global vector_store
    try:
        if vector_store is None:
            raise HTTPException(status_code=503, detail="Vector store not initialized")
        
        logger.info(f"Starting assessment for role: {request.role}, questions: {request.num_questions}")
        
        questions = get_questions_for_role(vector_store, request.role, request.num_questions)
        
        if not questions:
            raise HTTPException(
                status_code=404, 
                detail=f"No questions found for role: {request.role}"
            )
        
        question_models = [
            QuestionModel(
                question=q["question"],
                options=q["options"],
                answer=q["answer"]
            ) for q in questions
        ]
        
        return AssessmentResponse(
            role=request.role,
            questions=question_models,
            total_questions=len(question_models)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting assessment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/assessment/submit", response_model=ResultResponse)
async def submit_assessment(request: SubmissionRequest, background_tasks: BackgroundTasks):
    try:
        logger.info(f"Processing assessment submission for role: {request.role}")
        correct_answers = 0
        for i, (user_answer, question) in enumerate(zip(request.answers, request.questions)):
            if user_answer.strip().lower() == question.answer.strip().lower():
                correct_answers += 1
        
        total_questions = len(request.questions)
        percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        logger.info(f"Assessment completed: {correct_answers}/{total_questions} ({percentage:.1f}%)")

        try:
            feedback = get_feedback(correct_answers, total_questions, request.role)
        except Exception as e:
            logger.error(f"Error generating feedback: {str(e)}")
            feedback = f"Assessment completed with a score of {correct_answers} out of {total_questions} questions correct ({percentage:.1f}%). Detailed feedback is temporarily unavailable."
        
        return ResultResponse(
            role=request.role,
            score=correct_answers,
            total_questions=total_questions,
            percentage=round(percentage, 2),
            feedback=feedback
        )
        
    except Exception as e:
        logger.error(f"Error submitting assessment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/assessment/questions/{role}", response_model=AssessmentResponse)
async def get_questions_by_role(role: str, num_questions: int = 10):
    request = AssessmentRequest(role=role, num_questions=num_questions)
    return await start_assessment(request)

@app.get("/stats/role/{role}", response_model=Dict[str, Any])
async def get_role_stats(role: str):
    global vector_store
    try:
        if vector_store is None:
            raise HTTPException(status_code=503, detail="Vector store not initialized")
        
        if role not in KNOWLEDGE_BASE:
            raise HTTPException(status_code=404, detail=f"Role '{role}' not found")
        
        all_questions = vector_store._collection.get(where={"role": role})
        question_count = len(all_questions.get("metadatas", []))
        
        return {
            "role": role,
            "total_questions_available": question_count,
            "questions_in_knowledge_base": len(KNOWLEDGE_BASE[role])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting role stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    logger.error(f"ValueError: {str(exc)}")
    return HTTPException(status_code=400, detail=str(exc))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )