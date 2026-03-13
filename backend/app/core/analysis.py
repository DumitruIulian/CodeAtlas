"""
Generare analiză de arhitectură (Mermaid + hotspots) și verdict de sănătate pentru un proiect indexat.
Folosește PROJ_SUMMARY.txt din storage și Groq pentru diagramă + liste de hotspoturi.
"""
import json
import os
import re
from typing import Any, Dict, List, Tuple

from langchain_groq import ChatGroq

from app.core import history


def _project_storage_path(repo_url: str) -> str:
    slug = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    return os.path.join(history._get_storage_dir(), slug)


def _load_project_summary(project: Dict[str, Any]) -> str:
    """Încarcă conținutul PROJ_SUMMARY.txt din folderul de storage al proiectului."""
    path = _project_storage_path(project["url"])
    summary_path = os.path.join(path, "PROJ_SUMMARY.txt")
    if not os.path.exists(summary_path):
        return ""
    try:
        with open(summary_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def _strip_code_fences(text: str) -> str:
    """Elimină markdown code fences (```mermaid, ```json, etc.) din text."""
    if not text:
        return text
    t = text.strip()
    t = re.sub(r"^```\w*\s*\n?", "", t)
    t = re.sub(r"\n?```\s*$", "", t)
    return t.strip()


def _call_llm(prompt: str, system: str = "") -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return ""
    llm = ChatGroq(api_key=api_key, model="llama-3.3-70b-versatile", temperature=0.0)
    from langchain_core.messages import HumanMessage, SystemMessage
    messages = [SystemMessage(content=system), HumanMessage(content=prompt)] if system else [HumanMessage(content=prompt)]
    try:
        out = llm.invoke(messages)
        return getattr(out, "content", str(out)) or ""
    except Exception:
        return ""


def _parse_hotspots_from_response(response: str) -> List[Dict[str, Any]]:
    """Extrage o listă de hotspoturi din răspunsul LLM (JSON sau listă în text)."""
    response = _strip_code_fences(response.strip())
    # Încearcă bloc JSON
    match = re.search(r"\[[\s\S]*\]", response)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, list):
                return [h if isinstance(h, dict) else {"type": str(h), "file": "", "reason": ""} for h in data]
        except json.JSONDecodeError:
            pass
    # Fallback: câteva linii tip "Type: X, File: Y, Reason: Z"
    hotspots = []
    for line in response.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        part = {"type": "Complexity", "file": "", "reason": line}
        if "type" in line.lower():
            for seg in line.split(","):
                k, _, v = seg.partition(":")
                k, v = k.strip().lower(), v.strip()
                if k == "type":
                    part["type"] = v
                elif k == "file":
                    part["file"] = v
                elif k == "reason":
                    part["reason"] = v
        hotspots.append(part)
    return hotspots


def generate_analysis_for_project(project: Dict[str, Any]) -> Tuple[str, List[Dict[str, Any]], str]:
    """
    Generează diagramă Mermaid + listă de hotspoturi pentru proiect, pe baza PROJ_SUMMARY.txt.
    Returnează (mermaid_diagram, hotspots, health_status).
    """
    summary = _load_project_summary(project)
    if not summary:
        return "", [], "Ready for Audit"

    # 1) Mermaid
    mermaid_prompt = (
        "Based on the following PROJECT MAP / GLOBAL CONTEXT, generate a single Mermaid diagram "
        "that shows the high-level architecture: main modules, layers (e.g. frontend, backend, database), "
        "and key dependencies. Output ONLY the Mermaid code, no explanation.\n\n"
        "CONTEXT:\n" + summary[:12000]
    )
    mermaid_raw = _call_llm(
        mermaid_prompt,
        system="You are an expert software architect. Reply only with valid Mermaid diagram code, no markdown fences."
    )
    mermaid = _strip_code_fences(mermaid_raw).strip() if mermaid_raw else ""

    # 2) Hotspots (tipuri: Security, Bug, Risk, Debt, Complexity, Clean)
    hotspots_prompt = (
        "Based on the following PROJECT MAP, list up to 10 code/architecture hotspots. "
        "For each hotspot output: type (exactly one of: Security, Bug, Risk, Debt, Complexity, Clean), "
        "file (path if relevant), reason (short). "
        "Reply with a JSON array only, e.g. [{\"type\":\"Security\",\"file\":\"api/auth.py\",\"reason\":\"...\"}].\n\n"
        "CONTEXT:\n" + summary[:10000]
    )
    hotspots_raw = _call_llm(
        hotspots_prompt,
        system="You output only a valid JSON array of objects with keys: type, file, reason. No other text."
    )
    hotspots = _parse_hotspots_from_response(hotspots_raw or "[]")
    health_status = history.compute_health_from_hotspots(hotspots)

    return mermaid, hotspots, health_status
