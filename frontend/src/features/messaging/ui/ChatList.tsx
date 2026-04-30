import { Search, Users } from 'lucide-react';
import { ChatItem, getChatDisplayName } from '@/entities/chat';
import { useAuthStore } from '@/entities/session';
import type { Chat } from '@/entities/chat';

interface ChatListProps {
  chats: Chat[];
  selectedChatId: string | null;
  search: string;
  isLoading: boolean;
  onSearch: (v: string) => void;
  onSelect: (id: string) => void;
}

export function ChatList({
  chats,
  selectedChatId,
  search,
  isLoading,
  onSearch,
  onSelect,
}: ChatListProps) {
  const keycloakId = useAuthStore((s) => s.keycloakId);

  const filtered = chats.filter((c) =>
    getChatDisplayName(c, keycloakId).toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div className='border-border flex w-72 shrink-0 flex-col border-r bg-white'>
      <div className='border-border border-b px-4 pt-5 pb-4'>
        <h2 className='font-onest text-primary mb-3 text-lg font-medium'>Сообщения</h2>
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
          filtered.map((chat) => (
            <ChatItem
              key={chat.id}
              chat={chat}
              isSelected={chat.id === selectedChatId}
              keycloakId={keycloakId}
              onClick={() => onSelect(chat.id)}
            />
          ))
        )}
      </div>
    </div>
  );
}
