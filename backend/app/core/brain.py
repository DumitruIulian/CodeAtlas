import os
import shutil
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

def create_vector_store(chunks):
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    persist_directory = os.path.join(base_dir, "backend", "data", "chroma_db")
    
    print("🧠 Se încarcă modelul de embedding local...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    if os.path.exists(persist_directory):
        shutil.rmtree(persist_directory)

    print("🛰️ Se creează baza de date vectorială...")
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    return vector_store

def _build_messages(vector_store, question: str):
    # 1. Căutăm întotdeauna global_context (Project Map / PROJ_SUMMARY.txt)
    try:
        global_docs = vector_store.similarity_search(
            question,
            k=1,
            filter={"type": "global_context"},
        )
    except TypeError:
        # Dacă implementarea vector_store nu acceptă filter, cădem grațios înapoi
        global_docs = []

    # 2. Căutăm fragmentele relevante de cod
    raw_docs = vector_store.similarity_search(question, k=12)
    code_docs = [
        d for d in raw_docs if d.metadata.get("type") != "global_context"
    ]

    # 3. Combinăm: întâi Project Map, apoi fragmentele
    docs = list(global_docs) + code_docs

    context_parts = []
    visible_files: list[str] = []
    for d in docs:
        source_file = d.metadata.get("source", "Unknown")
        line_no = d.metadata.get("line", "N/A")
        content = f"--- FIȘIER: {source_file} (Linia: {line_no}) ---\n{d.page_content}"
        context_parts.append(content)

        if source_file and source_file not in visible_files:
            visible_files.append(source_file)

    context = "\n\n".join(context_parts)

    visible_files_section = ""
    if visible_files:
        visible_files_section = "Fișiere vizibile în acest context:\n" + "\n".join(
            f"- {path}" for path in visible_files[:20]
        )

    system = (
        "Ești **CodeAtlas**, un Senior Architect specializat în analiza arhitecturii aplicațiilor.\n"
        "- Ton: profesional, concis, tehnic dar ușor de înțeles (stil Senior Architect / Staff Engineer).\n"
        "- Nu inventa tehnologii, fișiere sau directoare care nu apar în contextul primit. "
        "Dacă nu ai informația în context, spune explicit că nu știi sau că nu apare în context.\n"
        "- Înainte de a formula orice răspuns, parcurge în detaliu conținutul fragmentelor de cod primite, nu doar numele fișierelor. "
        "Dacă utilizatorul întreabă \"cum funcționează X\", caută efectiv logica funcțiilor/metodelor și fluxul de date, nu doar fișierul în care apar.\n"
        "- Nu te limita la fragmentele de cod primite. Folosește în special documentul `PROJ_SUMMARY.txt` "
        "(Project Map / `type=\"global_context\"`) pentru a deduce cum interacționează modulele între ele.\n"
        "- Dacă utilizatorul întreabă despre un concept arhitectural (de exemplu \"cum funcționează auth-ul?\"), "
        "folosește Project Map pentru a identifica fișierele și modulele relevante (ex: controllere, servicii, hooks) "
        "și explică fluxul dintre ele chiar dacă nu ai tot codul lor în față.\n"
        "- Când informația este tehnică, descrie explicit implementarea: clasele, metodele principale relevante, "
        "parametrii importanți și cum circulă datele între componente. Nu te limita la liste de fișiere decât dacă "
        "utilizatorul cere în mod explicit un sumar de structură.\n"
        "- Înainte de a oferi un răspuns tehnic, identifică explicit **Zona de Impact**: `frontend`, `backend`, "
        "`database` sau o combinație (de exemplu `frontend + backend`). Deduci această zonă folosind Project Map "
        "și fișierele din context.\n"
        "- Dacă lipsește o informație importantă, indică clar ce fișier sau zonă ar fi trebuit, conform structurii "
        "de directoare, să conțină acea logică (de exemplu: `backend/app/api/auth.py` sau `frontend/src/hooks/useAuth.ts`).\n\n"
        "Structura de ieșire pentru FIECARE răspuns trebuie să fie STRICT următoarea (respectă spațiile libere dintre secțiuni):\n"
        "1. O linie de titlu principal de forma `### <emoji> Titlu scurt`.\n"
        "2. Un rând liber.\n"
        "3. Prima secțiune de bullet points trebuie să indice clar **Zona de Impact** (frontend/backend/database) "
        "și să sumarizeze, în 1-2 bullets, ce părți ale sistemului sunt afectate.\n"
        "4. Restul explicațiilor trebuie organizate în bullet points folosind `*`, nu în paragrafe lungi. "
        "Poți avea sub-bullets dar păstrează-le concise.\n"
        "5. Dacă întrebarea este despre structură sau locația fișierelor, inserează un mic arbore în stil `tree`, "
        "cu fiecare nivel pe linie separată și indentare clară.\n"
        "6. Menționează întotdeauna căile de fișiere între backticks, de exemplu `backend/app/main.py` sau "
        "`frontend/src/pages/Home.tsx`.\n"
        "7. Folosește bold strategic (`**text**`) pentru numele de fișiere, concepte cheie sau pași critici.\n"
        "8. Dacă utilizatorul întreabă despre o funcție sau bucată de cod prezentă în context, include un snippet scurt de cod "
        "într-un bloc Markdown cu limbajul specificat (de exemplu ```python, ```tsx), folosind DOAR conținut din context.\n\n"
        "NU începe niciun rând nou cu virgulă, punct sau alt semn de punctuație orfan. "
        "Fiecare bullet point trebuie să fie o propoziție de sine stătătoare, fără să depindă de semne de punctuație rămase de pe linia anterioară.\n"
        "Păstrează spațiere aerisită: lasă un rând liber între titlu, liste, blocuri de cod și orice alte secțiuni. "
        "Înainte să răspunzi, verifică mental că toate informațiile pe care le oferi provin din contextul primit; "
        "dacă un detaliu nu este acoperit de context, nu îl inventa.\n\n"
        f"{visible_files_section}"
    )

    user = f"CONTEXT:\n{context}\n\nÎNTREBARE: {question}"

    return [SystemMessage(content=system), HumanMessage(content=user)]


def ask_question_about_code(vector_store, question: str) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "❌ Eroare: Variabila de mediu GROQ_API_KEY nu este setată."

    llm = ChatGroq(
        api_key=api_key,
        model="llama-3.3-70b-versatile",
        temperature=0.0,
    )

    try:
        messages = _build_messages(vector_store, question)
        result = llm.invoke(messages)
        return getattr(result, "content", str(result))
    except Exception as e:
        return f"❌ Eroare: {str(e)}"


async def stream_answer_about_code(vector_store, question: str):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        yield "❌ Eroare: Variabila de mediu GROQ_API_KEY nu este setată."
        return

    llm = ChatGroq(
        api_key=api_key,
        model="llama-3.3-70b-versatile",
        temperature=0.0,
    )

    messages = _build_messages(vector_store, question)

    try:
        # LangChain: preferăm model.astream(messages). Dacă versiunea expune chain.astream,
        # îl putem introduce ulterior; aici folosim direct modelul.
        async for chunk in llm.astream(messages):
            text = getattr(chunk, "content", None)
            if text is None:
                text = str(chunk)
            if text:
                yield text
    except Exception as e:
        yield f"\n\n❌ Eroare: {str(e)}"