import os
import json
import re
from typing import List, Set

from git import Repo
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter
from langchain_core.documents import Document

EXCLUDED_DIRS = {"node_modules", "dist", ".git", "venv", "__pycache__"}
FRONTEND_EXTENSIONS = {".tsx", ".ts", ".jsx", ".js", ".json", ".css"}


def _build_project_structure_file(local_path: str) -> str:
    """
    Generează un fișier text cu structura proiectului (arbore directoare + fișiere),
    excluzând directoarele masive precum node_modules/dist/.git/venv.
    """
    structure_lines: list[str] = []

    for root, dirs, files in os.walk(local_path):
        # Excludem directoarele mari / nerelevante
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

        rel_root = os.path.relpath(root, local_path)
        depth = 0 if rel_root == "." else rel_root.count(os.sep)
        indent = "  " * depth
        folder_name = "." if rel_root == "." else os.path.basename(root)
        structure_lines.append(f"{indent}{folder_name}/")

        for filename in files:
            # Ignorăm fișiere foarte ascunse sau triviale
            if filename.startswith("."):
                continue
            structure_lines.append(f"{indent}  {filename}")

    content = "\n".join(structure_lines)
    out_path = os.path.join(local_path, "project_structure.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"🗺️  Harta de structură a proiectului salvată la: {out_path}")
    return out_path


def _detect_technologies(local_path: str) -> List[str]:
    """
    Detectează tehnologiile principale și pachetele folosite, pe baza fișierelor
    de config standard (package.json, requirements.txt, docker-compose.yml, go.mod etc.).
    """
    technologies: Set[str] = set()

    # Node / JS / TS stack
    package_json_path = os.path.join(local_path, "package.json")
    if os.path.exists(package_json_path):
        try:
            with open(package_json_path, "r", encoding="utf-8") as f:
                pkg = json.load(f)
            deps = pkg.get("dependencies", {}) or {}
            dev_deps = pkg.get("devDependencies", {}) or {}
            all_deps = {**deps, **dev_deps}

            technologies.add("JavaScript/TypeScript (package.json present)")
            if "react" in all_deps:
                technologies.add("React")
            if "next" in all_deps or "nextjs" in all_deps:
                technologies.add("Next.js")
            if "vue" in all_deps:
                technologies.add("Vue")
            if "svelte" in all_deps:
                technologies.add("Svelte")
            if "vite" in all_deps:
                technologies.add("Vite")

            for name in sorted(all_deps.keys())[:40]:
                technologies.add(f"npm package: {name}")
        except Exception as e:
            technologies.add(f"[WARN] Nu am putut analiza package.json: {e}")

    # Python stack
    requirements_path = os.path.join(local_path, "requirements.txt")
    if os.path.exists(requirements_path):
        technologies.add("Python (requirements.txt present)")
        try:
            with open(requirements_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    pkg_name = re.split(r"[<>=!~]", line)[0].strip()
                    if pkg_name:
                        technologies.add(f"pip package: {pkg_name}")
        except Exception as e:
            technologies.add(f"[WARN] Nu am putut analiza requirements.txt: {e}")

    # Go stack
    go_mod_path = os.path.join(local_path, "go.mod")
    if os.path.exists(go_mod_path):
        technologies.add("Go (go.mod present)")
        try:
            with open(go_mod_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("module "):
                        technologies.add(f"go module: {line.split(' ', 1)[1]}")
                    if line.startswith("require "):
                        require_part = line[len("require ") :].strip()
                        parts = require_part.split()
                        if parts:
                            technologies.add(f"go require: {parts[0]}")
        except Exception as e:
            technologies.add(f"[WARN] Nu am putut analiza go.mod: {e}")

    # Docker / docker-compose
    docker_compose_path = os.path.join(local_path, "docker-compose.yml")
    if os.path.exists(docker_compose_path):
        technologies.add("Docker Compose")
        try:
            with open(docker_compose_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("image:"):
                        image_name = line.split(":", 1)[1].strip()
                        technologies.add(f"Docker image: {image_name}")
        except Exception as e:
            technologies.add(f"[WARN] Nu am putut analiza docker-compose.yml: {e}")

    dockerfile_path = os.path.join(local_path, "Dockerfile")
    if os.path.exists(dockerfile_path):
        technologies.add("Dockerfile")

    return sorted(technologies)


def _extract_api_routes(local_path: str) -> List[str]:
    """
    Caută rute API în cod (FastAPI / router.*) și întoarce o listă textuală
    ușor de folosit în PROJ_SUMMARY.txt.
    """
    routes: List[str] = []
    route_patterns = [
        re.compile(r"@(app|router)\.(get|post|put|delete|patch)\((?P<quote>['\"])(?P<path>.+?)(?P=quote)"),
    ]

    for root, dirs, files in os.walk(local_path):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            if ext not in {".py", ".ts", ".tsx", ".js"}:
                continue

            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, local_path)

            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception:
                continue

            for pattern in route_patterns:
                for m in pattern.finditer(content):
                    method = m.group(2).upper()
                    path = m.group("path")
                    routes.append(f"{method} {path}  (file: {rel_path})")

    # Eliminăm duplicatele păstrând ordinea
    seen: Set[str] = set()
    unique_routes: List[str] = []
    for r in routes:
        if r not in seen:
            seen.add(r)
            unique_routes.append(r)

    return unique_routes


def _extract_interdependencies(local_path: str) -> List[str]:
    """
    Analizează importurile dintre fișiere pentru a construi o imagine a inter-dependențelor.
    Nu încearcă maparea perfectă la căi absolute, dar oferă o vedere utilă de ansamblu:
    - `file: X` importă module sau pachete `Y`.
    """
    edges: List[str] = []

    py_import_from = re.compile(r"^\\s*from\\s+([\\w\\.]+)\\s+import\\s+([\\w\\.,\\s*]+)")
    py_import = re.compile(r"^\\s*import\\s+([\\w\\.,\\s]+)")

    ts_import = re.compile(
        r"^\\s*import\\s+(?:[\\w\\*\\{\\},\\s]+\\s+from\\s+)?(?P<quote>['\\\"])(?P<module>.+?)(?P=quote)"
    )
    ts_require = re.compile(
        r"require\\((?P<quote>['\\\"])(?P<module>.+?)(?P=quote)\\)"
    )

    for root, dirs, files in os.walk(local_path):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            if ext not in {".py", ".ts", ".tsx", ".js"}:
                continue

            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, local_path)

            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
            except Exception:
                continue

            for line in lines:
                m_from = py_import_from.match(line)
                if m_from:
                    module = m_from.group(1)
                    targets = m_from.group(2).replace(" ", "")
                    edges.append(f"{rel_path}  ->  from {module} import {targets}")
                    continue

                m_imp = py_import.match(line)
                if m_imp:
                    modules = m_imp.group(1).replace(" ", "")
                    edges.append(f"{rel_path}  ->  import {modules}")
                    continue

                m_ts = ts_import.match(line)
                if m_ts:
                    module = m_ts.group("module")
                    edges.append(f"{rel_path}  ->  import from {module}")
                    continue

                m_req = ts_require.search(line)
                if m_req:
                    module = m_req.group("module")
                    edges.append(f"{rel_path}  ->  require({module})")

    # Eliminăm duplicatele păstrând ordinea
    seen: Set[str] = set()
    unique_edges: List[str] = []
    for e in edges:
        if e not in seen:
            seen.add(e)
            unique_edges.append(e)

    return unique_edges


def _build_project_summary_file(local_path: str, structure_file_path: str) -> str:
    """
    Construcție PROJ_SUMMARY.txt care combină:
    - arborele de directoare
    - tehnologiile detectate
    - rutele API detectate
    """
    # 1. Structura de directoare (folosim deja fișierul generat)
    try:
        with open(structure_file_path, "r", encoding="utf-8") as f:
            tree_content = f.read()
    except Exception:
        tree_content = "(nu am putut citi project_structure.txt)"

    # 2. Tehnologii
    technologies = _detect_technologies(local_path)

    # 3. Rute API
    api_routes = _extract_api_routes(local_path)

    # 4. Inter-dependențe între module/fisiere
    interdeps = _extract_interdependencies(local_path)

    lines: List[str] = []
    lines.append("=== PROJECT MAP / GLOBAL CONTEXT ===")
    lines.append("")
    lines.append("# 1. DIRECTORY TREE")
    lines.append("")
    lines.append(tree_content)
    lines.append("")
    lines.append("# 2. DETECTED TECHNOLOGIES")
    lines.append("")
    if technologies:
        for tech in technologies:
            lines.append(f"- {tech}")
    else:
        lines.append("- (Nicio tehnologie nu a putut fi detectată automat)")

    lines.append("")
    lines.append("# 3. API ROUTES")
    lines.append("")
    if api_routes:
        for route in api_routes:
            lines.append(f"- {route}")
    else:
        lines.append("- (Nu am putut detecta rute API după decoratori @app.* sau @router.*)")

    lines.append("")
    lines.append("# 4. INTERDEPENDENCIES (IMPORT GRAPH)")
    lines.append("")
    if interdeps:
        for edge in interdeps[:500]:
            # limităm la primele ~500 linii pentru a evita fișiere uriașe
            lines.append(f"- {edge}")
        if len(interdeps) > 500:
            lines.append(f"- ... și alte {len(interdeps) - 500} relații de import")
    else:
        lines.append("- (Nu am putut deduce inter-dependențe între fișiere pe baza importurilor)")

    content = "\n".join(lines)
    out_path = os.path.join(local_path, "PROJ_SUMMARY.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"🧭  Project Map global salvat la: {out_path}")
    return out_path


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

    # 3. Generăm fișierul de structură globală a proiectului
    structure_file_path = _build_project_structure_file(local_path)

    # 3.1. Generăm PROJ_SUMMARY.txt (Project Map / Global Context)
    project_summary_path = _build_project_summary_file(local_path, structure_file_path)

    # 4. Încărcăm fișierele Python cu parser de limbaj
    loader = GenericLoader.from_filesystem(
        local_path,
        glob="**/*",
        suffixes=[".py"],
        parser=LanguageParser(language=Language.PYTHON, parser_threshold=500)
    )
    documents = loader.load()

    # 5. Adăugăm manual documente pentru frontend & alte fișiere relevante
    extra_documents: list[Document] = []

    for root, dirs, files in os.walk(local_path):
        # Excludem directoarele mari / nerelevante
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

        for filename in files:
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, local_path)

            # Ignorăm fișierele din directoare excluse (de siguranță)
            if any(part in EXCLUDED_DIRS for part in rel_path.split(os.sep)):
                continue

            ext = os.path.splitext(filename)[1].lower()

            # Adăugăm project_structure.txt cu metadata clară
            if os.path.normpath(full_path) == os.path.normpath(structure_file_path):
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    extra_documents.append(
                        Document(
                            page_content=content,
                            metadata={"source": "Project Structure Map"}
                        )
                    )
                except Exception as e:
                    print(f"⚠️ Nu am putut citi project_structure.txt: {e}")
                continue

            # Selectăm fișiere frontend & config importante
            if ext in FRONTEND_EXTENSIONS:
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    extra_documents.append(
                        Document(
                            page_content=content,
                            metadata={"source": rel_path}
                        )
                    )
                except Exception as e:
                    print(f"⚠️ Nu am putut încărca fișierul {rel_path}: {e}")

    # 6. Adăugăm explicit PROJ_SUMMARY.txt ca Document cu metadata specială
    try:
        with open(project_summary_path, "r", encoding="utf-8") as f:
            summary_content = f.read()
        extra_documents.append(
            Document(
                page_content=summary_content,
                metadata={
                    "source": "PROJ_SUMMARY.txt",
                    "type": "global_context",
                },
            )
        )
        print("✅ PROJ_SUMMARY.txt adăugat la documentele pentru indexare (type=global_context).")
    except Exception as e:
        print(f"⚠️ Nu am putut citi PROJ_SUMMARY.txt: {e}")

    # 7. Combinăm documentele și filtrăm orice referință către directoare excluse
    all_documents = documents + extra_documents
    filtered_documents = [
        d
        for d in all_documents
        if not any(excl in d.metadata.get("source", "") for excl in EXCLUDED_DIRS)
    ]

    # 8. Spargem codul în bucățele (Code Splitting)
    # Important: folosește splitter-ul de limbaj ca să nu taie funcțiile la jumătate.
    # Folosim splitter-ul de Python și pentru alte fișiere – funcționează rezonabil pentru text generic.
    splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.PYTHON,
        chunk_size=2000,
        chunk_overlap=200
    )
    chunks = splitter.split_documents(filtered_documents)

    print(
        f"🧩 Rezultat: {len(chunks)} bucățele de cod gata pentru AI "
        f"(inclusiv Project Structure Map, PROJ_SUMMARY.txt și frontend)."
    )
    return chunks