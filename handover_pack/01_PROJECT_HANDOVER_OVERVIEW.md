# 01 — Project Handover Overview

> Scope: this document is a factual, evidence-backed summary of the
> repository at `Ragflow-minerU-v2-main/`. Every claim is tagged as
> **CONFIRMED**, **INFERRED**, or **UNKNOWN / NEEDS MANUAL INPUT**.

---

## 1. One-paragraph project summary

The repository is a **bundled RAG stack** that combines three third-party /
upstream projects with a **custom flowchart-understanding layer**. The main
retrieval platform is **RAGFlow** (`ragflow/`), the PDF parser is **MinerU**
served as an HTTP API (`MinerU/`), and a **classical computer-vision
flowchart extractor** (`flowchart/`) produces Mermaid (`.mmd`), RAG-ready
markdown (`*_rag.md`) and a graph JSON (`*_graph.json`) from
flowchart-style PDFs. A small glue layer inside RAGFlow
(`ragflow/api/utils/flowchart_on_upload.py` + a 7-line patch in
`ragflow/api/db/services/file_service.py`) automatically runs the flowchart
CLI during document upload when the filename contains a configured
substring (default: `flowchart`) and uploads the resulting companion files
into the same RAGFlow dataset so they are parsed and embedded alongside the
PDF. Everything is orchestrated with Docker Compose from the repo root.

- Evidence: [`docker-compose.yml`](../docker-compose.yml) lines 16–71,
  [`flowchart/INTEGRATION.md`](../flowchart/INTEGRATION.md),
  [`flowchart/ORIGINAL_STACK_SETUP.md`](../flowchart/ORIGINAL_STACK_SETUP.md),
  [`ragflow/api/utils/flowchart_on_upload.py`](../ragflow/api/utils/flowchart_on_upload.py),
  [`ragflow/api/db/services/file_service.py`](../ragflow/api/db/services/file_service.py)
  lines 515–522.

---

## 2. Exact problem being solved

**Problem (CONFIRMED):** RAGFlow + MinerU correctly ingest and embed the
text/tables/layout of technical PDFs, but **flowcharts embedded in those
PDFs are images** — their nodes and directed edges are not surfaced to the
retrieval layer, so chat/Q&A cannot answer questions like "what happens
after the `No` branch of the Weld decision?" or "which standard-steel
specification is used after the air inlet?".

The custom flowchart module:

1. Rasterises the PDF (`pdf2image` + Poppler).
2. Detects rectangles / diamonds as flowchart nodes (`opencv`).
3. Runs OCR on each node (`easyocr`).
4. Extracts connecting lines and arrows from the masked image, builds a
   `networkx` graph, and resolves arrow direction (`skimage.skeletonize` +
   local density heuristic).
5. Emits three artefacts per PDF:
   - `*.mmd` — Mermaid flowchart code
   - `*_rag.md` — plain-language node/edge text for embedding
   - `*_graph.json` — structured graph
6. Uploads `*_rag.md` (and optionally `.mmd`, `_graph.json`) to the **same
   RAGFlow dataset** as the original PDF so the retriever can ground chat
   answers on explicit node/edge sentences.

- Evidence: [`flowchart/cli.py`](../flowchart/cli.py) lines 40–83,
  [`flowchart/flowchart/shapes.py`](../flowchart/flowchart/shapes.py),
  [`flowchart/flowchart/ocr.py`](../flowchart/flowchart/ocr.py),
  [`flowchart/flowchart/lines.py`](../flowchart/flowchart/lines.py),
  [`flowchart/flowchart/exporter.py`](../flowchart/flowchart/exporter.py)
  (function `export_rag_markdown`),
  [`vit-test/Cooler_pipe_flowchart_rag.md`](../vit-test/Cooler_pipe_flowchart_rag.md)
  (sample output).

---

## 3. Project title candidates (evidence-backed)

| Candidate                                                           | Evidence |
|---------------------------------------------------------------------|----------|
| "Flowchart-aware RAG: integrating classical flowchart extraction into RAGFlow + MinerU" | Matches the three repos and the custom work. |
| "Enriching RAGFlow retrieval with flowchart node/edge embeddings" | Matches `export_rag_markdown` output and `vit-test/benchmark_queries.yaml`. |
| "A companion-upload pipeline for flowchart PDFs in RAGFlow" | Matches the upload-hook architecture. |
| "Industrial-diagram QA on top of MinerU + RAGFlow" | Matches sample PDFs: `Air_inlet_flowchart.pdf`, `Cooler_pipe_flowchart.pdf`, `Hose_flowchart.pdf` (automotive/industrial P&ID-style). |

The repo itself is named `Ragflow-minerU-v2` (see `docker-compose.yml` line
3 and `start-ragflow-mineru.ps1` line 1). **CONFIRMED.**

---

## 4. Domain / use case

- **INFERRED (strongly):** Industrial / automotive engineering
  documentation. Sample PDFs in `vit-test/` (`2D_design.pdf`,
  `Air_inlet_flowchart.pdf`, `Cooler_pipe_flowchart.pdf`,
  `Hose_flowchart.pdf`, `Way of working.pdf`, `Prompts.pdf`) describe
  material choices, coatings (KTL, galvanizing), welds and hose assemblies
  — typical of manufacturing / automotive specification trees.
- **INFERRED:** "VIT" in `vit-test/` and `README.md` line 1
  ("VIT test documents") is the name of the recipient organisation /
  course / team. **UNKNOWN / NEEDS MANUAL INPUT**: whether VIT means the
  academic institute (Vellore Institute of Technology), a specific
  industrial partner ("VIT" could be a team code), or a generic validation
  target.
- Evidence: [`vit-test/README.md`](../vit-test/README.md),
  [`.gitignore`](../.gitignore) line 2 (`Doc to be sent to VIT/`).

---

## 5. What makes this a combination of multiple repos/components

This is not a single project. It is a **stack assembled from four
independent code trees** plus a thin integration layer:

| Tree | Origin | Role | Evidence |
|------|--------|------|----------|
| `ragflow/` | Upstream open-source: **InfiniFlow RAGFlow** (Apache-2.0) | Main RAG platform (backend API, React UI, agent builder, parsers, retrieval, chat). | [`ragflow/LICENSE`](../ragflow/LICENSE), [`ragflow/README.md`](../ragflow/README.md) line 1–40 (InfiniFlow branding, Docker Hub badge), `version = "0.24.0"` in `ragflow/pyproject.toml` line 3. |
| `MinerU/` | Upstream open-source: **OpenDataLab MinerU** (AGPL-3.0) | PDF → Markdown / content-list parser, served via a FastAPI endpoint (`/file_parse`). | [`MinerU/pyproject.toml`](../MinerU/pyproject.toml) `license = "AGPL-3.0"`, [`MinerU/README.md`](../MinerU/README.md) OpenDataLab branding, [`MinerU/mineru/cli/fast_api.py`](../MinerU/mineru/cli/fast_api.py) line 125. |
| `flowchart/` | **Custom** (written for this project) | Classical-CV + OCR flowchart-to-RAG-markdown extractor, a CLI, and a RAGFlow ingestion helper. | [`flowchart/README.md`](../flowchart/README.md), [`flowchart/cli.py`](../flowchart/cli.py), `flowchart/flowchart/*.py`, [`flowchart/ragflow_ingest.py`](../flowchart/ragflow_ingest.py). No vendor license or upstream attribution. |
| `vit-test/` | **Custom** (test harness) | Sample input PDFs, pre-generated `.mmd` / `_rag.md` reference outputs, a YAML benchmark suite and setup notes. | [`vit-test/README.md`](../vit-test/README.md), [`vit-test/benchmark_queries.yaml`](../vit-test/benchmark_queries.yaml), [`vit-test/TESTING.md`](../vit-test/TESTING.md). |
| Glue | **Custom** | Upload-hook in RAGFlow and top-level Docker Compose that binds `flowchart/` + patched files into the RAGFlow container. | Top-level [`docker-compose.yml`](../docker-compose.yml) lines 54–71, [`ragflow/api/utils/flowchart_on_upload.py`](../ragflow/api/utils/flowchart_on_upload.py), 7-line patch in [`ragflow/api/db/services/file_service.py`](../ragflow/api/db/services/file_service.py) lines 515–522, [`ragflow/docker/docker-compose.flowchart.yml`](../ragflow/docker/docker-compose.flowchart.yml), [`start-ragflow-mineru.ps1`](../start-ragflow-mineru.ps1). |

See `06_CUSTOM_WORK_VS_BASE_SYSTEM.md` for file-level line counts.

---

## 6. High-level system explanation

```
User browser (UI)
       │  HTTP :80
       ▼
┌──────────────────────────────┐                  ┌────────────────────────┐
│ RAGFlow-cpu / ragflow-gpu    │  POST /file_parse │ MinerU-api (FastAPI)   │
│  - Flask API (port 9380)     │──────────────────▶│  - /file_parse         │
│  - web UI (port 80)          │                   │  - pipeline / VLM      │
│  - MySQL / Redis / MinIO /   │                   │    backends            │
│    Elasticsearch-or-Infinity │◀──────────────────│  - returns ZIP (md,    │
│                              │   zipped output   │    images, JSON)       │
└──────────────────────────────┘                   └────────────────────────┘
       │
       │  (same container, on PDF upload whose name contains "flowchart")
       │
       ▼
  flowchart_on_upload.py  ──►  python /flowchart-tools/cli.py <pdf>
                               ├─► <pdf>.mmd
                               ├─► <pdf>_rag.md           ◄─ uploaded to same KB
                               └─► <pdf>_graph.json
```

- Bind-mounts: top-level [`docker-compose.yml`](../docker-compose.yml)
  lines 54–71 mount `./flowchart` → `/flowchart-tools` and the two patched
  Python files into `/ragflow/api/...` read-only.
- MinerU is wired in by the RAGFlow-side MinerU parser
  ([`ragflow/deepdoc/parser/mineru_parser.py`](../ragflow/deepdoc/parser/mineru_parser.py)
  lines 214–243, 250–294). `MINERU_APISERVER` env var points at the
  `mineru-api` service.

---

## 7. Current project maturity

**INFERRED:** Prototype / academic / internal-validation stage.
Justification:

- No production-grade CI (`ragflow/.pre-commit-config.yaml` exists, but
  there is no repo-root CI workflow).
- No `.env` file shipped; `ragflow/docker/.env.single-bucket-example` is
  the only reference. The top-level docker-compose *requires* a user-created
  `ragflow/docker/.env` ([`docker-compose.yml`](../docker-compose.yml)
  line 3).
- Clear "VIT test documents" terminology in
  [`vit-test/README.md`](../vit-test/README.md) + benchmark YAML instead of
  automated evaluation harness.
- The flowchart graph_builder has heuristic cycle-reduction loops and
  fallback direction inference — explicitly marked as heuristics in
  [`flowchart/flowchart/graph_builder.py`](../flowchart/flowchart/graph_builder.py)
  lines 29–52 and [`flowchart/flowchart/lines.py`](../flowchart/flowchart/lines.py)
  lines 207–228.
- Sample outputs in `vit-test/` show extraction works but produces
  duplicated nodes (e.g. `Cooler_pipe_flowchart_rag.md` contains two
  different nodes both labelled `Std Steel 0011 1331 95`) — acceptable for
  research but not production.

**Not production-like.** **Not academic-paper-ready either** — no
evaluation numbers are committed.

---

## 8. What is CONFIRMED working

- RAGFlow main app, UI, and all base services can be brought up via
  `docker compose --env-file ragflow/docker/.env up -d`
  (pattern documented in [`docker-compose.yml`](../docker-compose.yml)
  lines 3–12 and implemented by `start-ragflow-mineru.ps1`).
- MinerU CPU and GPU Docker images build and expose `/file_parse` and
  `/openapi.json`; healthcheck confirms readiness
  ([`MinerU/docker/Dockerfile.api-cpu`](../MinerU/docker/Dockerfile.api-cpu)
  lines 30–33,
  [`docker-compose.yml`](../docker-compose.yml) lines 37–42).
- RAGFlow → MinerU integration is code-complete
  ([`ragflow/deepdoc/parser/mineru_parser.py`](../ragflow/deepdoc/parser/mineru_parser.py)
  class `MinerUParser`, lines 137–294).
- Flowchart extractor runs end-to-end on real PDFs: sample artefacts exist
  for `Cooler_pipe_flowchart.pdf`, `Hose_flowchart.pdf`,
  `Air_inlet_flowchart.pdf` (as `test_*`), all under `vit-test/`.
- Companion-on-upload hook has an import site inside RAGFlow at
  [`ragflow/api/db/services/file_service.py`](../ragflow/api/db/services/file_service.py)
  lines 515–522 and the implementation
  [`ragflow/api/utils/flowchart_on_upload.py`](../ragflow/api/utils/flowchart_on_upload.py).
- Batch helper `ragflow_ingest.py` implements poll-and-upload with state
  tracking, including `--extract-only` and `--loop`
  ([`flowchart/ragflow_ingest.py`](../flowchart/ragflow_ingest.py)).

---

## 9. What is PARTIAL

- The **hook vs manual-ingest** duality: both code paths exist and both
  require the same host-side setup (Poppler + Python deps inside the
  RAGFlow container). Only manual shell steps are documented; no
  automated provisioning
  ([`vit-test/TESTING.md`](../vit-test/TESTING.md) §2.2 asks the user to
  `apt-get install poppler-utils` inside the container).
- **Flowchart OCR accuracy**: the OCR step (`easyocr`) is lazy-loaded per
  node crop without any confidence filtering
  ([`flowchart/flowchart/ocr.py`](../flowchart/flowchart/ocr.py) lines
  12–25). Outputs in `vit-test/test_rag.md` vs
  `vit-test/Cooler_pipe_flowchart_rag.md` reveal OCR drift (e.g. "FelZn
  12p F4- AC- STD 6767K" vs "FelZn 12pF4 AC Std 6767k"). No post-processing
  normalisation.
- **Flowchart graph correctness**: edge direction uses a density
  heuristic and falls back to geometric top-down / left-right
  ([`flowchart/flowchart/lines.py`](../flowchart/flowchart/lines.py) lines
  196–228). Shape classification for decision vs process is heuristic
  ([`flowchart/flowchart/shapes.py`](../flowchart/flowchart/shapes.py)
  lines 34–48). No ground truth or test assertions.
- **Benchmarking**: `vit-test/benchmark_queries.yaml` defines eight
  template questions but has *no recorded answers or scores* — the scoring
  is left for the human operator (`scoring:` block).

---


