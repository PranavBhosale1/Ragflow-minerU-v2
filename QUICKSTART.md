# QUICKSTART — Ragflow-minerU-v2

Exact steps to bring the full stack up on a fresh machine. This guide is
derived from `handover_pack/04_SETUP_GUIDE.md` (evidence-backed) and
condensed to a single happy-path plus the most common alternatives.

---

## 1. Prerequisites

| Tool | Minimum | Notes |
|------|---------|-------|
| Docker Engine + Compose v2 | current | Uses `docker compose`, not `docker-compose`. |
| Disk | 50 GB+ | MinerU image + model weights + MinIO data. |
| RAM | 16 GB+ | Per `ragflow/CLAUDE.md` line 117. |
| NVIDIA driver + `nvidia-container-toolkit` | optional | Only for `docker-compose.mineru-gpu.yml`. |
| PowerShell 5+ | optional | Only if you use `start-ragflow-mineru.ps1` on Windows. |
| Poppler (inside RAGFlow container) | needed for flowchart hook | `apt-get install -y poppler-utils` (step 4). |
| Python 3.10+ | needed only for Path C (flowchart-only) | CLI also uses Poppler on the host. |

---

## 2. Clone and configure

```bash
git clone <this-repo-url> Ragflow-minerU-v2
cd Ragflow-minerU-v2

# Create the .env file that docker-compose.yml reads.
cp .env.example ragflow/docker/.env
$EDITOR ragflow/docker/.env
```

Mandatory things to change in `ragflow/docker/.env` before first boot:

- `ELASTIC_PASSWORD`, `MYSQL_PASSWORD`, `MINIO_PASSWORD`,
  `REDIS_PASSWORD` — set strong secrets.
- `COMPOSE_PROFILES` — pick ONE doc engine plus ONE runtime, e.g.
  `elasticsearch,cpu` (default) or `infinity,gpu`. Valid tokens are
  listed in `.env.example`.
- `TZ` — your timezone.

Optional but recommended for the custom feature:

```env
FLOWCHART_ON_UPLOAD=true
FLOWCHART_ROOT=/flowchart-tools
FLOWCHART_NAME_SUBSTRING=flowchart
FLOWCHART_POPPLER_PATH=/usr/bin
FLOWCHART_SUBPROCESS_TIMEOUT=900
FLOWCHART_UPLOAD_EXTRAS=true
```

---

## 3. Bring up the stack

### 3a. Linux / macOS — CPU MinerU (default)

```bash
docker compose --env-file ragflow/docker/.env up -d --build
```

First build downloads several GB of MinerU model weights. Budget
15–30 minutes depending on network.

### 3b. Linux / macOS — GPU MinerU

```bash
docker compose --env-file ragflow/docker/.env \
  -f docker-compose.yml \
  -f docker-compose.mineru-gpu.yml \
  up -d --build
```

### 3c. Windows

```powershell
.\start-ragflow-mineru.ps1 -Build            # CPU
.\start-ragflow-mineru.ps1 -MineruGpu -Build # GPU
```

Subsequent restarts (no rebuild):

```bash
docker compose --env-file ragflow/docker/.env up -d
# or on Windows:
.\start-ragflow-mineru.ps1
```

### Stop

```bash
docker compose --env-file ragflow/docker/.env down
```

---

## 4. One-time in-container deps (only if you want the flowchart hook)

The RAGFlow image does **not** ship with Poppler or the flowchart
Python deps. If `FLOWCHART_ON_UPLOAD=true`, install them once:

```bash
# Get the container name
docker ps --format '{{.Names}}' | grep ragflow

# Install Poppler + Python deps inside it
docker exec -it <ragflow-cpu-container> bash -lc "
  apt-get update && apt-get install -y poppler-utils &&
  pip install -r /flowchart-tools/requirements.txt
"

# Restart so the API re-reads env + deps
docker compose --env-file ragflow/docker/.env restart ragflow-cpu
# (or ragflow-gpu if that's your profile)
```

---

## 5. Verify

| Check | Expected |
|-------|----------|
| `curl http://localhost:${MINERU_PORT:-8000}/openapi.json` | 200 JSON |
| `docker ps` | `mineru-api` shows `healthy` |
| `http://localhost:${SVR_WEB_HTTP_PORT:-80}/` | RAGFlow UI loads |
| Inside ragflow container: `test -f /ragflow/api/utils/flowchart_on_upload.py && echo OK` | `OK` |
| Inside ragflow container: `ls /flowchart-tools/cli.py` | exists |

---

## 6. End-to-end smoke test

1. Log into the RAGFlow UI.
2. Create a dataset; keep MinerU as the PDF parser.
3. Enable **Parse on creation**.
4. Upload `vit-test/Air_inlet_flowchart.pdf`.
5. With the hook enabled you should see **four** documents appear:
   - `Air_inlet_flowchart.pdf`
   - `Air_inlet_flowchart_rag.md`
   - `Air_inlet_flowchart.mmd`
   - `Air_inlet_flowchart_graph.json`
6. Wait for parsing to finish.
7. Open chat and ask a question that only the flowchart text can
   answer (e.g. a label on one of the nodes — see
   `vit-test/benchmark_queries.yaml`).

If only the PDF appears:

- `FLOWCHART_ON_UPLOAD` is not `true`, or
- `FLOWCHART_ROOT` is wrong, or
- Poppler / deps were not installed inside the container, or
- The PDF filename does not contain `flowchart`.

Check `docker logs <ragflow-cpu-container> | grep -i flowchart`.

---

## 7. Alternative paths

### Path C — Flowchart only (no RAGFlow)

Run the CV + OCR pipeline on the host:

```bash
cd flowchart
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Linux: sudo apt install poppler-utils
# macOS: brew install poppler
python cli.py path/to/diagram.pdf -o diagram.mmd --json
# Outputs: diagram.mmd, diagram_rag.md, diagram_graph.json
```

### Batch / watch mode against an existing RAGFlow

```bash
export RAGFLOW_BASE_URL=http://127.0.0.1:9380
export RAGFLOW_API_KEY=ragflow-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
export RAGFLOW_DATASET_ID=<uuid-from-UI>
export POPPLER_PATH=/usr/bin  # or the Windows bin folder

cd flowchart
python ragflow_ingest.py --watch ../vit-test --loop --interval 30
```

Useful flags: `--extract-only`, `--no-parse`, `--include-extras`,
`--force`.

---

## 8. Common pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Forgot `--env-file ragflow/docker/.env` | `COMPOSE_PROFILES` unset, RAGFlow services don't start | Always pass `--env-file`. |
| Poppler missing inside container | Hook log: `Poppler executables not found on PATH` | Run step 4. |
| Second RAGFlow project running | Ports clash; compose sees two stacks | Stop the duplicate project in Docker Desktop. |
| `FLOWCHART_SUBPROCESS_TIMEOUT` too short for first run | First PDF times out while EasyOCR model downloads | Pre-warm by running `python cli.py` once on any PDF, or keep the default 900 s. |
| Uploading to a KB that already has the same filename | Companions saved as `_rag.md_1`, `_rag.md_2`, … | Delete old docs or change dataset. |
| MinerU first build fails behind restrictive network | Cannot reach HuggingFace | Set `HF_ENDPOINT` mirror inside `MinerU/docker/Dockerfile.api-cpu` environment. |

More pitfalls: `handover_pack/04_SETUP_GUIDE.md` §9–§10.
