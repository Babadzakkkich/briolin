import type { Message } from '@/entities/message/model/types';

export type ChatType = 'DIRECT' | 'GROUP';
export type ChatStatus = 'ACTIVE' | 'ARCHIVED' | 'BLOCKED';

export interface ChatParticipant {
  keycloak_id: string;
  display_name: string;
  username: string;
  avatar_url?: string;
  is_admin: boolean;
  joined_at: string;
}

export interface Chat {
  id: string;
  type: ChatType;
  status: ChatStatus;
  name?: string;
  description?: string;
  avatar_url?: string;
  participants: ChatParticipant[];
  created_at: string;
  updated_at: string;
  last_message?: Message;
  unread_count: number;
}

export interface ChatListResponse {
  chats: Chat[];
  total: number;
  page: number;
  size: number;
}
