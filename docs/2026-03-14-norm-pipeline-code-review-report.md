# 规范 PDF / OCR / 结构化链路代码审查报告（2026-03-14）

## 审查范围

- 目标文档：
  - `docs/2026-03-11-norm-api-debugging-playbook.md`
  - `docs/2026-03-11-norm-pdf-processing-workflow.md`
- 重点代码：
  - `services/api-server/app/workers/process_norm_document.py`
  - `services/api-server/app/services/norm_artifact_normalizer.py`
  - `services/api-server/app/services/norm_artifact_store.py`
  - `services/api-server/app/services/norm_index_builder.py`
  - `services/api-server/app/services/norm_commentary_builder.py`
  - `services/api-server/app/services/norm_workflow_validator.py`
  - `services/api-server/app/services/norm_ai_structurer.py`
  - `services/api-server/app/services/norm_ai_scope_patcher.py`
  - `services/api-server/app/services/norm_search_service.py`
  - `services/api-server/app/repositories/postgres_norm_structure_repository.py`

## 结论摘要

项目已经把“统一 OCR 中间层 + 本地生成正文条款索引 + 本地生成条文说明映射 + 本地校验 + 持久化检索”这一条主链路搭起来了，核心方向与两份文档是一致的。

但文档里最关键的工程化经验并没有完整落地，尤其是：

1. 没有把 AI 输入真正缩到 scope 级窗口。
2. 没有把 AI 的 commentary patch 合回最终结果。
3. 规范文档中特别强调的 `附录A / 本规范用词说明 / 引用标准名录` 等非数字根节点目前无法进入索引树。
4. 检索层没有落实“正文硬约束 + 条文说明解释增强”的双通道语义，当前是混合检索。

这意味着：当前实现能支撑 Phase 1 演示和小样本闭环，但距离文档中验证过的“大规范稳定处理路径”还有明显差距。

## Findings

### HIGH

1. `scope patching` 仍然把整份文档喂给每一次 AI 调用，文档中验证过的“按 scope 缩窗输入”没有落地。
   - 证据：
     - `docs/2026-03-11-norm-api-debugging-playbook.md:69-74,166-178,188-214` 明确要求避免整份大 JSON / 大文档直出，改为 `page_texts` 压缩后按 scope 分片，再本地拼接与校验。
     - `services/api-server/app/workers/process_norm_document.py:187-198` 在进入 AI patching 时，把 `normalized.markdown_text` 和完整 `page_texts` 直接传入 patcher。
     - `services/api-server/app/services/norm_ai_scope_patcher.py:47-58` 虽然循环 scope，但每个 scope 都复用同一份 `markdown_text` 和 `page_texts`，只裁剪了 `baseline_clause_index`。
     - `services/api-server/app/services/norm_ai_structurer.py:57-74` 会把整份 `markdown_text`、整份 `page_texts`、scope baseline 一起序列化发给模型。
   - 风险：
     - 会重新触发文档已经踩过的上下文过大、输出截断、长时间超时问题。
     - 第 4/5 章这类大章不会因为“有 scope 循环”就真的降载。
   - 建议：
     - 在 patcher 内先按 chapter/section scope 生成 scope-local `markdown_text` 和 scope-local `page_texts`。
     - AI 只接收当前 scope 的平铺目标，不再接收整份正文。
     - 补上缺口 scope 重跑机制，而不是重复整份输入。

2. AI 生成的 `commentary_result` 被直接丢弃，无法实现文档要求的“条文说明定点补片”。
   - 证据：
     - `docs/2026-03-11-norm-api-debugging-playbook.md:145-148,169-177,248-296,501-533` 把 commentary 从 section 级拉回 clause 级，正是分片补片路径里的核心目标之一。
     - `services/api-server/app/services/norm_ai_scope_patcher.py:52-58` 能拿到 `commentary_patch`。
     - `services/api-server/app/services/norm_ai_scope_patcher.py:74-87` 明确注释“Commentary patch is optional in Phase 1; keep the baseline by default.”，最终直接返回 `baseline_commentary_result`。
     - `services/api-server/app/services/norm_workflow_validator.py:53-61` 只检查 commentary 是否引用了不存在的 clause，不检查 commentary 是否缺失、是否仍停留在 section 粒度。
   - 风险：
     - 本地 builder 一旦只抽出粗粒度说明，AI 无法把它修正为 clause 级映射。
     - 校验也不会把这种“说明粒度不够”识别成失败。
   - 建议：
     - 把 `commentary_patch.entries/commentary_map` 参与本地合并。
     - 增加 commentary completeness / granularity 校验。
     - 将“正文补片”和“说明补片”拆成可独立重跑的 scope。

3. 非数字根节点完全不在解析能力范围内，文档要求保留的 `附录A / 本规范用词说明 / 引用标准名录` 目前无法入树。
   - 证据：
     - `docs/2026-03-11-norm-pdf-processing-workflow.md:180-188,648-649,704-706` 明确把 `附录A`、`本规范用词说明`、`引用标准名录` 作为最终结构的一部分。
     - `services/api-server/app/services/norm_index_builder.py:9-10` 只匹配数字 heading / 数字 clause。
     - `services/api-server/app/services/norm_index_builder.py:39-72` 全部解析流程都建立在纯数字 label 上。
     - `services/api-server/app/models/norm_clause_entry.py:4-16` 当前模型也没有 appendix / anchor / section_path 这类文档里提到的专用结构字段。
   - 风险：
     - 附录和规范尾部说明会系统性缺失，结构树与文档样例不一致。
     - 后续检索、写作约束、证据回链会漏掉附录类硬约束。
   - 建议：
     - 扩展 heading/clause 语法，支持 `附录A`、字母编号、非数字根节点。
     - 在本地归一化阶段补 `node_type=appendix/other-root`。
     - 用 fixture 把附录和尾部根节点锁成回归测试。

### MEDIUM

1. 标签排序全部采用字符串顺序，`4.10` 会排在 `4.2` 前面，`10` 会排在 `2` 前面。
   - 证据：
     - `services/api-server/app/services/norm_ai_scope_patcher.py:77-79` 对合并结果做 `str(label)` 排序。
     - `services/api-server/app/services/norm_search_service.py:62` 搜索结果按字符串 label 排序。
     - `services/api-server/app/repositories/postgres_norm_structure_repository.py:110,131,179` 数据库读取和检索也都直接 `order by label`。
   - 风险：
     - UI 目录顺序、搜索结果顺序、人工审核顺序都会错乱。
     - 复杂章节在补片后更容易出现“结构正确但展示顺序错误”的假阳性。
   - 建议：
     - 统一引入 label comparator，把 `4.10`、`4.2`、`附录A`、`引用标准名录` 都按规范语义排序。

2. 检索层没有实现文档要求的“双通道召回”，当前是把正文和条文说明混成一个检索面。
   - 证据：
     - `docs/2026-03-11-norm-pdf-processing-workflow.md:139-144` 明确要求“主召回：正文条款索引；辅召回：条文说明映射”。
     - `services/api-server/app/services/norm_search_service.py:114-123` 在内存检索里把 `title + summary_text + commentary_text` 合成单一 haystack。
     - `services/api-server/app/repositories/postgres_norm_structure_repository.py:170-177` 在持久化检索里也把 `title + summary_text + commentary_summary` 合并成同一个 `tsvector`。
   - 风险：
     - 条文说明会和正文硬约束被等权命中，违背文档定义的“硬约束 / 解释增强”边界。
     - 后续写作和审查难以区分“必须遵守”与“用于解释”的证据来源。
   - 建议：
     - 查询接口返回两个通道：`clause_hits` 与 `commentary_hits`。
     - 至少在排序和返回结构上区分正文命中与说明命中，再由上层拼接展示。

3. 本地校验只覆盖“结构存在性”，没有覆盖文档里强调的去重、归一化、附录修正、说明粒度等关键质量门。
   - 证据：
     - `docs/2026-03-11-norm-api-debugging-playbook.md:170-177,202-214,267-278,530-538` 把去重、clause_id 归一化、appendix/other 根节点修正、commentary 根节点和映射字段校验列为本地职责。
     - `services/api-server/app/services/norm_workflow_validator.py:19-71` 目前只验证 tree/entries 一致性、章节/小节存在性、commentary 是否引用未知条款，以及一个很粗的数量警告。
   - 风险：
     - 即使产物质量偏低，也可能被判定为可入库。
     - 文档里总结出的“必须本地兜底”的质量门没有真正执行。
   - 建议：
     - 增加 duplicate label、clause 粒度 commentary 覆盖、appendix roots、数值顺序、page range 反转等校验项。
     - 把质量报告单独落库，而不只存一个 `validation.json`。

## 文档方法落地情况

### 已落地

- 统一 OCR 适配层与项目级配置接线。
  - 见 `services/api-server/app/services/ocr_dispatcher.py`
  - 见 `services/api-server/app/services/remote_ocr_service.py`
- 统一 OCR 中间产物标准化为 `markdown_text + layout_payload + page_texts + metadata`。
  - 见 `services/api-server/app/services/norm_artifact_normalizer.py`
- 正文与条文说明分流处理。
  - 见 `services/api-server/app/workers/process_norm_document.py:90-139`
  - 见 `services/api-server/app/services/norm_markdown_splitter.py`
- 本地生成 `clause_index` 与 `commentary_map`，而不是完全依赖模型闭环。
  - 见 `services/api-server/app/services/norm_index_builder.py`
  - 见 `services/api-server/app/services/norm_commentary_builder.py`
- 本地重建树并在持久化层补 `path_labels`。
  - 见 `services/api-server/app/services/norm_index_builder.py:132-148`
  - 见 `services/api-server/app/repositories/postgres_norm_structure_repository.py:17-52,206-228`
- 产物持久化与检索链路闭环。
  - 见 `services/api-server/app/services/norm_artifact_store.py`
  - 见 `services/api-server/app/services/norm_library_service.py`

### 部分落地

- `layout.json -> page_texts` 压缩已落地，但没有进一步做 scope-local page window。
- `scope patching` 机制已存在，但只按 chapter 标签粗切，没有落实文档里的“4.1-4.4 / 4.9-4.12 / commentary-ch4-b2”这类细 scope。
- 本地 tree 重建已落地，但去重、clause_id 归一化、appendix/other root 修正还没有形成完整闭环。
- 调试工件已持久化，但主要落在运行时 artifact store；文档示例中的 `docs/generated/*.json` 不是当前系统的实际输出位置。
- 条文说明已单独建模，但检索阶段没有保持双通道语义。

### 未落地

- 细粒度 scope 输入裁剪与缺口 scope 定点重跑。
- AI commentary patch 的本地合并。
- Appendix / other root 节点建模。
- 文档中列出的 `section_path`、`anchor`、`appendix` 等 schema 能力。
- 面向结构质量的完整本地 quality gate。

## 验证情况与边界

### 已完成

- 通读目标文档并抽取关键方法论。
- 逐文件审查后端主链路、持久化与检索面。
- 使用代码智能工具查看关键文件符号。
- 运行项目级诊断工具：
  - `mcp__omx_code_intel__lsp_diagnostics_directory`
  - 返回 `totalErrors=0`、`totalWarnings=0`

### 未完成

- 未能在当前环境执行 Python 测试或最小运行复现。
  - `pytest` 不在 shell PATH 中。
  - `python3 -m pytest` 失败，因为当前 Python 环境缺少 `pytest`。
  - 直接跑最小脚本也失败，因为当前 Python 环境缺少 `pydantic`。

结论上，本报告以静态代码审查为主，问题判断依据充分，但尚缺一次真实依赖环境下的运行验证。

## 建议的修复优先级

1. 先修 AI scope 输入裁剪和 commentary patch 合并。
2. 再补 appendix / other-root 解析与排序规则。
3. 最后重做检索层的双通道召回和质量门细化。

