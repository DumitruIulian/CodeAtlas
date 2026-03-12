import os
from git import Repo
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter

def process_github_repo(repo_url: str):
    # 1. Stabilim unde salvăm codul descărcat
    # Mergem din folderul 'core' până în rădăcina proiectului, în 'storage'
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    repo_name = repo_url.split("/")[-1].replace(".git", "")
    local_path = os.path.join(base_dir, "storage", repo_name)

    # 2. Clonăm repository-ul de pe GitHub
    if not os.path.exists(local_path):
        print(f"📡 Se clonează {repo_url}...")
        Repo.clone_from(repo_url, local_path)
    else:
        print(f"✅ Proiectul există deja local la {local_path}")

    # 3. Încărcăm fișierele (doar Python pentru început)
    # Folosim un parser specializat care înțelege sintaxa programării
    loader = GenericLoader.from_filesystem(
        local_path,
        glob="**/*",
        suffixes=[".py"],
        parser=LanguageParser(language=Language.PYTHON, parser_threshold=500)
    )
    documents = loader.load()

    # 4. Spargem codul în bucățele (Code Splitting)
    # Important: folosește splitter-ul de limbaj ca să nu taie funcțiile la jumătate
    splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.PYTHON, 
        chunk_size=2000, 
        chunk_overlap=200
    )
    chunks = splitter.split_documents(documents)
    
    print(f"🧩 Rezultat: {len(chunks)} bucățele de cod gata pentru AI.")
    return chunks