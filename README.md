# Ragflow-minerU-v2 — Flowchart-aware RAG stack

A bundled Retrieval-Augmented-Generation (RAG) stack that combines three
projects with a thin integration layer, so that flowchart-style PDFs can
be parsed into retrievable node/edge text and answered by chat.

```
┌───────────────┐   HTTP :80 / :9380   ┌─────────────────────────────┐
│   Browser     │ ───────────────────▶ │  RAGFlow  (upstream)        │
└───────────────┘                      │  - API + React UI           │
                                       │  - MySQL / Redis / MinIO /  │
                                       │    Elasticsearch|Infinity   │
                                       │                             │
                                       │  on PDF upload whose name   │
                                       │  contains "flowchart":      │
                                       │                             │
                                       │  flowchart_on_upload.py ──┐ │
                                       └───────────────────────────┼─┘
                                                │  POST /file_parse │
                                                ▼                   │
                                       ┌─────────────────────────┐  │
                                       │  MinerU-api (upstream)  │  │
                                       │  PDF → Markdown         │  │
                                       └─────────────────────────┘  │
                                                                    │
                                       ┌─────────────────────────┐◀─┘
                                       │  flowchart/ (custom)    │
                                       │  classical CV + OCR     │
                                       │  → .mmd, _rag.md,       │
                                       │    _graph.json          │
                                       └─────────────────────────┘
```

---

## What this system is

- **RAGFlow** (`ragflow/`, Apache-2.0, v0.24.0) — main RAG platform:
  knowledge-base management, document parsing, chunking, retrieval,
  React UI, chat.
- **MinerU** (`MinerU/`, AGPL-3.0, ≥2.6.3) — PDF → Markdown parser
  served as a FastAPI endpoint (`/file_parse`).
- **flowchart/** (custom) — classical computer-vision + OCR pipeline
  that turns a flowchart image inside a PDF into three companion
  artefacts: `.mmd` (Mermaid), `_rag.md` (plain-language node/edge
  text for embedding), and `_graph.json` (structured graph).
- **Glue** (custom) — a ~180-line hook
  (`ragflow/api/utils/flowchart_on_upload.py`) plus a 7-line patch
  (`ragflow/api/db/services/file_service.py` lines 515–522) that
  automatically runs the flowchart CLI during document upload and
  uploads the companion files into the same knowledge base, so the
  retriever can ground chat answers on explicit flowchart facts.
- **vit-test/** (custom) — sample PDFs, committed reference outputs,
  and a qualitative benchmark YAML.

See `HANDOVER.md` for the split between upstream and custom work and
`handover_pack/` for evidence-backed deep-dives.

---

## Why it exists

RAGFlow + MinerU already embed the text, tables, and layout of technical
PDFs well, but **flowcharts inside those PDFs are images** — their
nodes and edges are never surfaced to the retriever. The custom
flowchart module extracts node/edge text so that chat can answer
questions like *“what happens after the No branch of the Weld
decision?”* or *“which standard-steel specification is used after the
air inlet?”*.

Typical source material: industrial / automotive specification
flowcharts (hose assemblies, cooler pipes, coatings, welds). Sample
PDFs are in `vit-test/`.

---

## Repository layout

```
Ragflow-minerU-v2-main/
├── README.md                        ← this file
├── QUICKSTART.md                    ← exact setup steps
├── HANDOVER.md                      ← upstream vs custom, status
├── DELIVERY_CHECKLIST.md            ← pre-handover checklist
├── .env.example                     ← template for ragflow/docker/.env
├── docker-compose.yml               ← top-level orchestration (custom)
├── docker-compose.mineru-gpu.yml    ← optional GPU overlay (custom)
├── start-ragflow-mineru.ps1         ← Windows launch helper (custom)
├── handover_pack/                   ← evidence-backed documentation
├── flowchart/                       ← CUSTOM: CV + OCR flowchart extractor
│   ├── cli.py, ragflow_ingest.py, run_comparison.py
│   ├── flowchart/                   ← package (pdf_converter, shapes,
│   │                                  ocr, lines, graph_builder, exporter)
│   ├── README.md, INTEGRATION.md, ORIGINAL_STACK_SETUP.md
│   └── flowchart.{json,mmd}         ← sample outputs
├── ragflow/                         ← UPSTREAM (Apache-2.0) + 1 patch
│   ├── LICENSE                      ← Apache-2.0
│   ├── api/utils/flowchart_on_upload.py     ← CUSTOM glue
│   ├── api/db/services/file_service.py      ← 7-line CUSTOM patch
│   └── docker/docker-compose.flowchart.yml  ← CUSTOM overlay
├── MinerU/                          ← UPSTREAM (AGPL-3.0) + Dockerfiles
│   ├── LICENSE.md                   ← AGPL-3.0
│   └── docker/Dockerfile.api-{cpu,gpu}       ← CUSTOM build recipes
└── vit-test/                        ← CUSTOM: sample PDFs and reference
                                        outputs for validation
```

---

## Quick start

```bash
# 1. Copy the env template and fill in values.
cp .env.example ragflow/docker/.env
$EDITOR ragflow/docker/.env

# 2. Bring up the stack (CPU MinerU).
docker compose --env-file ragflow/docker/.env up -d --build

# 3. Install Poppler + Python deps inside the RAGFlow container
#    (one-time; needed only for the flowchart hook).
docker exec -it <ragflow-cpu-container> bash -lc \
  "apt-get update && apt-get install -y poppler-utils && \
   pip install -r /flowchart-tools/requirements.txt"
docker compose --env-file ragflow/docker/.env restart ragflow-cpu

# 4. Open http://localhost:80 ; upload vit-test/Air_inlet_flowchart.pdf.
#    Expect 4 documents (PDF + .mmd + _rag.md + _graph.json).
```

See `QUICKSTART.md` for full prerequisites, GPU path, and verification
steps.

---

## Documentation map

| You want… | Read |
|-----------|------|
| Setup from scratch | `QUICKSTART.md` → `handover_pack/04_SETUP_GUIDE.md` |
| Run / test procedures | `handover_pack/05_RUN_AND_TEST_GUIDE.md` |
| What's upstream vs custom | `HANDOVER.md` → `handover_pack/06_CUSTOM_WORK_VS_BASE_SYSTEM.md` |
| Honest status of every subsystem | `handover_pack/07_CURRENT_STATUS_AND_LIMITATIONS.md` |
| Architecture walk-through | `handover_pack/03_SYSTEM_ARCHITECTURE_EXPLANATION.md` |
| API / CLI / env-var surface | `handover_pack/08_API_AND_INTERFACE_SUMMARY.md` |
| Component-by-component map | `handover_pack/02_REPO_COMPONENT_BREAKDOWN.md` |
| Final delivery checklist | `DELIVERY_CHECKLIST.md` |

---

## Licensing and attribution

This repository redistributes two upstream projects. Their original
licenses are preserved in-tree:

- **RAGFlow** — Apache License 2.0 — `ragflow/LICENSE`,
  upstream: <https://github.com/infiniflow/ragflow>
- **MinerU** — GNU AGPL-3.0 — `MinerU/LICENSE.md`,
  upstream: <https://github.com/opendatalab/MinerU>

Custom code (`flowchart/`, the glue files, Dockerfiles, `vit-test/`,
`handover_pack/`, top-level compose and scripts) has not been assigned a
license yet. **Apply a license before redistributing.** Because MinerU
is AGPL-3.0, any network-facing redistribution of the combined stack
inherits AGPL network-provision obligations — a **legal review is
recommended** before customer-facing deployment.

---

## Status at a glance

| Area | Status |
|------|--------|
| Docker Compose bring-up | Working |
| MinerU CPU / GPU build & `/file_parse` | Working |
| RAGFlow ↔ MinerU wiring | Working (upstream) |
| Flowchart CLI on sample PDFs | Working |
| `flowchart_on_upload` hook | Working (pending in-container Poppler install) |
| Batch uploader `ragflow_ingest.py` | Working |
| Flowchart OCR accuracy | Partial (no normalisation) |
| Shape / edge-direction heuristics | Partial (heuristic-only) |
| Automated tests & CI | Absent |
| Production hardening, AGPL audit | Not attempted |

See `HANDOVER.md` §3–§4 for details and `handover_pack/07_*.md` for the
full fragility map.
