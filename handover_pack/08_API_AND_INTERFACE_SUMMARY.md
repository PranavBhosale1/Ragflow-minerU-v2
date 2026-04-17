# 08 — API and Interface Summary

Every external / process-level interface in the stack.

---

## 1. Important HTTP endpoints

### 1.1 MinerU (`mineru-api`) — external FastAPI

| Method | Path | Purpose | Evidence |
|--------|------|---------|----------|
| GET | `/openapi.json` | Auto-generated OpenAPI spec; also used by healthcheck. | Top-level `docker-compose.yml` line 38 healthcheck; `MinerU/docker/Dockerfile.api-cpu` line 31. |
| POST | `/file_parse` | Accepts multipart `files=@<pdf>` plus form fields (`backend`, `parse_method`, `return_md`, `return_middle_json`, `return_content_list`, `return_images`, `response_format_zip`, `lang_list`, `server_url`, ...). Returns a ZIP when `response_format_zip=true`. | `MinerU/mineru/cli/fast_api.py` line 125; payload shape from `ragflow/deepdoc/parser/mineru_parser.py` lines 262–294. |

Available parse backends (validated server-side) — `mineru_parser.py`
line 208:
`pipeline`, `vlm-http-client`, `vlm-transformers`, `vlm-vllm-engine`,
`vlm-mlx-engine`, `vlm-vllm-async-engine`, `vlm-lmdeploy-engine`.

### 1.2 RAGFlow Flask API (upstream)

Prefixed under `/v1/document/...` (internal UI API) and under
`/api/v1/...` (external HTTP API used by SDKs and `ragflow_ingest.py`).

Internal API routes picked out from
`ragflow/api/apps/document_app.py` (lines 67–873):

| Path | Method | Purpose |
|------|--------|---------|
| `/v1/document/upload` | POST | Upload one or more files to a kb. |
| `/v1/document/web_crawl` | POST | Import from URL. |
| `/v1/document/create` | POST | Create document metadata. |
| `/v1/document/list` | POST | List docs (body filter). |
| `/v1/document/filter` | POST | Filter docs. |
| `/v1/document/infos` | POST | Batch-fetch doc infos. |
| `/v1/document/metadata/summary`, `/update` | POST | Metadata mgmt. |
| `/v1/document/thumbnails` | GET | Doc thumbnails. |
| `/v1/document/change_status` | POST | Enable/disable. |
| `/v1/document/rm` | POST | Delete. |
| `/v1/document/run` | POST | Trigger parse. |
| `/v1/document/rename` | POST | Rename. |
| `/v1/document/get/<doc_id>` | GET | Fetch one. |
| `/v1/document/download/<attachment_id>` | GET | Download attachment. |
| `/v1/document/change_parser` | POST | Switch parser. |
| `/v1/document/image/<image_id>` | GET | Fetch embedded image. |
| `/v1/document/artifact/<filename>` | GET | Fetch artefact. |
| `/v1/document/upload_and_parse` | POST | One-shot upload + parse. |

External (token-auth) API used by `ragflow_ingest.py`:

| Path | Method | Purpose | Evidence |
|------|--------|---------|----------|
| `/api/v1/datasets/{dataset_id}/documents` | POST | Upload a file (multipart). Header `Authorization: Bearer <API_KEY>`. | `flowchart/ragflow_ingest.py` lines 68–83. |
| `/api/v1/datasets/{dataset_id}/chunks` | POST | Start parsing given `document_ids`. Header `Authorization: Bearer <API_KEY>`, body `{"document_ids": [...]}`. | `flowchart/ragflow_ingest.py` lines 86–102. |

(Upstream RAGFlow SDK and HTTP test cases cover many more endpoints; this
document lists only the ones relevant to this project's integration
surface.)

---

## 2. Important CLI commands

### 2.1 `flowchart/cli.py`

```
python cli.py <pdf> [-o OUT.mmd] [--poppler-path PATH]
               [--no-rag-text] [--rag-out PATH]
               [--json] [--json-out PATH]
```

- Default output: `flowchart.mmd` next to the command. Sets the stem for
  all companion files.
- `POPPLER_PATH` env var is read when `--poppler-path` is absent
  (`flowchart/cli.py` line 115).
- Debug images `debug_edges_{page}.png` are written in the current
  working dir when the hook runs (side-effect of
  `detect_edges_and_arrows(debug_path=...)`).

### 2.2 `flowchart/ragflow_ingest.py`

```
python ragflow_ingest.py --watch <dir>
       [--out <dir>] [--name-substring STR]
       [--base-url URL] [--api-key KEY] [--dataset-id ID]
       [--poppler-path PATH]
       [--include-extras] [--no-parse] [--force]
       [--interval SECONDS] [--loop]
       [--state-file PATH] [--extract-only]
```

Environment variables accepted as defaults: `RAGFLOW_BASE_URL`,
`RAGFLOW_API_KEY`, `RAGFLOW_DATASET_ID`, `POPPLER_PATH`,
`FLOWCHART_NAME_SUBSTRING`. Evidence: lines 265–305.

### 2.3 `flowchart/run_comparison.py`

```
python run_comparison.py <pdf>
       [--poppler PATH] [--page N] [--out FILE]
```

Produces a visual overlay `comparison_output.png` (default) plus a
`debug_detector.png`. Lines 114–140.

### 2.4 MinerU server

Launched inside the container by Docker `CMD`:
`mineru-api --host 0.0.0.0 --port 8000` — `Dockerfile.api-cpu` line 33,
`Dockerfile.api-gpu` line 40.

### 2.5 Top-level launcher

Windows:
```
.\start-ragflow-mineru.ps1 [-MineruGpu] [-Build] [ComposeArgs...]
```
Evidence: `start-ragflow-mineru.ps1` lines 9–33.

---

## 3. Important scripts

| Script | Role |
|--------|------|
| `start-ragflow-mineru.ps1` | Windows launcher. |
| `flowchart/cli.py` | Main extractor entry. |
| `flowchart/ragflow_ingest.py` | Batch/watch uploader. |
| `flowchart/run_comparison.py` | Visual debug renderer. |
| `ragflow/docker/entrypoint.sh` | Upstream container entrypoint for RAGFlow. |
| `ragflow/docker/launch_backend_service.sh` | Upstream script to launch the Flask backend from source. |
| `ragflow/docker/migration.sh` | Upstream DB migration helper. |
| `ragflow/run_tests.py` | Upstream pytest runner (not wired to this stack). |

---

## 4. Key input / output formats

### 4.1 `*_rag.md` (custom RAG layer)

```
# Flowchart extraction (RAG layer)

This block summarizes an extracted flowchart as structured facts for search.

Source: <absolute PDF path at extraction time>

## Nodes

- Node 0 (process|decision): <OCR text>
- ...

## Edges (directed)

- From node A (<label>) to node B (<label>).
- ...

## Summary

The flowchart contains N node(s) and M directed edge(s).
```

Evidence: `flowchart/flowchart/exporter.py` lines 38–83.

### 4.2 `*.mmd` (Mermaid)

```
flowchart TD
    n0["label..."]
    n1{"decision label"}
    n0 --> n1
```
Evidence: `flowchart/flowchart/exporter.py` lines 25–35.

### 4.3 `*_graph.json`

```json
{
  "nodes": [
    {"id": 0, "type": "process|decision", "text": "...",
     "bbox": [x,y,w,h], "search_area": [x1,y1,x2,y2]}
  ],
  "edges": [
    {"from": 0, "to": 5}
  ]
}
```
Evidence: `flowchart/flowchart/exporter.py` lines 94–119;
concrete example `flowchart/flowchart.json`.

### 4.4 MinerU `/file_parse` request

Payload (form fields; `ragflow/deepdoc/parser/mineru_parser.py` 262–278):

```
output_dir=./output
lang_list=<lang>
backend=pipeline
parse_method=auto
formula_enable=true
table_enable=true
server_url=
return_md=true
return_middle_json=true
return_model_output=true
return_content_list=true
return_images=true
response_format_zip=true
start_page_id=0
end_page_id=99999
```

### 4.5 MinerU `/file_parse` response

- `Content-Type: application/zip`.
- ZIP contents include `*.md`, `*_middle.json`, `*_content_list.json`,
  `*_model.json`, and images.

### 4.6 RAGFlow dataset upload (external API)

Request: `multipart/form-data`, field name `file`.
Response: `{"code": 0, "data": [{"id": "<doc_id>", ...}, ...]}`.
Evidence: `flowchart/ragflow_ingest.py` lines 73–83.

---

## 5. Authentication patterns

- **RAGFlow UI**: cookie/session (Flask-Login). Not used by custom
  scripts.
- **RAGFlow external HTTP API**: `Authorization: Bearer <API_KEY>` where
  the key is generated from the UI (Settings → Model providers / API
  token). Evidence: `flowchart/ragflow_ingest.py` line 70.
- **MinerU**: **no auth** on `/file_parse` or `/openapi.json`. Relies on
  the Docker network isolation. **Exposing `MINERU_PORT` on a public IP
  is unsafe** (not explicitly stated anywhere but evident from code).
- **Upload hook**: not an HTTP interface — it runs inside the RAGFlow
  process. Access control is whatever RAGFlow enforces on the calling
  upload endpoint.

---

## 6. File naming expectations

- **Primary trigger for the hook**: the PDF filename contains
  `FLOWCHART_NAME_SUBSTRING` (default `flowchart`, case-insensitive).
  Evidence: `flowchart_on_upload.py` lines 33–36; `ragflow_ingest.py`
  line 126 (`sub in p.name.lower()`).
- **Companion stem**: derived from the PDF stem (`Path(pdf).stem`).
  `<stem>_rag.md`, `<stem>.mmd`, `<stem>_graph.json`.
- Upload ordering for companions (`flowchart_on_upload.py` lines 117–135):
  `_rag.md` first, then `.mmd`, then `_graph.json`.

---

## 7. Environment-triggered behaviours

| Variable | Default | Effect when set |
|----------|---------|-----------------|
| `FLOWCHART_ON_UPLOAD` | unset (disabled) | `true`/`1`/`yes` enables the hook. |
| `FLOWCHART_ROOT` | unset | Required absolute path to directory containing `cli.py`. |
| `FLOWCHART_NAME_SUBSTRING` | `flowchart` | Case-insensitive filename match that gates hook execution. |
| `FLOWCHART_POPPLER_PATH` | unset | Overrides `POPPLER_PATH` for the subprocess environment. |
| `POPPLER_PATH` | unset | Used by `pdf2image` if `FLOWCHART_POPPLER_PATH` is not set. |
| `FLOWCHART_SUBPROCESS_TIMEOUT` | `900` (seconds) | Timeout for the CLI subprocess. |
| `FLOWCHART_UPLOAD_EXTRAS` | `true` | When `false`, only `*_rag.md` is uploaded. |
| `MINERU_APISERVER` | (set by compose) | Base URL of MinerU service. Required by the MinerU parser. |
| `MINERU_MODEL_SOURCE` | `local` (set by compose) | Make MinerU read baked-in model paths from `/root/mineru.json`. |
| `MINERU_PORT` | `8000` | Host port for MinerU service. |
| `COMPOSE_PROFILES` | (user-set in `.env`) | Selects document engine and CPU/GPU variant. |
| `RAGFLOW_IMAGE` | (user-set) | RAGFlow image to pull; default expected `infiniflow/ragflow:v0.24.0`. |
| `RAGFLOW_BASE_URL`, `RAGFLOW_API_KEY`, `RAGFLOW_DATASET_ID` | unset | Defaults for `ragflow_ingest.py`. |

---

## 8. Subprocess calls (glue surface)

The only subprocess invocation authored for this project is inside
`flowchart_on_upload.py` lines 65–82:

```python
cmd = [
    sys.executable,
    str(cli),
    str(pdf_path),
    "-o",
    str(mmd),
    "--json",
]
proc = subprocess.run(
    cmd,
    cwd=str(td_path),
    env=env,                  # inherits + PYTHONPATH + POPPLER_PATH
    timeout=timeout,          # FLOWCHART_SUBPROCESS_TIMEOUT
    capture_output=True,
    text=True,
)
```

`ragflow_ingest.py` does not shell out — it `importlib.util`-loads
`cli.py` in-process (`ragflow_ingest.py` lines 35–47).

---

## 9. Integration points (summary)

| Integration | Where |
|-------------|-------|
| RAGFlow ⇄ MinerU | `ragflow/deepdoc/parser/mineru_parser.py` + `docker-compose.yml` env `MINERU_APISERVER`. |
| RAGFlow ⇄ Flowchart CLI (in-process) | `ragflow/api/db/services/file_service.py` lines 515–522 → `ragflow/api/utils/flowchart_on_upload.py` subprocess. |
| External automation ⇄ Flowchart + RAGFlow | `flowchart/ragflow_ingest.py` → RAGFlow `/api/v1/datasets/{id}/documents` + `/chunks`. |
| Compose mounts | Top-level `docker-compose.yml` lines 54–71. |
| UI ⇄ MinerU config | `ragflow/web/src/pages/user-setting/setting-model/modal/mineru-modal/` — upstream UI for configuring MinerU endpoint. |

---

## 10. Ports and URLs (defaults)

| Service | Host port | URL |
|---------|-----------|-----|
| RAGFlow Web UI | `${SVR_WEB_HTTP_PORT:-80}` | `http://localhost:80/` |
| RAGFlow HTTP API | `${SVR_HTTP_PORT:-9380}` | `http://localhost:9380/` |
| RAGFlow HTTPS | `${SVR_WEB_HTTPS_PORT:-443}` | — |
| RAGFlow admin | `${ADMIN_SVR_HTTP_PORT:-9381}` | `http://localhost:9381/` |
| RAGFlow MCP | `${SVR_MCP_PORT:-9382}` | `http://localhost:9382/` |
| MinerU | `${MINERU_PORT:-8000}` | `http://localhost:8000/` |
| MinIO | `${MINIO_PORT:-9000}` | `http://localhost:9000/` |
| MinIO console | `${MINIO_CONSOLE_PORT:-9001}` | `http://localhost:9001/` |
| MySQL (exposed) | `${EXPOSE_MYSQL_PORT:-5455}` | — |
| Elasticsearch | `${ES_PORT:-1200}` | — |

Evidence: `ragflow/docker/docker-compose.yml` lines 31–38;
`ragflow/docker/docker-compose-base.yml` lines 8, 43, 108, 191, 208, 230;
top-level `docker-compose.yml` line 32.
