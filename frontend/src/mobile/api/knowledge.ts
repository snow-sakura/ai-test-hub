/**
 * 移动端知识库 API 层
 */
import client from './client'
import type { KnowledgeBase } from '../../shared/types/ai_chat'

const BASE_URL = '/v1'

export const knowledgeBaseApi = {
  /** 获取知识库列表 */
  list(): Promise<KnowledgeBase[]> {
    return client.get(`${BASE_URL}/knowledge-base`).then((res) => res.data)
  },
  /** 创建知识库 */
  create(data: { name: string; description?: string }): Promise<KnowledgeBase> {
    return client.post(`${BASE_URL}/knowledge-base`, data).then((res) => res.data)
  },
}
