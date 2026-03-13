import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional


def _get_base_dir() -> str:
    # Mergem din folderul 'core' până în rădăcina proiectului
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


def _get_history_path() -> str:
    base_dir = _get_base_dir()
    data_dir = os.path.join(base_dir, "backend", "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "projects.json")


def _read_projects() -> List[Dict[str, Any]]:
    path = _get_history_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except Exception:
        # Dacă fișierul e corupt, îl ignorăm pentru a nu bloca aplicația
        return []


def _write_projects(projects: List[Dict[str, Any]]) -> None:
    path = _get_history_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(projects, f, ensure_ascii=False, indent=2)


def add_or_update_project(
    repo_url: str,
    repo_name: str,
    languages: list[str],
    chunks_count: int,
) -> None:
    """
    Adaugă sau actualizează un proiect în istoricul local.
    Structură proiect:
    - url, name, languages, chunks, last_indexed_at (ISO), last_indexed_unix (sec).
    """
    projects = _read_projects()
    now = datetime.utcnow()
    iso_timestamp = now.isoformat(timespec="seconds") + "Z"
    unix_ts = int(now.timestamp())

    # Căutăm proiectul existent (dacă există) pentru a păstra eventualul health_status
    existing: Optional[Dict[str, Any]] = None
    for p in projects:
        if p.get("url") == repo_url:
            existing = p
            break

    entry = {
        "url": repo_url,
        "name": repo_name,
        "languages": sorted(set(languages)),
        "chunks": int(chunks_count),
        "last_indexed_at": iso_timestamp,
        "last_indexed_unix": unix_ts,
    }

    # Status inițial de sănătate: dacă există deja unul, îl păstrăm, altfel marcăm ca "Ready for Audit"
    if existing and "health_status" in existing:
        entry["health_status"] = existing["health_status"]
    else:
        entry["health_status"] = "Ready for Audit"

    updated = False
    for idx, project in enumerate(projects):
        if project.get("url") == repo_url:
            projects[idx] = {**project, **entry}
            updated = True
            break

    if not updated:
        projects.append(entry)

    _write_projects(projects)


def compute_health_from_hotspots(hotspots: List[Dict[str, Any]]) -> str:
    """
    Derivează un verdict de sănătate din lista de hotspots (tipuri: Security, Bug, Risk, Debt, Complexity, Clean).
    """
    if not hotspots:
        return "Clean Architecture"
    types_seen = set()
    for h in hotspots:
        t = (h.get("type") or h.get("category") or "").strip().lower()
        if t:
            types_seen.add(t)
    if any(x in types_seen for x in ("security", "bug", "risk")):
        return "Security / Bug Risk"
    if any(x in types_seen for x in ("debt", "complexity")):
        return "Technical Debt / Complexity"
    return "Clean Architecture"


def save_project_analysis(
    repo_url: str,
    mermaid: str,
    hotspots: List[Dict[str, Any]],
    health_status: str,
) -> None:
    """
    Salvează rezultatul analizei (mermaid, hotspots, health_status) în projects.json pentru proiectul dat.
    """
    projects = _read_projects()
    for p in projects:
        if p.get("url") == repo_url:
            p["analysis_mermaid"] = mermaid
            p["analysis_hotspots"] = hotspots
            p["health_status"] = health_status
            break
    _write_projects(projects)


def _project_storage_path(repo_url: str) -> str:
    """Calea către folderul storage al proiectului (storage/<repo_slug>)."""
    slug = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    return os.path.join(_get_storage_dir(), slug)


def get_projects() -> List[Dict[str, Any]]:
    """
    Returnează lista de proiecte indexate local, sortată descrescător după data ultimei indexări.
    Dacă un proiect are status "Ready for Audit" dar are deja analysis_hotspots salvate,
    recalculează health_status din hotspots.
    """
    projects = _read_projects()
    for p in projects:
        if not p.get("health_status"):
            p["health_status"] = "Pending Audit"
        # Dynamic recovery: dacă e "Ready for Audit" dar avem hotspoturi salvate, derivăm verdictul
        if p.get("health_status") == "Ready for Audit" and p.get("analysis_hotspots"):
            p["health_status"] = compute_health_from_hotspots(p["analysis_hotspots"])
        # Opțional: dacă există PROJ_SUMMARY.txt dar nu avem hotspots, păstrăm "Ready for Audit"
    projects.sort(key=lambda x: x.get("last_indexed_unix", 0), reverse=True)
    return projects


def _get_storage_dir() -> str:
    base_dir = _get_base_dir()
    return os.path.join(base_dir, "storage")


def _compute_storage_usage_bytes() -> int:
    storage_dir = _get_storage_dir()
    if not os.path.exists(storage_dir):
        return 0

    total_bytes = 0
    for root, _, files in os.walk(storage_dir):
        for filename in files:
            full_path = os.path.join(root, filename)
            try:
                total_bytes += os.path.getsize(full_path)
            except OSError:
                continue
    return total_bytes


def get_stats() -> Dict[str, Any]:
    """
    Calculează statistici globale:
    - total_repos
    - total_chunks
    - storage_bytes (dimensiunea folderului storage/)
    - api_calls (placeholder, momentan 0)
    """
    projects = _read_projects()
    total_repos = len(projects)
    total_chunks = sum(int(p.get("chunks", 0)) for p in projects)
    storage_bytes = _compute_storage_usage_bytes()

    return {
        "total_repos": total_repos,
        "total_chunks": total_chunks,
        "storage_bytes": storage_bytes,
        "api_calls": 0,
    }


def get_project_by_id(repo_id: str) -> Optional[Dict[str, Any]]:
    """
    Găsește un proiect după identificator:
    - întâi potrivire exactă pe name
    - apoi potrivire exactă pe url
    """
    projects = _read_projects()
    for p in projects:
        if p.get("name") == repo_id:
            return p
    for p in projects:
        if p.get("url") == repo_id:
            return p
    return None


def reset_projects() -> None:
    """
    Golește istoricul proiectelor (projects.json devine un array gol).
    """
    _write_projects([])

