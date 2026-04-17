# HANDOVER — Ragflow-minerU-v2

This document summarises exactly what is upstream, what is custom, what
is working, and what is partial. It is the condensed version of
`handover_pack/06_CUSTOM_WORK_VS_BASE_SYSTEM.md` and
`handover_pack/07_CURRENT_STATUS_AND_LIMITATIONS.md`. Evidence lives in
the `handover_pack/` directory — every claim there is tagged
**CONFIRMED**, **INFERRED**, or **UNKNOWN / NEEDS MANUAL INPUT** with
file:line references.

---

## 1. What is UPSTREAM (imported, third-party)

| Tree | Project | Upstream | License | Version | Notes |
|------|---------|----------|---------|---------|-------|
| `ragflow/` | InfiniFlow RAGFlow | <https://github.com/infiniflow/ragflow> | Apache-2.0 (`ragflow/LICENSE`) | 0.24.0 (`ragflow/pyproject.toml` L3) | Essentially untouched except for a 7-line patch (see §2) and one new file. The entire `web/`, `rag/`, `deepdoc/`, `api/apps/`, `helm/`, `docker/` surface is upstream. |
| `MinerU/` | OpenDataLab MinerU | <https://github.com/opendatalab/MinerU> | **AGPL-3.0** (`MinerU/LICENSE.md`) | `mineru[api,pipeline,vlm]>=2.6.3,<3` — installed from pip at Docker build time | The tree is a convenient vendor copy; the container pip-installs MinerU, it does not build from this tree. Only `MinerU/mineru/backend/vlm/vlm_analyze.py` is actually used (COPY-ed over the pip-installed file). |
| `ragflow/deepdoc/parser/mineru_parser.py` | Upstream RAGFlow | same as `ragflow/` | Apache-2.0 | upstream | Provides the HTTP bridge RAGFlow→MinerU. **No modification needed.** |

All upstream `LICENSE`, `README*`, `CLAUDE.md`, `AGENTS.md`,
`SECURITY.md`, `MinerU_CLA.md`, and notice-files remain in place.

> **AGPL note.** MinerU is AGPL-3.0. Because the combined stack exposes
> MinerU functionality over a network, any public / customer-facing
> deployment of this repository inherits AGPL network-provision
> obligations. **Do a legal review before distributing binaries or
> hosting publicly.**

---

## 2. What is CUSTOM (written for this project)

Line counts from `wc -l`; see `handover_pack/06_*.md` table for
per-file evidence.

### 2.1 The flowchart module — `flowchart/` (~1,100 LOC)

A **classical-CV + OCR** pipeline that extracts node/edge text from
flowchart PDFs and emits three artefacts:

| File | LOC | Role |
|------|----:|------|
| `flowchart/cli.py` | 132 | Argparse entry; defines `process_pdf()`. |
| `flowchart/flowchart/__init__.py` | 10 | Package manifest. |
| `flowchart/flowchart/pdf_converter.py` | 91 | Poppler resolution + `pdf_to_images`. |
| `flowchart/flowchart/preprocess.py` | 50 | Grayscale / threshold / `mask_shapes`. |
| `flowchart/flowchart/shapes.py` | 50 | OpenCV contour → process/decision. |
| `flowchart/flowchart/ocr.py` | 25 | Per-node EasyOCR crop. |
| `flowchart/flowchart/lines.py` | 253 | Skeletonise, simplify, arrow-direction heuristic. |
| `flowchart/flowchart/graph_builder.py` | 54 | `networkx.DiGraph` + cycle reduction. |
| `flowchart/flowchart/exporter.py` | 119 | Mermaid / `*_rag.md` / `*_graph.json` emitters. |
| `flowchart/ragflow_ingest.py` | 359 | Watch directory, run CLI, POST to RAGFlow API. |
| `flowchart/run_comparison.py` | 141 | Visual debug overlay (see §4 — fragile). |
| `flowchart/requirements.txt` | 7 | Runtime deps. |

Output format notes:
- `*.mmd` — Mermaid source (human readable).
- `*_rag.md` — one English sentence per node/edge, designed for the
  RAGFlow default chunker.
- `*_graph.json` — structured graph with `nodes`, `edges`, optional
  `bbox` / `search_area`.

### 2.2 Glue inside RAGFlow

| File | LOC | Role |
|------|----:|------|
| `ragflow/api/utils/flowchart_on_upload.py` | **180 (new file)** | Decides whether a PDF upload triggers companion generation; runs the CLI; uploads `*_rag.md`, `*.mmd`, `*_graph.json` back into the same knowledge base via `FileService.upload_document`. |
| `ragflow/api/db/services/file_service.py` | **+7 (patch)** | Calls `maybe_append_flowchart_rag_document` after PDF upload. Try/except fenced so hook failures cannot break the primary upload. |
| `ragflow/docker/docker-compose.flowchart.yml` | 31 | Overlay that mounts the two files + `flowchart/` into the RAGFlow container when deploying from `ragflow/docker/` alone. |

The 7-line patch verbatim (`ragflow/api/db/services/file_service.py`,
lines 515–522):

```515:522:ragflow/api/db/services/file_service.py
                try:
                    from api.utils.flowchart_on_upload import maybe_append_flowchart_rag_document

                    maybe_append_flowchart_rag_document(
                        kb, user_id, safe_parent_path, filename, blob, files
                    )
                except Exception:
                    logging.exception("Flowchart companion on upload failed")
```

### 2.3 Glue at the stack level

| File | LOC | Role |
|------|----:|------|
| `docker-compose.yml` (repo root) | 71 | Single assembly point: `include:` ragflow's compose, add `mineru-api` service, patch ragflow services to depend on `mineru-api` and bind-mount the hook + tools. |
| `docker-compose.mineru-gpu.yml` | 17 | GPU MinerU overlay. |
| `start-ragflow-mineru.ps1` | 33 | Windows launcher (env-file resolution + GPU switch). |

### 2.4 MinerU Dockerfiles (project-specific build recipes)

| File | Role |
|------|------|
| `MinerU/docker/Dockerfile.api-cpu` | Python 3.12 bookworm + `pip install mineru[api,pipeline,vlm]>=2.6.3`; COPY the patched `vlm_analyze.py` over site-packages; pre-download pipeline+VLM weights so image is self-contained. |
| `MinerU/docker/Dockerfile.api-gpu` | CUDA variant of the above. |
| `MinerU/mineru/backend/vlm/vlm_analyze.py` | **Modified** upstream file — the only actually-used modification of MinerU. Fixes a HuggingFace snapshot-path validator. |

### 2.5 Content: `vit-test/`

Pure content folder:

- Three flowchart PDFs whose filenames contain `flowchart`
  (`Air_inlet_flowchart.pdf`, `Cooler_pipe_flowchart.pdf`,
  `Hose_flowchart.pdf`).
- Non-flowchart PDFs to exercise the MinerU path (`2D_design.pdf`,
  `Way of working.pdf`, `Prompts.pdf`).
- Pre-generated reference outputs (`*.mmd`, `*_rag.md`, `*_graph.json`)
  that can be diffed against a fresh run.
- `benchmark_queries.yaml` — 8 qualitative queries for manual scoring.
- `README.md`, `TESTING.md` — operator procedure.

### 2.6 Documentation: `handover_pack/`

Evidence-backed handover pack (00–08) with file:line references. This
is the authoritative technical record.

**Custom total:** ~1,490 lines of Python across 14 files, plus the
7-line patch, three Dockerfiles, three compose files, one PowerShell
script, and ~20 Markdown / YAML docs.

---

## 3. What is WORKING (confirmed)

- Docker Compose bring-up from the repo root:
  `docker compose --env-file ragflow/docker/.env up -d [--build]`.
  The compose topology is complete and consistent.
- **MinerU** CPU and GPU images build; `/file_parse` and
  `/openapi.json` respond; healthcheck turns green.
- **RAGFlow → MinerU wiring** via `MINERU_APISERVER=http://mineru-api:8000`
  — this is upstream RAGFlow behaviour; no custom code was needed.
- **Flowchart CLI** end-to-end on the three shipped sample PDFs.
  Pre-generated reference outputs are committed in `vit-test/`.
- **Upload hook**: `FileService.upload_document` →
  `maybe_append_flowchart_rag_document` → subprocess CLI → recursive
  `FileService.upload_document` for companions. All code is in place;
  requires the one-time in-container Poppler+deps install.
- **Batch uploader** `ragflow_ingest.py`: state-tracking, `--watch`,
  `--loop`, `--extract-only`, `--no-parse`, `--force`,
  `--include-extras` all implemented.
- **Documentation**: three deployment paths (top-level compose,
  `ragflow/docker/` overlay, Windows-from-source) documented in
  `handover_pack/04_SETUP_GUIDE.md`.

---

## 4. What is PARTIAL (works but has known weaknesses)

- **Flowchart OCR quality.** No post-processing / normalisation.
  Comparing `vit-test/test_rag.md` (Hose_flowchart) with
  `vit-test/Hose_flowchart_rag.md` shows drift (`"STD 6767K"` vs
  `"Std 6767k"`, `"Sp F4"` vs `"8p F4"`). Good enough for adjacent-
  chunk retrieval, unreliable for exact-match fact retrieval.
- **Shape classification.** `flowchart/flowchart/shapes.py` line 43
  contains `shape = "process" if not (0.8 < aspect < 1.2) else "process"`
  — both branches return `"process"`. In practice decision shapes are
  only detected by the earlier `minAreaRect` rotation check (line 39).
  Purely axis-aligned diamond quads will be missed.
- **Edge direction.** Density heuristic with geometric fallback
  (top-down / left-right). Correct on the shipped samples but can
  flip on unusual layouts (bottom-up, right-left).
- **Graph cycle reduction.** `graph_builder.build_graph` has a bare
  `except Exception: pass` — silently swallows failures with no log.
- **Companion deduplication.** Re-uploading the same
  `*flowchart*.pdf` creates `_rag.md_1`, `_rag.md_2`, … (RAGFlow's
  `FileService` default behaviour).
- **Watch mode is polling-only** (`ragflow_ingest.py`), default
  30 s interval; files rewritten with the same mtime are skipped
  unless `--force`.
- **Benchmark harness** (`vit-test/benchmark_queries.yaml`) defines
  only the *questions*; no recorded answers or scores. Manual A/B.
- **`flowchart/run_comparison.py`** uses `np.linalg.norm` without
  importing `numpy as np` (line 99 vs top-of-file imports). **Will
  raise `NameError` if called.** Debug tool only, not part of the
  main pipeline. Flagged but not fixed (no-logic-change handover).

---

## 5. What is NOT PRESENT

- No `.env` shipped (until this handover's `.env.example`).
- No automated test suite for the custom code.
- No CI workflow at the repo root (`.github/` exists only under
  upstream `ragflow/` and `MinerU/`).
- No observability/metrics for the flowchart subprocess.
- No cache keyed on PDF hash — re-uploads re-run the full pipeline.
- No TLS / authentication hardening beyond upstream defaults.
- No Helm / Kubernetes integration for the custom pieces.
- AGPL-3.0 compliance plan for MinerU redistribution is **not drafted**.

---

## 6. Open questions for the receiver

(From `handover_pack/07_*.md` §9 — things that the code alone cannot
answer.)

- Who maintains the fork of RAGFlow long-term?
- Deployment target: on-prem GPU box, workstation, cloud VM?
- AGPL compliance plan for MinerU?
- Does “VIT” in `vit-test/` refer to an institute, a team, a customer,
  or a product code?
- Success criteria for `benchmark_queries.yaml`?
- Expected LLM / embedding provider(s) and key ownership?
- User-auth model (local, OIDC, LDAP)?
- Data-residency / privacy requirements?

---

## 7. Known-good reference data

The following samples are committed and match a fresh CLI run on the
corresponding PDFs (aside from OCR-drift noise in the `Hose` samples):

| PDF | Companion artefacts in `vit-test/` |
|-----|-----------------------------------|
| `Air_inlet_flowchart.pdf` | (regenerate on demand) |
| `Cooler_pipe_flowchart.pdf` | `Cooler_pipe_flowchart.mmd`, `Cooler_pipe_flowchart_rag.md` |
| `Hose_flowchart.pdf` | `Hose_flowchart.mmd`, `Hose_flowchart_rag.md`, and a second older pass `test.mmd`, `test_graph.json`, `test_rag.md` |

`flowchart/flowchart.{json,mmd}` are **legacy samples** (noted as such
in `flowchart/INTEGRATION.md` line 65); they are kept for reference
only.

---

## 8. Minimal acceptance test for the receiver

1. Complete `QUICKSTART.md` steps 1–5.
2. Upload `vit-test/Air_inlet_flowchart.pdf` through the UI.
3. Confirm 4 documents appear in the dataset.
4. Wait for parsing to complete.
5. Ask one question from `vit-test/benchmark_queries.yaml` in the
   chat; confirm the answer cites a chunk that originated in
   `Air_inlet_flowchart_rag.md`.

If all five pass, the inherited system works end-to-end on sample
material. Steps 1–5 should take ~1 hour of wall-clock time on a
modern workstation (most of which is the first MinerU build).
