# 05 — Run & Test Guide

How to start the full stack, partial components, and how to test each one
with the evidence committed in the repo.

---

## 1. Starting the full system

From the repo root:

```bash
# Linux/macOS
docker compose --env-file ragflow/docker/.env up -d
# With GPU MinerU overlay
docker compose --env-file ragflow/docker/.env \
    -f docker-compose.yml -f docker-compose.mineru-gpu.yml up -d

# Windows
.\start-ragflow-mineru.ps1
.\start-ragflow-mineru.ps1 -MineruGpu
.\start-ragflow-mineru.ps1 -Build     # triggers --build
```

Evidence: `start-ragflow-mineru.ps1` lines 21–33; top-level
`docker-compose.yml` header comments lines 1–14.

Expected containers:

| Container | Image | Port(s) |
|-----------|-------|---------|
| `ragflow-mineru-ragflow-cpu-1` (or `-gpu-1`) | `${RAGFLOW_IMAGE}` | 80, 443, 9380, 9381, 9382, 9384 |
| `mineru-api` | `mineru-api-cpu:local` / `mineru-api-gpu:local` | `${MINERU_PORT:-8000}` |
| `*-mysql-*`, `*-minio-*`, `*-redis-*`, `*-es01-*` (or Infinity/OpenSearch/OceanBase/SeekDB) | upstream images | see `ragflow/docker/docker-compose-base.yml` |

---

## 2. Starting partial components individually

### 2.1 MinerU only

```bash
cd MinerU
docker compose up -d --build
curl http://localhost:8000/openapi.json | jq .info
```
Evidence: `MinerU/docker-compose.yml` lines 1–20, `MinerU/mineru/cli/fast_api.py`
line 125.

### 2.2 Flowchart CLI only (no RAGFlow, no Docker)

```bash
cd flowchart
pip install -r requirements.txt
# Linux: sudo apt install poppler-utils
# Windows: set POPPLER_PATH or use --poppler-path
python cli.py ../vit-test/Air_inlet_flowchart.pdf \
       -o ../vit-test/Air_inlet_flowchart.mmd --json
```
Outputs: `Air_inlet_flowchart.mmd`, `Air_inlet_flowchart_rag.md`,
`Air_inlet_flowchart_graph.json` in `vit-test/`.

Evidence: `flowchart/cli.py`, `flowchart/README.md` lines 27–41.

### 2.3 RAGFlow base stack only (no MinerU, no flowchart hook)

```bash
cd ragflow/docker
docker compose --env-file .env --profile elasticsearch --profile cpu up -d
```
Evidence: `ragflow/docker/README.md`, `docker-compose-base.yml` lines 2–70.

### 2.4 Standalone flowchart overlay on bare RAGFlow

```bash
cd ragflow/docker
docker compose -f docker-compose.yml -f docker-compose.flowchart.yml \
    --profile cpu up -d
```
Evidence: `ragflow/docker/docker-compose.flowchart.yml` lines 1–31;
`vit-test/TESTING.md` §2.

---

## 3. Testing document upload

1. Open `http://localhost:80/`.
2. Create a dataset. Pick **MinerU** as the PDF parser (UI setting; see
   `ragflow/web/src/pages/user-setting/setting-model/modal/mineru-modal/`
   for the configuration dialog).
3. Upload any PDF (e.g. `vit-test/2D_design.pdf`).
4. Verify that the document appears in the dataset with the MinerU parser
   assigned.
5. Tick **Parse on creation** (or trigger parse manually). Watch progress
   in the UI and in container logs:
   ```bash
   docker logs -f <ragflow-cpu container>
   ```

CLI-only smoke test (no UI):

```bash
curl -X POST http://localhost:9380/api/v1/datasets/<id>/documents \
    -H "Authorization: Bearer <API_KEY>" \
    -F "file=@vit-test/2D_design.pdf"
```
Evidence: same endpoint used by `ragflow_ingest.py` lines 68–83.

---

## 4. Testing parser behaviour (MinerU)

Direct test against MinerU's FastAPI:

```bash
curl -X POST http://localhost:8000/file_parse \
  -F "files=@vit-test/2D_design.pdf;type=application/pdf" \
  -F "backend=pipeline" \
  -F "parse_method=auto" \
  -F "return_md=true" \
  -F "return_content_list=true" \
  -F "response_format_zip=true" \
  --output out.zip
unzip -l out.zip
```
The request body mirrors the payload constructed by RAGFlow in
`ragflow/deepdoc/parser/mineru_parser.py` lines 262–278.

Health probe (used by both the compose healthcheck and RAGFlow's
`check_installation`): `GET /openapi.json`.

---

## 5. Testing flowchart extraction

### 5.1 End-to-end via the hook (recommended)

1. Ensure `FLOWCHART_ON_UPLOAD=true`, `FLOWCHART_ROOT=/flowchart-tools`,
   and Poppler + deps are installed inside the ragflow container (§04
   step 8).
2. Upload `vit-test/Air_inlet_flowchart.pdf` via the UI.
3. Expected result (from `vit-test/TESTING.md` §4):
   - `Air_inlet_flowchart.pdf`
   - `Air_inlet_flowchart_rag.md`
   - `Air_inlet_flowchart.mmd`
   - `Air_inlet_flowchart_graph.json`
4. Verify by browsing the dataset — four rows in the document list.

### 5.2 Offline via the CLI

```bash
cd flowchart
python cli.py ../vit-test/Air_inlet_flowchart.pdf \
    -o ../vit-test/Air_inlet_flowchart.mmd --json
```
Compare with committed reference: `vit-test/test_rag.md` and
`vit-test/test_graph.json` were produced from the same PDF on the author's
Windows machine (`Source:` comment at line 5 of `test_rag.md`).

### 5.3 Batch / watch via `ragflow_ingest.py`

```bash
cd flowchart
python ragflow_ingest.py --watch ../vit-test --extract-only
# or, with uploads:
python ragflow_ingest.py --watch ../vit-test \
    --base-url http://127.0.0.1:9380 \
    --api-key $RAGFLOW_API_KEY \
    --dataset-id $RAGFLOW_DATASET_ID
```
Loop mode:
```bash
python ragflow_ingest.py --watch ../vit-test --loop --interval 30
```
Evidence: `flowchart/ragflow_ingest.py` lines 245–355.

### 5.4 Visual debug overlay

```bash
cd flowchart
python run_comparison.py ../vit-test/Air_inlet_flowchart.pdf \
    --out overlay.png --page 0
# also produces debug_detector.png
```
Evidence: `flowchart/run_comparison.py` lines 42–66.

---

## 6. Testing retrieval

1. In a dataset that has both the MinerU-parsed PDF and the `*_rag.md`
   companion, go to **Retrieval Testing** (built-in RAGFlow UI panel).
2. Ask a question from `vit-test/benchmark_queries.yaml`, e.g.:
   - Q1 "What is the first decision or branch after the start of the
     flowchart?"
   - Q3 "List all outgoing paths from the weld-related decision (if
     present)."
   - Q7 "Which standard steel or paint specification numbers appear in
     the flowchart?"
3. Inspect the list of returned chunks. You should see lines from the
   `*_rag.md` such as:
   `From node 16 (Use Welds?) to node 12 (No).`
   (see `vit-test/Cooler_pipe_flowchart_rag.md` line 74).

A/B protocol (from `vit-test/README.md` §13–17):

1. Run the 8 queries against a dataset that contains **only** the PDF
   (MinerU-parsed).
2. Add the `*_rag.md` companion and re-run.
3. Record which chunk ids are returned and whether the flowchart facts
   now appear.

---

## 7. Testing chat / querying

1. Open the RAGFlow UI → Chat.
2. Bind an assistant to the dataset with flowchart documents.
3. Configure an LLM via Settings → Model Providers (see
   `ragflow/conf/llm_factories.json` for built-in providers).
4. Ask a flowchart question; the citations panel should link to chunks
   from `*_rag.md`.

(No automated chat test script is shipped. `vit-test/benchmark_queries.yaml`
is explicitly a manual scoring template.)

---

## 8. Validating outputs

Artefact-level sanity checks:

| Output | Sanity check | Evidence |
|--------|--------------|----------|
| `*.mmd` | Starts with `flowchart TD`; lines match `n\d+["..."]` or `n\d+{".."}` for decision; edges look like `n0 --> n5`. | `flowchart/flowchart/exporter.py` lines 25–35. |
| `*_rag.md` | Contains `# Flowchart extraction (RAG layer)`, then `## Nodes`, `## Edges (directed)`, `## Summary`. | Committed samples under `vit-test/`. |
| `*_graph.json` | `{"nodes":[{id,type,text,bbox?,search_area?}], "edges":[{from,to}]}`. | `exporter.py` lines 94–119. |
| MinerU ZIP | Contains `*.md` plus optional `*.json` and images. | `mineru_parser.py` lines 148–196 unzip logic. |

Smoke test of the hook without the UI:

```bash
docker exec -it <ragflow-cpu container> bash -lc "\
    PYTHONPATH=/flowchart-tools \
    python /flowchart-tools/cli.py /tmp/test_flowchart.pdf \
       -o /tmp/test.mmd --json"
ls /tmp/test*
```

---

## 9. Where to look for logs

| Source | Location |
|--------|----------|
| RAGFlow container (host) | `docker logs <ragflow-cpu>` — includes Python `logging` from the flowchart hook (`LOG.info/warning/error/exception` in `flowchart_on_upload.py`). |
| RAGFlow bind-mount log dir | `ragflow/docker/ragflow-logs/` (created on first start; referenced by `ragflow/docker/docker-compose.yml` line 40). |
| MinerU container | `docker logs mineru-api` — `loguru` formatted (see `MinerU/mineru/cli/fast_api.py` lines 17–21). |
| Flowchart subprocess stdout/stderr | Captured by the hook (`capture_output=True`, `text=True`) and logged on non-zero exit (`flowchart_on_upload.py` lines 89–94). |
| `ragflow_ingest.py` | Uses `logging.basicConfig(level=INFO)` and prints to stderr (`ragflow_ingest.py` lines 246–249). State at `<watch>/.flowchart_ragflow_state.json`. |

---

## 10. Example inputs to use

All live in `vit-test/`:

- `Air_inlet_flowchart.pdf` — small decision-style flowchart; most tests
  use this.
- `Cooler_pipe_flowchart.pdf` — larger multi-branch flowchart.
- `Hose_flowchart.pdf` — compact flowchart, useful quick-run.
- `2D_design.pdf`, `Way of working.pdf`, `Prompts.pdf` — non-flowchart
  PDFs that should *not* trigger the companion hook (filename does not
  contain `flowchart`).

Companion reference outputs (for diffing against your run):

- `vit-test/Cooler_pipe_flowchart.mmd`, `Cooler_pipe_flowchart_rag.md`
- `vit-test/Hose_flowchart.mmd`, `Hose_flowchart_rag.md`
- `vit-test/test.mmd`, `vit-test/test_rag.md`, `vit-test/test_graph.json`
  (for `Air_inlet_flowchart.pdf`).

---

## 11. How to know if something worked

- **System up**: UI loads, `mineru-api` healthcheck green.
- **PDF upload**: document row appears in the dataset with the expected
  parser.
- **MinerU parse**: Parse status becomes "parsed"; chunk count > 0.
  Logs show `[MinerU] invoke api: http://mineru-api:8000/file_parse`.
- **Flowchart hook**: Upload response (UI or REST) lists the three
  companion files; logs show `Flowchart companion added: <filename>`
  (`flowchart_on_upload.py` line 152).
- **Flowchart CLI**: Prints `Processing page N...`, `Graph built: N
  nodes, M edges`, `Exported RAG layer: ...`, `Exported graph JSON: ...`.
- **Retrieval**: Retrieval testing panel returns at least one chunk whose
  source document is `*_rag.md`.
- **Chat**: Answer includes cited chunks that match the flowchart node
  labels in the source image.

---

## 12. Things explicitly NOT tested by the repo

- No pytest / jest config added for the flowchart module.
- `vit-test/benchmark_queries.yaml` is a scoring *template*; no automated
  runner exists.
- The RAGFlow upstream has `ragflow/test/` and `run_tests.py` but those
  are not wired into this stack.
