# 🧭 CodeAtlas


  CodeAtlas este o platformă avansată de analiză a codului sursă care utilizează **RAG (Retrieval-Augmented Generation)** pentru a transforma repository-urile complexe de pe GitHub în hărți mentale interactive. Folosind LLM-uri de ultimă generație, CodeAtlas permite dezvoltatorilor să înțeleagă arhitecturi complexe, fluxuri de date și dependențe în câteva secunde.

## 🛠️ Stack Tehnologic

### Backend
* **FastAPI:** Server asincron de înaltă performanță.
* **LangChain:** Orchestrarea pipeline-ului RAG.
* **ChromaDB:** Stocare și regăsire vectorială a fragmentelor de cod.
* **Groq Cloud:** Inferență ultra-rapidă pentru modelele Llama 3.

### Frontend
* **React (Vite):** Interfață modernă și reactivă.
* **Tailwind CSS:** Design minimalist cu accente neon.
* **React Router:** Navigare fluidă între Dashboard, Analiză și Chat.

---

## ⚙️ Instalare și Configurare

### 1. Clonare Repository
```powershell
git clone [https://github.com/DumitruIulian/AI-Source-Code-Navigator.git](https://github.com/DumitruIulian/AI-Source-Code-Navigator.git)
cd AI-Source-Code-Navigator
```

## 2. Configurare Backend
Accesează folderul backend și configurează mediul virtual:

```PowerShell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Variabile de Mediu:
Creează un fișier .env în folderul backend/ și adaugă cheia ta:
```
GROQ_API_KEY=cheia_ta_aici
```
3. Configurare Frontend
Într-un terminal nou, instalează dependențele pentru interfață:
```PowerShell

cd frontend
npm install
```
🚀 Lansarea Aplicației (Tutorial)
Pentru ca aplicația să funcționeze corect, trebuie să pornești ambele servere (Backend și Frontend).

Pasul 1: Pornire Backend
Din rădăcina proiectului:
```PowerShell
$env:PYTHONPATH = "backend"; .\venv\Scripts\python.exe -m app.main
```
Serverul va rula la: https://www.google.com/search?q=http://127.0.0.1:8000

Pasul 2: Pornire Frontend
Într-un alt terminal, din folderul frontend:
```PowerShell
cd frontend
npm run dev
```
Accesează aplicația la: http://localhost:5173

