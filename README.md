🚀 AI Source Code Navigator

Aplicație Full-Stack care folosește RAG (Retrieval-Augmented Generation) pentru a analiza cod sursă de pe GitHub folosind AI.

🛠️ Tehnologii
Backend: FastAPI, LangChain, Groq (Llama 3), ChromaDB

Frontend: React (Vite), Tailwind CSS

⚙️ Instalare și Configurare
1. Clonare proiect
PowerShell
git clone https://github.com/DumitruIulian/AI-Source-Code-Navigator.git
cd AI-Source-Code-Navigator
2. Configurare Backend
Creează mediul virtual și instalează librăriile:

PowerShell
python -m venv venv
.\venv\Scripts\activate
pip install -r backend/requirements.txt
Creează un fișier .env în folderul backend/ și adaugă cheia ta:

Plaintext
GROQ_API_KEY=cheia_ta_aici

3. Configurare Frontend
Într-un terminal nou:

PowerShell

cd frontend
npm install
🚀 Pornirea Aplicației
Pasul 1: Pornire Backend
Din folderul principal (rădăcină), rulează:

PowerShell

$env:PYTHONPATH = "backend"; .\venv\Scripts\python.exe -m app.main
Interfața API (Swagger): http://127.0.0.1:8000/docs

Pasul 2: Pornire Frontend
Într-un alt terminal, în folderul frontend, rulează:

PowerShell

npm run dev
Aplicația poate fi accesată la: http://localhost:5173

📖 Cum funcționează?
Introduci un link de GitHub în interfață.

Backend-ul clonează codul și îl salvează în folderul storage/.

Codul este spart în bucăți (chunks) și indexat în baza de date vectorială ChromaDB.

Poți pune întrebări despre logica codului, iar AI-ul îți va răspunde bazându-se pe fișierele scanate.