import { useState } from 'react';
import { Search, TextSearch, Users } from 'lucide-react';
import { ChatItem, getChatDisplayName, getOtherParticipant } from '@/entities/chat';
import { useAuthStore } from '@/entities/session';
import type { Chat } from '@/entities/chat';
import { MessageSearchPanel } from './MessageSearchPanel';

interface ChatListProps {
  chats: Chat[];
  selectedChatId: string | null;
  search: string;
  isLoading: boolean;
  onlineUsers: Set<string>;
  onSearch: (v: string) => void;
  onSelect: (id: string) => void;
  onDeleteChat: (chatId: string) => void;
  onMarkChatRead: (chatId: string) => void;
}

export function ChatList({
  chats,
  selectedChatId,
  search,
  isLoading,
  onlineUsers,
  onSearch,
  onSelect,
  onDeleteChat,
  onMarkChatRead,
}: ChatListProps) {
  const keycloakId = useAuthStore((s) => s.keycloakId);
  const [showMessageSearch, setShowMessageSearch] = useState(false);

  const filtered = chats.filter((c) =>
    getChatDisplayName(c, keycloakId).toLowerCase().includes(search.toLowerCase()),
  );
  const onlineCount = chats.filter((c) => {
    const other = getOtherParticipant(c, keycloakId);
    return other && onlineUsers.has(other.keycloak_id);
  }).length;

  return (
    <div className='border-border flex h-full w-full flex-col border-r bg-white'>
      <div className='border-border border-b px-4 pt-5 pb-4'>
        <div className='mb-3 flex items-center justify-between'>
          <h2 className='font-onest text-primary text-lg font-medium'>Сообщения</h2>
          <div className='flex items-center gap-2'>
            {onlineCount > 0 && (
              <span className='flex items-center gap-1 text-[12px] text-green-600'>
                <span className='h-1.5 w-1.5 rounded-full bg-green-500' />
                {onlineCount} онлайн
              </span>
            )}
            <button
              onClick={() => setShowMessageSearch(true)}
              title='Поиск по сообщениям'
              className='text-secondary hover:text-primary hover:bg-muted/15 flex h-7 w-7 cursor-pointer items-center justify-center rounded-lg transition-colors'
            >
              <TextSearch size={16} />
            </button>
          </div>
        </div>
        <div className='relative'>
          <Search
            size={14}
            className='text-muted pointer-events-none absolute top-1/2 left-3 -translate-y-1/2'
            strokeWidth={2.2}
          />
          <input
            value={search}
            onChange={(e) => onSearch(e.target.value)}
            placeholder='Поиск...'
            className='border-border focus:border-accent font-inter text-primary placeholder:text-muted w-full rounded-xl border bg-white py-2 pr-3 pl-8 text-[13px] transition-colors outline-none'
          />
        </div>
      </div>

      <div className='flex-1 overflow-y-auto'>
        {isLoading ? (
          <div className='flex flex-col gap-2 p-4'>
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className='bg-surface h-14 animate-pulse rounded-xl' />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className='flex flex-col items-center justify-center gap-2 px-6 py-12 text-center'>
            <Users size={24} className='text-muted' strokeWidth={1.8} />
            <p className='text-secondary text-[13px]'>Нет активных чатов</p>
          </div>
        ) : (
          filtered.map((chat) => {
            const other = getOtherParticipant(chat, keycloakId);
            return (
              <ChatItem
                key={chat.id}
                chat={chat}
                isSelected={chat.id === selectedChatId}
                keycloakId={keycloakId}
                online={!!other && onlineUsers.has(other.keycloak_id)}
                onClick={() => onSelect(chat.id)}
                onDelete={() => onDeleteChat(chat.id)}
                onMarkRead={() => onMarkChatRead(chat.id)}
              />
            );
          })
        )}
      </div>

      {showMessageSearch && (
        <MessageSearchPanel
          chats={chats}
          keycloakId={keycloakId}
          onSelectChat={onSelect}
          onClose={() => setShowMessageSearch(false)}
        />
      )}
    </div>
  );
}
