import { apiClient } from '@/shared/api/client';
import type { Chat, ChatListResponse } from '../model/types';

export const chatApi = {
  getChats: (params?: { skip?: number; limit?: number; chat_type?: string; status?: string }) =>
    apiClient.get<ChatListResponse>('/chats/', { params }).then((r) => r.data),

  createDirectChat: (participantKeycloakId: string) =>
    apiClient
      .post<Chat>('/chats/', { type: 'direct', participant_ids: [participantKeycloakId] })
      .then((r) => r.data),

  getOnlineStatus: (keycloakId: string) =>
    apiClient
      .get<{ online: boolean }>(`/chats/online/users/${keycloakId}`)
      .then((r) => r.data),
};
