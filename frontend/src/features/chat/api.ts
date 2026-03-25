import { apiClient } from '@/shared/api/client';
import type { Chat, ChatListResponse, Message, MessageListResponse } from './types';

export const chatApi = {
  getChats: (params?: { skip?: number; limit?: number; chat_type?: string; status?: string }) =>
    apiClient.get<ChatListResponse>('/api/v1/chats/', { params }).then((r) => r.data),

  getMessages: (chatId: string, params?: { skip?: number; limit?: number; before?: string }) =>
    apiClient
      .get<MessageListResponse>(`/api/v1/chats/${chatId}/messages`, { params })
      .then((r) => r.data),

  sendMessage: (chatId: string, content: string, replyToId?: string) =>
    apiClient
      .post<Message>(`/api/v1/chats/${chatId}/messages`, {
        content,
        message_type: 'text',
        ...(replyToId && { reply_to_id: replyToId }),
      })
      .then((r) => r.data),

  markRead: (chatId: string, messageIds: string[]) =>
    apiClient.post(`/api/v1/chats/${chatId}/read`, { message_ids: messageIds }).then((r) => r.data),

  editMessage: (messageId: string, content: string) =>
    apiClient.put<Message>(`/api/v1/chats/messages/${messageId}`, { content }).then((r) => r.data),

  deleteMessage: (messageId: string) =>
    apiClient.delete(`/api/v1/chats/messages/${messageId}`).then((r) => r.data),

  createDirectChat: (participantId: string) =>
    apiClient
      .post<Chat>('/api/v1/chats/chats/', { type: 'DIRECT', participant_ids: [participantId] })
      .then((r) => r.data),
};
