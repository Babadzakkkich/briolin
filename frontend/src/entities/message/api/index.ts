import { apiClient } from '@/shared/api/client';
import type { Message, MessageListResponse } from '../model/types';

export const messageApi = {
  getMessages: (chatId: string, params?: { skip?: number; limit?: number; before?: string }) =>
    apiClient.get<MessageListResponse>(`/chats/${chatId}/messages`, { params }).then((r) => r.data),

  send: (chatId: string, content: string, replyToId?: string) =>
    apiClient
      .post<Message>(`/chats/${chatId}/messages`, {
        content,
        message_type: 'text',
        ...(replyToId && { reply_to_id: replyToId }),
      })
      .then((r) => r.data),

  markRead: (chatId: string, messageIds: string[]) =>
    apiClient.post(`/chats/${chatId}/read`, { message_ids: messageIds }).then((r) => r.data),

  edit: (messageId: string, content: string) =>
    apiClient.put<Message>(`/chats/messages/${messageId}`, { content }).then((r) => r.data),

  delete: (messageId: string) =>
    apiClient.delete(`/chats/messages/${messageId}`).then((r) => r.data),
};
