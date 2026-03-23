from __future__ import annotations

#
# Optional: when FLOWCHART_ON_UPLOAD=true, PDFs whose name contains FLOWCHART_NAME_SUBSTRING
# (default: flowchart) trigger the external flowchart CLI to generate companion files and upload them
# in the same request (same dataset / folder as the PDF).
#
# Requires on the RAGFlow server host:
#   FLOWCHART_ROOT     — absolute path to the folder that contains cli.py (see ../flowchart in this repo)
#   POPPLER_PATH or FLOWCHART_POPPLER_PATH — Poppler bin dir (Windows/Linux)
#
import logging
import os
import subprocess
import sys
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional

from werkzeug.datastructures import FileStorage

from api.db import FileType
from api.utils.file_utils import filename_type

LOG = logging.getLogger(__name__)


def flowchart_companion_enabled() -> bool:
    return os.environ.get("FLOWCHART_ON_UPLOAD", "").strip().lower() in ("1", "true", "yes")


def should_run_flowchart_extraction(filename: str) -> bool:
    sub = os.environ.get("FLOWCHART_NAME_SUBSTRING", "flowchart").lower()
    return sub in filename.lower()


def upload_extras_enabled() -> bool:
    return os.environ.get("FLOWCHART_UPLOAD_EXTRAS", "true").strip().lower() in ("1", "true", "yes")


def _run_cli_and_collect_outputs(pdf_blob: bytes, stored_filename: str) -> Optional[Dict[str, bytes]]:
    root = os.environ.get("FLOWCHART_ROOT", "").strip()
    if not root:
        LOG.warning("FLOWCHART_ON_UPLOAD is enabled but FLOWCHART_ROOT is not set")
        return None
    root_p = Path(root)
    cli = root_p / "cli.py"
    if not cli.is_file():
        LOG.error("FLOWCHART_ROOT is invalid: missing cli.py at %s", cli)
        return None

    stem = Path(stored_filename).stem
    timeout = int(os.environ.get("FLOWCHART_SUBPROCESS_TIMEOUT", "900"))
    with tempfile.TemporaryDirectory(prefix="flowchart_rag_") as td:
        td_path = Path(td)
        pdf_path = td_path / Path(stored_filename).name
        pdf_path.write_bytes(pdf_blob)
        mmd = td_path / f"{stem}.mmd"
        env = os.environ.copy()
        env["PYTHONPATH"] = str(root_p)
        poppler = os.environ.get("FLOWCHART_POPPLER_PATH") or os.environ.get("POPPLER_PATH")
        if poppler:
            env["POPPLER_PATH"] = poppler
        cmd = [
            sys.executable,
            str(cli),
            str(pdf_path),
            "-o",
            str(mmd),
            "--json",
        ]
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(td_path),
                env=env,
                timeout=timeout,
                capture_output=True,
                text=True,
            )
        except subprocess.TimeoutExpired:
            LOG.error("flowchart cli timed out after %ss", timeout)
            return None
        except Exception:
            LOG.exception("flowchart cli failed to start")
            return None
        if proc.returncode != 0:
            LOG.error(
                "flowchart cli failed (exit %s): stdout=%s stderr=%s",
                proc.returncode,
                proc.stdout,
                proc.stderr,
            )
            return None

        out: Dict[str, bytes] = {}
        rag_path = td_path / f"{stem}_rag.md"
        if rag_path.is_file():
            out[f"{stem}_rag.md"] = rag_path.read_bytes()
        mmd_path = td_path / f"{stem}.mmd"
        if mmd_path.is_file():
            out[f"{stem}.mmd"] = mmd_path.read_bytes()
        graph_path = td_path / f"{stem}_graph.json"
        if graph_path.is_file():
            out[f"{stem}_graph.json"] = graph_path.read_bytes()

        if f"{stem}_rag.md" not in out:
            LOG.error("flowchart cli did not produce %s_rag.md", stem)
            return None

        if not upload_extras_enabled():
            return {f"{stem}_rag.md": out[f"{stem}_rag.md"]}
        return out


def _upload_companion_files(
    kb,
    user_id,
    parent_path: str,
    files_map: Dict[str, bytes],
    files_out: list,
) -> None:
    """Upload in order: *_rag.md, *.mmd, *_graph.json."""

    def _order_key(name: str) -> tuple:
        if name.endswith("_rag.md"):
            return (0, name)
        if name.endswith(".mmd"):
            return (1, name)
        if name.endswith("_graph.json"):
            return (2, name)
        return (3, name)

    order = sorted(files_map.keys(), key=_order_key)

    from api.db.services.file_service import FileService

    for name in order:
        data = files_map[name]
        fs = FileStorage(stream=BytesIO(data), filename=name, name="file")
        try:
            err, extra = FileService.upload_document(kb, [fs], user_id, parent_path=parent_path)
        except Exception:
            LOG.exception("Flowchart companion upload failed for %s", name)
            continue
        if err:
            LOG.warning("Flowchart companion upload %s: %s", name, err)
            continue
        for pair in extra:
            files_out.append(pair)
        LOG.info("Flowchart companion added: %s", name)


def maybe_append_flowchart_rag_document(kb, user_id, parent_path, stored_filename: str, pdf_blob: bytes, files_out: list) -> None:
    """
    Generate companion files from the PDF and upload as extra documents; append (doc_dict, blob) to files_out.
    Uses FileService.upload_document; failures are logged and do not fail the primary PDF upload.
    """
    if filename_type(stored_filename) != FileType.PDF.value:
        return

    if not should_run_flowchart_extraction(stored_filename):
        return

    if not flowchart_companion_enabled():
        LOG.info(
            "Flowchart PDF %r uploaded without automatic companions. "
            "To add *_rag.md, *.mmd, *_graph.json on upload, set FLOWCHART_ON_UPLOAD=true and "
            "FLOWCHART_ROOT to the folder containing flowchart/cli.py, then restart the API.",
            stored_filename,
        )
        return

    outputs = _run_cli_and_collect_outputs(pdf_blob, stored_filename)
    if not outputs:
        return

    _upload_companion_files(kb, user_id, parent_path, outputs, files_out)
