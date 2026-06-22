import { apiClient } from '@/shared/api/client';
import type { MatchWithAnswers } from '@/entities/matching';
import type { Message } from '@/entities/message';
import type { Chat, ChatListResponse } from '../model/types';

interface SearchMessagesResponse {
  messages: Message[];
  total: number;
  query: string;
}

interface OnlineUsersResponse {
  online_users: string[];
  count: number;
}

export const chatApi = {
  getChats: (params?: { skip?: number; limit?: number; chat_type?: string; status?: string }) =>
    apiClient.get<ChatListResponse>('/chats/', { params }).then((r) => r.data),

  getChat: (chatId: string) => apiClient.get<Chat>(`/chats/${chatId}`).then((r) => r.data),

  createDirectChat: (participantKeycloakId: string) =>
    apiClient
      .post<Chat>('/chats/', { type: 'direct', participant_ids: [participantKeycloakId] })
      .then((r) => r.data),

  deleteChat: (chatId: string) => apiClient.delete<{ message: string }>(`/chats/${chatId}`).then((r) => r.data),

  getOnlineUsers: () =>
    apiClient.get<OnlineUsersResponse>('/chats/online/users').then((r) => r.data),

  searchMessages: (params: { query: string; chatId?: string; skip?: number; limit?: number }) =>
    apiClient
      .get<SearchMessagesResponse>('/chats/search/messages', {
        params: { query: params.query, chat_id: params.chatId, skip: params.skip, limit: params.limit },
      })
      .then((r) => r.data),

  getMatchAnswers: (chatId: string) =>
    apiClient.get<MatchWithAnswers>(`/chats/${chatId}/match-answers`).then((r) => r.data),
};
