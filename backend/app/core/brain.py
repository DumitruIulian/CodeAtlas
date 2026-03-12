import os
import shutil
from dotenv import load_dotenv
from groq import Groq  # Importăm Groq
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

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

def ask_question_about_code(vector_store, question):
    api_key = os.getenv("GROQ_API_KEY")
    client = Groq(api_key=api_key)
    
    # 1. Căutăm bucățile de cod
    docs = vector_store.similarity_search(question, k=4)
    
    # 2. Construim contextul incluzând sursa pentru fiecare bucată
    context_parts = []
    for d in docs:
        source_file = d.metadata.get("source", "Unknown")
        line_no = d.metadata.get("line", "N/A")
        content = f"--- FIȘIER: {source_file} (Linia: {line_no}) ---\n{d.page_content}"
        context_parts.append(content)
    
    context = "\n\n".join(context_parts)

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system", 
                    "content": "Ești un Senior Developer. Răspunde concret. Când menționezi ceva, specifică obligatoriu fișierul și linia din contextul oferit. Folosește formatare Markdown (bold, liste, blocuri de cod)."
                },
                {
                    "role": "user", 
                    "content": f"CONTEXT:\n{context}\n\nÎNTREBARE: {question}"
                }
            ],
            model="llama-3.3-70b-versatile",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"❌ Eroare: {str(e)}"