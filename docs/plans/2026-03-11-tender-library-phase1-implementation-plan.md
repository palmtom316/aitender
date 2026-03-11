# 投标资料库 Phase 1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 `aitender` 中交付一个可演示、可验收的“投标资料库 Phase 1”最小可用产品，支持规范规程 PDF 的上传、OCR、结构化、检索与高亮召回。

**Architecture:** 采用前后端分层架构：前端提供登录、项目、上传、检索与结果查看界面；后端提供权限、文档入库、OCR 适配、结构化处理、检索 API。规范结构化链路采用“统一 OCR 中间格式 + 本地算法重建最终结构”的方案，大模型只承担必要的语义抽取，不承担最终结构闭环。

**Tech Stack:** `Next.js`、`TypeScript`、`Tailwind CSS`、`FastAPI`、`Pydantic`、`PostgreSQL`、`Redis`、对象存储、可插拔 OCR 适配层

---

## Requirements Summary

- 项目总范围覆盖 6 个模块，但本计划只详细实施“投标资料库 Phase 1”。
- 首期仅支持“规范规程 PDF”链路，不实施其他资料类型的完整处理流程。
- 首期必须交付可用前端，而不是只做后端原型。
- 首期需要单组织基础协作能力，支持 `admin`、`project_manager`、`writer`、`viewer` 角色。
- OCR 采用可插拔接口，`MinerU` 与商业 OCR API 都要保留接入位。
- 检索以词法检索和结构化过滤为主，不引入向量检索。

## Acceptance Criteria

1. 用户可以登录、进入项目、看到授权范围内的资料库数据。
2. 用户可以上传规范规程 PDF，并看到处理状态、成功结果或失败原因。
3. 后端可以通过统一 OCR 接口接入至少一个真实 OCR 实现，以及一个备用适配器骨架。
4. 系统可以把 OCR 结果标准化为统一内部结构，并生成正文条款索引和条文说明映射。
5. 用户可以按关键词、章节路径、条款号检索规范内容。
6. 用户可以查看条款详情、页码范围、摘要、条文说明和高亮预览。
7. 全链路具备基础日志、任务状态和错误追踪能力。
8. 关键后端接口、核心结构化算法和最小前端流程具备可执行测试。

## Assumed Repository Shape

当前仓库仅有基础骨架，实施时建议采用如下目录：

- `apps/web`
- `services/api-server`
- `workers/document-worker`
- `packages/shared`
- `docs`

如果实施前决定采用其他目录结构，必须先统一调整本计划中的文件路径，再进入编码。

## Implementation Steps

### Task 1: 建立工程目录与基础运行骨架

**Files:**
- Modify: `README.md`
- Create: `apps/web/package.json`
- Create: `apps/web/tsconfig.json`
- Create: `apps/web/next.config.ts`
- Create: `apps/web/src/app/layout.tsx`
- Create: `apps/web/src/app/page.tsx`
- Create: `services/api-server/pyproject.toml`
- Create: `services/api-server/app/main.py`
- Create: `services/api-server/app/core/config.py`
- Create: `workers/document-worker/README.md`
- Create: `packages/shared/README.md`

**Step 1: Write the failing test**

创建最小健康检查测试文件：

- `services/api-server/tests/test_health.py`
- `apps/web/src/app/__tests__/home.test.tsx`

测试目标：

- API 返回健康状态
- Web 首页可以正常渲染系统标题

**Step 2: Run test to verify it fails**

Run:

```bash
pytest services/api-server/tests/test_health.py -q
```

Run:

```bash
npm --prefix apps/web test -- --runInBand
```

Expected:

- API 测试失败，因为应用尚未建立
- Web 测试失败，因为页面与测试基座尚未建立

**Step 3: Write minimal implementation**

- 初始化前后端最小工程结构
- 创建 API 健康检查路由
- 创建 Web 首页，显示 `aitender` 与 Phase 1 标识

**Step 4: Run test to verify it passes**

Run:

```bash
pytest services/api-server/tests/test_health.py -q
```

Run:

```bash
npm --prefix apps/web test -- --runInBand
```

Expected:

- 两侧最小测试通过

**Step 5: Commit**

```bash
git add README.md apps/web services/api-server workers/document-worker packages/shared
git commit -m "chore: scaffold web and api foundations"
```

### Task 2: 建立认证、组织、项目和基础角色模型

**Files:**
- Create: `services/api-server/app/models/user.py`
- Create: `services/api-server/app/models/organization.py`
- Create: `services/api-server/app/models/project.py`
- Create: `services/api-server/app/models/project_member.py`
- Create: `services/api-server/app/api/routes/auth.py`
- Create: `services/api-server/app/api/routes/projects.py`
- Create: `services/api-server/app/services/auth_service.py`
- Create: `services/api-server/app/services/project_service.py`
- Create: `services/api-server/tests/test_auth.py`
- Create: `services/api-server/tests/test_projects.py`
- Create: `apps/web/src/app/login/page.tsx`
- Create: `apps/web/src/app/projects/page.tsx`
- Create: `apps/web/src/components/auth/login-form.tsx`
- Create: `apps/web/src/components/projects/project-list.tsx`

**Step 1: Write the failing test**

覆盖以下行为：

- 用户可登录
- 角色可以绑定到项目
- 只返回当前用户有权限访问的项目

**Step 2: Run test to verify it fails**

Run:

```bash
pytest services/api-server/tests/test_auth.py services/api-server/tests/test_projects.py -q
```

Expected:

- 因缺少模型、路由和权限逻辑而失败

**Step 3: Write minimal implementation**

- 建立最小认证与项目访问控制
- 固定首期角色：`admin`、`project_manager`、`writer`、`viewer`
- Web 端提供登录页和项目列表页

**Step 4: Run test to verify it passes**

Run:

```bash
pytest services/api-server/tests/test_auth.py services/api-server/tests/test_projects.py -q
```

Expected:

- 认证与项目访问控制测试通过

**Step 5: Commit**

```bash
git add services/api-server apps/web
git commit -m "feat: add auth, projects, and role boundaries"
```

### Task 3: 建立文档上传、版本记录与对象存储抽象

**Files:**
- Create: `services/api-server/app/models/document.py`
- Create: `services/api-server/app/models/document_version.py`
- Create: `services/api-server/app/models/document_artifact.py`
- Create: `services/api-server/app/api/routes/documents.py`
- Create: `services/api-server/app/services/document_service.py`
- Create: `services/api-server/app/integrations/storage/base.py`
- Create: `services/api-server/app/integrations/storage/local.py`
- Create: `services/api-server/tests/test_document_upload.py`
- Create: `apps/web/src/app/projects/[projectId]/library/page.tsx`
- Create: `apps/web/src/components/library/upload-panel.tsx`
- Create: `apps/web/src/components/library/document-table.tsx`

**Step 1: Write the failing test**

覆盖以下行为：

- 上传规范 PDF 成功创建文档与版本记录
- 文档默认落到 `norm_library`
- 失败上传不会产生脏记录

**Step 2: Run test to verify it fails**

Run:

```bash
pytest services/api-server/tests/test_document_upload.py -q
```

Expected:

- 因缺少上传接口和持久化逻辑而失败

**Step 3: Write minimal implementation**

- 建立上传 API
- 建立本地对象存储抽象
- 建立项目资料库页面，支持上传并展示文档状态

**Step 4: Run test to verify it passes**

Run:

```bash
pytest services/api-server/tests/test_document_upload.py -q
```

Expected:

- 上传与版本记录测试通过

**Step 5: Commit**

```bash
git add services/api-server apps/web
git commit -m "feat: add document upload and artifact persistence"
```

### Task 4: 建立 OCR 适配层与处理任务编排

**Files:**
- Create: `services/api-server/app/integrations/ocr/base.py`
- Create: `services/api-server/app/integrations/ocr/mineru_adapter.py`
- Create: `services/api-server/app/integrations/ocr/commercial_adapter.py`
- Create: `services/api-server/app/services/ocr_dispatcher.py`
- Create: `services/api-server/app/models/norm_processing_job.py`
- Create: `services/api-server/app/workers/process_norm_document.py`
- Create: `services/api-server/tests/test_ocr_dispatcher.py`
- Create: `workers/document-worker/worker.py`

**Step 1: Write the failing test**

覆盖以下行为：

- 可以根据配置选择 OCR 供应商
- 适配层输出统一结果结构
- OCR 失败时任务状态更新为失败并记录错误

**Step 2: Run test to verify it fails**

Run:

```bash
pytest services/api-server/tests/test_ocr_dispatcher.py -q
```

Expected:

- 因缺少 OCR 抽象和任务状态逻辑而失败

**Step 3: Write minimal implementation**

- 定义 OCR 抽象接口
- 实现 `MinerU` 与商业 OCR 的适配骨架
- 建立文档处理任务与状态机

**Step 4: Run test to verify it passes**

Run:

```bash
pytest services/api-server/tests/test_ocr_dispatcher.py -q
```

Expected:

- OCR 路由与任务状态测试通过

**Step 5: Commit**

```bash
git add services/api-server workers/document-worker
git commit -m "feat: add OCR adapter layer and processing jobs"
```

### Task 5: 标准化 OCR 中间产物并保存调试工件

**Files:**
- Create: `services/api-server/app/schemas/norm_artifacts.py`
- Create: `services/api-server/app/services/norm_artifact_normalizer.py`
- Create: `services/api-server/app/services/norm_artifact_store.py`
- Create: `services/api-server/tests/test_norm_artifact_normalizer.py`
- Create: `services/api-server/tests/fixtures/norm_artifacts/`

**Step 1: Write the failing test**

覆盖以下行为：

- 不同 OCR 适配器输出可归一到统一结构
- 标准化结果至少包含原文 Markdown、页布局文本和元数据
- 中间调试工件可保存并追踪

**Step 2: Run test to verify it fails**

Run:

```bash
pytest services/api-server/tests/test_norm_artifact_normalizer.py -q
```

Expected:

- 因标准化逻辑不存在而失败

**Step 3: Write minimal implementation**

- 定义统一中间结构
- 保存 `full.md`、`layout.json` 或等价对象
- 保存任务调试工件和来源信息

**Step 4: Run test to verify it passes**

Run:

```bash
pytest services/api-server/tests/test_norm_artifact_normalizer.py -q
```

Expected:

- 中间产物标准化测试通过

**Step 5: Commit**

```bash
git add services/api-server
git commit -m "feat: normalize OCR artifacts for downstream processing"
```

### Task 6: 实现规范正文条款索引生成链路

**Files:**
- Create: `services/api-server/app/services/norm_index_builder.py`
- Create: `services/api-server/app/services/norm_page_locator.py`
- Create: `services/api-server/app/services/norm_summary_builder.py`
- Create: `services/api-server/app/models/norm_clause_entry.py`
- Create: `services/api-server/app/api/routes/norms.py`
- Create: `services/api-server/tests/test_norm_index_builder.py`
- Create: `services/api-server/tests/fixtures/norm_samples/`

**Step 1: Write the failing test**

覆盖以下行为：

- 能从样例规范中提取章、节、条款层级
- 能定位页码范围
- 能输出结构化 `clause_index`

**Step 2: Run test to verify it fails**

Run:

```bash
pytest services/api-server/tests/test_norm_index_builder.py -q
```

Expected:

- 因索引构建链路不存在而失败

**Step 3: Write minimal implementation**

- 先解析正文窗口
- 提取章节结构与条款号
- 重建树并持久化条款索引

**Step 4: Run test to verify it passes**

Run:

```bash
pytest services/api-server/tests/test_norm_index_builder.py -q
```

Expected:

- 正文索引构建测试通过

**Step 5: Commit**

```bash
git add services/api-server
git commit -m "feat: build norm clause index from normalized artifacts"
```

### Task 7: 实现条文说明映射与结构校验链路

**Files:**
- Create: `services/api-server/app/services/norm_commentary_builder.py`
- Create: `services/api-server/app/services/norm_structure_validator.py`
- Create: `services/api-server/app/models/norm_commentary_entry.py`
- Create: `services/api-server/tests/test_norm_commentary_builder.py`
- Create: `services/api-server/tests/test_norm_structure_validator.py`

**Step 1: Write the failing test**

覆盖以下行为：

- 能识别条文说明窗口并建立 `clause_id -> commentary` 映射
- 能校验条款树与说明映射的基本一致性
- 结构缺失或脏数据时能返回明确错误

**Step 2: Run test to verify it fails**

Run:

```bash
pytest services/api-server/tests/test_norm_commentary_builder.py services/api-server/tests/test_norm_structure_validator.py -q
```

Expected:

- 因说明映射与结构校验逻辑不存在而失败

**Step 3: Write minimal implementation**

- 实现条文说明构建器
- 实现本地结构校验器
- 在处理任务链中加入校验阶段

**Step 4: Run test to verify it passes**

Run:

```bash
pytest services/api-server/tests/test_norm_commentary_builder.py services/api-server/tests/test_norm_structure_validator.py -q
```

Expected:

- 说明映射与结构校验测试通过

**Step 5: Commit**

```bash
git add services/api-server
git commit -m "feat: add commentary mapping and structure validation"
```

### Task 8: 建立规范检索 API 与结果过滤能力

**Files:**
- Create: `services/api-server/app/services/norm_search_service.py`
- Create: `services/api-server/app/api/routes/norm_search.py`
- Create: `services/api-server/tests/test_norm_search.py`
- Create: `services/api-server/app/db/fts.sql`

**Step 1: Write the failing test**

覆盖以下行为：

- 支持关键词搜索
- 支持按 `clause_id`、章节路径过滤
- 返回摘要、页码和条文说明摘要

**Step 2: Run test to verify it fails**

Run:

```bash
pytest services/api-server/tests/test_norm_search.py -q
```

Expected:

- 因检索 API 与索引逻辑不存在而失败

**Step 3: Write minimal implementation**

- 建立 PostgreSQL FTS 查询
- 提供结构化过滤参数
- 返回前端可直接消费的结果结构

**Step 4: Run test to verify it passes**

Run:

```bash
pytest services/api-server/tests/test_norm_search.py -q
```

Expected:

- 检索测试通过

**Step 5: Commit**

```bash
git add services/api-server
git commit -m "feat: add norm search and filtering APIs"
```

### Task 9: 建立资料库前端页面、详情联动与高亮预览

**Files:**
- Create: `apps/web/src/app/projects/[projectId]/library/norms/[documentId]/page.tsx`
- Create: `apps/web/src/components/library/norm-search-panel.tsx`
- Create: `apps/web/src/components/library/norm-tree.tsx`
- Create: `apps/web/src/components/library/norm-result-list.tsx`
- Create: `apps/web/src/components/library/norm-detail-panel.tsx`
- Create: `apps/web/src/components/library/norm-highlight-viewer.tsx`
- Create: `apps/web/src/lib/api/norms.ts`
- Create: `apps/web/src/app/projects/[projectId]/library/__tests__/norm-library.test.tsx`

**Step 1: Write the failing test**

覆盖以下行为：

- 页面可展示上传文档列表
- 页面可执行检索并显示结果
- 点击结果后可联动树结构、详情和高亮预览

**Step 2: Run test to verify it fails**

Run:

```bash
npm --prefix apps/web test -- --runInBand norm-library
```

Expected:

- 因组件和 API 适配层不存在而失败

**Step 3: Write minimal implementation**

- 完成资料库主界面
- 接入检索 API
- 提供条款详情与高亮预览容器

**Step 4: Run test to verify it passes**

Run:

```bash
npm --prefix apps/web test -- --runInBand norm-library
```

Expected:

- 前端资料库主流程测试通过

**Step 5: Commit**

```bash
git add apps/web
git commit -m "feat: build norm library search and preview UI"
```

### Task 10: 加入处理日志、失败回显和基础可观测性

**Files:**
- Create: `services/api-server/app/services/audit_service.py`
- Create: `services/api-server/app/api/routes/jobs.py`
- Create: `services/api-server/tests/test_processing_jobs.py`
- Create: `apps/web/src/components/library/job-status-panel.tsx`
- Create: `apps/web/src/components/library/error-state.tsx`

**Step 1: Write the failing test**

覆盖以下行为：

- 可查询处理任务状态
- 失败原因可展示
- 关键处理步骤落审计或日志记录

**Step 2: Run test to verify it fails**

Run:

```bash
pytest services/api-server/tests/test_processing_jobs.py -q
```

Expected:

- 因任务状态查询和日志落库能力不存在而失败

**Step 3: Write minimal implementation**

- 建立任务查询 API
- 保存关键步骤日志
- 前端展示任务状态、失败原因与重试提示

**Step 4: Run test to verify it passes**

Run:

```bash
pytest services/api-server/tests/test_processing_jobs.py -q
```

Expected:

- 任务状态测试通过

**Step 5: Commit**

```bash
git add services/api-server apps/web
git commit -m "feat: expose processing status and failure feedback"
```

### Task 11: 端到端串联首条规范处理闭环

**Files:**
- Create: `services/api-server/tests/test_norm_pipeline_e2e.py`
- Create: `apps/web/e2e/norm-library.spec.ts`
- Modify: `README.md`
- Modify: `docs/2026-03-11-aitender-product-requirements-prd.md`

**Step 1: Write the failing test**

覆盖以下行为：

- 从上传规范 PDF 到可检索结果形成完整闭环
- Web 端能完成最小用户流程

**Step 2: Run test to verify it fails**

Run:

```bash
pytest services/api-server/tests/test_norm_pipeline_e2e.py -q
```

Run:

```bash
npm --prefix apps/web run test:e2e
```

Expected:

- 在闭环未打通前失败

**Step 3: Write minimal implementation**

- 修补接口、异步任务、状态更新和页面交互中的缺口
- 补齐 README 启动说明

**Step 4: Run test to verify it passes**

Run:

```bash
pytest services/api-server/tests/test_norm_pipeline_e2e.py -q
```

Run:

```bash
npm --prefix apps/web run test:e2e
```

Expected:

- 首条端到端流程通过

**Step 5: Commit**

```bash
git add README.md docs apps/web services/api-server
git commit -m "feat: ship norm library phase 1 MVP"
```

## Risks and Mitigations

- OCR 供应商输出格式差异大
  - 通过统一中间结构与适配层隔离差异
- 规范 PDF 高亮预览实现复杂
  - 首期允许先用“页码定位 + 命中文本高亮片段”实现，避免一开始做重型 PDF 标注系统
- 结构化准确率不足
  - 通过固定样例、结构校验器和调试工件回放补强
- 仓库当前没有现成工程骨架
  - 先完成基础脚手架和健康检查，再进入业务开发
- 其他资料类型容易造成首期范围膨胀
  - 只做页面和接口预留，不进入 Phase 1 交付闭环

## Verification Steps

- API 单元测试：

```bash
pytest services/api-server/tests -q
```

- Web 单元测试：

```bash
npm --prefix apps/web test -- --runInBand
```

- Web 端到端测试：

```bash
npm --prefix apps/web run test:e2e
```

- 手工验收：
  - 登录系统
  - 创建或进入项目
  - 上传规范 PDF
  - 查看处理状态
  - 搜索指定条款
  - 打开详情与高亮预览

## Roadmap Beyond Phase 1

- 招标分析：
  - 基于招标文件生成结构化响应清单、风险清单和写作任务树
- 标书编制：
  - 基于项目目录与证据包逐章生成内容
- 标书审核：
  - 基于规范、招标要求和企业事实做缺失与冲突检查
- 标书排版：
  - 将已确认内容写入企业模板并导出 `DOCX`
- 标书管理：
  - 做版本追踪、归档、回灌和项目审计

Plan complete and saved to `docs/plans/2026-03-11-tender-library-phase1-implementation-plan.md`. Two execution options:

**1. Subagent-Driven (this session)** - 我在当前会话按任务逐步实施并在关键节点复核

**2. Parallel Session (separate)** - 新开执行会话，按计划文档批量推进

如果你下一步要我开工，我建议直接用当前会话按该计划执行。
