# Norm Pipeline Gap Close Design

**Date:** 2026-03-14

## Goal

After configuring provider APIs (OCR and optionally DeepSeek/LLM), a user can upload a scanned norm PDF and reliably obtain:

- `norm_clause_entries` (chapter/section/clause index) with robust `page_start/page_end`, `path_labels`, `summary_text`, `tags`, and `commentary_summary`.
- `norm_commentary_entries` representing the separate “条文说明” structure and clause-level commentary text.
- A searchable experience (FTS) and “jump-to-page + sidebar highlight” UX for scanned PDFs (no bbox).

## Non-Goals (Phase 1)

- PDF page block-level rectangle highlights (requires bbox/coordinate data from OCR). For scanned PDFs without bbox/text layer, Phase 1 will not draw rectangles on the PDF.
- A full bid-writing module and enforcement loop. This phase only produces the norm constraints data (entries + commentary) in a stable, validated form.

## Context / Current Gaps

- Built-in OCR adapters are stubs; live processing requires project-level OCR API configuration.
- Baseline index builder is too naive:
  - No “正文窗口” filtering or目录剔除.
  - Page locator is a simplistic substring check.
  - Summary/tags are placeholders.
- The DeepSeek playbook’s “scope splitting + flat entries + local merge + validation + patch reruns” is not implemented.
- Validation is currently minimal (tree/entries consistency only).

## Phase 1 Outcome (No BBox)

### User Experience

- Upload PDF.
- When processing completes:
  - Search norms by keyword, clause id, and path prefix.
  - Select a clause result:
    - PDF viewer jumps to `page_start`.
    - Sidebar shows `content_preview` (OCR excerpt) with query text highlighting.
    - Sidebar shows `commentary_summary` (from clause commentary mapping) when present.

### Data Produced

- `norm_clause_entries` persisted (Postgres) and searchable via FTS.
- `norm_commentary_entries` persisted (Postgres).
- Processing artifacts persisted to storage for replay/debug:
  - Normalized OCR: `full.md`, `layout.json` (or equivalent), `metadata.json`.
  - Derived: `clause_index.json`, `commentary.json`.
  - Validation: `validation.json` and `quality_report.json`.

## Architecture

### Inputs

From OCR (remote API):

- `markdown_text` (or `markdown`)
- `layout_payload.pages[]` (or `pages[]`) as per current normalizer: per-page text for page matching.

### Core Pipeline (Deterministic First)

1. OCR -> normalize artifacts (`markdown_text + page_texts`).
2. Rule-based extraction:
   - Clause index:
     - Skip directory noise and restrict to “正文窗口” (from first “1 总则/1总则” to before “修订说明”).
     - Parse chapters/sections/clauses from `full.md` patterns.
     - Build tree and `path_labels`.
     - Page locating using candidate matching within正文窗口 and sequential search.
     - Build `content_preview` from OCR text for each clause (used by UI).
     - Provide baseline tags (optional weak rules: must/shall/not, etc).
   - Commentary extraction:
     - Start after “修订说明”, skip the second “目次”, then parse commentary chapters/sections/clauses.
     - Build `commentary_map` keyed by clause id, with `commentary_text`, `summary_text`, `page_start/page_end`, and `section_path`.
     - Persist `norm_commentary_entries` and backfill `norm_clause_entries.commentary_summary`.
3. Validate using strict “workflow” requirements (hard gate).

### LLM Fallback (DeepSeek) When Rule Gate Fails

Trigger: deterministic validation fails (missing required sections, tree mismatch, etc).

Approach:

- Split into scopes following the playbook (example: `clause-ch1-3`, `clause-ch4-a/b/c`, `clause-ch5`, `commentary`).
- For each scope, call DeepSeek (OpenAI-compatible `/chat/completions`) to output flat `entries` only (no tree rebuild).
- Local merge:
  - Normalize ids/labels, de-duplicate, resolve parent links, rebuild tree, rebuild `commentary_map`.
  - Re-run the same strict validator.
- If still failing: mark job failed and persist all debug artifacts.

### Observability

- Job audit logs should include steps:
  - `rule_parse_started/completed`
  - `rule_validate_failed` with summary counts
  - `ai_patch_scope_started/completed` per scope
  - `merge_completed`
  - `final_validation_passed/failed`

## Testing Strategy

- Add golden fixtures from OCR outputs (`full.md + page_texts/layout`) for at least 2 representative norms.
- Unit tests:
  -正文窗口 detection and目录剔除.
  - Clause parser correctness (chapter/section/clause).
  - Commentary extractor correctness (skip 2nd TOC, map to clause ids).
  - Validator: enforce workflow hard requirements.
- Integration test:
  - Upload flow with a mocked OCR payload -> pipeline produces entries and persists to Postgres.

## Phase 2 (BBox Highlighters)

When OCR provides block/line bbox (page coords + dimensions):

- Store highlight anchors per clause: `highlight_blocks = [{page, bboxes:[...]}, ...]`.
- Frontend overlays rectangles on PDF pages.

## Success Criteria (Phase 1)

- Upload succeeds (with configured OCR API) and produces persisted `norm_clause_entries` and `norm_commentary_entries`.
- Search endpoint returns non-empty items for a known fixture query.
- For fixture norms: chapter 4/5 section completeness passes validator; `page_start/page_end` coverage meets threshold.
- UI can jump to page and show `content_preview` with query highlighting.

