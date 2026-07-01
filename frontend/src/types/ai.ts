/**
 * 配置中心类型定义
 *
 * 对应后端 config_center 模块的数据结构。
 * 包含 AI 模型配置、提示词配置、生成行为配置的 CRUD 类型。
 */

// 部分其他模块从 @/types/ai 导入的 AI 测试类型
export type { GeneratedTestCase } from './aitest'

// ======================================================================
// AI 模型配置
// ======================================================================

/** AI 模型配置详情（GET 列表/单个 响应） */
export interface AIModelConfigDetail {
  id: number
  name: string
  model_type: string
  role: string
  api_key?: string | null
  base_url: string
  model_name: string
  max_tokens: number
  temperature: number
  top_p: number
  is_active: boolean
  created_by: number
  created_at?: string | null
  updated_at?: string | null
}

/** 创建 AI 模型配置请求 */
export interface AIModelConfigCreate {
  name: string
  model_type: string
  role: string
  api_key?: string | null
  base_url: string
  model_name: string
  max_tokens?: number
  temperature?: number
  top_p?: number
}

/** 更新 AI 模型配置请求（所有字段可选） */
export interface AIModelConfigUpdate {
  name?: string
  model_type?: string
  role?: string
  api_key?: string | null
  base_url?: string
  model_name?: string
  max_tokens?: number
  temperature?: number
  top_p?: number
  is_active?: boolean
}

// ======================================================================
// 提示词配置
// ======================================================================

/** 提示词配置详情 */
export interface PromptConfigDetail {
  id: number
  name: string
  prompt_type: string
  content: string
  is_active: boolean
  created_by: number
  created_at?: string | null
  updated_at?: string | null
}

/** 创建提示词配置请求 */
export interface PromptConfigCreate {
  name: string
  prompt_type: string
  content: string
}

/** 更新提示词配置请求（所有字段可选） */
export interface PromptConfigUpdate {
  name?: string
  prompt_type?: string
  content?: string
  is_active?: boolean
}

// ======================================================================
// 生成行为配置
// ======================================================================

/** 生成行为配置数据（对应后端 GenerationConfigDetail） */
export interface GenerationConfigData {
  id: number
  name: string
  default_output_mode: string
  enable_auto_review: boolean
  review_timeout: number
  is_active: boolean
  created_at?: string | null
  updated_at?: string | null
}

/** 更新生成行为配置请求（所有字段可选） */
export interface GenerationConfigUpdate {
  name?: string
  default_output_mode?: string
  enable_auto_review?: boolean
  review_timeout?: number
}
