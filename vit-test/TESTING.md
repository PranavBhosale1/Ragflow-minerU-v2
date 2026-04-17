# Testing checklist: MinerU + flowchart RAG companion

**If you already run RAGFlow elsewhere (e.g. `ragflow-mineru` with MinerU):** do **not** spin up a second stack from `ragflow/docker`. Add flowchart to that deployment — see **[`flowchart/ORIGINAL_STACK_SETUP.md`](../flowchart/ORIGINAL_STACK_SETUP.md)**.

---

Follow **one** backend path below if you deploy **from this repo’s** `ragflow/docker` only. Then run the **verification** steps.

---

## 1. Prerequisites (all paths)

- [ ] This repo layout includes `flowchart/cli.py` and `flowchart/flowchart/` (Python package).
- [ ] You have at least one PDF whose **filename contains** `flowchart`, e.g. `Air_inlet_flowchart.pdf` in this folder.
- [ ] RAGFlow is running and you can log in, create a dataset, and upload files.

---

## 2. Path A — RAGFlow in Docker (automatic companions on upload)

### 2.1 Start compose with the flowchart overlay

From **`ragflow/docker`** on your machine (paths in `docker-compose.flowchart.yml` assume this repo layout: `…/Ragflow-minerU-v2/ragflow/docker`).

```bash
cd ragflow/docker
docker compose -f docker-compose.yml -f docker-compose.flowchart.yml --profile cpu up -d
```

Use `--profile gpu` instead if you normally use the GPU service (`ragflow-gpu`).

This overlay mounts:

- **`../../flowchart` → `/flowchart-tools`** — extractor (`cli.py`)
- **`../api` → `/ragflow/api`** — **required** so the container runs **this repo’s** upload hook (prebuilt Hub images alone do not include it)

### 2.2 Install Poppler + Python deps **inside** the running API container (one-time)

The stock image may not include Poppler or EasyOCR. Example for `ragflow-cpu`:

```bash
docker compose -f docker-compose.yml -f docker-compose.flowchart.yml --profile cpu exec ragflow-cpu bash -lc "
  apt-get update && apt-get install -y poppler-utils &&
  pip install -r /flowchart-tools/requirements.txt
"
```

If `pip` fails, try `python3 -m pip` or the path your image uses for RAGFlow’s Python.

### 2.3 Enable the upload hook in `.env`

Edit `ragflow/docker/.env` and set (uncomment / add):

```env
FLOWCHART_ON_UPLOAD=true
FLOWCHART_ROOT=/flowchart-tools
FLOWCHART_NAME_SUBSTRING=flowchart
FLOWCHART_POPPLER_PATH=/usr/bin
```

Restart the stack so the API picks up env:

```bash
docker compose -f docker-compose.yml -f docker-compose.flowchart.yml --profile cpu up -d
```

### 2.4 Confirm the hook is loaded

After §2.1, the container’s `/ragflow/api/utils/flowchart_on_upload.py` should exist and match your clone. Quick check:

```bash
docker compose -f docker-compose.yml -f docker-compose.flowchart.yml --profile cpu exec ragflow-cpu test -f /ragflow/api/utils/flowchart_on_upload.py && echo OK
```

---


## 3. Path B — RAGFlow from source on Windows (no Docker)

### 3.1 System tools

- [ ] Poppler on `PATH`, or set `POPPLER_PATH` to the `bin` folder (see `flowchart/README.md`).
- [ ] `pip install -r flowchart/requirements.txt` in the **same** Python environment that runs `ragflow_server`.

### 3.2 Environment for the API process

Before starting RAGFlow’s backend, set:

```powershell
$env:FLOWCHART_ON_UPLOAD="true"
$env:FLOWCHART_ROOT="C:\Users\Pranav\Desktop\Ragflow-minerU-v2\flowchart"
$env:FLOWCHART_NAME_SUBSTRING="flowchart"
$env:POPPLER_PATH="C:\path\to\poppler\Library\bin"
```

Adjust `FLOWCHART_ROOT` to your clone path.

---

## 4. Verification (UI)

1. Create or open a **dataset** (MinerU can stay configured for PDF parsing).
2. Upload **`Air_inlet_flowchart.pdf`** (from this folder).
3. When the upload hook is **enabled** and working, you should see **four** documents for that one upload:
   - `Air_inlet_flowchart.pdf`
   - `Air_inlet_flowchart_rag.md`
   - `Air_inlet_flowchart.mmd`
   - `Air_inlet_flowchart_graph.json`  
   If you only see the PDF, the API is not running with the hook + env (see §2.4 / Path B), or extraction failed (check logs).

4. If you use **Parse on creation**, wait until all listed files finish parsing (same upload response should list every document so each gets parsed).

5. Open **chat** against that dataset and ask something that only the flowchart text answers (e.g. a label on a specific node).

**Troubleshooting**

- Server log (look for `Flowchart` / `flowchart cli`): if you see  
  `Flowchart PDF '…' uploaded without automatic companions` → set `FLOWCHART_ON_UPLOAD=true` and `FLOWCHART_ROOT`, restart the API.
- To upload **only** `*_rag.md` (faster), set `FLOWCHART_UPLOAD_EXTRAS=false`.

---

## 5. Optional: API-only upload (no upload hook)

If the hook is not enabled, generate files locally and push with the helper:

```powershell
cd ..\flowchart
python ragflow_ingest.py --watch "C:\Users\Pranav\Desktop\Ragflow-minerU-v2\vit-test" --base-url http://127.0.0.1:9380 --api-key YOUR_KEY --dataset-id YOUR_DATASET_ID
```

Use `--extract-only` to test extraction without RAGFlow.

---

## 6. Done when

- [ ] Uploading a `*flowchart*.pdf` yields an extra `*_rag.md` in the same dataset (hook path), **or** you successfully ingest via `ragflow_ingest.py`.
- [ ] Parsing completes and chat retrieves answers from flowchart content.
