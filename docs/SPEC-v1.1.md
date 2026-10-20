# AI-Test-Hub v1.1 实施规格说明书（Spec）

> 版本：v1.1 ｜ 日期：2026-10-18 ｜ 模式：Spec + Loop Engineering 逐项浏览器验证

## 1. 背景与目标

当前系统的 AI 生成链路存在「结果不成功 / 结果缺失」问题，且缺少按模型计费类型差异化的
任务序列调度能力。本迭代目标：

1. **修复生成可靠性缺陷**（A–H 全部关闭，见 §3）
2. **实现生成序列调度**：免费模型 → 全局单任务串行序列；付费模型 → 并行多任务（上限可配）
3. **前端显示优化**：阶段循环序列时间线、排队位次、批次看板、空态兜底
4. **文档补全**：README 全流程（主副标题+文字+自动截图）、需求/技术/操作文档
5. **清理**：测试缓存、QA 截图/报告、无关产物、数据库演示残留
6. **交付**：敏感数据不入库 → 提交 GitHub → GitHub Pages 纯静态 Demo

## 2. 现状盘点

- 半成品（未提交）：`generation_scheduler.py`、billing migration、模型/schema 字段、`ai.py` 创建任务接线、`docs/REQUIREMENTS.md`
- 前端：调度/计费/批次相关 0 实现
- 缺陷清单见 §3

## 3. 缺陷清单（已验证）

| ID | 严重度 | 位置 | 问题 | 修复方案 |
|----|--------|------|------|----------|
| A | 🔴 | `graph/sse_stream.py` L311-332、`graph/autogen_pipeline.py` L354-375 | 失败分支 `flush` 后 `rollback`，失败状态丢失 | 改独立 session `commit`，删 rollback |
| B | 🔴 | `config_center/api/configs.py:55-59` | GET 列表直接突变 ORM 对象 → 脱敏 Key 写回 DB → 生成 401 | 脱敏在响应副本上做，绝不改 ORM |
| C | 🔴 | LangGraph/AutoGen 只写 `generated_case_item` | 任务详情/统计读 `generated_test_case` → 恒为 0（结果缺失） | 两管线补写 `generated_test_case`；前端详情统一走 items API |
| D | 🔴 | 三条管线 analyze 结果均不落库 | 刷新后「需求分析」永远空白 | 阶段结果写 `generated_content.analysis` + `ai_generation_result` |
| E | 🟠 | `ai.py` 队列生命周期 | 断线后事件永久丢失、无法重连、队列泄漏 | 已由 `StreamBroker`（回放+重连）替换，需完成全部接线 |
| F | 🟠 | revise / continue | 不清理旧 `generated_case_item`（数据翻倍）；`enable_auto_review` 不落库；跳阶段是假的 | revise 清旧 items、写开关；continue 复制产物真实续跑 |
| G | 🟠 | `ai_tester.py:407` | 后台任务用请求级 session → MissingGreenlet、消息丢失 | 独立 `async_session_factory` + 显式 commit |
| H | 🟡 | alembic / seed | aitest 表无 create_table 迁移；seed 不建 PromptConfig → 新环境直接报错 | 迁移补表；seed 补默认提示词 |
| I | 🟡 | `GenerationRecordsView.vue` | 服务端分页与客户端二次过滤混用 → 翻页丢数据 | 统一服务端筛选 |

## 4. 生成序列设计（核心新功能）

```
提交 N 条需求（批量） → N 个任务共享 batch_id
        │
        ▼
GenerationScheduler（进程内）
  ├─ billing=free  → Semaphore(1)：全局单任务序列，后进先出 FIFO 排队，推送 queue_position
  └─ billing=paid  → Semaphore(PAID_MODEL_CONCURRENCY=4)：并行执行
        │
        ▼
StreamBroker（任务级事件总线）
  · 生产者 O(1) 追加 + 历史保留 10min
  · 消费者任意时刻接入回放（刷新/断线重连不丢事件）
```

- 任务状态机扩展：`queued → pending → analyzing → generating → reviewing → revising → completed/failed/cancelled`
- 前端：模型配置页可选计费类型；生成页/序列看板显示排队位次与执行模式提示

## 5. 阶段计划（Loop Engineering：每阶段浏览器验证通过才进下一阶段）

- **P1 后端修复与调度接线**：A/B/C/D/F/G + scheduler 全接线（create/revise/cancel/list/batch）+ 重启僵尸任务恢复 + seed 补全 → `py_compile` + API 冒烟验证
- **P2 前端优化与序列 UI**：批次序列看板、排队位次、阶段时间线、详情读 items、记录页分页修正 → `vue-tsc` + `lint` + **浏览器全流程验证 + 自动截图检查**
- **P3 文档**：README 全流程（每步骤主副标题+文字+浏览器自动截图）、`docs/TECHNICAL.md`、`docs/GUIDE.md`
- **P4 清理与交付**：删 qa-screenshots/qa-*.mjs/旧截图/构建产物/数据库演示数据 → 密钥审计（.env 已 gitignore）→ 提交推送 GitHub → GitHub Pages Demo（纯静态交互演示，数据为演示样例）→ README 附 Demo 链接

## 6. 验收标准（执行结果）

| # | 验收项 | 结果 | 验证方式 |
|---|--------|------|----------|
| 1 | 免费模型连发多任务：严格串行，UI 显示排队位次 | ✅ | 浏览器实测：第 1 条「生成中」、其余「排队第 1/2 位」，逐条递补 |
| 2 | 付费模型连发多任务：并行执行（≤4） | ✅ | 浏览器实测：3 条同时「需求分析」进行中，30s 内全部完成（串行需 90s） |
| 3 | 生成结果可持久回看：分析/用例/评审阶段内容刷新后不丢失 | ✅ | `generated_content={analysis,text}` + `ai_generation_result` 四阶段落库 |
| 4 | 打开模型配置页后真实 API Key 不被污染 | ✅ | `configs.py` 脱敏改在响应副本上；连开 3 次页面后 DB Key 仍为原值 |
| 5 | SSE 刷新重连可回放；失败任务状态正确落库 | ✅ | StreamBroker 历史回放（断线后重连收到完整事件序列）；失败任务 `status=failed` + 错误原因入库 |
| 6 | 并发批量无死锁/锁超时 | ✅ | 4 路并行 ×2 轮：0 次 1213/1205，MissingGreenlet 清零 |
| 7 | 「继续生成」真实跳过阶段并复用产物 | ✅ | `continue_from_stage=review`：10s 完成（跳过分析+编写），analysis 保留 |
| 8 | 重新生成不产生重复数据 | ✅ | revise 前后 `generated_test_case`/`generated_case_item` 均为 6 条 |
| 9 | `vue-tsc` 0 错误 | ✅ | `npx vue-tsc --noEmit` 无输出（eslint 未安装于本项目依赖，故不可用） |
| 10 | 浏览器控制台无报错 | ✅ | Playwright 实测登录/生成/序列/详情/配置页 0 error |
| 11 | 关键流程截图归档 | ✅ | `docs/images/` 12 张（首页/总览/流式/完成/序列排队/序列完成/配置/记录/用例库/评审/聊天室/Demo） |
| 12 | 仓库无密钥/隐私数据 | ✅ | `git grep` 扫描 sk-/ghp_/PAT 均无命中；`.env`、`uploads/` 已 gitignore |
| 13 | Pages Demo 可访问且交互正常 | ✅ | https://snow-sakura.github.io/ai-test-hub/ —— 串行/并行模拟 + GitHub 数据源读取 5 条记录 |
| 14 | 清理无关内容 | ✅ | 删除 qa-screenshots(14)、qa-*.mjs、ai-chat-before.png、9 个无引用重复类型文件、演示数据（81 任务/952 衍生行） |

## 7. 交付物清单

| 交付物 | 位置 |
|--------|------|
| 需求规格 | `docs/REQUIREMENTS.md` |
| 技术规格 | `docs/SPEC-v1.1.md`（本文档） |
| 技术设计 | `docs/TECHNICAL.md` |
| 操作手册 | `docs/USER_GUIDE.md` |
| 全流程说明 + 截图 | `README.md` + `docs/images/` |
| 在线 Demo | `demo/`（GitHub Pages + GitHub Actions + GitHub 仓库数据源） |
| 离线联调 Mock | `backend/scripts/mock_llm_server.py` |
