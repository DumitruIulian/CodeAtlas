from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os

from app.core.ingestion import process_github_repo
from app.core.brain import create_vector_store, ask_question_about_code, stream_answer_about_code
from app.core import history

app = FastAPI(title="AI Source Code Navigator API")

# --- CONFIGURARE CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # Mai sigur decât "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Aliniem numele câmpurilor cu JSON-ul din React
class QueryRequest(BaseModel):
    repoUrl: str  # <--- Schimbat din repo_url în repoUrl
    question: str

# Reținem baza de date pentru a nu o recrea la fiecare întrebare despre același repo
vector_db = None
last_repo = None

@app.get("/")
def read_root():
    return {"status": "online", "message": "AI Navigator is ready"}


@app.get("/api/projects")
def list_projects():
    """
    Returnează lista proiectelor indexate local, folosită de Dashboard.
    """
    try:
        projects = history.get_projects()
        return {"projects": projects}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
def get_stats():
    """
    Returnează statistici agregate pentru Dashboard.
    """
    try:
        stats = history.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
async def analyze_code(request: QueryRequest, stream: bool = Query(False)):
    global vector_db, last_repo
    print(f"📡 Cerere primită pentru: {request.repoUrl}")
    
    try:
        # Verificăm dacă repo-ul s-a schimbat sau dacă e prima rulare
        if vector_db is None or last_repo != request.repoUrl:
            print("📦 Procesare repo nou (clonare + indexare)...")
            chunks = process_github_repo(request.repoUrl)
            vector_db = create_vector_store(chunks)
            last_repo = request.repoUrl
        else:
            print("🧠 Folosim baza de date existentă (Context deja salvat).")
        
        if stream:
            print("✅ Streaming răspuns (LangChain astream) ...")
            return StreamingResponse(
                stream_answer_about_code(vector_db, request.question),
                media_type="text/plain; charset=utf-8",
                headers={"Cache-Control": "no-cache"}
            )

        answer = ask_question_about_code(vector_db, request.question)
        print("✅ Răspuns generat!")
        return {"status": "success", "answer": answer}
        
    except Exception as e:
        print(f"❌ Eroare: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)