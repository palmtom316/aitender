# Norm Pipeline Gap Close Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make scanned norm PDF uploads reliably produce validated, persisted `norm_clause_entries` + `norm_commentary_entries`, with search + jump-to-page + sidebar excerpt highlighting (no bbox), and automatic DeepSeek patching when rule validation fails.

**Architecture:** Deterministic rule extraction runs first (正文窗口 + 目录剔除 + tree rebuild + page range inference + commentary map). A strict validator gates success. If the gate fails and DeepSeek is configured, run scope-based patch calls that output flat entries only, then merge locally and re-validate.

**Tech Stack:** FastAPI, Pydantic, Postgres (FTS), pytest, Next.js (react-pdf)

---

### Task 1: Add Fixtures For TOC + 修订说明 + 条文说明

**Files:**
- Create: `services/api-server/tests/fixtures/norm_samples/sample_norm_with_toc_and_revision.md`
- Modify: `services/api-server/tests/test_norm_index_builder.py`
- Modify: `services/api-server/tests/test_norm_commentary_builder.py`

**Step 1: Write/extend failing tests**

- Update `test_norm_index_builder` to assert:
  - TOC lines are not treated as body clauses.
  - Content after `修订说明` is excluded from body clause index.
- Update `test_norm_commentary_builder` to assert:
  - Commentary parsing ignores revision intro and 2nd TOC.
  - Commentary map only contains clause-level commentary.

**Step 2: Run tests to verify they fail**

Run: `cd services/api-server && python -m pytest -q tests/test_norm_index_builder.py::test_norm_index_builder_extracts_chapter_section_and_clause_entries`

Expected: FAIL (builder currently lacks TOC/revision handling).

**Step 3: Commit**

```bash
git add services/api-server/tests/fixtures/norm_samples/sample_norm_with_toc_and_revision.md \
        services/api-server/tests/test_norm_index_builder.py \
        services/api-server/tests/test_norm_commentary_builder.py
git commit -m "test: add toc/revision fixtures for norm parsing"
```

### Task 2: Implement Markdown Splitter (Body vs Commentary)

**Files:**
- Create: `services/api-server/app/services/norm_markdown_splitter.py`
- Create: `services/api-server/tests/test_norm_markdown_splitter.py`

**Step 1: Write failing tests**

Test expectations:
- `split(markdown_text)` returns:
  - `body_markdown` from first body chapter heading to before `修订说明`
  - `commentary_markdown` after `修订说明`
  - `toc_markdown` (first TOC block) for expectations/validation

**Step 2: Run tests**

Run: `cd services/api-server && python -m pytest -q tests/test_norm_markdown_splitter.py`

Expected: FAIL (module missing).

**Step 3: Minimal implementation**

Implement:
- Detect headings containing `目次` and `修订说明`.
- Keep the first TOC block (for expected section labels).
- Body starts at first heading matching `# 1` / `# 1 ` (or first numeric chapter heading).

**Step 4: Run tests**

Expected: PASS.

**Step 5: Commit**

```bash
git add services/api-server/app/services/norm_markdown_splitter.py \
        services/api-server/tests/test_norm_markdown_splitter.py
git commit -m "feat: split norm markdown into toc/body/commentary segments"
```

### Task 3: Implement TOC Parser For Expected Chapter/Section Labels

**Files:**
- Create: `services/api-server/app/services/norm_toc_parser.py`
- Create: `services/api-server/tests/test_norm_toc_parser.py`

**Step 1: Write failing tests**

Given a TOC markdown snippet, parse:
- chapter labels: `1`, `2`, `4`, `5`, ...
- section labels: `4.1`..`4.12`, `5.1`.. etc when present in TOC lines

**Step 2: Run tests**

Run: `cd services/api-server && python -m pytest -q tests/test_norm_toc_parser.py`

Expected: FAIL.

**Step 3: Implement**

Rules:
- Match `^(\\d+(?:\\.\\d+)*)\\s+(.+?)(?:\\(|$)` in TOC lines.
- Keep only chapter/section labels (0 or 1 dot). Ignore clause-level labels (2+ dots).

**Step 4: Run tests**

Expected: PASS.

**Step 5: Commit**

```bash
git add services/api-server/app/services/norm_toc_parser.py \
        services/api-server/tests/test_norm_toc_parser.py
git commit -m "feat: parse toc into expected chapter/section labels"
```

### Task 4: Upgrade Page Locator (正文窗口 + Candidate Matching + Range Inference)

**Files:**
- Modify: `services/api-server/app/services/norm_page_locator.py`
- Create: `services/api-server/tests/test_norm_page_locator.py`

**Step 1: Write failing tests**

Cases:
- Locate should search only within the provided page window.
- Clause `page_end` should be inferred using the next located clause start (same page or later).

**Step 2: Run tests**

Run: `cd services/api-server && python -m pytest -q tests/test_norm_page_locator.py`

Expected: FAIL.

**Step 3: Implement minimal improvements**

Implementation sketch:
- Add optional `page_min/page_max` bounds.
- Add `locate_many(entries, page_texts)` that:
  - Locates start pages in order using candidate strings:
    - exact `label`
    - `label + title` (normalized whitespace)
    - short title prefix (first N chars)
  - After starts are located, infer `page_end` as:
    - next_start_page if next exists and next_start_page >= start_page
    - otherwise start_page

**Step 4: Run tests**

Expected: PASS.

**Step 5: Commit**

```bash
git add services/api-server/app/services/norm_page_locator.py \
        services/api-server/tests/test_norm_page_locator.py
git commit -m "feat: improve page locating with windowed sequential matching"
```

### Task 5: Upgrade Clause Index Builder (Skip TOC + 正文窗口 + Better Tree)

**Files:**
- Modify: `services/api-server/app/services/norm_index_builder.py`
- Modify: `services/api-server/tests/test_norm_index_builder.py`

**Step 1: Update tests (already failing from Task 1)**

Extend assertions:
- Entries include chapter/section/clause layers only from body content.
- TOC labels do not create entries.

**Step 2: Implement**

Builder changes:
- Accept optional `expected_sections` from TOC parser.
- Use `NormPageLocator.locate_many(...)` to assign ranges.
- Generate `path_labels` deterministically (parent chain).
- Add `content_preview` for clause nodes (set placeholder until Task 8 adds full extraction).

**Step 3: Run tests**

Run: `cd services/api-server && python -m pytest -q tests/test_norm_index_builder.py`

Expected: PASS.

**Step 4: Commit**

```bash
git add services/api-server/app/services/norm_index_builder.py \
        services/api-server/tests/test_norm_index_builder.py
git commit -m "feat: make norm index builder toc/revision aware and page-range stable"
```

### Task 6: Upgrade Commentary Builder (Skip Revision Intro + 2nd TOC + Tree + Map)

**Files:**
- Modify: `services/api-server/app/services/norm_commentary_builder.py`
- Modify: `services/api-server/tests/test_norm_commentary_builder.py`

**Step 1: Adjust tests (from Task 1)**

Assertions:
- Only clause-level commentary lines become `commentary_map` entries.
- No duplicate labels; errors list reports duplicates.

**Step 2: Implement**

Builder changes:
- Accept already-sliced `commentary_markdown` (from splitter).
- Skip `目次` blocks inside commentary.
- Return a `tree` (same shape as index builder) and `summary_text` (can be empty baseline).

**Step 3: Run tests**

Run: `cd services/api-server && python -m pytest -q tests/test_norm_commentary_builder.py`

Expected: PASS.

**Step 4: Commit**

```bash
git add services/api-server/app/services/norm_commentary_builder.py \
        services/api-server/tests/test_norm_commentary_builder.py
git commit -m "feat: build commentary entries/map with toc skipping and tree"
```

### Task 7: Implement Strict Workflow Validator (Hard Gate + Report)

**Files:**
- Create: `services/api-server/app/services/norm_workflow_validator.py`
- Create: `services/api-server/tests/test_norm_workflow_validator.py`

**Step 1: Write failing tests**

Validator checks:
- `tree`/`entries` consistency (all tree nodes exist in entries).
- `entries` contains chapter+section+clause when expected sections exist.
- TOC-derived expected chapter/section labels must exist in entries.
- `commentary_map` cannot reference unknown clause labels.

**Step 2: Run tests**

Run: `cd services/api-server && python -m pytest -q tests/test_norm_workflow_validator.py`

Expected: FAIL.

**Step 3: Implement**

Return shape:
```py
{"ok": bool, "errors": [..], "warnings": [..], "stats": {...}}
```

**Step 4: Run tests**

Expected: PASS.

**Step 5: Commit**

```bash
git add services/api-server/app/services/norm_workflow_validator.py \
        services/api-server/tests/test_norm_workflow_validator.py
git commit -m "feat: add strict norm workflow validator with toc completeness"
```

### Task 8: Add `content_preview` To Clause Entries (DB + Model + Search)

**Files:**
- Modify: `services/api-server/app/models/norm_clause_entry.py`
- Modify: `services/api-server/app/db/schema.sql`
- Modify: `services/api-server/app/db/fts.sql`
- Modify: `services/api-server/app/repositories/postgres_norm_structure_repository.py`
- Modify: `services/api-server/app/services/norm_search_service.py`
- Create: `services/api-server/tests/test_postgres_repositories_integration.py` (extend existing) OR add a new focused test.

**Step 1: Write failing test**

Persist and search should return `content_preview` for a clause.

**Step 2: Implement**

- Add `content_preview: str = ""` to `NormClauseEntry`.
- Add column `content_preview text not null default ''` to `norm_clause_entries`.
- Update insert/select/search queries to include it.
- Include `content_preview` in `/norm-search/query` response items.

**Step 3: Run tests**

Run: `cd services/api-server && python -m pytest -q`

Expected: PASS.

**Step 4: Commit**

```bash
git add services/api-server/app/models/norm_clause_entry.py \
        services/api-server/app/db/schema.sql \
        services/api-server/app/db/fts.sql \
        services/api-server/app/repositories/postgres_norm_structure_repository.py \
        services/api-server/app/services/norm_search_service.py \
        services/api-server/tests
git commit -m "feat: persist and query clause content previews"
```

### Task 9: Wire Rule Pipeline Into `process_norm_document` (Always Persist Debug Artifacts)

**Files:**
- Modify: `services/api-server/app/workers/process_norm_document.py`
- Modify: `services/api-server/tests/test_norm_pipeline_e2e.py`
- Modify: `services/api-server/tests/test_norm_pipeline_configured_services.py`

**Step 1: Update failing tests**

E2E pipeline should now:
- Build rule-based clause index and commentary result (not empty commentary by default).
- Run strict validation and record audit steps.
- Persist `clause_index.json`, `commentary.json`, `validation.json`, `quality_report.json` artifacts regardless of backend.

**Step 2: Implement**

Pipeline changes:
- Use `NormMarkdownSplitter` to derive `toc/body/commentary` markdown.
- Use `NormTocParser` to derive expected chapters/sections.
- Build baseline clause index from body markdown and body page window.
- Build baseline commentary from sliced commentary markdown.
- Backfill clause `commentary_summary` from commentary map.
- Validate with `NormWorkflowValidator`.
- If ok: persist entries + artifacts.
- If not ok: proceed to Task 10 (AI patcher) if configured; else fail.

Audit steps to add:
- `rule_parse_started`, `rule_parse_completed`
- `rule_validate_passed` / `rule_validate_failed`

**Step 3: Run tests**

Run: `cd services/api-server && python -m pytest -q tests/test_norm_pipeline_e2e.py`

Expected: PASS.

**Step 4: Commit**

```bash
git add services/api-server/app/workers/process_norm_document.py \
        services/api-server/tests/test_norm_pipeline_e2e.py \
        services/api-server/tests/test_norm_pipeline_configured_services.py
git commit -m "feat: rule-first norm pipeline with strict validation and artifacts"
```

### Task 10: Implement DeepSeek Scope Patcher (Auto Trigger On Rule Failure)

**Files:**
- Create: `services/api-server/app/services/norm_ai_scope_patcher.py`
- Create: `services/api-server/tests/test_norm_ai_scope_patcher.py`
- Modify: `services/api-server/app/workers/process_norm_document.py`

**Step 1: Write failing tests**

Use a fake AI client/structurer to simulate:
- Rule validation fails due to missing expected section labels.
- Patcher is called per scope (assert call count and scope labels).
- After merge, validator passes and pipeline persists.

**Step 2: Implement**

Patcher responsibilities:
- Plan scopes:
  - Default: by chapter label from TOC.
  - If a chapter is “large” (heuristic on body markdown length), split by section label groups.
- For each scope:
  - Call `NormAIStructurer` (or a new lightweight client) with:
    - `baseline_clause_index` limited to that scope
    - `markdown_text` sliced to scope
    - `page_texts` limited to scope page window
  - Require AI output to be `entries` only or normalize to entries and ignore AI tree.
- Merge:
  - De-dupe by label.
  - Preserve baseline for nodes not covered by patch.
  - Rebuild tree and path_labels deterministically.

Pipeline integration:
- On `rule_validate_failed`:
  - If analysis config configured:
    - record `ai_patch_started`
    - run patcher scopes, record per-scope steps
    - record `ai_patch_completed`
    - re-validate
  - Else: mark failed

**Step 3: Run tests**

Run: `cd services/api-server && python -m pytest -q tests/test_norm_ai_scope_patcher.py`

Expected: PASS.

**Step 4: Commit**

```bash
git add services/api-server/app/services/norm_ai_scope_patcher.py \
        services/api-server/tests/test_norm_ai_scope_patcher.py \
        services/api-server/app/workers/process_norm_document.py
git commit -m "feat: auto deepseek scope patching on rule validation failure"
```

### Task 11: Frontend Phase 1: Display `content_preview` And Query Highlight In Sidebar

**Files:**
- Modify: `apps/web/src/lib/api/norms.ts`
- Modify: `apps/web/src/components/library/norm-detail-panel.tsx`
- (Optional) Modify: `apps/web/src/components/library/norm-search-panel.tsx`

**Step 1: Update types and mapping**

- Extend API response mapping to include `content_preview`.

**Step 2: Update UI**

- Show `content_preview` in detail panel, and highlight query tokens in the excerpt.
- Keep PDF viewer behavior: jump to `pageStart`.

**Step 3: Run web unit/e2e tests**

Run: `npm --prefix apps/web test -- --runInBand`

Expected: PASS.

**Step 4: Commit**

```bash
git add apps/web/src/lib/api/norms.ts \
        apps/web/src/components/library/norm-detail-panel.tsx \
        apps/web/src/components/library/norm-search-panel.tsx
git commit -m "feat(web): show clause content preview with query highlighting"
```

### Task 12: End-to-End Local Verification (Manual)

**Step 1: Start services**

- Postgres + API + Web as per your local runbook.

**Step 2: Configure project OCR + (optional) DeepSeek**

- Set OCR base_url/api_key/model in AI settings.
- If using AI fallback: set analysis base_url/api_key/model to DeepSeek compatible `/chat/completions`.

**Step 3: Upload a scanned norm PDF**

Expected:
- Job completes.
- Search returns items.
- Selecting an item jumps to correct PDF page and shows excerpt + commentary.

**Step 4: Capture artifacts**

Verify `tmp/storage/norm_artifacts/<doc>/<version>/` includes:
- `full.md`, `layout.json`, `clause_index.json`, `commentary.json`, `validation.json`, `quality_report.json`

