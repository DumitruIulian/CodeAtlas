from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.ingestion import ingest_repo # Presupun că ai asta în ingestion.py
from app.core.brain import create_vector_store, ask_question_about_code

router = APIRouter()

# Definim structura datelor care vin de la React
class AnalyzeRequest(BaseModel):
    repoUrl: str
    question: str

@router.post("/analyze")
async def analyze_code(request: AnalyzeRequest):
    try:
        print(f"📥 Primire cerere pentru: {request.repoUrl}")
        
        # 1. Procesăm codul (Download + Split în chunks)
        # Atenție: ingest_repo trebuie să returneze 'chunks'
        chunks = ingest_repo(request.repoUrl)
        
        # 2. Creăm baza de date vectorială
        vector_store = create_vector_store(chunks)
        
        # 3. Întrebăm modelul Llama 3 via Groq
        answer = ask_question_about_code(vector_store, request.question)
        
        return {"status": "success", "analysis": answer}
        
    except Exception as e:
        print(f"❌ Eroare: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))