# Norm Pipeline Remediation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Close the norm PDF pipeline gaps identified in the 2026-03-14 review so the project matches the documented “local-first, scoped AI patching, validated merge” design.

**Architecture:** Keep the current deterministic-first pipeline in place, but tighten the fallback path so AI receives only scope-local windows, commentary patches are merged locally, non-numeric roots can enter the tree, and retrieval preserves the clause/commentary boundary defined in the docs. Treat validation and ordering as first-class pipeline concerns rather than incidental byproducts of persistence or UI formatting.

**Tech Stack:** FastAPI, Pydantic, pytest, Next.js, TypeScript, Vitest, PostgreSQL FTS

---

## Requirements Summary

- Preserve the current OCR -> normalize -> local baseline parse -> validate -> optional AI patch -> persist flow in [process_norm_document.py](/Users/palmtom/Projects/aitender/services/api-server/app/workers/process_norm_document.py).
- Make AI patching conform to the scoped strategy described in [2026-03-11-norm-api-debugging-playbook.md](/Users/palmtom/Projects/aitender/docs/2026-03-11-norm-api-debugging-playbook.md) and [2026-03-11-norm-pdf-processing-workflow.md](/Users/palmtom/Projects/aitender/docs/2026-03-11-norm-pdf-processing-workflow.md).
- Preserve the documented separation between “正文硬约束” and “条文说明解释增强”.
- Keep diffs small and reversible.
- Restore a clean local verification baseline first:
  - backend targeted pytest passes
  - frontend targeted vitest passes
  - `apps/web` typecheck passes

## Current Baseline

- Environment has been bootstrapped locally:
  - `.venv` created at repo root
  - `apps/web/node_modules` installed
- Verified passing:
  - `PYTHONPATH=services/api-server .venv/bin/pytest services/api-server/tests/test_norm_pipeline_e2e.py services/api-server/tests/test_norm_pipeline_configured_services.py services/api-server/tests/test_norm_ai_scope_patcher.py services/api-server/tests/test_norm_workflow_validator.py -q`
  - `cd apps/web && npm test -- --runInBand 'src/app/projects/[projectId]/library/__tests__/norm-library.test.tsx' 'src/lib/api/__tests__/norms.test.ts'`
- Verified failing:
  - `cd apps/web && npx tsc --noEmit`
  - Failure source: [norm-library.test.tsx](/Users/palmtom/Projects/aitender/apps/web/src/app/projects/[projectId]/library/__tests__/norm-library.test.tsx) mocks omit required `contentPreview`.

## Acceptance Criteria

- AI fallback sends scope-local `markdown_text` and scope-local `page_texts`, not whole-document payloads.
- AI commentary patch participates in local merge and can improve clause-level `commentary_map`.
- Clause tree can represent `appendix` and `other` roots such as `附录A` / `本规范用词说明` / `引用标准名录`.
- Label ordering is semantic, not raw string order, across patch merge, repository reads, search results, and UI tree/result rendering.
- Retrieval returns or preserves distinct clause-first and commentary-second semantics.
- Validation covers duplicate labels, non-numeric roots, commentary completeness/granularity, and invalid page range/order conditions.
- `apps/web` typecheck passes.
- New or updated regression tests cover every fixed gap.

## Risks And Mitigations

- Risk: Scope slicing heuristics may cut away necessary context.
  - Mitigation: Add fixture-driven tests for chapter scopes and commentary scopes before implementation.
- Risk: Adding appendix/non-numeric roots may destabilize parent/path inference.
  - Mitigation: Introduce a shared label parser/comparator with explicit tests before wiring into builders/repositories.
- Risk: Search API shape changes could ripple into the UI.
  - Mitigation: Add backend compatibility layer first, then adapt frontend types/components with tests in the same task.
- Risk: Existing JSON/Postgres repositories may diverge in behavior.
  - Mitigation: Update both repositories in the same step and verify both JSON-path tests and Postgres integration assumptions.

## Implementation Tasks

### Task 0: Restore Clean Verification Baseline

**Files:**
- Modify: [norm-library.test.tsx](/Users/palmtom/Projects/aitender/apps/web/src/app/projects/[projectId]/library/__tests__/norm-library.test.tsx)
- Modify: [norms.test.ts](/Users/palmtom/Projects/aitender/apps/web/src/lib/api/__tests__/norms.test.ts)

**Steps:**
1. Update mocked `NormSearchResult` payloads so they include `contentPreview`.
2. Re-run:
   - `cd apps/web && npm test -- --runInBand 'src/app/projects/[projectId]/library/__tests__/norm-library.test.tsx' 'src/lib/api/__tests__/norms.test.ts'`
   - `cd apps/web && npx tsc --noEmit`
3. Commit after typecheck is green.

### Task 1: Implement Scope-Local AI Input Slicing

**Files:**
- Modify: [process_norm_document.py](/Users/palmtom/Projects/aitender/services/api-server/app/workers/process_norm_document.py)
- Modify: [norm_ai_scope_patcher.py](/Users/palmtom/Projects/aitender/services/api-server/app/services/norm_ai_scope_patcher.py)
- Modify: [norm_ai_structurer.py](/Users/palmtom/Projects/aitender/services/api-server/app/services/norm_ai_structurer.py)
- Modify: [test_norm_ai_scope_patcher.py](/Users/palmtom/Projects/aitender/services/api-server/tests/test_norm_ai_scope_patcher.py)
- Add or modify: fixture under [services/api-server/tests/fixtures/norm_samples](/Users/palmtom/Projects/aitender/services/api-server/tests/fixtures/norm_samples)

**Steps:**
1. Write failing tests proving each scope call receives only local markdown/page windows.
2. Add scope descriptors richer than “chapter only”; include at least clause-body scopes and commentary scopes.
3. Implement helpers that derive:
   - scope-local markdown slice
   - scope-local page range/window
   - scope-local baseline entries
4. Keep AI payload flat-entry focused; do not re-send full document context.
5. Re-run targeted backend tests.

### Task 2: Merge AI Commentary Patch And Strengthen Commentary Gate

**Files:**
- Modify: [norm_ai_scope_patcher.py](/Users/palmtom/Projects/aitender/services/api-server/app/services/norm_ai_scope_patcher.py)
- Modify: [norm_workflow_validator.py](/Users/palmtom/Projects/aitender/services/api-server/app/services/norm_workflow_validator.py)
- Modify: [process_norm_document.py](/Users/palmtom/Projects/aitender/services/api-server/app/workers/process_norm_document.py)
- Modify: [test_norm_ai_scope_patcher.py](/Users/palmtom/Projects/aitender/services/api-server/tests/test_norm_ai_scope_patcher.py)
- Modify: [test_norm_workflow_validator.py](/Users/palmtom/Projects/aitender/services/api-server/tests/test_norm_workflow_validator.py)
- Modify: [test_norm_pipeline_configured_services.py](/Users/palmtom/Projects/aitender/services/api-server/tests/test_norm_pipeline_configured_services.py)

**Steps:**
1. Add failing tests where baseline commentary is incomplete and AI patch must improve it.
2. Merge `commentary_patch.entries` and `commentary_patch.commentary_map` locally.
3. Backfill merged commentary summaries onto clause entries before persistence.
4. Extend validator with commentary granularity/completeness checks, not just unknown-label checks.
5. Re-run targeted backend tests and ensure AI fallback path still passes.

### Task 3: Add Appendix / Other Roots And Semantic Label Ordering

**Files:**
- Modify: [norm_clause_entry.py](/Users/palmtom/Projects/aitender/services/api-server/app/models/norm_clause_entry.py)
- Modify: [norm_commentary_entry.py](/Users/palmtom/Projects/aitender/services/api-server/app/models/norm_commentary_entry.py)
- Modify: [norm_index_builder.py](/Users/palmtom/Projects/aitender/services/api-server/app/services/norm_index_builder.py)
- Modify: [norm_commentary_builder.py](/Users/palmtom/Projects/aitender/services/api-server/app/services/norm_commentary_builder.py)
- Modify: [norm_library_service.py](/Users/palmtom/Projects/aitender/services/api-server/app/services/norm_library_service.py)
- Modify: [json_norm_structure_repository.py](/Users/palmtom/Projects/aitender/services/api-server/app/repositories/json_norm_structure_repository.py)
- Modify: [postgres_norm_structure_repository.py](/Users/palmtom/Projects/aitender/services/api-server/app/repositories/postgres_norm_structure_repository.py)
- Add: shared label parsing/sort utility under [services/api-server/app/services](/Users/palmtom/Projects/aitender/services/api-server/app/services)
- Add or modify tests:
  - [test_norm_index_builder.py](/Users/palmtom/Projects/aitender/services/api-server/tests/test_norm_index_builder.py)
  - [test_norm_commentary_builder.py](/Users/palmtom/Projects/aitender/services/api-server/tests/test_norm_commentary_builder.py)
  - repository/integration tests as needed

**Steps:**
1. Add failing fixtures covering `附录A`, `本规范用词说明`, `引用标准名录`, and numeric labels like `4.2` vs `4.10`.
2. Implement node parsing/normalization for `chapter` / `section` / `clause` / `appendix` / `other`.
3. Replace raw string sorting with shared semantic sort keys in services and repositories.
4. Verify path reconstruction and tree rebuild still work for mixed label families.
5. Re-run unit and repository tests.

### Task 4: Restore Clause/Commentary Dual-Channel Retrieval

**Files:**
- Modify: [norm_search_service.py](/Users/palmtom/Projects/aitender/services/api-server/app/services/norm_search_service.py)
- Modify: [postgres_norm_structure_repository.py](/Users/palmtom/Projects/aitender/services/api-server/app/repositories/postgres_norm_structure_repository.py)
- Modify: [json_norm_structure_repository.py](/Users/palmtom/Projects/aitender/services/api-server/app/repositories/json_norm_structure_repository.py)
- Modify: search route/schema files under [services/api-server/app/api](/Users/palmtom/Projects/aitender/services/api-server/app/api)
- Modify frontend types and consumers:
  - [norms.ts](/Users/palmtom/Projects/aitender/apps/web/src/lib/api/norms.ts)
  - [library-workspace.tsx](/Users/palmtom/Projects/aitender/apps/web/src/components/library/library-workspace.tsx)
  - related tests under [apps/web/src](/Users/palmtom/Projects/aitender/apps/web/src)

**Steps:**
1. Decide on API shape:
   - preferred: separate `clause_hits` and `commentary_hits`
   - fallback-compatible option: clause items annotated with hit-source priority
2. Add failing backend tests for mixed clause/commentary matches.
3. Implement repository/service/query changes.
4. Update frontend mapping and rendering so hard constraints remain primary and commentary remains secondary.
5. Re-run backend search tests, frontend vitest, and `npx tsc --noEmit`.

### Task 5: Expand Quality Gate And Debug Artifacts

**Files:**
- Modify: [norm_workflow_validator.py](/Users/palmtom/Projects/aitender/services/api-server/app/services/norm_workflow_validator.py)
- Modify: [process_norm_document.py](/Users/palmtom/Projects/aitender/services/api-server/app/workers/process_norm_document.py)
- Modify or add scripts under [services/api-server/scripts](/Users/palmtom/Projects/aitender/services/api-server/scripts)
- Modify tests:
  - [test_norm_workflow_validator.py](/Users/palmtom/Projects/aitender/services/api-server/tests/test_norm_workflow_validator.py)
  - [test_norm_library_service.py](/Users/palmtom/Projects/aitender/services/api-server/tests/test_norm_library_service.py)
  - [test_postgres_repositories_integration.py](/Users/palmtom/Projects/aitender/services/api-server/tests/test_postgres_repositories_integration.py)

**Steps:**
1. Add failing tests for:
   - duplicate labels
   - reversed/invalid page ranges
   - missing appendix/other roots when expected
   - commentary too coarse or empty after patching
2. Extend validator output to include richer stats and quality findings.
3. Persist `quality_report.json` alongside `validation.json`.
4. Ensure failure messages remain actionable in job audit logs.
5. Re-run targeted tests and one broader pipeline integration pass.

### Task 6: Final Regression Pass And Documentation Sync

**Files:**
- Modify: [2026-03-14-norm-pipeline-code-review-report.md](/Users/palmtom/Projects/aitender/docs/2026-03-14-norm-pipeline-code-review-report.md) only if outcomes need a follow-up note
- Modify docs if implementation changes actual behavior contracts:
  - [2026-03-11-norm-pdf-processing-workflow.md](/Users/palmtom/Projects/aitender/docs/2026-03-11-norm-pdf-processing-workflow.md)
  - [2026-03-11-norm-api-debugging-playbook.md](/Users/palmtom/Projects/aitender/docs/2026-03-11-norm-api-debugging-playbook.md)

**Steps:**
1. Run the focused backend and frontend suites touched above.
2. Run:
   - `PYTHONPATH=services/api-server .venv/bin/pytest services/api-server/tests -q`
   - `cd apps/web && npm test`
   - `cd apps/web && npx tsc --noEmit`
3. If Postgres is available, run [test_postgres_repositories_integration.py](/Users/palmtom/Projects/aitender/services/api-server/tests/test_postgres_repositories_integration.py) as a final persistence check.
4. Update docs only where shipped behavior now materially differs from the current text.

## Verification Steps

- Backend targeted tests:
  - `PYTHONPATH=services/api-server .venv/bin/pytest services/api-server/tests/test_norm_ai_scope_patcher.py -q`
  - `PYTHONPATH=services/api-server .venv/bin/pytest services/api-server/tests/test_norm_workflow_validator.py -q`
  - `PYTHONPATH=services/api-server .venv/bin/pytest services/api-server/tests/test_norm_pipeline_configured_services.py -q`
  - `PYTHONPATH=services/api-server .venv/bin/pytest services/api-server/tests/test_norm_pipeline_e2e.py -q`
- Backend broader pass:
  - `PYTHONPATH=services/api-server .venv/bin/pytest services/api-server/tests -q`
- Frontend:
  - `cd apps/web && npm test -- --runInBand 'src/app/projects/[projectId]/library/__tests__/norm-library.test.tsx' 'src/lib/api/__tests__/norms.test.ts'`
  - `cd apps/web && npm test`
  - `cd apps/web && npx tsc --noEmit`

## Suggested Execution Order

1. Task 0
2. Task 1
3. Task 2
4. Task 3
5. Task 5
6. Task 4
7. Task 6

Rationale:
- Fix the verification baseline first.
- Repair pipeline correctness before changing retrieval semantics.
- Strengthen quality gates before broadening search/UI behavior.
