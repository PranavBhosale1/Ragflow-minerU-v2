# RAGFlow + MinerU + flowchart extractor (v1)

## Ingestion strategy (recommended)

Use **companion uploads** into the **same RAGFlow dataset** as the MinerU-parsed PDF:

1. Upload and parse the original PDF with **MinerU** (text, tables, general layout).
2. Run the flowchart CLI on flowchart-heavy PDFs (or single-page exports):

   ```bash
   cd flowchart
   python cli.py path/to/diagram.pdf -o outputs/diagram.mmd --json
   ```

3. Upload the generated **RAG layer** markdown (`diagram_rag.md` by default) to the **same knowledge base**.

Naming convention (keeps chunks traceable):

| Artifact | Example | Role |
|----------|---------|------|
| Source PDF | `spec_section_3.pdf` | MinerU ingestion |
| Mermaid (optional archive) | `spec_section_3.mmd` | Human review / diagrams |
| RAG layer (required for search) | `spec_section_3_rag.md` | Embeddings target for flowchart facts |
| Structured graph (optional) | `spec_section_3_graph.json` | Apps, audits, UI, non-RAG tools |

If you prefer a **single file** per document, concatenate MinerU’s exported markdown and `*_rag.md` with a clear heading (e.g. `## Flowchart extraction`) in a preprocessing script, then upload **one** merged `.md` instead of two files.

## RAGFlow settings

- Keep **MinerU** as the PDF parser for the main PDF upload.
- Treat `*_rag.md` as a normal text/markdown upload (built-in chunking is fine).

## Automatic companion on upload (RAGFlow server)

If you run a patched tree that includes [`ragflow/api/utils/flowchart_on_upload.py`](../ragflow/api/utils/flowchart_on_upload.py), the API will **during the same upload request** add companion files (by default `*_rag.md`, `*.mmd`, `*_graph.json`) when:

- The file is a **PDF**, and
- The stored filename contains the substring from **`FLOWCHART_NAME_SUBSTRING`** (default: `flowchart`), and
- **`FLOWCHART_ON_UPLOAD=true`**, and
- **`FLOWCHART_ROOT`** points to the directory that contains **`cli.py`** (this repo’s `flowchart/` folder).

Also set **`POPPLER_PATH`** or **`FLOWCHART_POPPLER_PATH`** to Poppler’s `bin` directory on the **machine running the RAGFlow API** (Docker: install Poppler in the image or mount tools + deps).

The companion file appears in the upload response together with the PDF, so **Parse on creation** runs on **both** documents when enabled in the UI.

Environment variables:

| Variable | Meaning |
|----------|---------|
| `FLOWCHART_ON_UPLOAD` | `true` / `1` to enable |
| `FLOWCHART_ROOT` | Absolute path to folder containing `cli.py` |
| `FLOWCHART_NAME_SUBSTRING` | Default `flowchart` |
| `FLOWCHART_POPPLER_PATH` or `POPPLER_PATH` | Poppler `bin` |
| `FLOWCHART_SUBPROCESS_TIMEOUT` | Seconds (default `900`) |
| `FLOWCHART_UPLOAD_EXTRAS` | `true` (default): also upload `.mmd` and `_graph.json`; `false`: only `*_rag.md` |

The RAGFlow process must be able to run `python cli.py` (same dependencies as the standalone flowchart project: see `flowchart/requirements.txt`).

**Concrete setup + Docker compose overlay:** see [`vit-test/TESTING.md`](../vit-test/TESTING.md).

## CLI reference

- Default outputs next to `-o`: `<stem>_rag.md` (always, unless `--no-rag-text`).
- `--json` writes `<stem>_graph.json` (override with `--json-out`).
- Legacy `flowchart.json` in this repo is a **sample**; the CLI emits `*_graph.json` with `nodes` / `edges` and optional `bbox` / `search_area` when present on nodes.

## Automated scan + upload (filename contains `flowchart`)

Script: [`ragflow_ingest.py`](ragflow_ingest.py) scans a folder (recursively) for `*.pdf` whose name contains a substring (default: `flowchart`), runs the extractor, uploads `*_rag.md` to a dataset via the RAGFlow HTTP API, then calls **Start parsing** (`POST /api/v1/datasets/{id}/chunks`).

**Prerequisites:** RAGFlow API key (Model providers / API token), target **dataset ID**, Poppler on `PATH` or `POPPLER_PATH`, `pip install requests` (listed in `requirements.txt`).

**One-shot (process all matching PDFs once):**

```powershell
cd flowchart
$env:RAGFLOW_API_KEY="your_api_key"
$env:RAGFLOW_DATASET_ID="your_kb_id"
$env:RAGFLOW_BASE_URL="http://127.0.0.1:9380"
$env:POPPLER_PATH="C:\path\to\poppler\Library\bin"
python ragflow_ingest.py --watch "C:\path\to\vit-test"
```

**Keep watching** (poll every 30s; drop new `*flowchart*.pdf` files and they are processed automatically):

```powershell
python ragflow_ingest.py --watch "C:\path\to\vit-test" --loop --interval 30
```

- `--include-extras` — also upload `.mmd` and `_graph.json`.
- `--no-parse` — upload only (parse later from the UI).
- `--extract-only` — local extraction only (no RAGFlow calls).
- State is stored in `<watch>\.flowchart_ragflow_state.json` to avoid re-uploading unchanged PDFs; use `--force` to redo.

**Note:** This does not replace MinerU for the original PDF; run it **in addition** so the dataset contains both the MinerU output and the flowchart RAG layer. Typical flow: upload PDFs with MinerU as usual, then run this script on the same folder (or copy flowchart PDFs here) so companion markdown is added and parsed.
