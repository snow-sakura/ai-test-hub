# AI 聊天室

AI 聊天室页面 UI 规范和 API 说明。

## 页面布局

### 三栏布局

| 区域 | 宽度 | 内容 |
|------|------|------|
| 左栏 | 280px | 会话列表 |
| 主区域 | 自适应 | 聊天区域 |
| 右栏 | 280px | 工具面板 |

### 响应式设计

- **桌面端**: 三栏布局
- **平板端**: 隐藏右栏，可通过按钮展开
- **移动端**: 单列布局，侧边栏转为抽屉式

## 会话列表

### 布局

- 标题栏：图标 + 标题 + 新建按钮
- 搜索框：支持按标题搜索
- 会话列表项：标题、时间、未读标记
- 空状态：无会话时显示提示

### 会话项

| 内容 | 说明 |
|------|------|
| 标题 | 会话标题（自动生成或手动设置） |
| 时间 | 最后消息时间 |
| 未读标记 | 红点显示未读消息 |
| 删除按钮 | hover 显示删除按钮 |

## 聊天区域

### 聊天头部

- 会话标题
- 知识库标签（已关联时显示）
- 操作按钮：重命名、删除、清空

### 消息列表

- 用户消息：右对齐，蓝色气泡
- AI 消息：左对齐，灰色气泡
- 流式输出：打字动画效果
- Markdown 渲染：AI 回复支持 Markdown 格式

### 消息气泡

| 类型 | 样式 |
|------|------|
| 用户 | 右对齐，蓝色背景，白色文字 |
| AI | 左对齐，灰色背景，深色文字 |
| 系统 | 居中，浅灰色背景 |

### 输入区域

- 文本输入框
- 文件上传按钮
- 发送按钮
- 快捷指令按钮

## 工具面板

### 模型设置

- 模型选择下拉框
- 当前模型信息显示

### 知识库关联

- 知识库选择下拉框
- 已关联知识库显示

### 快捷指令

- 常用指令列表
- 点击快速填充输入框

### 使用提示

- 使用说明
- 快捷键提示

## API 接口

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/ai-chat/sessions | 获取会话列表 |
| POST | /api/v1/ai-chat/sessions | 创建新会话 |
| GET | /api/v1/ai-chat/sessions/{id} | 获取会话详情 |
| PUT | /api/v1/ai-chat/sessions/{id} | 更新会话 |
| DELETE | /api/v1/ai-chat/sessions/{id} | 删除会话 |
| GET | /api/v1/ai-chat/sessions/{id}/messages | 获取消息列表 |
| POST | /api/v1/ai-chat/sessions/{id}/messages/stream | 发送消息(流式) |
| POST | /api/v1/ai-chat/files/upload | 上传文件 |

## SSE 事件类型

| 事件类型 | 说明 | 数据结构 |
|----------|------|----------|
| `user_message` | 用户消息已保存 | `{ id: number, content: string }` |
| `token` | AI 回复内容 | `{ content: string }` |
| `complete` | AI 回复完成 | `{ content: string }` |
| `error` | 错误信息 | `{ message: string, traceback: string }` |

## 状态管理

使用 Pinia store `chat.ts` 管理聊天状态：

| State | Type | Description |
|-------|------|-------------|
| `sessions` | ChatSession[] | 会话列表 |
| `currentSession` | ChatSession \| null | 当前会话 |
| `messages` | ChatMessage[] | 当前会话消息 |
| `selectedModel` | string | 选中的模型 |
| `selectedKnowledgeBaseId` | number \| null | 选中的知识库ID |
| `knowledgeBases` | KnowledgeBase[] | 知识库列表 |
| `modelOptions` | OptionItem[] | 模型选项 |
| `isStreaming` | boolean | 是否正在流式输出 |

## 方法

| Method | Description |
|--------|-------------|
| `loadSessions()` | 加载会话列表 |
| `createSession()` | 创建新会话 |
| `selectSession(session)` | 选择会话 |
| `deleteSession(id)` | 删除会话 |
| `updateSession(id, data)` | 更新会话 |
| `sendMessage(content, fileIds)` | 发送消息 |
| `addMessage(message)` | 添加消息 |
| `updateMessageContent(id, content)` | 更新消息内容 |
| `rateMessage(id, rating)` | 评价消息 |
| `loadKnowledgeBases()` | 加载知识库列表 |
| `uploadFile(file)` | 上传文件 |
| `abortCurrentRequest()` | 取消当前请求 |

## 错误处理

- 请求取消：使用 AbortController 管理
- 组件卸载：自动取消正在进行的请求
- 错误提示：通过 ElMessage 显示错误信息
- `net::ERR_ABORTED`：正常浏览器行为，不影响功能

## Markdown 渲染

- 使用 marked 库进行 Markdown 解析
- AI 回复内容使用 v-html 渲染
- 添加 Markdown 样式支持
