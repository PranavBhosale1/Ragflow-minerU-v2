# VIT test documents

**→ Use your existing Docker stack (e.g. ragflow-mineru):** [../flowchart/ORIGINAL_STACK_SETUP.md](../flowchart/ORIGINAL_STACK_SETUP.md)  
**→ Testing from this repo’s `ragflow/docker` only:** [TESTING.md](TESTING.md)

Place PDFs shared for validation (e.g. “Doc to be sent to VIT”) in this directory.

## Layout

- Add your `.pdf` files here for reproducible runs.
- Companion outputs from the flowchart extractor are written next to the PDF when you run the CLI from another directory, or use explicit `-o` / `--rag-out` / `--json` paths.

## A/B workflow (MinerU vs flowchart RAG layer)

1. Ingest the same PDF through RAGFlow with **MinerU** only; note retrieval gaps on flowchart questions.
2. Run `python -m flowchart.cli` (from repo root with `PYTHONPATH=flowchart` or from inside `flowchart/`) on the PDF; upload the generated `*_rag.md` (and optionally merge with MinerU markdown) into the **same dataset**.
3. Re-run queries from [`benchmark_queries.yaml`](benchmark_queries.yaml) (eight template questions + scoring notes) and compare hit quality.

This folder can be gitignored for proprietary PDFs; keep the README and benchmark file in version control.

## Next steps (after your PDFs are here)

1. **Dependencies (flowchart extractor, one-time per machine)**  
   From the `flowchart` directory: `pip install -r requirements.txt`  
   Install **Poppler** for Windows and either add its `bin` folder to `PATH` or set `POPPLER_PATH` (see [`../flowchart/README.md`](../flowchart/README.md)).

2. **Run extraction on each flowchart PDF** (outputs land next to `-o`):  
   ```powershell
   cd flowchart
   python cli.py "..\vit-test\YourFile.pdf" -o "..\vit-test\YourFile.mmd" --json
   ```  
   You should get `YourFile.mmd`, `YourFile_rag.md` (upload this to RAG), and `YourFile_graph.json` (optional).

3. **RAGFlow**  
   - Add or keep the **same PDF** in your dataset with **MinerU** as the PDF parser.  
   - **Also upload** `YourFile_rag.md` to that **same** knowledge base (plain markdown upload is fine).  
   - Ask questions from [`benchmark_queries.yaml`](benchmark_queries.yaml) (customize wording to match your diagrams).

4. **Compare**  
   Run the same questions **before** and **after** adding `*_rag.md` and note whether retrieved chunks include the flowchart facts.

## Automation (filename contains `flowchart`)

Use [`../flowchart/ragflow_ingest.py`](../flowchart/ragflow_ingest.py): it scans this folder (recursively) for `*flowchart*.pdf`, generates `*_rag.md`, uploads to RAGFlow, and starts parsing. See [`../flowchart/INTEGRATION.md`](../flowchart/INTEGRATION.md) for env vars (`RAGFLOW_API_KEY`, `RAGFLOW_DATASET_ID`, `POPPLER_PATH`) and flags (`--loop`, `--extract-only`, etc.).
