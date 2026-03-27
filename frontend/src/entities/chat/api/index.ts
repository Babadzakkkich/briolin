import { apiClient } from '@/shared/api/client';
import type { Chat, ChatListResponse } from '../model/types';

export const chatApi = {
  getChats: (params?: { skip?: number; limit?: number; chat_type?: string; status?: string }) =>
    apiClient.get<ChatListResponse>('/api/v1/chats/', { params }).then((r) => r.data),

  createDirectChat: (participantId: string) =>
    apiClient
      .post<Chat>('/api/v1/chats/chats/', { type: 'DIRECT', participant_ids: [participantId] })
      .then((r) => r.data),
};
