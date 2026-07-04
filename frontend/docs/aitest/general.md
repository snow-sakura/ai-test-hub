# 通用规则

aitest 模块通用 UI 规范。

## 布局

- 页面容器不设 `max-width`，padding `24px 16px`
- 使用 Flexbox 布局，确保内容自适应

## 表格

- 表格包裹在 `el-card.config-table-card` 暖色卡片内
- 列宽全用 `min-width` 比例分配，不用固定 `width`
- 文字列加 `show-overflow-tooltip` 防换行

## 搜索

- 搜索框 `flex: 1` 填充右侧空白
- 使用 `el-input-group` 包裹搜索输入框和搜索按钮

## 按钮

- 主要操作按钮使用 `el-button--primary`
- 次要操作使用默认按钮样式
- 图标按钮使用 `el-button--text`

## 表单

- 表单项使用 `el-form-item`，label 宽度统一
- 输入框使用 `el-input`，添加适当的 placeholder
- 表单验证使用 Element Plus 内置验证规则

## 弹窗

- 弹窗宽度根据内容调整，最小宽度 `400px`
- 添加成员弹窗宽度 ≥ `540px`
- 弹窗标题清晰明确

## 颜色变量

- 主色调: `#C67B5C` (暖橙色)
- 辅助色: `#D4A574` (金色)
- 成功色: `#10b981` (绿色)
- 警告色: `#f59e0b` (橙色)
- 危险色: `#ef4444` (红色)
- 背景色: `#FBF7F0` (暖米色)
- 卡片背景: `#FFFDF9` (接近白色)
- 文字色: `#3D2E1F` (深棕色)

## 动画

- 页面切换使用平滑过渡
- 弹窗显示/隐藏使用淡入淡出效果
- 按钮 hover 状态添加过渡动画
