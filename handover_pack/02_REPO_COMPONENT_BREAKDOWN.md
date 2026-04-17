# 02 — Repo / Component Breakdown

Every folder in the repository, mapped to role, origin, inputs, outputs,
and integration points.

Legend:
- **Upstream** = vendored from a public open-source project, essentially
  untouched.
- **Upstream + modified** = vendored but edited for this project.
- **Custom** = authored for this project.
- **Glue** = small integration file authored for this project, sitting
  inside an upstream tree.

---

## A. Top-level files

| File | Origin | Purpose | Evidence |
|------|--------|---------|----------|
| [`docker-compose.yml`](../docker-compose.yml) | Custom | Orchestrator. Includes `ragflow/docker/docker-compose.yml`, adds the `mineru-api` service, patches `ragflow-cpu` / `ragflow-gpu` with bind mounts for the flowchart tools + two patched Python files. | Comments in lines 1–14, services lines 22–71. |
| [`docker-compose.mineru-gpu.yml`](../docker-compose.mineru-gpu.yml) | Custom | Optional overlay: switches MinerU to the CUDA Dockerfile with `gpus: all`. | Lines 1–17. |
| [`start-ragflow-mineru.ps1`](../start-ragflow-mineru.ps1) | Custom | Windows PowerShell launcher that loads `ragflow/docker/.env` and optionally merges the GPU overlay. | Lines 9–33. |
| [`.gitignore`](../.gitignore) | Custom | Declares local/ignored content including `vit-test/.flowchart_ragflow_state.json` (state file for `ragflow_ingest.py`) and a `Doc to be sent to VIT/` directory. | Lines 2, 23. |

No root `README.md` exists. The closest “project front page” is
[`flowchart/ORIGINAL_STACK_SETUP.md`](../flowchart/ORIGINAL_STACK_SETUP.md).

---

## B. `ragflow/` — Main application platform

### Role
RAGFlow is the central application: REST API, Web UI, dataset/knowledge-
base management, document parsing orchestration, chunking, embedding,
retrieval, chat, agent builder.

### Origin
**Upstream + modified.** Direct vendored snapshot of
[`infiniflow/ragflow`](https://github.com/infiniflow/ragflow) version
`0.24.0` (`ragflow/pyproject.toml` line 3). Contains the upstream multi-
language READMEs, LICENSE (Apache-2.0), and every standard subfolder of an
official RAGFlow release (`api`, `rag`, `deepdoc`, `agent`, `web`,
`docker`, `helm`, `sdk`, `docs`, `mcp`, `admin`, etc.).

**Custom additions inside this tree (see §F below):**
- [`ragflow/api/utils/flowchart_on_upload.py`](../ragflow/api/utils/flowchart_on_upload.py)
  — authored for this project. No upstream equivalent exists in RAGFlow
  0.24.0.
- 7-line patch at [`ragflow/api/db/services/file_service.py`](../ragflow/api/db/services/file_service.py)
  lines 515–522 that calls `maybe_append_flowchart_rag_document(...)`.
- [`ragflow/docker/docker-compose.flowchart.yml`](../ragflow/docker/docker-compose.flowchart.yml)
  — optional overlay that bind-mounts the same files when someone deploys
  from `ragflow/docker/` alone.

### Key subfolders

| Path | Purpose | Evidence |
|------|---------|----------|
| `ragflow/api/` | Flask API server, apps (blueprints), DB models and services. | `ragflow/api/ragflow_server.py`, `ragflow/api/apps/*.py`. |
| `ragflow/api/apps/document_app.py` | Upload + parse endpoints (`/upload`, `/run`, `/rm`, ...). | Grep results lines 67–873. |
| `ragflow/deepdoc/parser/` | Built-in PDF parsers including the MinerU remote parser. | [`ragflow/deepdoc/parser/mineru_parser.py`](../ragflow/deepdoc/parser/mineru_parser.py). |
| `ragflow/rag/` | Chunking (`rag/app/*.py`), retrieval (`rag/nlp`), RAPTOR, GraphRAG, LLM adapters. | `ragflow/rag/flow/parser/parser.py`. |
| `ragflow/agent/` | Workflow / agent builder components. | `ragflow/agent/`. |
| `ragflow/web/` | React + UmiJS front-end (port 80 served via nginx). | `ragflow/web/package.json`, `ragflow/web/vite.config.ts`. |
| `ragflow/docker/` | Base compose files, entrypoint, nginx conf templates. | `ragflow/docker/docker-compose.yml`, `ragflow/docker/docker-compose-base.yml`. |
| `ragflow/conf/` | Default service configuration + LLM factory catalogue. | `ragflow/conf/service_conf.yaml`, `ragflow/conf/llm_factories.json`. |
| `ragflow/helm/` | Helm chart (not used by the top-level compose). | Not modified. |
| `ragflow/mcp/` | Optional MCP server. | Disabled by default; see commented block in `ragflow/docker/docker-compose.yml` lines 12–26. |

### Inputs
- PDF / DOCX / image files uploaded through the UI or `/v1/datasets/{id}/documents`.
- Configuration via `ragflow/docker/.env` and `service_conf.yaml.template`.

### Outputs
- Parsed chunks indexed in Elasticsearch / Infinity / OpenSearch / OceanBase
  (profile-selected; see `ragflow/docker/docker-compose-base.yml` lines
  2–146).
- Web chat responses at `http://localhost:${SVR_WEB_HTTP_PORT:-80}`.

### How it connects
- Talks to MinerU via HTTP (`MINERU_APISERVER`) for PDF parsing
  ([`ragflow/deepdoc/parser/mineru_parser.py`](../ragflow/deepdoc/parser/mineru_parser.py)
  line 290: `self.mineru_api}/file_parse`).
- Runs the flowchart CLI via subprocess when the hook env vars are set
  ([`ragflow/api/utils/flowchart_on_upload.py`](../ragflow/api/utils/flowchart_on_upload.py)
  lines 65–95).

### Setup dependencies
MySQL, Redis, MinIO, and one document engine (Elasticsearch default /
Infinity / OpenSearch / OceanBase / SeekDB) — all declared as Compose
profiles in `ragflow/docker/docker-compose-base.yml`.

---

## C. `MinerU/` — PDF parser (served as HTTP API)

### Role
Turns a PDF into Markdown + structured content lists + page images. It is
the PDF-ingestion backbone for RAGFlow in this stack.

### Origin
**Upstream + (small) modification.** Vendored snapshot of
[`opendatalab/MinerU`](https://github.com/opendatalab/MinerU) licensed
**AGPL-3.0** ([`MinerU/pyproject.toml`](../MinerU/pyproject.toml) line 8).

A single patched file is shipped: `MinerU/mineru/backend/vlm/vlm_analyze.py`
which is `COPY`-ed over the pip-installed version inside the Dockerfile
([`MinerU/docker/Dockerfile.api-cpu`](../MinerU/docker/Dockerfile.api-cpu)
line 21, same in `.api-gpu` line 27). The comment in the GPU Dockerfile
explains:
> "Fix HF hub snapshot paths in mineru.json vs transformers.from_pretrained
> (HFValidationError on repo id)".

This is a workaround patch for a known MinerU VLM bug; everything else in
`MinerU/mineru/` is installed straight from pip
(`pip install "mineru[api,pipeline,vlm]>=2.6.3,<3"`).

### Key files

| Path | Purpose |
|------|---------|
| [`MinerU/docker/Dockerfile.api-cpu`](../MinerU/docker/Dockerfile.api-cpu) | Builds `mineru-api-cpu:local`; pre-downloads pipeline+VLM weights. |
| [`MinerU/docker/Dockerfile.api-gpu`](../MinerU/docker/Dockerfile.api-gpu) | Builds `mineru-api-gpu:local` with CUDA PyTorch (cu124). |
| `MinerU/docker-compose.yml` | Standalone compose for building/running MinerU alone. |
| [`MinerU/mineru/cli/fast_api.py`](../MinerU/mineru/cli/fast_api.py) | Defines `POST /file_parse` (line 125). |
| `MinerU/mineru.template.json` | Template config; `MINERU_MODEL_SOURCE=local` makes the container read `/root/mineru.json` generated at build. |
| `MinerU/projects/mcp/`, `.../multi_gpu_v2/`, `.../mineru_tianshu/` | Extra sidecar projects from upstream, **unused** by this stack. |

### Inputs
- Multipart POST to `/file_parse` with the PDF (see call in
  [`ragflow/deepdoc/parser/mineru_parser.py`](../ragflow/deepdoc/parser/mineru_parser.py)
  lines 262–294).

### Outputs
- A ZIP containing markdown, middle-JSON, content-list JSON, and page
  images (`return_md`, `return_middle_json`, `return_content_list`,
  `return_images` set to `True` in request body).

### How it connects
Called by RAGFlow's `MinerUParser`. Reachable on Docker network as
`http://mineru-api:8000`
([`docker-compose.yml`](../docker-compose.yml) lines 52–53, 66–67).

### Setup dependencies
Large model weights downloaded during `docker build` (`RUN
mineru-models-download -s huggingface -m all`). GPU variant additionally
requires NVIDIA driver + nvidia-container-toolkit.

---

## D. `flowchart/` — Custom flowchart extractor

### Role
The project-specific PDF → graph → RAG-text pipeline. This is the primary
**custom contribution** of this project.

### Origin
**Custom.** No LICENSE, no upstream attribution, no vendor branding;
written from scratch for this project.

### Structure

```
flowchart/
├── cli.py                      — argparse entry (process_pdf)
├── ragflow_ingest.py           — batch/watch uploader into RAGFlow HTTP API
├── run_comparison.py           — debug overlay renderer (cv2.arrowedLine)
├── requirements.txt            — opencv-python / easyocr / pdf2image / numpy / networkx / scikit-image / requests
├── README.md                   — install + CLI usage
├── INTEGRATION.md              — RAGFlow + MinerU + flowchart integration pattern
├── ORIGINAL_STACK_SETUP.md     — how to bolt the hook onto an existing ragflow-mineru deployment
├── flowchart.json              — SAMPLE structured output (not live)
├── flowchart.mmd               — SAMPLE Mermaid output (not live)
└── flowchart/                  — implementation package
    ├── __init__.py             — package marker, exposes submodules
    ├── pdf_converter.py        — pdf2image + Poppler resolution
    ├── preprocess.py           — greyscale → blur → Otsu threshold → mask
    ├── shapes.py               — contour-based shape (process/decision) detection
    ├── ocr.py                  — EasyOCR per-node crop text
    ├── lines.py                — skeletonise → simplify → arrow-direction heuristic
    ├── graph_builder.py        — networkx DiGraph + cycle-reduction pass
    └── exporter.py             — Mermaid / RAG markdown / graph JSON
```

### Key files (line counts)

| File | LOC | Evidence |
|------|----:|----------|
| `cli.py` | 132 | See full contents. |
| `flowchart/exporter.py` | 119 | Functions `export_graph`, `export_graph_json`, `export_rag_markdown`. |
| `flowchart/lines.py` | 253 | `detect_edges_and_arrows`, `build_skeleton_graph`, `check_local_arrowhead`. |
| `flowchart/pdf_converter.py` | 91 | Poppler resolution logic. |
| `flowchart/preprocess.py` | 50 | `preprocess`, `mask_shapes`. |
| `flowchart/shapes.py` | 50 | `detect_shapes`. |
| `flowchart/ocr.py` | 25 | `get_reader`, `extract_text`. |
| `flowchart/graph_builder.py` | 54 | `build_graph`. |
| `flowchart/__init__.py` | 10 | Package manifest. |
| `ragflow_ingest.py` | 359 | Watch + upload. |
| `run_comparison.py` | 141 | Visual debugging tool. |

### Inputs
- A PDF on disk, optionally a `POPPLER_PATH`.

### Outputs
- Per-PDF:
  - `<stem>.mmd` (always, name taken from `-o`)
  - `<stem>_rag.md` (default; disable with `--no-rag-text`)
  - `<stem>_graph.json` (with `--json`)
  - `debug_edges_<page>.png` (when `detect_edges_and_arrows` is called
    with a `debug_path`)

Sample artefacts in `vit-test/`: `Cooler_pipe_flowchart.mmd`,
`Cooler_pipe_flowchart_rag.md`, `Hose_flowchart.mmd`,
`Hose_flowchart_rag.md`, `test.mmd`, `test_rag.md`, `test_graph.json`.

### How it connects
Three distinct integration modes all call `process_pdf`:

1. **Standalone CLI** — `python flowchart/cli.py <pdf>` drops artefacts
   beside the PDF.
2. **In-process companion on upload** — the RAGFlow API calls it via
   `subprocess.run([sys.executable, cli.py, ...])`
   ([`ragflow/api/utils/flowchart_on_upload.py`](../ragflow/api/utils/flowchart_on_upload.py)
   lines 65–82).
3. **Out-of-process batch uploader** — `ragflow_ingest.py` imports
   `process_pdf` dynamically and then POSTs artefacts to the RAGFlow API
   (`/api/v1/datasets/{id}/documents` and `/chunks`).

### Setup dependencies
- Python deps: `opencv-python`, `easyocr`, `pdf2image`, `numpy`,
  `networkx`, `scikit-image`, `requests`
  ([`flowchart/requirements.txt`](../flowchart/requirements.txt)).
- System dep: **Poppler** (`pdfinfo`, `pdftoppm`) on PATH or via
  `POPPLER_PATH`.

---

## E. `vit-test/` — Sample inputs, reference outputs, benchmark

### Role
Test corpus + evaluation stub.

### Origin
**Custom.**

### Contents

| File | Kind | Evidence |
|------|------|----------|
| `2D_design.pdf`, `Prompts.pdf`, `Way of working.pdf` | Non-flowchart reference PDFs for generic RAGFlow/MinerU testing. | Exist in folder. |
| `Air_inlet_flowchart.pdf`, `Cooler_pipe_flowchart.pdf`, `Hose_flowchart.pdf` | Flowchart PDFs matching the `FLOWCHART_NAME_SUBSTRING=flowchart` rule. | Trigger the hook. |
| `Cooler_pipe_flowchart.mmd`, `Hose_flowchart.mmd`, `test.mmd` | Pre-computed Mermaid outputs. | 1–28 lines each; shape attributes visible. |
| `Cooler_pipe_flowchart_rag.md`, `Hose_flowchart_rag.md`, `test_rag.md` | Pre-computed RAG layer markdown (node/edge lines). | Used for embedding. |
| `test_graph.json` | Pre-computed graph JSON for `Air_inlet_flowchart.pdf`. | Matches `flowchart/flowchart.json` schema. |
| `benchmark_queries.yaml` | 8 template questions + a qualitative scoring rubric. | [`vit-test/benchmark_queries.yaml`](../vit-test/benchmark_queries.yaml). |
| `README.md`, `TESTING.md` | Procedure documentation. | See file-level details. |

### Inputs / Outputs
- Inputs: PDFs in this folder.
- Outputs: the extractor writes `*.mmd`, `*_rag.md`, `*_graph.json`
  back into this folder.

### How it connects
- [`flowchart/ragflow_ingest.py`](../flowchart/ragflow_ingest.py) is
  designed to `--watch` this folder and push into RAGFlow.

---

## F. Custom glue inside `ragflow/`

### `ragflow/api/utils/flowchart_on_upload.py` (CUSTOM, new file)
- Public function `maybe_append_flowchart_rag_document(kb, user_id,
  parent_path, stored_filename, pdf_blob, files_out)`.
- Gating:
  - `filename_type(...) == FileType.PDF.value` (else skip).
  - filename contains `FLOWCHART_NAME_SUBSTRING` (default `flowchart`).
  - `FLOWCHART_ON_UPLOAD=true`.
  - `FLOWCHART_ROOT` points to a directory containing `cli.py`.
- Execution:
  - Writes the uploaded blob to a temp dir.
  - Runs `python cli.py <pdf> -o <stem>.mmd --json` as a subprocess with
    `PYTHONPATH=FLOWCHART_ROOT` and `POPPLER_PATH` propagated.
  - Reads the produced `{stem}_rag.md`, `{stem}.mmd`, `{stem}_graph.json`
    from the temp dir and uploads them via `FileService.upload_document`
    into the same dataset.
- Evidence: lines 29–180 of the file.

### `ragflow/api/db/services/file_service.py` (CUSTOM, 7-line patch)
```515:522:ragflow/api/db/services/file_service.py
                try:
                    from api.utils.flowchart_on_upload import maybe_append_flowchart_rag_document

                    maybe_append_flowchart_rag_document(
                        kb, user_id, safe_parent_path, filename, blob, files
                    )
                except Exception:
                    logging.exception("Flowchart companion on upload failed")
```
This is inserted inside `FileService.upload_document` after the main PDF
has been stored and its document row appended to `files`. All surrounding
code is upstream RAGFlow.

### `ragflow/docker/docker-compose.flowchart.yml` (CUSTOM)
Optional overlay used only if the operator deploys from `ragflow/docker/`
directly (not via the top-level compose). Mounts the same three paths.

---

## G. Mapping to the "standard" architectural roles requested

| Role in spec | Concrete component in this repo |
|--------------|---------------------------------|
| **Main app / main platform** | `ragflow/` (RAGFlow 0.24.0). |
| **Parser system** | `MinerU/` + `ragflow/deepdoc/parser/mineru_parser.py`. |
| **OCR / flowchart module** | `flowchart/` (custom). Uses EasyOCR internally. |
| **Ingestion scripts** | `flowchart/ragflow_ingest.py` and the upload hook `ragflow/api/utils/flowchart_on_upload.py`. |
| **Frontend** | `ragflow/web/` (React + UmiJS). |
| **Backend** | `ragflow/api/` (Flask). |
| **Storage / DB / vector / search layer** | MySQL (metadata), Redis (queue), MinIO (blobs), and one of ES / Infinity / OpenSearch / OceanBase / SeekDB (search/vector) — all in `ragflow/docker/docker-compose-base.yml`. |
| **Deployment layer** | Top-level `docker-compose.yml` + `docker-compose.mineru-gpu.yml` + `start-ragflow-mineru.ps1`. `ragflow/helm/` exists but is unused. |
| **Evaluation scripts** | `vit-test/benchmark_queries.yaml` (manual). No automated runner. |
| **Custom adapters / integration glue** | `ragflow/api/utils/flowchart_on_upload.py`, the 7-line patch in `file_service.py`, the two optional compose overlays. |

---

## H. Components mentioned in docs but NOT used in this stack

- `ragflow/helm/` — Helm chart. No Kubernetes manifests reference it from
  the top-level; untouched.
- `ragflow/mcp/` — MCP server; disabled (commented-out command in
  `ragflow/docker/docker-compose.yml` lines 12–26).
- `ragflow/sdk/`, `ragflow/example/` — upstream SDK + examples.
- `MinerU/projects/mcp/`, `MinerU/projects/multi_gpu_v2/`,
  `MinerU/projects/mineru_tianshu/` — upstream extras; the Dockerfiles
  only install the pip `mineru[api,pipeline,vlm]` distribution and the
  patched `vlm_analyze.py`.
- `MinerU/tests/`, `ragflow/test/` — upstream test suites; not wired into
  this stack.
