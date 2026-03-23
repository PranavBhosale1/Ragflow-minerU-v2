# Use your **original** RAGFlow stack (`ragflow-mineru`) — flowchart + MinerU in one place

You do **not** need a second full RAGFlow deployment from `ragflow/docker` in this repo. Keep **one** stack (the one that already has MinerU and your data) and add only what’s missing below.

## 1. Remove the duplicate stack (optional cleanup)

In **Docker Desktop**, stop and remove the extra project created from `Ragflow-minerU-v2/ragflow/docker` (it may show as `docker`, `ragflow-mineru-v2`, or similar). That avoids port confusion and double resource use.

Your **original** `ragflow-mineru` project stays as the only running RAGFlow.

## 2. Files from **this repo** that the original stack must use

The upload hook is **not** in the stock Docker image. You need these files from this clone on disk:

| Path in this repo | Role |
|-------------------|------|
| [`ragflow/api/utils/flowchart_on_upload.py`](../ragflow/api/utils/flowchart_on_upload.py) | Flowchart hook |
| [`ragflow/api/db/services/file_service.py`](../ragflow/api/db/services/file_service.py) | Calls the hook after PDF upload |
| [`flowchart/`](../flowchart/) (whole folder) | `cli.py` + CV/OCR pipeline |

**Ways to get them into the running container:**

- **Bind mounts** (best for dev): in **your** `ragflow-mineru` `docker-compose.yml`, add to the `ragflow` service:

  ```yaml
  volumes:
    - C:/Users/Pranav/Desktop/Ragflow-minerU-v2/flowchart:/flowchart-tools:ro
    - C:/Users/Pranav/Desktop/Ragflow-minerU-v2/ragflow/api:/ragflow/api:ro
  ```

  Adjust paths if your clone lives elsewhere. Use forward slashes on Windows in compose.

- **Or** copy those two Python files into whatever tree your original stack uses and rebuild the image (less flexible).

## 3. Environment variables (same stack as MinerU)

In **your** original stack’s `.env` (or compose `environment:`), add:

```env
FLOWCHART_ON_UPLOAD=true
FLOWCHART_ROOT=/flowchart-tools
FLOWCHART_NAME_SUBSTRING=flowchart
FLOWCHART_POPPLER_PATH=/usr/bin
```

Keep your existing **MinerU** variables (`MINERU_APISERVER`, etc.) — no need to redo MinerU setup.

## 4. One-time install **inside** the RAGFlow container

```bash
docker exec -it <your-ragflow-container> bash
apt-get update && apt-get install -y poppler-utils
pip install -r /flowchart-tools/requirements.txt
```

Use the same Python/pip the app uses (sometimes `/ragflow/.venv/bin/pip`).

## 5. Restart and test

Restart the `ragflow-mineru` stack, then upload a `*flowchart*.pdf` with **Parse on creation**. You should see the PDF plus `*_rag.md`, `*.mmd`, and `*_graph.json` in the same dataset.

## Why this repo’s `ragflow/docker` still exists

It is a **reference** compose layout (with [`docker-compose.flowchart.yml`](../ragflow/docker/docker-compose.flowchart.yml)) for people who deploy from this repo only. You can ignore it if everything runs under **ragflow-mineru**.
