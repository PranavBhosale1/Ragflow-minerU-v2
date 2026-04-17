"""
Watch a folder for PDFs whose names contain a marker (default: 'flowchart'),
run the local extractor, then upload RAG artifacts to a RAGFlow dataset and start parsing.

Requires: requests (see requirements.txt). Optional: watchdog for efficient --watch.

Environment (optional):
  RAGFLOW_BASE_URL   e.g. http://127.0.0.1:9380
  RAGFLOW_API_KEY
  RAGFLOW_DATASET_ID
  POPPLER_PATH       Poppler bin directory (Windows)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

_PKG_ROOT = Path(__file__).resolve().parent
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

try:
    import requests
except ImportError as e:
    raise SystemExit("Install requests: pip install requests") from e


def _load_process_pdf():
    import importlib.util

    cli_path = _PKG_ROOT / "cli.py"
    spec = importlib.util.spec_from_file_location("flowchart_cli_standalone", cli_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {cli_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.process_pdf


process_pdf = _load_process_pdf()

LOG = logging.getLogger("ragflow_ingest")

DEFAULT_NAME_SUBSTRING = "flowchart"
STATE_FILENAME = ".flowchart_ragflow_state.json"


def _api_url(base: str, path: str) -> str:
    base = base.rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    return base + path


def _check_api_response(data: Dict[str, Any]) -> None:
    code = data.get("code")
    if code not in (0, None):
        raise RuntimeError(data.get("message") or str(data))


def upload_document(base_url: str, api_key: str, dataset_id: str, file_path: Path) -> str:
    url = _api_url(base_url, f"/api/v1/datasets/{dataset_id}/documents")
    headers = {"Authorization": f"Bearer {api_key}"}
    with open(file_path, "rb") as f:
        files = {"file": (file_path.name, f)}
        r = requests.post(url, headers=headers, files=files, timeout=600)
    r.raise_for_status()
    data = r.json()
    _check_api_response(data)
    rows = data.get("data") or []
    if not rows:
        raise RuntimeError(f"Upload returned no documents: {data}")
    doc_id = rows[0].get("id")
    if not doc_id:
        raise RuntimeError(f"Upload response missing id: {data}")
    return doc_id


def start_parse(base_url: str, api_key: str, dataset_id: str, document_ids: List[str]) -> None:
    if not document_ids:
        return
    url = _api_url(base_url, f"/api/v1/datasets/{dataset_id}/chunks")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    r = requests.post(
        url,
        headers=headers,
        json={"document_ids": document_ids},
        timeout=120,
    )
    r.raise_for_status()
    data = r.json()
    _check_api_response(data)


def load_state(state_path: Path) -> Dict[str, Any]:
    if not state_path.exists():
        return {}
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_state(state_path: Path, state: Dict[str, Any]) -> None:
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def _mtime_key(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def collect_pdf_candidates(watch_dir: Path, name_substring: str) -> List[Path]:
    sub = name_substring.lower()
    out: List[Path] = []
    for p in watch_dir.rglob("*.pdf"):
        if sub in p.name.lower():
            out.append(p)
    return sorted(out)


def run_pipeline(
    pdf_path: Path,
    out_dir: Path,
    poppler_path: Optional[str],
    emit_json: bool,
) -> Dict[str, Path]:
    """Run extractor; return paths keyed as rag, mmd, graph (if any)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = pdf_path.stem
    mmd_path = out_dir / f"{stem}.mmd"
    process_pdf(
        str(pdf_path),
        str(mmd_path),
        poppler_path,
        emit_rag_text=True,
        rag_out=None,
        emit_json=emit_json,
        json_out=None,
    )
    result: Dict[str, Path] = {
        "mmd": mmd_path,
        "rag": out_dir / f"{stem}_rag.md",
    }
    if emit_json:
        result["graph"] = out_dir / f"{stem}_graph.json"
    return result


def process_one_pdf(
    pdf_path: Path,
    out_dir: Path,
    base_url: str,
    api_key: str,
    dataset_id: str,
    poppler_path: Optional[str],
    include_extras: bool,
    parse_uploads: bool,
    state: Dict[str, Any],
    force: bool,
    upload: bool = True,
) -> None:
    key = str(pdf_path.resolve())
    mt = _mtime_key(pdf_path)
    prev = state.get(key)
    if isinstance(prev, dict) and prev.get("mtime") == mt and prev.get("ok") and not force:
        LOG.info("Skip (unchanged): %s", pdf_path)
        return

    LOG.info("Extract flowchart: %s", pdf_path)
    artifacts = run_pipeline(
        pdf_path,
        out_dir=out_dir,
        poppler_path=poppler_path,
        emit_json=include_extras,
    )

    upload_ids: List[str] = []
    rag_path = artifacts["rag"]
    if not rag_path.exists():
        raise FileNotFoundError(rag_path)

    if not upload:
        LOG.info("Extract-only: wrote %s (and related outputs)", rag_path)
        state[key] = {"mtime": mt, "ok": True, "uploaded_doc_ids": []}
        return

    LOG.info("Upload RAG layer: %s", rag_path)
    upload_ids.append(upload_document(base_url, api_key, dataset_id, rag_path))

    if include_extras:
        for label in ("mmd", "graph"):
            p = artifacts.get(label)
            if p and p.exists():
                LOG.info("Upload %s: %s", label, p)
                upload_ids.append(upload_document(base_url, api_key, dataset_id, p))

    if parse_uploads and upload_ids:
        LOG.info("Start parsing for %d document(s)", len(upload_ids))
        start_parse(base_url, api_key, dataset_id, upload_ids)

    state[key] = {"mtime": mt, "ok": True, "uploaded_doc_ids": upload_ids}
    LOG.info("Done: %s", pdf_path)


def scan_loop(
    watch_dir: Path,
    out_dir: Path,
    name_substring: str,
    interval: float,
    state_path: Path,
    **kwargs: Any,
) -> None:
    state = load_state(state_path)
    seen: Set[str] = set()
    while True:
        try:
            for pdf in collect_pdf_candidates(watch_dir, name_substring):
                sk = str(pdf.resolve())
                process_one_pdf(
                    pdf,
                    out_dir=out_dir,
                    state=state,
                    **kwargs,
                )
                save_state(state_path, state)
                seen.add(sk)
        except Exception as e:
            LOG.exception("Scan loop error: %s", e)
        time.sleep(interval)


def main(argv: Optional[List[str]] = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    p = argparse.ArgumentParser(description="Flowchart extract + RAGFlow upload")
    p.add_argument(
        "--watch",
        type=Path,
        required=True,
        help="Directory to scan for *flowchart*.pdf (recursive)",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory for .mmd / _rag.md (default: same as --watch)",
    )
    p.add_argument(
        "--name-substring",
        default=os.environ.get("FLOWCHART_NAME_SUBSTRING", DEFAULT_NAME_SUBSTRING),
        help=f"Process PDFs whose name contains this (default: {DEFAULT_NAME_SUBSTRING!r})",
    )
    p.add_argument("--base-url", default=os.environ.get("RAGFLOW_BASE_URL", "http://127.0.0.1:9380"))
    p.add_argument("--api-key", default=os.environ.get("RAGFLOW_API_KEY", ""))
    p.add_argument("--dataset-id", default=os.environ.get("RAGFLOW_DATASET_ID", ""))
    p.add_argument("--poppler-path", default=os.environ.get("POPPLER_PATH"))
    p.add_argument(
        "--include-extras",
        action="store_true",
        help="Also upload .mmd and _graph.json (in addition to _rag.md)",
    )
    p.add_argument(
        "--no-parse",
        action="store_true",
        help="Upload only; do not call POST .../chunks to start parsing",
    )
    p.add_argument("--force", action="store_true", help="Reprocess even if mtime unchanged")
    p.add_argument(
        "--interval",
        type=float,
        default=30.0,
        help="Polling interval seconds when using --loop (default: 30)",
    )
    p.add_argument(
        "--loop",
        action="store_true",
        help="Keep scanning --watch every --interval (simple polling)",
    )
    p.add_argument(
        "--state-file",
        type=Path,
        default=None,
        help=f"Path to JSON state file (default: <watch>/{STATE_FILENAME})",
    )
    p.add_argument(
        "--extract-only",
        action="store_true",
        help="Only run local extraction; do not call RAGFlow (no API key needed)",
    )
    args = p.parse_args(argv)

    if not args.extract_only and (not args.api_key or not args.dataset_id):
        LOG.error("Set --api-key and --dataset-id (or RAGFLOW_API_KEY / RAGFLOW_DATASET_ID), or use --extract-only.")
        return 2

    watch_dir = args.watch.resolve()
    if not watch_dir.is_dir():
        LOG.error("Not a directory: %s", watch_dir)
        return 2

    out_dir = (args.out or watch_dir).resolve()
    state_path = args.state_file or (watch_dir / STATE_FILENAME)

    kwargs = dict(
        base_url=args.base_url.rstrip("/"),
        api_key=args.api_key,
        dataset_id=args.dataset_id,
        poppler_path=args.poppler_path,
        include_extras=args.include_extras,
        parse_uploads=not args.no_parse,
        force=args.force,
        upload=not args.extract_only,
    )

    if args.loop:
        LOG.info("Polling %s every %ss; press Ctrl+C to stop", watch_dir, args.interval)
        try:
            scan_loop(
                watch_dir=watch_dir,
                out_dir=out_dir,
                name_substring=args.name_substring,
                interval=args.interval,
                state_path=state_path,
                **kwargs,
            )
        except KeyboardInterrupt:
            LOG.info("Stopped.")
        return 0

    state = load_state(state_path)
    n = 0
    for pdf in collect_pdf_candidates(watch_dir, args.name_substring):
        process_one_pdf(pdf, out_dir=out_dir, state=state, **kwargs)
        save_state(state_path, state)
        n += 1
    if n == 0:
        LOG.warning("No PDFs matching %r under %s", args.name_substring, watch_dir)
    else:
        LOG.info("Processed %d PDF(s).", n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
