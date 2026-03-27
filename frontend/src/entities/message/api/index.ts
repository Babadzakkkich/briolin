import { apiClient } from '@/shared/api/client';
import type { Message, MessageListResponse } from '../model/types';

export const messageApi = {
  getMessages: (chatId: string, params?: { skip?: number; limit?: number; before?: string }) =>
    apiClient
      .get<MessageListResponse>(`/api/v1/chats/${chatId}/messages`, { params })
      .then((r) => r.data),

  send: (chatId: string, content: string, replyToId?: string) =>
    apiClient
      .post<Message>(`/api/v1/chats/${chatId}/messages`, {
        content,
        message_type: 'text',
        ...(replyToId && { reply_to_id: replyToId }),
      })
      .then((r) => r.data),

  markRead: (chatId: string, messageIds: string[]) =>
    apiClient.post(`/api/v1/chats/${chatId}/read`, { message_ids: messageIds }).then((r) => r.data),

  edit: (messageId: string, content: string) =>
    apiClient.put<Message>(`/api/v1/chats/messages/${messageId}`, { content }).then((r) => r.data),

  delete: (messageId: string) =>
    apiClient.delete(`/api/v1/chats/messages/${messageId}`).then((r) => r.data),
};
