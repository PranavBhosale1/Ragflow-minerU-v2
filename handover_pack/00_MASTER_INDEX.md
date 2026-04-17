# 00 — Master Index

Generated handover pack for the `Ragflow-minerU-v2-main` workspace.
All files are evidence-backed — every substantive claim points at a
file path and line number in the source tree.

Read them in numeric order for a top-down understanding, or jump to
the topic you need.

---

## Files in this pack

| # | File | What it covers |
|---|------|----------------|
| 00 | `00_MASTER_INDEX.md` | *This file.* Map of the handover pack. |
| 01 | `01_PROJECT_HANDOVER_OVERVIEW.md` | One-paragraph project summary, problem statement, project-title candidates, domain, maturity status, confirmed-vs-partial-vs-unknown overview. |
| 02 | `02_REPO_COMPONENT_BREAKDOWN.md` | Every major folder / repo / subsystem: purpose, upstream vs. custom, role, key files, inputs, outputs, connectivity, setup deps, evidence. |
| 03 | `03_SYSTEM_ARCHITECTURE_EXPLANATION.md` | Plain-English architecture walkthrough: end-to-end, user flow, ingestion, parsing, flowchart processing, storage, retrieval, query answering, batch/watch mode; plus a textual architecture diagram and data/control-flow explanations. |
| 04 | `04_SETUP_GUIDE.md` | Setup from scratch: prerequisites, software versions, env vars, OS notes, install/build/startup order, verification, common pitfalls. |
| 05 | `05_RUN_AND_TEST_GUIDE.md` | How to run the full system, run pieces individually, test upload / parse / flowchart / retrieval / chat; how to validate outputs; where logs live; example inputs. |
| 06 | `06_CUSTOM_WORK_VS_BASE_SYSTEM.md` | Two sections: (A) base/upstream/imported; (B) custom/modified/project-specific. For each, what/why/where/how-it-integrates, with evidence. |
| 07 | `07_CURRENT_STATUS_AND_LIMITATIONS.md` | Honest technical status: fully working / partial / experimental / incomplete / fragile / not-production-ready; known limitations from code and docs; unknowns that code alone cannot answer. |
| 08 | `08_API_AND_INTERFACE_SUMMARY.md` | Endpoints, CLI commands, scripts, input/output formats, auth patterns, filename expectations, env-triggered behaviour, subprocess calls, integration points, default ports. |

---

## Evidence-tagging conventions

Every claim in these documents uses one of three tags:

- **CONFIRMED** — directly supported by code / config / doc in the
  repository.
- **INFERRED** — plausibly follows from code evidence but not explicitly
  stated.
- **UNKNOWN / NEEDS MANUAL INPUT** — cannot be answered from the repo
  and requires external clarification. Collected in `10_*.md`.

---

## Top-level layout of the inspected workspace

```
Ragflow-minerU-v2-main/
├── docker-compose.yml                # Top-level orchestration (glue)
├── docker-compose.mineru-gpu.yml     # Optional GPU overlay for MinerU
├── start-ragflow-mineru.ps1          # Windows launch helper
├── .gitignore
├── flowchart/                        # CUSTOM: CV + OCR flowchart extractor
│   ├── cli.py
│   ├── ragflow_ingest.py
│   ├── run_comparison.py
│   ├── requirements.txt
│   ├── README.md, INTEGRATION.md, ORIGINAL_STACK_SETUP.md, TESTING.md
│   ├── flowchart.json, flowchart.mmd  # sample outputs
│   └── flowchart/
│       ├── pdf_converter.py
│       ├── preprocess.py
│       ├── shapes.py
│       ├── ocr.py
│       ├── lines.py
│       ├── graph_builder.py
│       └── exporter.py
├── ragflow/                          # UPSTREAM (Apache-2.0, v0.24.0) + custom patches
│   ├── api/
│   │   ├── db/services/file_service.py        # 7-line patch (CUSTOM)
│   │   └── utils/flowchart_on_upload.py       # CUSTOM glue
│   ├── deepdoc/parser/mineru_parser.py        # Upstream: RAGFlow→MinerU bridge
│   ├── docker/docker-compose*.yml, docker-compose-base.yml
│   ├── docker/docker-compose.flowchart.yml    # CUSTOM overlay
│   ├── web/                                   # React/UmiJS UI (upstream)
│   └── ...
├── MinerU/                           # UPSTREAM (AGPL-3.0, v2.6.3) + project Dockerfiles
│   ├── docker/Dockerfile.api-cpu              # CUSTOM (builds the API service)
│   ├── docker/Dockerfile.api-gpu              # CUSTOM
│   ├── mineru/cli/fast_api.py
│   └── ...
├── vit-test/                         # CUSTOM: sample PDFs, pre-generated artefacts, benchmark questions
│   ├── Air inlet filter diff pressure.pdf
│   ├── Cooler pipe cleanliness test.pdf
│   ├── Hose_flowchart.pdf
│   ├── *.mmd, *_rag.md, *_graph.json
│   └── benchmark_queries.yaml
└── handover_pack/                    # This pack
```

---

## Quick links for reviewers

- **"What is this?"** → `01_PROJECT_HANDOVER_OVERVIEW.md` §1–§2.
- **"How is it put together?"** → `03_SYSTEM_ARCHITECTURE_EXPLANATION.md`.
- **"How do I run it?"** → `04_SETUP_GUIDE.md` then `05_RUN_AND_TEST_GUIDE.md`.
- **"What did you actually build?"** → `06_CUSTOM_WORK_VS_BASE_SYSTEM.md` §B.
- **"What is broken?"** → `07_CURRENT_STATUS_AND_LIMITATIONS.md`.

---

## How this pack was produced

1. Mapped the workspace with directory listings.
2. Read top-level compose, launch scripts, and `.gitignore`.
3. Opened each subproject (`flowchart/`, `ragflow/`, `MinerU/`,
   `vit-test/`) and inspected their docs, dependency manifests, and
   entry points.
4. Read the custom glue files (`flowchart_on_upload.py`,
   `file_service.py` patch, `docker-compose.yml` overlay) to
   understand integration.
5. Read the MinerU Dockerfiles to understand the service's build
   surface.
6. Read the flowchart pipeline modules end-to-end.
7. Cross-referenced sample inputs (`vit-test/*.pdf`) with the
   committed sample outputs (`vit-test/*_rag.md`,
   `flowchart/flowchart.json`).
8. Wrote each document with explicit file-path references and
   CONFIRMED / INFERRED / UNKNOWN tagging.

No 