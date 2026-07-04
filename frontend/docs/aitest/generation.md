# AI 用例生成页面

AI 用例生成的 UI 规范和 SSE 事件说明。

## 页面布局

### 2×2 阶段卡片布局

页面分为四个阶段卡片：

| 位置 | 阶段 | 卡片标题 |
|------|------|----------|
| 左上 | 分析 | 需求分析 |
| 右上 | 生成 | 用例生成 |
| 左下 | 评审 | 用例评审 |
| 右下 | 改进 | 用例改进 |

### 实时日志面板

- 位于四个阶段卡片下方
- 显示生成过程的实时日志
- 支持自动滚动到底部

## SSE 事件类型

### 传统 Pipeline (`use_langgraph=false`)

| 事件类型 | 说明 | 数据结构 |
|----------|------|----------|
| `status` | 阶段状态更新 | `{ stage: string, status: string }` |
| `chunk` | 生成阶段内容 | `{ content: string, stage: string }` |
| `review_chunk` | 评审阶段内容 | `{ content: string }` |
| `revise_chunk` | 改进阶段内容 | `{ content: string }` |
| `done` | 生成完成 | `{ success: boolean, task_id: string }` |
| `error` | 错误信息 | `{ message: string }` |

### LangGraph Pipeline (`use_langgraph=true`)

| 事件类型 | 说明 | 数据结构 |
|----------|------|----------|
| `testing_stage` | 阶段开始 | `{ stage: string }` |
| `testing_review` | 评审结果 | `{ score: number, feedback: string }` |
| `testing_done` | 生成完成 | `{ success: boolean }` |
| `chunk` | 各阶段内容 | `{ content: string, stage: string }` |
| `error` | 错误信息 | `{ message: string }` |

## 状态管理

使用 Pinia store `generation.ts` 管理生成状态：

| State | Type | Description |
|-------|------|-------------|
| `isGenerating` | boolean | 是否正在生成 |
| `currentStage` | string | 当前阶段 |
| `stageResults` | object | 各阶段结果 |
| `generationLog` | string[] | 生成日志 |
| `currentTaskId` | string | 当前任务ID |

## 生成记录列表

- 展示历史生成任务列表
- 支持按项目筛选
- 显示任务状态、生成时间、用例数量
- 点击可查看任务详情
