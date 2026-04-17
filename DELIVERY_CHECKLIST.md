# DELIVERY CHECKLIST — Ragflow-minerU-v2

Use this checklist immediately before handing the repository over.
Every item references a concrete file, command, or test. Check each
box only after you have verified it on a fresh clone.

---

## A. Repository hygiene

- [ ] Top-level `README.md` present and accurate.
- [ ] `QUICKSTART.md` present and accurate.
- [ ] `HANDOVER.md` present and accurate.
- [ ] `DELIVERY_CHECKLIST.md` (this file) present.
- [ ] `.env.example` present at the repo root.
- [ ] `.gitignore` still excludes `Doc to be sent to VIT/`, state file,
      `__pycache__`, OS files.
- [ ] No `__pycache__/`, `*.pyc`, `.DS_Store`, `Thumbs.db`, `*.swp`,
      `*.orig`, `*.bak`, `*~` files anywhere in the tree.
      Verify: `find . -name '__pycache__' -o -name '*.pyc' -o -name '.DS_Store' -o -name 'Thumbs.db' -o -name '*.swp' -o -name '*.bak' -o -name '*.orig' 2>/dev/null`
- [ ] No stale `venv/`, `.venv/`, `node_modules/` committed.
- [ ] No secrets in any committed file (double-check `.env*`,
      `*.yaml`, any shell scripts). Verify with `rg -i 'api[_-]?key|password|secret|token' --hidden --glob '!handover_pack'`.

---

## B. Licenses and attribution

- [ ] `ragflow/LICENSE` (Apache-2.0) present and untouched.
- [ ] `MinerU/LICENSE.md` (AGPL-3.0) present and untouched.
- [ ] `MinerU/MinerU_CLA.md` preserved.
- [ ] Upstream `README.md`, `SECURITY.md`, and language variants
      (`ragflow/README_*.md`, `MinerU/README_zh-CN.md`) preserved.
- [ ] The `HANDOVER.md` “AGPL note” is visible to the receiver.
- [ ] A decision has been made on a license for the CUSTOM code
      (`flowchart/`, glue files, `vit-test/`, Dockerfiles, compose
      files, handover pack). **Recommend: choose one before the
      repository leaves the organisation.**
      _Suggested options:_ Apache-2.0 (compatible with RAGFlow;
      AGPL-3.0 is still imposed at the stack level by MinerU),
      AGPL-3.0 (matches MinerU), or proprietary.

---

## C. Sample data preserved

All samples that demonstrate functionality are kept. The following
files are **legacy duplicate samples** — they are intentionally
preserved because they are cited by `handover_pack/07_*.md` §2 as
evidence of OCR drift. Receiver may delete if undesired:

- `flowchart/flowchart.json` — legacy sample referenced by
  `flowchart/INTEGRATION.md` line 65.
- `flowchart/flowchart.mmd` — legacy sample alongside the JSON.
- `vit-test/test.mmd`, `vit-test/test_graph.json`,
  `vit-test/test_rag.md` — older pass on `Hose_flowchart.pdf`,
  useful for A/B comparison vs `Hose_flowchart_*`.

Preserved because they are in-scope:

- [ ] `vit-test/*.pdf` — three `*flowchart*.pdf` + three non-flowchart
      PDFs.
- [ ] `vit-test/Cooler_pipe_flowchart_rag.md`,
      `Cooler_pipe_flowchart.mmd`.
- [ ] `vit-test/Hose_flowchart_rag.md`, `Hose_flowchart.mmd`.
- [ ] `vit-test/benchmark_queries.yaml`.
- [ ] `vit-test/README.md`, `vit-test/TESTING.md`.

---

## D. Handover pack

- [ ] `handover_pack/00_MASTER_INDEX.md` through
      `handover_pack/08_API_AND_INTERFACE_SUMMARY.md` present.
- [ ] All internal links in `handover_pack/*.md` resolve.
- [ ] Evidence tags (CONFIRMED / INFERRED / UNKNOWN) intact.

---

## E. Configuration and secrets

- [ ] `ragflow/docker/.env` is **not** committed (only `.env.example`).
- [ ] `.env.example` documents every variable used by
      `docker-compose.yml`, `docker-compose.mineru-gpu.yml`,
      `ragflow/docker/docker-compose.yml`,
      `ragflow/api/utils/flowchart_on_upload.py`, and
      `flowchart/ragflow_ingest.py`.
- [ ] Placeholder passwords clearly marked `CHANGE-ME-*`.

---

## F. Runtime smoke test (performed on fresh clone)

1. [ ] `cp .env.example ragflow/docker/.env`; fill passwords.
2. [ ] `docker compose --env-file ragflow/docker/.env up -d --build`
      — completes (first build ~15–30 min).
3. [ ] `docker ps` — `mineru-api` reaches `healthy`.
4. [ ] `curl -fsS http://localhost:${MINERU_PORT:-8000}/openapi.json`
      returns 200.
5. [ ] `http://localhost:${SVR_WEB_HTTP_PORT:-80}/` — RAGFlow UI loads,
      account creation works.
6. [ ] Inside the ragflow container:
      `apt-get update && apt-get install -y poppler-utils && pip install -r /flowchart-tools/requirements.txt`
      succeeds; container restarted.
7. [ ] Upload `vit-test/Air_inlet_flowchart.pdf` via UI with **Parse
      on creation** enabled.
8. [ ] Dataset shows 4 documents:
      `Air_inlet_flowchart.pdf`, `.mmd`, `_rag.md`, `_graph.json`.
9. [ ] All 4 parse successfully.
10. [ ] In chat, ask one question from
       `vit-test/benchmark_queries.yaml` that relies on flowchart
       content; retrieved chunks include a line from `_rag.md`.
11. [ ] `docker compose --env-file ragflow/docker/.env down` cleans up.

If any step fails, see `QUICKSTART.md` §8 and
`handover_pack/04_SETUP_GUIDE.md` §9–§10 before escalating.

---

## G. Host-side / flowchart-only smoke test

- [ ] `cd flowchart && python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt`
      installs cleanly (Python 3.10+).
- [ ] Host has Poppler (`pdftoppm` and `pdfinfo` on PATH, or
      `POPPLER_PATH` set).
- [ ] `python cli.py ../vit-test/Air_inlet_flowchart.pdf -o /tmp/air.mmd --json`
      produces `air.mmd`, `air_rag.md`, `air_graph.json`
      with non-empty node/edge content.

---

## H. Optional fixes the receiver may want to apply (documented, not
       performed during handover)

The handover preserves runtime behaviour. These are known issues that
require minor code changes and are explicitly OUT OF SCOPE for this
clean-up pass:

- [ ] `flowchart/run_comparison.py` line 99 uses `np.linalg.norm`
      without `import numpy as np` — add the import or remove the
      unused debug function. Evidence:
      `handover_pack/07_CURRENT_STATUS_AND_LIMITATIONS.md` §3.
- [ ] `flowchart/flowchart/shapes.py` line 43 has both ternary
      branches returning `"process"`. Decide intended behaviour and
      re-enable decision detection.
      Evidence: `handover_pack/07_*.md` §2.
- [ ] `flowchart/flowchart/graph_builder.py` has a bare
      `except Exception: pass` around cycle reduction — add at least a
      log line. Evidence: `handover_pack/07_*.md` §2.
- [ ] Add a CI workflow at repo root (`.github/workflows/*.yml`) to
      at least lint + run any tests once they exist.
- [ ] Add a cache keyed on PDF `content_hash` to skip re-extraction on
      duplicate uploads. Evidence: `handover_pack/07_*.md` §4.
- [ ] Expand `benchmark_queries.yaml` with recorded expected-answer
      chunks and a simple runner.

---

## I. Known unknowns that must be resolved off-repo

These questions cannot be answered from the code alone (see
`handover_pack/07_*.md` §9). **Resolve before production use.**

- [ ] Owner / long-term maintainer of this fork.
- [ ] AGPL-3.0 compliance plan for MinerU redistribution (legal
      review sign-off).
- [ ] Intended deployment target (on-prem GPU / workstation / cloud).
- [ ] Success criteria for `benchmark_queries.yaml`.
- [ ] Meaning of “VIT” in `vit-test/` and `.gitignore`.
- [ ] Intended LLM / embedding provider and key ownership.
- [ ] User-auth model (local / OIDC / LDAP).
- [ ] Data-residency / privacy requirements for industrial specs.
- [ ] SLA / uptime expectations.

---

## J. Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Outgoing maintainer | | | |
| Incoming maintainer | | | |
| Legal / compliance (AGPL review) | | | |

Once every box in §A–§G is checked and every question in §I has a
documented answer, the repository is ready to transfer.
