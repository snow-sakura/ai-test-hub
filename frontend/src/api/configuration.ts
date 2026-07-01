/**
 * 配置中心 API 封装
 *
 * 提供 AI 模型配置、提示词配置、生成行为配置的完整 CRUD 接口。
 */

import type { ApiResponse } from '@/types/api'
import type {
  AIModelConfigCreate,
  AIModelConfigDetail,
  AIModelConfigUpdate,
  GenerationConfigData,
  GenerationConfigUpdate,
  PromptConfigCreate,
  PromptConfigDetail,
  PromptConfigUpdate,
} from '@/types/ai'
import client from './client'

/** 配置中心 API */
export const configApi = {
  // ====================================================================
  // AI 模型配置
  // ====================================================================

  /**
   * 获取所有 AI 模型配置列表
   */
  getModelList(): Promise<ApiResponse<AIModelConfigDetail[]>> {
    return client.get('/v1/configs/models/all').then((res) => res.data)
  },

  /**
   * 创建 AI 模型配置
   */
  createModel(data: AIModelConfigCreate): Promise<ApiResponse<AIModelConfigDetail>> {
    return client.post('/v1/configs/models', data).then((res) => res.data)
  },

  /**
   * 更新 AI 模型配置
   */
  updateModel(id: number, data: AIModelConfigUpdate): Promise<ApiResponse<AIModelConfigDetail>> {
    return client.put(`/v1/configs/models/${id}`, data).then((res) => res.data)
  },

  /**
   * 删除 AI 模型配置
   */
  deleteModel(id: number): Promise<ApiResponse> {
    return client.delete(`/v1/configs/models/${id}`).then((res) => res.data)
  },

  /** 批量删除模型配置 */
  batchDeleteModels(ids: number[]): Promise<ApiResponse> {
    return client.post('/v1/configs/models/batch-delete', { ids }).then((res) => res.data)
  },

  /**
   * 设为活跃模型
   */
  activateModel(id: number): Promise<ApiResponse<AIModelConfigDetail>> {
    return client.post(`/v1/configs/models/${id}/activate`).then((res) => res.data)
  },

  // ====================================================================
  // 提示词配置
  // ====================================================================

  /**
   * 获取所有提示词配置列表
   */
  getPromptList(): Promise<ApiResponse<PromptConfigDetail[]>> {
    return client.get('/v1/configs/prompts').then((res) => res.data)
  },

  /**
   * 创建提示词配置
   */
  createPrompt(data: PromptConfigCreate): Promise<ApiResponse<PromptConfigDetail>> {
    return client.post('/v1/configs/prompts', data).then((res) => res.data)
  },

  /**
   * 更新提示词配置
   */
  updatePrompt(id: number, data: PromptConfigUpdate): Promise<ApiResponse<PromptConfigDetail>> {
    return client.put(`/v1/configs/prompts/${id}`, data).then((res) => res.data)
  },

  /**
   * 删除提示词配置
   */
  deletePrompt(id: number): Promise<ApiResponse> {
    return client.delete(`/v1/configs/prompts/${id}`).then((res) => res.data)
  },

  /** 批量删除提示词配置 */
  batchDeletePrompts(ids: number[]): Promise<ApiResponse> {
    return client.post('/v1/configs/prompts/batch-delete', { ids }).then((res) => res.data)
  },

  // ====================================================================
  // 生成行为配置
  // ====================================================================

  /**
   * 获取当前生效的生成行为配置
   */
  getGenerationConfig(): Promise<ApiResponse<GenerationConfigData>> {
    return client.get('/v1/configs/generation-config').then((res) => res.data)
  },

  /**
   * 更新生成行为配置
   */
  updateGenerationConfig(data: GenerationConfigUpdate): Promise<ApiResponse<GenerationConfigData>> {
    return client.put('/v1/configs/generation-config', data).then((res) => res.data)
  },
}
