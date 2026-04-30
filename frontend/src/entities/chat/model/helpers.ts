import type { Chat } from './types';

export function getChatDisplayName(chat: Chat, myKeycloakId: string | null): string {
  if (chat.name) return chat.name;
  if (chat.type === 'DIRECT') {
    const other = chat.participants.find((p) => p.keycloak_id !== myKeycloakId);
    return other?.display_name ?? 'Чат';
  }
  return 'Групповой чат';
}

export function getChatAvatarUrl(chat: Chat, myKeycloakId: string | null): string | null {
  if (chat.avatar_url) return chat.avatar_url;
  if (chat.type === 'DIRECT') {
    const other = chat.participants.find((p) => p.keycloak_id !== myKeycloakId);
    return other?.avatar_url ?? null;
  }
  return null;
}
