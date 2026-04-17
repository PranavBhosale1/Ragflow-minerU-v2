# 03 — System Architecture Explanation

This document explains what happens when a user interacts with the system,
end to end. Every arrow in a diagram is backed by evidence in the codebase.

---

## 1. Textual architecture diagram

```
                    ┌─────────────────────────────────────────┐
                    │                 User                     │
                    │  (web browser  /  REST client  /  CLI)   │
                    └───────────────┬─────────────────────────┘
                                    │
                                    │ HTTP 80 / 9380
                                    ▼
┌───────────────────────────────────────────────────────────────────────┐
│  ragflow-cpu   OR   ragflow-gpu     (single container, Flask + nginx) │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────────┐  │
│  │ web/  React  │  │ api/ Flask   │  │ rag/ + deepdoc/  (chunking │  │
│  │ UI (nginx)   │  │ blueprints   │  │  + parsing + retrieval)    │  │
│  └──────────────┘  └──────┬───────┘  └──────────────┬─────────────┘  │
│                           │                          │                │
│                (file upload │ /document/upload)       │                │
│                           ▼                          │                │
│   ┌────────────────────────────────────────┐        │                │
│   │ FileService.upload_document()          │        │                │
│   │  (ragflow/api/db/services/file_service)│        │                │
│   │  • stores blob in MinIO                │        │                │
│   │  • inserts Document + File rows        │        │                │
│   │  • >>> custom hook call <<<            │        │                │
│   └────────────────────────────────────────┘        │                │
│                           │                          │                │
│      ┌────────────────────┴────────────────────┐    │                │
│      ▼ (only when PDF name contains            │    │                │
│        FLOWCHART_NAME_SUBSTRING)               │    │                │
│   ┌────────────────────────────────────────┐  │    │                │
│   │ maybe_append_flowchart_rag_document()  │  │    │                │
│   │ (api/utils/flowchart_on_upload.py)     │  │    │                │
│   │                                        │  │    │                │
│   │   subprocess.run([python,              │  │    │                │
│   │       /flowchart-tools/cli.py,         │  │    │                │
│   │       <pdf>, -o <stem>.mmd, --json])   │  │    │                │
│   │                                        │  │    │                │
│   │   → *_rag.md, *.mmd, *_graph.json      │  │    │                │
│   │   → FileService.upload_document(...)   │  │    │                │
│   │       for each companion file          │  │    │                │
│   └────────────────────────────────────────┘  │    │                │
│                                                 │    │                │
│                                                 │    │                │
│   Parsing workflow (when "Parse on creation")   │    │                │
│   triggers for EVERY doc that was just added:   │    │                │
│                                                 │    │                │
│   ┌────────────────────────────────────────┐  │    │                │
│   │ MinerUParser (ragflow/deepdoc/parser)  │◀─┘    │                │
│   │  POST http://mineru-api:8000/file_parse│       │                │
│   └────────────────┬───────────────────────┘       │                │
└────────────────────┼──────────────────────────────────────────────────┘
                     │                               │
                     │ multipart PDF                 │
                     ▼                               ▼
   ┌──────────────────────────────┐    ┌─────────────────────────────────┐
   │  mineru-api (FastAPI)        │    │  Document engine                │
   │  (MinerU/mineru/cli/fast_api │    │  (ES / Infinity / OpenSearch /  │
   │   .py)                       │    │   OceanBase / SeekDB)           │
   │  • pipeline / VLM / VLM-http │    │  + MySQL (metadata)             │
   │  • returns ZIP with md/json/ │    │  + Redis (queue)                │
   │    images                    │    │  + MinIO (blobs)                │
   └──────────────────────────────┘    └─────────────────────────────────┘
```

Evidence map:
- "User → UI / API": top-level `docker-compose.yml` comment
  `Web UI: http://localhost:${SVR_WEB_HTTP_PORT:-80}` line 8.
- "FileService → hook": `ragflow/api/db/services/file_service.py`
  lines 515–522.
- "hook → subprocess": `ragflow/api/utils/flowchart_on_upload.py`
  lines 65–95.
- "hook → FileService.upload_document for companions": same file lines
  117–152.
- "MinerUParser → /file_parse": `ragflow/deepdoc/parser/mineru_parser.py`
  line 290.
- "Inter-container DNS": `MINERU_APISERVER: http://mineru-api:8000`
  in `docker-compose.yml` lines 52, 67.

---

## 2. End-to-end workflow (user uploads a flowchart PDF and asks a
question)

1. User opens the RAGFlow UI at `http://localhost:80` and creates a
   knowledge base (= RAGFlow "dataset").
2. User uploads `Air_inlet_flowchart.pdf` with **Parse on creation**
   enabled.
3. The React UI calls `POST /v1/document/upload` on the RAGFlow Flask API
   (`ragflow/api/apps/document_app.py` line 67).
4. `FileService.upload_document` stores the PDF in MinIO and writes a row
   in MySQL. This is **upstream** behaviour.
5. **Custom step**: the try-block at `file_service.py` lines 515–522
   runs `maybe_append_flowchart_rag_document`. Because the filename
   contains `flowchart`, the hook:
   - Launches `python /flowchart-tools/cli.py <pdf> -o <stem>.mmd --json`
     in a temporary directory.
   - Inside that subprocess the flowchart pipeline runs (see §4).
   - The hook reads `*_rag.md`, `*.mmd`, `*_graph.json` and calls
     `FileService.upload_document` again for each of them. These rows are
     appended to the *same* `files` list that RAGFlow's upload response
     returns — so they are visible to the UI immediately.
6. Because **Parse on creation** was ticked, each of those four documents
   is queued for parsing. RAGFlow's worker picks the correct parser:
   - PDFs → `MinerUParser` if the dataset is configured to use MinerU.
   - `.md` / `.mmd` / `.json` → the generic naïve/text parsers
     (`ragflow/rag/app/naive.py` and friends).
7. `MinerUParser.run()` POSTs the PDF to `http://mineru-api:8000/file_parse`
   and unzips the returned ZIP into a temp dir, then converts the
   markdown + content list into RAGFlow chunks.
8. Chunks go through embedding and are indexed into the configured search
   engine (ES by default).
9. User opens Chat and asks e.g. "what happens after the `No` branch of
   the Weld decision?"
10. RAGFlow's retriever hits the embeddings; because `*_rag.md` contains a
    sentence like
    `From node 5 (Use Welds?) to node 3 (No).`, that chunk scores highly
    and is passed to the LLM, which produces a grounded answer.

---

## 3. User flow

- **Web UI only.** Users never run the flowchart CLI directly. They drag
  a PDF into a knowledge base, press parse, and chat.
- Admin / dev flow: run `.\start-ragflow-mineru.ps1` (Windows) or
  `docker compose --env-file ragflow/docker/.env up -d` (Linux/macOS) to
  bring the stack up.

---

## 4. Backend flow (inside RAGFlow)

1. **HTTP layer**: Flask blueprint `document_app` (`/upload`, `/run`,
   `/get`, `/rm`, ...). See grep results over
   `ragflow/api/apps/document_app.py` lines 67–873.
2. **Service layer**: `FileService.upload_document` handles filename
   sanitisation, MinIO storage, DB inserts, broken-PDF repair
   (`file_service.py` lines 480–514).
3. **Parser selection**: `self.get_parser(filetype, filename,
   kb.parser_id)` on line 498 picks the parser id.
4. **Parse worker**: consumes the job queue and runs the selected parser
   class. For PDFs: `MinerUParser` from
   `ragflow/deepdoc/parser/mineru_parser.py`.
5. **Chunking**: Apps like `rag/app/naive.py`, `rag/app/manual.py`
   convert parsed content into `Chunk` objects.
6. **Index**: chunks land in the document engine + embeddings.

---

## 5. Document ingestion flow

- PDF: `FileService.upload_document` → `read_potential_broken_pdf` →
  MinIO → DB → (optional) flowchart hook → parse worker →
  `MinerUParser`.
- Markdown / MMD / JSON companion files: same `FileService.upload_document`
  call from inside the hook, but the parser selection just picks the
  naïve text parser.

---

## 6. Parsing flow (MinerU)

1. RAGFlow sends a multipart POST to `/file_parse`
   (`mineru_parser.py` line 290).
2. FastAPI handler `fast_api.py:125` (`@app.post("/file_parse", ...)`)
   accepts the file.
3. MinerU runs its chosen backend — `pipeline` (classic), VLM
   (`vlm-transformers` / `vlm-http-client` / `vlm-vllm-engine` / ...).
   Valid backends listed at `mineru_parser.py` line 208.
4. MinerU zips `md`, `middle.json`, `content_list.json`, images, and
   returns a ZIP.
5. RAGFlow calls `_extract_zip_no_root` (`mineru_parser.py` line 148) to
   safely unpack the archive under a temp folder, and then converts the
   content list to RAGFlow internal chunks (not shown in snippet; lives
   further down the file).

---

## 7. Flowchart processing flow (custom)

1. **PDF → images**: `pdf_to_images` in `flowchart/flowchart/pdf_converter.py`
   uses `pdf2image.convert_from_path(dpi=300, poppler_path=...)` and
   writes `page_{i}.png`.
2. **Preprocess** (`preprocess.py`): greyscale → Gaussian blur → Otsu
   binary inverse.
3. **Shape detection** (`shapes.py`): `cv2.findContours` → polygon
   approximation; quadrilaterals ≥ 1000 px² are nodes. Near-square
   rotated quads are classified as `decision`; others as `process`.
4. **OCR** (`ocr.py`): per-node crop → `easyocr.Reader(["en"]).readtext`
   → concatenated text stored in `node["text"]`.
5. **Line / arrow detection** (`lines.py`):
   - Mask nodes out of the binary image (`preprocess.mask_shapes`).
   - Dilate + skeletonise (scikit-image).
   - Build a pixel-level graph (`build_skeleton_graph`) and simplify
     chains of degree-2 pixels (`simplify_graph_topology`).
   - Expand each node's bbox into a "search area" rim (proximity 20 px).
   - Walk interface vertices; for each pair, compare local pixel density
     at both endpoints (`check_local_arrowhead`) to decide arrow
     direction. If ambiguous, fall back to centroid geometry
     (top→bottom, left→right).
6. **Graph build** (`graph_builder.py`): `networkx.DiGraph`; one pass
   attempts to reduce cycles by reversing individual edges (heuristic).
7. **Export** (`exporter.py`):
   - `export_graph` → `*.mmd` (`flowchart TD` + `nX["label"]` /
     `nX{"label"}` + `nX --> nY`).
   - `export_rag_markdown` → `*_rag.md` with `## Nodes`, `## Edges`,
     `## Summary` sections (human-readable English sentences for
     embeddings).
   - `export_graph_json` → `*_graph.json` with `nodes[]`, `edges[]`,
     optional `bbox` and `search_area`.

---

## 8. Storage / indexing flow

- **MinIO**: raw file blobs keyed by `(kb.id, location)`
  (`file_service.py` line 480).
- **MySQL**: `Document`, `File`, `Knowledgebase`, `Task`, `Dialog` rows.
  See `ragflow/api/db/db_models.py` (upstream).
- **Search engine**: RAGFlow picks one of `elasticsearch`, `infinity`,
  `opensearch`, `oceanbase`, `seekdb` via the `COMPOSE_PROFILES` env. See
  `ragflow/docker/docker-compose-base.yml` profiles.
- Embeddings: created by the LLM/embedding provider configured in the UI
  (see `ragflow/conf/llm_factories.json`, and
  `ragflow/docs/guides/models/supported_models.mdx`).

---

## 9. Retrieval flow

Standard upstream RAGFlow retrieval:
1. User question → embedding via configured embedder.
2. Vector + BM25 (or equivalent) search in the configured engine.
3. Reranker (optional).
4. Retrieved chunks + system prompt → LLM → answer with citations.

Custom part is purely additive: **the `*_rag.md` artefacts give the
retriever chunks that mention flowchart node/edge text in plain English**,
which would otherwise only exist as pixel labels inside the PDF.

---

## 10. Query-answering flow (chat)

- Endpoint: `ragflow/api/apps/dialog_app.py` + `conversation_app.py`
  (upstream; not modified in this project).
- LLM call goes through `ragflow/rag/llm/*` abstractions.
- Answers include citations pointing to chunk ids; when a flowchart
  `*_rag.md` chunk is cited, it appears in the UI side-panel alongside the
  PDF chunk.

---

## 11. Optional batch / watch-folder flow

Run independently of the hook (useful when the RAGFlow container doesn't
have Poppler/EasyOCR installed):

```
flowchart/ragflow_ingest.py --watch <dir> [--loop] [--interval N]
     │
     ▼
Scan dir for *.pdf whose name contains FLOWCHART_NAME_SUBSTRING (default
"flowchart").
     │
     ▼
Call process_pdf(...) (dynamically imported from cli.py)
     │
     ▼
POST <stem>_rag.md [and <stem>.mmd, <stem>_graph.json if --include-extras]
  to http://<base-url>/api/v1/datasets/<id>/documents (Bearer <api-key>)
     │
     ▼
POST /api/v1/datasets/<id>/chunks with document_ids to start parsing
```

State is written to `.flowchart_ragflow_state.json` inside the watched
directory so unchanged PDFs are skipped
(`ragflow_ingest.py` lines 105–116, 174–214).

---

## 12. Where external services are involved

| External call | Initiator | URL pattern | File |
|---------------|-----------|-------------|------|
| MinerU parse | RAGFlow parser | `POST /file_parse` on `mineru-api:8000` | `ragflow/deepdoc/parser/mineru_parser.py` line 290 |
| MinerU health | RAGFlow parser | `GET /openapi.json` | `mineru_parser.py` lines 219–222 |
| Hugging Face | MinerU Docker build | `mineru-models-download -s huggingface -m all` | `Dockerfile.api-cpu` line 24, `Dockerfile.api-gpu` line 31 |
| LLM providers | RAGFlow chat | SaaS endpoints configured by user | `ragflow/conf/llm_factories.json` |
| RAGFlow REST | `ragflow_ingest.py` | `POST /api/v1/datasets/{id}/documents`, `POST /api/v1/datasets/{id}/chunks` | `flowchart/ragflow_ingest.py` lines 68–102 |

---

## 13. Where custom code is involved

- `flowchart/` (entire tree).
- `ragflow/api/utils/flowchart_on_upload.py`.
- 7 lines added to `ragflow/api/db/services/file_service.py` (lines
  515–522).
- Top-level `docker-compose.yml`, `docker-compose.mineru-gpu.yml`,
  `start-ragflow-mineru.ps1`, and the optional overlay
  `ragflow/docker/docker-compose.flowchart.yml`.
- `vit-test/` (test corpus + `benchmark_queries.yaml`).

Everything else is upstream RAGFlow or MinerU.

---

## 14. What fails gracefully vs what does not

| Failure mode | Behaviour |
|--------------|-----------|
| Flowchart subprocess timeout (default 900 s) | Logged at ERROR, returns `None`; the primary PDF upload still succeeds. Evidence: `flowchart_on_upload.py` lines 82–95, and the try/except around the hook call in `file_service.py` line 521. |
| Flowchart CLI non-zero exit | Same as above — logged, hook returns `None`, PDF upload unaffected. |
| `FLOWCHART_ROOT` missing or wrong | Logged WARNING (`FLOWCHART_ON_UPLOAD is enabled but FLOWCHART_ROOT is not set`), no companions generated, PDF upload unaffected. |
| `FLOWCHART_ON_UPLOAD=false` | Logs an INFO describing how to enable; no extraction. |
| Poppler missing | `resolve_poppler_path` raises `RuntimeError` with a detailed hint; caught by the subprocess; no companions; PDF upload unaffected. |
| MinerU API not reachable | `MinerUParser.check_installation` returns `(False, reason)` and sets error state so the parse job fails visibly in RAGFlow. |
| EasyOCR model download on first run | First parse is slow but not fatal; download happens inside the container. |
| Document engine down / not profiled | The compose `depends_on` does **not** gate the search engine, only MySQL and MinerU. If the engine profile is missing, indexing fails at chunk time (upstream behaviour). |

Known **non-graceful** paths:

- If `cli.py` succeeds but produces **no** `*_rag.md`, the hook logs an
  error and skips companion upload (flowchart_on_upload.py lines
  108–110); no retry.
- `graph_builder.build_graph`'s cycle-reduction pass catches a bare
  `Exception` (`graph_builder.py` line 51) — silent swallow.
- `ocr.extract_text` has no error handling if `easyocr` fails to load the
  language model (first-run download failures would crash the subprocess).

---

## 15. Component interaction summary

| From | To | Protocol | Direction | Evidence |
|------|----|----------|-----------|----------|
| Browser | `ragflow-cpu` | HTTP 80 | req/resp | compose ports 32 |
| Browser | `ragflow-cpu` | HTTP 9380 (REST) | req/resp | compose ports 34 |
| `ragflow-cpu` | MinIO/MySQL/Redis/ES | TCP | req/resp | upstream |
| `ragflow-cpu` | `mineru-api:8000` | HTTP | req/resp | mineru_parser.py line 290 |
| `ragflow-cpu` | local `cli.py` | subprocess | fire-and-forget with timeout | flowchart_on_upload.py line 73–82 |
| `ragflow_ingest.py` | `ragflow` REST | HTTPS/HTTP | req/resp | ragflow_ingest.py lines 68, 94 |

---

## 16. Data flow summary

PDF bytes → (MinIO) → MinerU (via HTTP) → Markdown + images →
(RAGFlow chunker) → (embedder) → (search engine)

PDF bytes → (flowchart subprocess) → `*.mmd` + `*_rag.md` + `*_graph.json`
→ (FileService.upload_document) → same pipeline as above for the text
files → `*_rag.md` chunks land in the same index as the PDF chunks.

---

## 17. Control flow summary

- The upload endpoint is **synchronous** with respect to the hook: the
  subprocess blocks the HTTP response up to `FLOWCHART_SUBPROCESS_TIMEOUT`
  seconds (default 900). That is intentional — the docs say "the
  companion file appears in the upload response together with the PDF"
  (`flowchart/INTEGRATION.md` line 44).
- Parsing itself is **asynchronous** (RAGFlow task queue, upstream).
- `ragflow_ingest.py --loop` is a simple polling loop (`time.sleep(interval)`),
  no watchdog dependency (ragflow_ingest.py line 242). State is persisted
  to JSON between iterations.
