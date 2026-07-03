export interface ChatSession {
  id: number
  name: string
  model: string
  knowledge_base_id?: number
  knowledge_base_name?: string
  message_count: number
  created_by: number
  created_at?: string
  updated_at?: string
  first_message?: string
}

export interface ChatMessageFile {
  id: number
  file_name: string
  file_size: number
  file_type: string
  is_image: boolean
}

export interface ChatMessage {
  id: number
  session_id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  rating?: string
  created_at?: string
  files: ChatMessageFile[]
}

export interface ChatMessageBody {
  content: string
  model: string
  file_ids: number[]
  knowledge_base_id?: number | null
}

export interface KnowledgeBase {
  id: number
  name: string
  description?: string
  status: string
  embedding_model: string
  document_count: number
  created_by: number
  created_at?: string
  updated_at?: string
}

export interface KBDocument {
  id: number
  knowledge_base_id: number
  filename: string
  file_path: string
  file_size: number
  status: string
  chunk_count: number
  error_message?: string
  created_at?: string
  updated_at?: string
}

export interface KBSearchResult {
  id: number
  knowledge_base_id: number
  knowledge_base_name: string
  document_id: number
  document_name: string
  content: string
  score: number
}