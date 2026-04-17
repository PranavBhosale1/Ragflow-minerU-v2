# 04 — Setup Guide (from scratch)

This guide reproduces the exact commands/files shipped in this repository.
When two paths exist (Windows PowerShell vs. Linux/macOS, Docker vs. from
source), both are listed.

---

## 1. Prerequisites

Mandatory (CONFIRMED from Dockerfiles, scripts, docs):

| Tool | Minimum version | Evidence |
|------|-----------------|----------|
| Docker Engine + Compose v2 | Any current; project uses `docker compose` (not `docker-compose`). | Top-level `docker-compose.yml` headers + `start-ragflow-mineru.ps1`. |
| PowerShell 5+ (Windows) or Bash | To run `start-ragflow-mineru.ps1` on Windows; otherwise plain `docker compose`. | `start-ragflow-mineru.ps1`. |
| 16 GB+ RAM, 50 GB+ disk | Stated in `ragflow/CLAUDE.md` line 117. | |

Conditional (depending on chosen sub-path):

| Tool | Needed for | Evidence |
|------|------------|----------|
| NVIDIA driver + nvidia-container-toolkit | `docker-compose.mineru-gpu.yml` overlay. | `docker-compose.mineru-gpu.yml` lines 1–17. |
| Python 3.12 | Running the flowchart CLI on the host or inside a RAGFlow container; also RAGFlow's own Python requirement is ≥3.12 (`ragflow/pyproject.toml` line 8). | |
| Poppler (`pdftoppm`, `pdfinfo`) | `flowchart/cli.py` and the in-container hook. | `flowchart/README.md`, `flowchart/INTEGRATION.md`. |
| Node ≥ 18.20.4 | Only for `ragflow/web/` dev build (not needed for Docker-only runs). | `ragflow/CLAUDE.md` line 113. |
| `uv` Python packager | Only for RAGFlow-from-source development. | `ragflow/CLAUDE.md` line 47–49. |

**OS notes from the repo**

- Windows: `POPPLER_PATH` env var, backslash paths.
  `flowchart/README.md` walks through the specific Poppler build on
  `oschwartz10612/poppler-windows`.
- macOS: `ragflow/docker/docker-compose-macos.yml` exists but is
  explicitly marked unmaintained in `ragflow/docker/README.md` line 21.
- Linux: `sudo apt install poppler-utils`
  (`flowchart/README.md` line 10).

---

## 2. Required environment variables

### 2.1 RAGFlow base stack (`ragflow/docker/.env`)

**This file is NOT shipped with the repo** (see §1 of `docker-compose.yml`:
"Requires ragflow/docker/.env (copy from ragflow/docker if missing)"). You
must create it before anything starts. The canonical variables documented
in `ragflow/docker/README.md`:

```env
# Document engine (pick ONE) and runtime (pick ONE):
COMPOSE_PROFILES=elasticsearch,cpu        # or infinity,cpu / elasticsearch,gpu / ...

# Search engine
STACK_VERSION=8.11.3
ES_PORT=1200
ELASTIC_PASSWORD=change-me
DOC_ENGINE=elasticsearch                  # or infinity / opensearch / oceanbase / seekdb

# MySQL
MYSQL_PASSWORD=change-me
MYSQL_PORT=3306
EXPOSE_MYSQL_PORT=5455

# MinIO
MINIO_PORT=9000
MINIO_CONSOLE_PORT=9001
MINIO_USER=admin
MINIO_PASSWORD=change-me

# Redis
REDIS_PORT=6379
REDIS_PASSWORD=change-me

# RAGFlow app
RAGFLOW_IMAGE=infiniflow/ragflow:v0.24.0
SVR_WEB_HTTP_PORT=80
SVR_WEB_HTTPS_PORT=443
SVR_HTTP_PORT=9380
ADMIN_SVR_HTTP_PORT=9381
SVR_MCP_PORT=9382
GO_HTTP_PORT=9384
GO_ADMIN_PORT=9383
MEM_LIMIT=8073741824
TZ=Asia/Shanghai
```

Authoritative references:
- `ragflow/docker/README.md` lines 23–115.
- Variable use sites in `ragflow/docker/docker-compose.yml` lines 32–40
  and `ragflow/docker/docker-compose-base.yml`.

### 2.2 MinerU container (already set by top-level compose)

| Var | Value | Set where |
|-----|-------|-----------|
| `MINERU_MODEL_SOURCE` | `local` | `docker-compose.yml` line 34 |
| `MINERU_PORT` | default `8000` | `docker-compose.yml` line 32 |
| `NVIDIA_VISIBLE_DEVICES` | `all` (GPU overlay only) | `docker-compose.mineru-gpu.yml` line 15 |

### 2.3 RAGFlow ↔ MinerU wiring (set automatically by top-level compose)

| Var | Value | Set where |
|-----|-------|-----------|
| `MINERU_APISERVER` | `http://mineru-api:8000` | `docker-compose.yml` lines 53, 67 |

### 2.4 Flowchart hook

Add to `ragflow/docker/.env` (or to the service `environment:` block):

```env
FLOWCHART_ON_UPLOAD=true
FLOWCHART_ROOT=/flowchart-tools
FLOWCHART_NAME_SUBSTRING=flowchart        # optional; default "flowchart"
FLOWCHART_POPPLER_PATH=/usr/bin           # Linux; Windows: your Poppler bin dir
FLOWCHART_SUBPROCESS_TIMEOUT=900          # optional; default 900 seconds
FLOWCHART_UPLOAD_EXTRAS=true              # optional; default true
```

Evidence: `ragflow/api/utils/flowchart_on_upload.py` lines 29–40, 42–114;
`flowchart/INTEGRATION.md` env table; `flowchart/ORIGINAL_STACK_SETUP.md`
section 3.

### 2.5 `ragflow_ingest.py` (optional batch uploader)

| Var | Example |
|-----|---------|
| `RAGFLOW_BASE_URL` | `http://127.0.0.1:9380` |
| `RAGFLOW_API_KEY` | `ragflow-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| `RAGFLOW_DATASET_ID` | dataset UUID from UI |
| `POPPLER_PATH` | Poppler `bin` directory |

Evidence: `flowchart/ragflow_ingest.py` lines 268–271.

---

## 3. Optional vs. mandatory dependencies

| Item | Mandatory? | Why |
|------|-----------|-----|
| RAGFlow, MySQL, MinIO, Redis, one search engine | YES | Core app. |
| MinerU | YES, for PDF parsing with the configured dataset. | Without it, PDFs fall back to legacy parsers. |
| Flowchart CLI (host or in-container) | OPTIONAL but required for the custom feature. | Without it the system runs as vanilla RAGFlow + MinerU. |
| Poppler | Mandatory **if** flowchart extraction is enabled. | pdf2image binding. |
| GPU | Optional; makes MinerU VLM usable (CPU VLM is slow). | `Dockerfile.api-cpu` comment line 3. |
| TEI (`tei-cpu` / `tei-gpu` profiles) | Optional; alternative embedder. | `docker-compose-base.yml` lines 244–276. |
| Kibana, OceanBase, Sandbox executor, OpenSearch | Optional profiles. | same. |

---

## 4. Installation order (recommended)

### Path A — Everything in Docker (recommended, matches the repo)

1. Install Docker and (for GPU path) nvidia-container-toolkit.
2. Clone the repository.
3. `cp ragflow/docker/.env.single-bucket-example ragflow/docker/.env` —
   but you must re-write most values. Better: author `ragflow/docker/.env`
   from scratch using §2.1 as a checklist. Keep `COMPOSE_PROFILES` at
   **minimum** `elasticsearch,cpu` (or any supported combination).
4. Add the flowchart-hook variables from §2.4.
5. From repo root: `docker compose --env-file ragflow/docker/.env up -d --build`.
   - First build downloads **several GB** of MinerU weights.
   - On Windows use `.\start-ragflow-mineru.ps1 -Build` which does the
     same thing with the env-file resolved to the right path.
   - For GPU MinerU:
     `.\start-ragflow-mineru.ps1 -MineruGpu -Build`
     or
     `docker compose --env-file ragflow/docker/.env -f docker-compose.yml -f docker-compose.mineru-gpu.yml up -d --build`.
6. Wait until the MinerU healthcheck is green
   (`curl http://localhost:${MINERU_PORT:-8000}/openapi.json`).
7. Wait until RAGFlow UI at `http://localhost:${SVR_WEB_HTTP_PORT:-80}`
   responds.
8. **One-time, inside the ragflow container**, install Poppler + Python
   deps (only needed if the flowchart hook will be used):
   ```bash
   docker exec -it <ragflow container name> bash -lc "\
     apt-get update && apt-get install -y poppler-utils && \
     pip install -r /flowchart-tools/requirements.txt"
   ```
   Evidence: `vit-test/TESTING.md` §2.2, `flowchart/ORIGINAL_STACK_SETUP.md`
   §4.
9. Restart the ragflow container so it sees the hook env vars and deps:
   `docker compose --env-file ragflow/docker/.env restart ragflow-cpu`
   (or `ragflow-gpu`).

### Path B — RAGFlow from source on Windows (no Docker for RAGFlow)

Documented in `vit-test/TESTING.md` §3:

1. Install Poppler; set `POPPLER_PATH`.
2. `cd flowchart && pip install -r requirements.txt` in the **same** venv
   that will run `ragflow_server`.
3. Start RAGFlow from source with the env vars from §2.4.

This path is referenced but the repo does not include a RAGFlow-from-source
start script at root — use RAGFlow's own `docker/launch_backend_service.sh`
(`ragflow/CLAUDE.md` line 58).

### Path C — flowchart only (no RAGFlow)

1. Python 3.10+ virtualenv.
2. `cd flowchart && pip install -r requirements.txt`.
3. Install Poppler.
4. `python cli.py path/to/flowchart.pdf -o out.mmd --json`.

Outputs land beside `-o`.

---

## 5. Build order (when building from Dockerfiles)

1. `mineru-api` (slow; pre-downloads weights). Build target is
   `./MinerU` with `docker/Dockerfile.api-cpu` (default) or
   `docker/Dockerfile.api-gpu` (overlay).
2. Base infra services (`elasticsearch`/`infinity`, `mysql`, `minio`,
   `redis`, optional `tei-*`) start automatically via the profile
   selection.
3. `ragflow-cpu` / `ragflow-gpu` — uses `${RAGFLOW_IMAGE}`; no local
   build. If you want a local RAGFlow image, use
   `ragflow/Dockerfile` (upstream; not referenced from the top-level
   compose) and set `RAGFLOW_IMAGE` to your tag.

---

## 6. Service startup order

`docker-compose.yml` enforces:

- `ragflow-cpu` depends on `mysql` (healthy) and `mineru-api` (started)
  — lines 45–50.
- `ragflow-gpu` same — lines 60–65.
- MinerU itself depends only on its image build and its own healthcheck
  (internal `curl` on `/openapi.json`).

There is **no explicit dependency** between RAGFlow and the document
engine (ES/Infinity/...). Upstream RAGFlow retries internally; plan for a
60–120 s warm-up after `up -d`.

---

## 7. Commands to run

```bash
# Full stack (CPU MinerU)
docker compose --env-file ragflow/docker/.env up -d --build
# Full stack (GPU MinerU)
docker compose --env-file ragflow/docker/.env \
    -f docker-compose.yml -f docker-compose.mineru-gpu.yml up -d --build

# Windows equivalents
.\start-ragflow-mineru.ps1 -Build
.\start-ragflow-mineru.ps1 -MineruGpu -Build

# Subsequent restarts (no rebuild)
.\start-ragflow-mineru.ps1
docker compose --env-file ragflow/docker/.env up -d

# Stop
docker compose --env-file ragflow/docker/.env down
```

---

## 8. How to verify health

- `curl http://localhost:${MINERU_PORT:-8000}/openapi.json` → 200 JSON
  (matches the healthcheck on `docker-compose.yml` line 38).
- `docker ps` shows `mineru-api` with status `healthy`.
- `curl http://localhost:${SVR_HTTP_PORT:-9380}/v1/system/version` (or
  any RAGFlow public endpoint; exact path is in `ragflow/api/apps/`).
- Browse `http://localhost:${SVR_WEB_HTTP_PORT:-80}/` — RAGFlow UI.
- From inside ragflow container, confirm the hook:
  `test -f /ragflow/api/utils/flowchart_on_upload.py && echo OK` — see
  `vit-test/TESTING.md` §2.4.
- From inside ragflow container, confirm the flowchart tools:
  `ls /flowchart-tools && python -c "import flowchart.cli"`.

---

## 9. Common setup pitfalls (evidence-backed)

| Pitfall | Evidence |
|---------|----------|
| Forgetting `--env-file ragflow/docker/.env` when running compose from repo root — `COMPOSE_PROFILES` is then unset and RAGFlow does not start. | `docker-compose.yml` lines 3–12. |
| Missing Poppler inside the RAGFlow container causes the hook to log `Poppler executables not found on PATH`. | `flowchart/flowchart/pdf_converter.py` lines 17–25. |
| `FLOWCHART_ON_UPLOAD` not set → INFO log "uploaded without automatic companions" but no failure; easy to miss. | `flowchart_on_upload.py` lines 167–172. |
| Mounting all of `../api` over `/ragflow/api` replaces other upstream files with host paths. Docs warn: "Do NOT mount all of ../api". | Top-level `docker-compose.yml` line 55; `ragflow/docker/docker-compose.flowchart.yml` line 11. |
| Running `docker compose` from `MinerU/` or `ragflow/docker/` alone brings up a **second** RAGFlow project; the doc `flowchart/ORIGINAL_STACK_SETUP.md` warns to stop the duplicate. | `flowchart/ORIGINAL_STACK_SETUP.md` §1. |
| First MinerU build downloads model weights over HuggingFace; can time out in restricted networks. Upstream MinerU has an `HF_ENDPOINT` mirror option. | `ragflow/docker/README.md` line 99 (mentions `HF_ENDPOINT`), `Dockerfile.api-cpu` line 24. |
| OCR first-run latency: EasyOCR downloads its English model lazily — the first PDF parse can time out near `FLOWCHART_SUBPROCESS_TIMEOUT=900 s`. Pre-warm by running the CLI once. | `flowchart/flowchart/ocr.py` line 5 (`# Lazy import to avoid startup cost`). |

---

## 10. Troubleshooting notes from the repo

From `vit-test/TESTING.md` §4:

- If you only see the PDF after upload, check: `FLOWCHART_ON_UPLOAD=true`,
  `FLOWCHART_ROOT` correct, container has Poppler + deps.
- Set `FLOWCHART_UPLOAD_EXTRAS=false` to upload only `*_rag.md` (faster).
- To test extraction without touching RAGFlow, use
  `python ragflow_ingest.py --watch <dir> --extract-only`.

From `flowchart/README.md`:

- Poppler path handling accepts either the `bin` folder or the direct
  `pdftoppm.exe` path — see `resolve_poppler_path` in
  `flowchart/flowchart/pdf_converter.py` lines 27–54.

From `flowchart/ORIGINAL_STACK_SETUP.md` §5:

- After adding env vars, restart the stack so the API picks them up.

---

## 11. Minimal happy-path for a new evaluator

```bash
# 1. Create ragflow/docker/.env with COMPOSE_PROFILES=elasticsearch,cpu
#    and all the vars listed in §2.1.

# 2. Add the 4 flowchart vars from §2.4.

# 3. Boot:
docker compose --env-file ragflow/docker/.env up -d --build

# 4. Wait ~5 min for healthchecks.

# 5. Install deps inside ragflow container once:
docker exec -it <ragflow-cpu container> bash -lc \
  "apt-get update && apt-get install -y poppler-utils && \
   pip install -r /flowchart-tools/requirements.txt"

docker compose --env-file ragflow/docker/.env restart ragflow-cpu

# 6. Open http://localhost:80/ ; create dataset; upload vit-test/Air_inlet_flowchart.pdf.
#    Expect 4 documents to appear (PDF + .mmd + _rag.md + _graph.json).
```
