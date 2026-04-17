Flowchart extractor — classical CV pipeline

This project converts a PDF flowchart into Mermaid flowchart code using a classical computer-vision pipeline (local only).

Install (Python):

pip install -r requirements.txt

System deps:
- Ubuntu: `sudo apt install poppler-utils`
- Windows: download poppler binaries and add the `bin` folder to PATH or set the `POPPLER_PATH` environment variable.

Windows quick instructions:
1. Download poppler for Windows (recommended builds): https://github.com/oschwartz10612/poppler-windows/releases
2. Unzip and use the folder that contains **`pdftoppm.exe`**. For the usual release layout it is **`…\poppler-VERSION\Library\bin`** (not the zip root).
3. Either add that `bin` folder to your PATH, or set **`POPPLER_PATH`** / `--poppler-path` to:
   - the **`bin` folder** (e.g. `...\poppler-25.12.0\Library\bin`), **or**
   - the full path to **`pdftoppm.exe`** — the CLI accepts both and resolves the folder automatically.

```
set POPPLER_PATH=C:\Users\Pranav\Desktop\poppler-25.12.0\Library\bin\pdftoppm.exe
python cli.py input.pdf --poppler-path "C:\Users\Pranav\Desktop\poppler-25.12.0\Library\bin\pdftoppm.exe"
```

You can use the `bin` directory path instead of the `.exe` if you prefer.

Quick usage:

python cli.py path/to/flowchart.pdf

Outputs in the current directory (by default):

- `flowchart.mmd` — Mermaid source
- `flowchart_rag.md` — plain-language nodes/edges for **RAG / embedding** (recommended for RAGFlow)
- Optional: `flowchart_graph.json` — structured graph (`--json`), same schema family as a sample `flowchart.json` in this folder

Flags:

- `--no-rag-text` — skip the `*_rag.md` companion
- `--rag-out PATH` — custom path for the RAG markdown
- `--json` / `--json-out PATH` — emit JSON for downstream tools

See [INTEGRATION.md](INTEGRATION.md) for RAGFlow + MinerU ingestion patterns.

**Batch automation:** [ragflow_ingest.py](ragflow_ingest.py) scans a directory for `*flowchart*.pdf`, generates RAG files, and uploads them to a dataset via the RAGFlow API (optional `--loop`).
