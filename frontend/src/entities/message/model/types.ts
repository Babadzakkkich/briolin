export type MessageType = 'text' | 'image' | 'file' | 'audio' | 'video';
export type MessageStatus = 'sent' | 'delivered' | 'failed';

export interface MessageReadStatus {
  keycloak_id: string;
  read_at: string;
}

export interface Message {
  id: string;
  chat_id: string;
  sender_keycloak_id: string;
  sender_display_name: string;
  content: string;
  message_type: MessageType;
  status: MessageStatus;
  created_at: string;
  updated_at: string;
  is_edited: boolean;
  reply_to_id?: string;
  media_url?: string;
  media_type?: string;
  file_size?: number;
  read_by: MessageReadStatus[];
  read_count: number;
  is_read_by_me: boolean;
}

export interface MessageListResponse {
  messages: Message[];
  total: number;
}

export type WsEventType =
  | 'message'
  | 'typing'
  | 'read_receipt'
  | 'bulk_read_receipt'
  | 'error'
  | 'connection'
  | 'connection_established'
  | 'message_updated'
  | 'message_deleted'
  | 'user_online'
  | 'user_offline'
  | 'pong';

export interface WsMessage {
  type: WsEventType;
  chat_id?: string;
  message?: Message;
  sender_id?: string;
  display_name?: string;
  is_typing?: boolean;
  message_id?: string;
  message_ids?: string[];
  timestamp?: string;
  connection_id?: string;
  user_id?: string;
  error?: string;
  deleted_by?: string;
}
