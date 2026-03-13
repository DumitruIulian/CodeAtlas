import json
import os
from datetime import datetime
from typing import Any, Dict, List


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

    entry = {
        "url": repo_url,
        "name": repo_name,
        "languages": sorted(set(languages)),
        "chunks": int(chunks_count),
        "last_indexed_at": iso_timestamp,
        "last_indexed_unix": unix_ts,
    }

    updated = False
    for idx, project in enumerate(projects):
        if project.get("url") == repo_url:
            projects[idx] = {**project, **entry}
            updated = True
            break

    if not updated:
        projects.append(entry)

    _write_projects(projects)


def get_projects() -> List[Dict[str, Any]]:
    """
    Returnează lista de proiecte indexate local, sortată descrescător după data ultimei indexări.
    """
    projects = _read_projects()
    projects.sort(key=lambda p: p.get("last_indexed_unix", 0), reverse=True)
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

