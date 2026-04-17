# 06 — Custom Work vs. Base / Upstream System

The single most important question for a viva/handover: *what did you
actually build, and what did you inherit?* This document answers that with
files, line counts, and provenance evidence.

---

## A. Base / Upstream / Imported components

### A.1 RAGFlow (`ragflow/`)

- **Upstream**: `github.com/infiniflow/ragflow`.
- **License**: Apache-2.0 (`ragflow/LICENSE`).
- **Version**: `0.24.0` (`ragflow/pyproject.toml` line 3).
- **Evidence of provenance**: `ragflow/README.md` line 1–40 (InfiniFlow
  branding, Docker Hub badge pointing at
  `infiniflow/ragflow:v0.24.0`); `ragflow/CLAUDE.md` describing the
  project's upstream architecture; unchanged multi-language README files.
- **Modification status**: **essentially untouched**, with two explicit
  exceptions identified below. No other drift from upstream has been
  verified — this is **UNKNOWN / NEEDS MANUAL INPUT** without a diff
  against the pristine `v0.24.0` tag.

What RAGFlow provides:

- Knowledge-base / dataset management (`ragflow/api/apps/kb_app.py`).
- Document upload and parsing orchestration
  (`ragflow/api/apps/document_app.py`,
  `ragflow/api/db/services/file_service.py`).
- Built-in PDF parsers including the MinerU remote adapter
  (`ragflow/deepdoc/parser/mineru_parser.py`).
- Chunking strategies (`ragflow/rag/app/*.py`).
- Embedding and LLM adapters (`ragflow/rag/llm/*.py`).
- Retrieval + reranking + chat (`ragflow/rag/nlp`, `ragflow/api/apps/dialog_app.py`).
- React/UmiJS frontend (`ragflow/web/`).
- Deployment manifests: `ragflow/docker/`, `ragflow/helm/`.

### A.2 MinerU (`MinerU/`)

- **Upstream**: `github.com/opendatalab/MinerU`.
- **License**: **AGPL-3.0** (`MinerU/pyproject.toml` line 8). This is a
  copyleft licence with network-provision obligations — flag this for the
  legal review.
- **Version**: pulled at build time via
  `pip install "mineru[api,pipeline,vlm]>=2.6.3,<3"`
  (`MinerU/docker/Dockerfile.api-cpu` line 19).
- **Modification status**: **one file modified**. The Dockerfiles COPY a
  local `MinerU/mineru/backend/vlm/vlm_analyze.py` over the pip-installed
  file inside the container (`Dockerfile.api-cpu` line 21,
  `Dockerfile.api-gpu` line 27). The GPU Dockerfile comments this as a
  fix for a HuggingFace snapshot-path validator.
- Everything else (`MinerU/mineru/**` except that file) is effectively a
  convenient vendor copy for diffing and is not actually used — the
  container installs MinerU from pip.

What MinerU provides:

- PDF → markdown conversion with multiple backends.
- FastAPI server exposing `POST /file_parse` and `GET /openapi.json`
  (`MinerU/mineru/cli/fast_api.py` line 125).
- Weight management + `mineru-models-download` CLI.

---

## B. Custom / Modified / Project-specific Work

The table below maps every custom file in the repository. Line counts are
from `wc -l`.

| Path | LOC | Role | Evidence |
|------|----:|------|----------|
| `flowchart/cli.py` | 132 | Argparse entry. Defines `process_pdf()` used by the CLI and the hook. | Full file read. |
| `flowchart/flowchart/__init__.py` | 10 | Package manifest. | Full file read. |
| `flowchart/flowchart/pdf_converter.py` | 91 | Poppler resolution + `pdf_to_images`. | Full file read. |
| `flowchart/flowchart/preprocess.py` | 50 | Grayscale / threshold / `mask_shapes`. | Full file read. |
| `flowchart/flowchart/shapes.py` | 50 | OpenCV contour shape detection → `process` / `decision`. | Full file read. |
| `flowchart/flowchart/ocr.py` | 25 | EasyOCR per-node crop. | Full file read. |
| `flowchart/flowchart/lines.py` | 253 | Skeletonise, simplify, arrow-direction heuristic, debug image. | Full file read. |
| `flowchart/flowchart/graph_builder.py` | 54 | `networkx.DiGraph` + cycle-reduction pass. | Full file read. |
| `flowchart/flowchart/exporter.py` | 119 | Export Mermaid / `*_rag.md` / `*_graph.json`. | Full file read. |
| `flowchart/ragflow_ingest.py` | 359 | Watch dir, run CLI, POST to RAGFlow API, start parse. | Full file read. |
| `flowchart/run_comparison.py` | 141 | Visual debug overlay renderer. | Full file read. |
| `flowchart/requirements.txt` | 7 | Deps for the custom module. | Full file read. |
| `flowchart/README.md`, `INTEGRATION.md`, `ORIGINAL_STACK_SETUP.md` | — | Project documentation. | Full files read. |
| `flowchart/flowchart.json`, `flowchart.mmd` | — | **Sample** outputs committed for reference. | `INTEGRATION.md` line 65 ("Legacy `flowchart.json` in this repo is a **sample**"). |
| `ragflow/api/utils/flowchart_on_upload.py` | 180 | **Glue**: invokes the flowchart CLI from inside RAGFlow and uploads companions. | Full file read. |
| `ragflow/api/db/services/file_service.py` | +7 (within a 717-line file) | **Glue patch**: calls the hook after PDF upload. | Lines 515–522. |
| `ragflow/docker/docker-compose.flowchart.yml` | 31 | **Glue**: overlay compose file to mount the hook + tools when deploying from `ragflow/docker/`. | Full file read. |
| `docker-compose.yml` (repo root) | 71 | **Glue**: top-level stack with MinerU service + the three bind mounts into ragflow. | Full file read. |
| `docker-compose.mineru-gpu.yml` | 17 | **Glue**: GPU MinerU overlay. | Full file read. |
| `start-ragflow-mineru.ps1` | 33 | Windows launcher. | Full file read. |
| `MinerU/docker/Dockerfile.api-cpu` | 33 | Project-specific build recipe. Not present upstream in identical form. | Full file read. |
| `MinerU/docker/Dockerfile.api-gpu` | 40 | Project-specific GPU build recipe. | Full file read. |
| `MinerU/docker-compose.yml` | 20 | Standalone compose for MinerU alone. | Full file read. |
| `MinerU/mineru/backend/vlm/vlm_analyze.py` | — | **Modified copy** of an upstream file; COPY-ed over the pip-installed one in the Dockerfile. | `Dockerfile.api-gpu` line 27 comment. |
| `vit-test/README.md`, `TESTING.md`, `benchmark_queries.yaml` | 5 + 140 + 43 | Test corpus docs. | Full files read. |
| `vit-test/*.pdf`, `*.mmd`, `*_rag.md`, `*_graph.json` | — | Sample inputs + reference outputs. | Directory listing. |

**Total custom/modified Python (excluding vendored file copies): ~1,490
lines** across 14 files, plus the ~7-line patch in `file_service.py`.

---

### B.1 Custom piece: `flowchart/` package

**What was built**

- A **classical-CV flowchart parser** that does not depend on any neural
  model for layout / shape detection. The only learning component is
  EasyOCR for text.
- A CLI (`cli.py`) that writes three artefact types.
- A **RAG-friendly markdown format** (`*_rag.md`) that expresses graph
  facts as English sentences — specifically designed to be chunked well
  by RAGFlow's default chunker and retrieved on natural-language queries.
- A watchdog-free batch uploader (`ragflow_ingest.py`) that uses only
  `requests`.

**What problem it solves**

See §2 of `01_PROJECT_HANDOVER_OVERVIEW.md`. In short: MinerU outputs the
*text* around a flowchart (caption etc.) but the flowchart itself
remains an opaque image. The custom module transforms that image into
node/edge text chunks that MinerU's output does not contain.

**Files that contain the work** — see Table B above.

**Integration**

Three modes, all routing through `process_pdf()`:

1. Direct CLI.
2. In-process subprocess from the RAGFlow API (`flowchart_on_upload.py`
   lines 73–82 spawn `sys.executable cli.py ...`).
3. Out-of-process batch uploader (`ragflow_ingest.py` imports
   `process_pdf` dynamically via `importlib.util`).

---

### B.2 Custom piece: `ragflow/api/utils/flowchart_on_upload.py`

**What was built**: a 180-line module inside RAGFlow's own package that:

1. Decides whether a PDF upload qualifies for companion generation
   (`flowchart_companion_enabled`, `should_run_flowchart_extraction`,
   `upload_extras_enabled`).
2. Runs the CLI in a temp directory with `PYTHONPATH` set to
   `FLOWCHART_ROOT`.
3. Collects the three output files.
4. Uploads them via RAGFlow's own `FileService.upload_document` back into
   the same knowledge base / folder.
5. Appends every upload result to the `files` list that the primary
   upload endpoint returns, so the UI sees them immediately.

**Problem it solves**: keep the companion upload **atomic** with the
primary PDF upload, so Parse-on-creation runs for all artefacts from a
single UI action.

**Integration**: called from `FileService.upload_document` in
`ragflow/api/db/services/file_service.py` lines 515–522 — the only other
custom change inside RAGFlow.

---

### B.3 Custom piece: the 7-line patch in `file_service.py`

```515:522:ragflow/api/db/services/file_service.py
                try:
                    from api.utils.flowchart_on_upload import maybe_append_flowchart_rag_document

                    maybe_append_flowchart_rag_document(
                        kb, user_id, safe_parent_path, filename, blob, files
                    )
                except Exception:
                    logging.exception("Flowchart companion on upload failed")
```

Deliberately tiny: fenced by `try/except` so any bug in the hook cannot
fail the primary PDF upload. This file is otherwise untouched upstream
RAGFlow code (717 LOC total).

---

### B.4 Custom piece: top-level Docker orchestration

`docker-compose.yml` (repo root) is the **single assembly point**:

- `include:` pulls in `ragflow/docker/docker-compose.yml` so all base
  services (ES/Infinity/..., MySQL, MinIO, Redis, `ragflow-cpu`,
  `ragflow-gpu`) are available.
- Adds a new `mineru-api` service backed by `./MinerU/docker/Dockerfile.api-cpu`.
- Patches `ragflow-cpu` / `ragflow-gpu` to:
  - depend on `mineru-api`.
  - set `MINERU_APISERVER=http://mineru-api:8000`.
  - bind-mount `./flowchart` and the two patched files read-only.

This compose file plus its PowerShell wrapper is the "glue" that turns
three separate projects into one stack.

---

### B.5 Custom piece: MinerU Dockerfiles

`MinerU/docker/Dockerfile.api-cpu` and `Dockerfile.api-gpu` are
project-specific. They are not part of upstream MinerU's release tooling
— they:

- Start from `python:3.12-bookworm` (CPU) or add CUDA wheels for GPU.
- Pip-install `mineru[api,pipeline,vlm]>=2.6.3,<3`.
- Pre-download model weights at build time so the resulting image is
  self-contained (`MINERU_MODEL_SOURCE=local`).
- COPY the locally modified `vlm_analyze.py` into site-packages to patch
  a runtime bug.

---

### B.6 Custom piece: `vit-test/`

Pure content folder:

- Input PDFs (including three whose filename matches the
  `FLOWCHART_NAME_SUBSTRING=flowchart` rule).
- Pre-generated reference outputs for visual diffing.
- `benchmark_queries.yaml` — a qualitative evaluation template.
- `README.md` / `TESTING.md` — end-to-end procedure docs.

This is the closest thing the repo has to a test suite.

---

## C. Upstream components: per-file modification status

| Upstream file | Modified? | How to tell |
|---------------|-----------|-------------|
| `ragflow/api/db/services/file_service.py` | **Yes** (7-line addition) | Diff to pristine `v0.24.0` would show the try-block import of `maybe_append_flowchart_rag_document`. |
| `ragflow/api/utils/flowchart_on_upload.py` | **New file, not in upstream** | No equivalent exists in upstream; confirmed by its dependency on this repo's `flowchart/` tree. |
| `ragflow/docker/docker-compose.flowchart.yml` | **New file, not in upstream** | Header comment refers to paths relative to this specific repo layout. |
| Everything else under `ragflow/` | **Presumed unchanged** — UNKNOWN without an automated diff. | Not verified file-by-file. |
| `MinerU/mineru/backend/vlm/vlm_analyze.py` | **Modified** | The Dockerfiles COPY over the pip-installed version. |
| Everything else under `MinerU/` | **Presumed unchanged** | Not verified; note that the Dockerfiles don't actually install MinerU from this tree — they pip-install it — so only `vlm_analyze.py` is actually used. |

> Recommendation (for the reviewer): run
> `git diff <pristine-v0.24.0>..HEAD -- ragflow/` to confirm no other
> unintentional drift in the RAGFlow tree. This is the only reliable way
> to bound the modification surface. Marked **UNKNOWN / NEEDS MANUAL
> INPUT**.

---

## D. Why the split into these pieces

- **RAGFlow** provides a mature UI, chunking, retrieval, chat, MinIO/MySQL
  wiring, and an agent/workflow builder. Reimplementing any of this would
  be months of work.
- **MinerU** provides high-quality PDF-to-markdown including tables and
  formulas. RAGFlow ships an adapter for it out of the box
  (`deepdoc/parser/mineru_parser.py`), so wiring is already available.
- **Flowchart** is the novel bit: neither RAGFlow nor MinerU produces
  structured node/edge text for diagrammatic content. This is where the
  project's intellectual contribution lives.

---

## E. Evidence index (quick-look)

| Claim | File | Lines |
|-------|------|-------|
| RAGFlow version 0.24.0 | `ragflow/pyproject.toml` | 3 |
| MinerU AGPL-3.0 | `MinerU/pyproject.toml` | 8 |
| MinerU installed from pip, not vendored tree | `MinerU/docker/Dockerfile.api-cpu` | 18–19 |
| MinerU `vlm_analyze.py` patched | `MinerU/docker/Dockerfile.api-cpu` | 21; `Dockerfile.api-gpu` 27 |
| Flowchart subprocess invocation | `ragflow/api/utils/flowchart_on_upload.py` | 65–95 |
| 7-line patch in RAGFlow | `ragflow/api/db/services/file_service.py` | 515–522 |
| Top-level bind mounts | `docker-compose.yml` | 54–71 |
| Optional ragflow-only overlay | `ragflow/docker/docker-compose.flowchart.yml` | 20–31 |
| Sample artefacts | `vit-test/Cooler_pipe_flowchart_rag.md`, `Hose_flowchart_rag.md`, `test_rag.md`, `test_graph.json` | — |
