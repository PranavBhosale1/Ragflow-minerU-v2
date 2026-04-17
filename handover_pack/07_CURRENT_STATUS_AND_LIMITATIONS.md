# 07 — Current Status and Limitations

A brutally honest technical status report, backed by code and doc
evidence. No marketing, no best-case scenarios.

---

## 1. What is fully working (CONFIRMED)

- **Bring-up of the full stack** via Docker Compose from the repo root:
  `docker compose --env-file ragflow/docker/.env up -d [--build]`. The
  compose topology is complete and consistent (ragflow + mineru-api +
  base services). Healthchecks and depends-on are defined.
- **MinerU HTTP service** builds on CPU and GPU; `POST /file_parse` is
  reachable (this is an upstream-maintained endpoint that RAGFlow already
  knows how to call).
- **RAGFlow → MinerU parsing** path is in place and **in upstream
  RAGFlow** — no custom code was needed to wire it up beyond setting
  `MINERU_APISERVER`.
- **Flowchart CLI** end-to-end: reads a PDF, produces `.mmd`, `_rag.md`,
  and `_graph.json`. Sample outputs are committed for three different
  real PDFs (Air inlet, Cooler pipe, Hose).
- **Flowchart upload hook**: the code path from `FileService.upload_document`
  → `maybe_append_flowchart_rag_document` → subprocess CLI →
  `FileService.upload_document` (recursive, for companions) is complete.
- **Batch uploader `ragflow_ingest.py`**: polling loop, state file,
  `--extract-only`, `--no-parse`, `--force`, `--include-extras` all
  implemented.
- **Documentation**: step-by-step setup guides exist for three deployment
  shapes (top-level compose, `ragflow/docker/` overlay, Windows source).

## 2. What is partially working (INFERRED from code + samples)

- **Flowchart OCR quality**: no text post-processing. Comparing
  `vit-test/test_rag.md` (`Hose_flowchart`) and
  `vit-test/Hose_flowchart_rag.md`, OCR noise is visible
  ("STD 6767K" vs "Std 6767k", "Sp F4" vs "8p F4"). Acceptable for
  retrieval of *adjacent* chunks, unreliable for exact-match fact
  retrieval.
- **Shape classification**: `flowchart/flowchart/shapes.py` line 43
  contains the revealing expression
  `shape = "process" if not (0.8 < aspect < 1.2) else "process"` —
  i.e. both branches return `"process"`. The decision-shape path is only
  reached via the `minAreaRect` rotation check earlier in the function
  (line 39). **Decision-vs-process detection is effectively a single
  heuristic (rotated near-square)**; purely axis-aligned diamonds drawn
  as rotated bounding-box quads will be missed. Evidence:
  `flowchart/flowchart/shapes.py` lines 34–48.
- **Edge direction inference**: relies on a density heuristic around
  endpoints; falls back to centroid comparison when ambiguous. Correct
  for the committed samples, but the fallback flips direction based on
  geometry alone, which will be wrong on flowcharts that route bottom→top
  or right→left. Evidence: `flowchart/flowchart/lines.py` lines 196–228.
- **Graph cycle reduction**: a bare `except Exception: pass` silently
  swallows errors in `graph_builder.build_graph` — if cycle reduction
  raises, no logging, no retry. Evidence:
  `flowchart/flowchart/graph_builder.py` lines 29–52.
- **Companion file deduplication**: the hook uploads companions via
  `FileService.upload_document`, which itself increments locations on
  name collision. Re-uploading the same `*flowchart*.pdf` will create
  additional `_rag.md_N` files. Evidence: surrounding code in
  `file_service.py` lines 476–520.
- **`ragflow_ingest.py` watch mode**: polling only (not `watchdog`),
  interval default 30 s, state file in the watched dir. If a file is
  overwritten with the same mtime, it is skipped unless `--force`.
- **Benchmarking**: only *questions*, no recorded answers or scores. Set
  up for manual A/B evaluation.

## 3. What is experimental / proof-of-concept

- The entire `flowchart/` module: classical CV + EasyOCR is a known
  fragile approach for arbitrary flowchart layouts. It works on
  rectangular/diamond P&ID-style charts with reasonably-spaced nodes
  (the kind shipped in `vit-test/`). It will struggle on:
  - Hand-drawn flowcharts.
  - Non-rectangular or rounded-rectangle nodes (they will not match the
    `len(approx) == 4` test in `shapes.py` line 27).
  - Flowcharts with curved edges.
  - Multi-column layouts where node centroids suggest ambiguous flow.
- `run_comparison.py` is a debug visualiser, not a test runner.
  Evidence: function `detect_arrows_from_mask` is defined but
  `numpy` (`np`) is used without import in that function
  (`run_comparison.py` line 99 uses `np.linalg.norm`, but there is no
  `import numpy as np` at the top of the file — the top imports only
  `cv2`, `sys`, and `Path`). **This will raise `NameError` at runtime.**

## 4. What is incomplete

- No `.env` template for the top-level stack. Operators must synthesise
  one from `ragflow/docker/README.md`. Only `ragflow/docker/.env.single-bucket-example`
  exists and it covers MinIO single-bucket mode only.
- No automated test suite for the custom code (flowchart module, hook,
  ingest script).
- No CI workflow at the repo root (`/.github/` at root is absent; only
  upstream `ragflow/.github/` and `MinerU/.github/` exist).
- No Kubernetes / Helm integration for the custom pieces. RAGFlow has a
  Helm chart in `ragflow/helm/` but the top-level compose does not touch
  it.
- No observability / metrics for the flowchart subprocess (no timing
  counters, no success-rate logging, no parse-result database rows).
- No cache for flowchart extraction. A re-upload of the same PDF will
  rerun the whole CV/OCR pipeline (typical cost: ~tens of seconds per
  page on CPU, dominated by EasyOCR first-run download and per-node
  inference).
- No graceful interaction between the hook and MinerU — they run
  independently on the same PDF. If MinerU already happened to extract
  the flowchart as an image tagged with a caption, you will get
  redundant chunks.
- No explicit user permission check on the companion uploads — the hook
  reuses the `user_id` passed into `upload_document`, which is the
  uploading user. OK but worth confirming in multi-tenant setups.

## 5. What is fragile

- **Filename-based triggering** of the hook. The default substring is
  `flowchart`. Any PDF with that substring, even unrelated, will run the
  full CV/OCR pipeline (slow). Configurable but not context-aware.
- **Subprocess timeout**: default 900 s. A hanging CLI blocks the upload
  request for 15 minutes before HTTP responds.
- **First-run EasyOCR model download** inside the subprocess — if the
  container has no internet access, the very first parse fails.
- **Model weights** for MinerU are baked into the image. Rebuilds without
  network access will not succeed. Re-downloading takes several GB.
- **`_rag.md` size**: for large flowcharts (say 100 nodes / 200 edges)
  the file is a single flat markdown with one line per node/edge.
  Default RAGFlow chunking may split mid-graph, reducing retrieval
  precision. No chunking hint is written into the file.

## 6. What is NOT production-ready

- No TLS termination for any custom piece. `ragflow/docker/` includes
  HTTPS setup docs, but the top-level compose does not.
- Default passwords are whatever the operator puts in `.env`. The
  example file (`single-bucket-example`) includes strings like
  `your-secret-password-here`.
- MinerU's AGPL-3.0 may impose network-provision obligations — **legal
  review required** before any customer-facing deployment.
- No audit logging beyond what RAGFlow/Flask write to stdout.
- No backup strategy for MinIO / MySQL; upstream compose defines named
  volumes with `driver: local`.
- No rate limiting or abuse protection on the RAGFlow API surface.

## 7. What would still be needed for real deployment

- Author a canonical `ragflow/docker/.env` and commit (minus secrets) as
  `.env.example`.
- Add healthchecks and dependencies on the document engine and MinIO
  from the RAGFlow services.
- Replace the filename-based hook trigger with a per-dataset setting or
  a parser preset, so operators can opt in explicitly.
- Add a cache keyed by PDF `content_hash` to skip re-extraction.
- Add structured logging for the hook (success/fail/duration).
- Provide unit tests for `flowchart/flowchart/*.py` and integration tests
  for the hook.
- Fix `run_comparison.py` `NameError` on `np` and add it (or remove it
  if unused).
- Expand `benchmark_queries.yaml` with recorded expected-answer chunks
  and write a simple runner that posts each question and asserts a chunk
  hit.
- License audit (AGPL-3.0 MinerU vs. intended distribution model).
- HTTPS + authentication hardening for the RAGFlow UI.

## 8. Known limitations explicitly stated in the repo

- "VLM on CPU is slow; for GPU use a CUDA base image..." —
  `MinerU/docker/Dockerfile.api-cpu` comment line 3.
- "First build downloads pipeline+VLM weights (large)" — top-level
  `docker-compose.yml` line 23.
- "The companion file appears in the upload response together with the
  PDF, so Parse on creation runs on both documents when enabled in the
  UI." — `flowchart/INTEGRATION.md` line 44. Implies: if Parse on
  creation is **off**, the companion files exist but are not parsed.
- "This does not replace MinerU for the original PDF; run it in
  addition..." — `flowchart/INTEGRATION.md` line 95.
- "Legacy `flowchart.json` in this repo is a sample" —
  `flowchart/INTEGRATION.md` line 65.
- `vit-test/benchmark_queries.yaml` scoring block: "For each query,
  record pass/fail..." — manual, undocumented outcomes.

## 9. Organisational unknowns that code alone cannot answer

- **Ownership**: who maintains this fork of RAGFlow? Any contract with
  InfiniFlow?
- **AGPL compliance plan** for MinerU redistribution.
- **Deployment target**: on-prem GPU box? single workstation? cloud
  VM? compute budgets?
- **Evaluation success criteria**: what hit rate is "good enough" over
  `benchmark_queries.yaml`?
- **User identity**: is "VIT" an institute, a team, a customer code, a
  product name?
- **Security posture**: expected user auth model (LDAP/OIDC/local)?
- **Scale**: expected number of datasets, number of concurrent uploads,
  PDF size distribution?
- **Credentials**: intended LLM provider(s) and whose API keys?
- **SLA / uptime** expectations.
- **Data residency / privacy** requirements for industrial specs.

All of the above are **UNKNOWN / NEEDS MANUAL INPUT**.

---

## 10. Summary matrix

| Area | Status |
|------|--------|
| Stack brings up | Working |
| MinerU parse | Working |
| Flowchart CLI | Working on provided samples |
| Hook integration | Working (pending in-container Poppler install) |
| Batch uploader | Working |
| OCR quality | Partial / noisy |
| Shape detection | Weak (decision class heuristic suspicious) |
| Edge direction | Heuristic; correct on samples |
| Evaluation | Manual-only (no runner, no scores) |
| Production hardening | Not attempted |
| License compliance | Not reviewed |
| Tests / CI | Absent |
