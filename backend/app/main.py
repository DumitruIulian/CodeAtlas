from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os
import shutil
import time
import gc
import threading
from datetime import datetime

from app.core.ingestion import process_github_repo
from app.core.brain import create_vector_store, ask_question_about_code, stream_answer_about_code
from app.core import history
from app.core.analysis import generate_analysis_for_project

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


def _force_delete(path: str) -> None:
  """
  Șterge un director în mod robust (inclusiv pe Windows):
  - încearcă până la 3 ori cu rmtree
  - la eșec de permisiune, așteaptă 0.5s și reîncearcă
  - ca ultimă soluție, redenumește directorul în *_DELETED_timestamp
  """
  if not os.path.exists(path):
      print(f"ℹ️ FORCE-DELETE: {path} nu există, nimic de șters.")
      return

  for attempt in range(3):
      try:
          shutil.rmtree(path, ignore_errors=False)
          print(f"✅ FORCE-DELETE: {path} șters cu succes la încercarea {attempt + 1}")
          return
      except PermissionError as e:
          print(f"⚠️ FORCE-DELETE: PermissionError la {path} (încercarea {attempt + 1}): {e}")
          time.sleep(0.5)
          gc.collect()
      except Exception as e:
          print(f"❌ FORCE-DELETE: eroare la ștergerea {path}: {e}")
          break

  # Ultima soluție: redenumim folderul ca să nu mai fie folosit
  try:
      ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
      new_name = f"{path}_DELETED_{ts}"
      os.rename(path, new_name)
      print(f"⚠️ FORCE-DELETE: nu am reușit să șterg {path}, l-am redenumit în {new_name}")
  except Exception as e:
      print(f"❌ FORCE-DELETE: nu am putut nici redenumi {path}: {e}")

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
            # Audit în background: verdictul apare în Dashboard după ce se salvează
            def run_audit():
                try:
                    proj = history.get_project_by_id(request.repoUrl)
                    if proj:
                        mermaid, hotspots, health_status = generate_analysis_for_project(proj)
                        history.save_project_analysis(request.repoUrl, mermaid, hotspots, health_status)
                        print(f"✅ Audit salvat: health_status={health_status}")
                except Exception as e:
                    print(f"⚠️ Audit background: {e}")
            threading.Thread(target=run_audit, daemon=True).start()
        else:
            print("🧠 Folosim baza de date existentă (Context deja salvat).")
            # La fiecare mesaj în chat, actualizăm verdictul de sănătate în background
            def run_audit_existing():
                try:
                    proj = history.get_project_by_id(request.repoUrl)
                    if proj:
                        mermaid, hotspots, health_status = generate_analysis_for_project(proj)
                        history.save_project_analysis(request.repoUrl, mermaid, hotspots, health_status)
                except Exception as e:
                    print(f"⚠️ Audit (chat) background: {e}")
            threading.Thread(target=run_audit_existing, daemon=True).start()
        
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


@app.post("/api/system/clear-cache")
def clear_vector_cache():
    """
    Șterge conținutul folderului ChromaDB și resetează vector_db/last_repo.
    """
    global vector_db, last_repo

    base_dir = history._get_base_dir()  # type: ignore[attr-defined]
    chroma_dir = os.path.join(base_dir, "backend", "data", "chroma_db")

    print("🧹 CLEAR-CACHE: încerc să închid conexiunile active către ChromaDB...")
    vector_db = None
    last_repo = None
    gc.collect()

    print(f"🧹 CLEAR-CACHE: ștergere cache vectorial la {chroma_dir}")
    _force_delete(chroma_dir)

    try:
        os.makedirs(chroma_dir, exist_ok=True)
        print(f"ℹ️ CLEAR-CACHE: recreat directorul gol ChromaDB la {chroma_dir}")
    except Exception as e:
        print(f"❌ CLEAR-CACHE: eroare la recrearea directorului ChromaDB: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Vector cache cleared successfully"}


@app.post("/api/system/reset-app")
def reset_application_data():
    """
    Resetează aplicația la setările de fabrică:
    - șterge baza de date vectorială (ChromaDB)
    - golește projects.json
    - șterge conținutul folderului storage/
    """
    global vector_db, last_repo

    base_dir = history._get_base_dir()  # type: ignore[attr-defined]
    chroma_dir = os.path.join(base_dir, "backend", "data", "chroma_db")
    data_dir = os.path.join(base_dir, "backend", "data")
    storage_dir = history._get_storage_dir()  # type: ignore[attr-defined]

    print("🧹 RESET-APP: închid conexiunile către ChromaDB și curăț starea in-memory...")
    vector_db = None
    last_repo = None
    gc.collect()

    # 1. Ștergem ChromaDB cu helper-ul robust
    print(f"🧹 RESET-APP: ștergere ChromaDB la {chroma_dir}")
    _force_delete(chroma_dir)

    # 2. Golește projects.json
    try:
        print("🧹 RESET-APP: golire projects.json")
        history.reset_projects()
        print("🔥 DEBUG: projects.json cleared successfully")
    except Exception as e:
        print(f"❌ RESET-APP: eroare la golirea projects.json: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    # 3. Șterge fișierele din storage/ cu helper robust
    print(f"🧹 RESET-APP: ștergere director storage la {storage_dir}")
    _force_delete(storage_dir)

    # 4. Re-creăm directoarele necesare (backend/data, chroma_db, storage)
    try:
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(chroma_dir, exist_ok=True)
        os.makedirs(storage_dir, exist_ok=True)
        print("ℹ️ RESET-APP: directoarele backend/data, chroma_db și storage au fost recreate goale.")
    except Exception as e:
        print(f"❌ RESET-APP: eroare la recrearea directoarelor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Application reset to factory settings"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)