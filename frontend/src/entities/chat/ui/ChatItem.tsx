import { ChatAvatar } from './ChatAvatar';
import type { Chat } from '../model/types';

function formatTime(dateStr: string) {
  const date = new Date(dateStr);
  const now = new Date();
  const isToday = date.toDateString() === now.toDateString();
  if (isToday) return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
  return date.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' });
}

interface ChatItemProps {
  chat: Chat;
  isSelected: boolean;
  onClick: () => void;
}

export function ChatItem({ chat, isSelected, onClick }: ChatItemProps) {
  const lastText = chat.last_message?.content;
  const lastTime = chat.last_message?.created_at;

  return (
    <button
      onClick={onClick}
      className={[
        'flex w-full cursor-pointer items-center gap-3 px-4 py-3 text-left transition-colors duration-75',
        isSelected ? 'bg-accent/10' : 'hover:bg-surface',
      ].join(' ')}
    >
      <ChatAvatar name={chat.name} />
      <div className='min-w-0 flex-1'>
        <div className='flex items-center justify-between gap-2'>
          <span className={`truncate text-[14px] font-medium ${isSelected ? 'text-accent' : 'text-primary'}`}>
            {chat.name ?? 'Чат'}
          </span>
          {lastTime && (
            <span className='text-muted shrink-0 text-[11px]'>{formatTime(lastTime)}</span>
          )}
        </div>
        <div className='mt-0.5 flex items-center justify-between gap-2'>
          <span className='text-secondary truncate text-[12px]'>{lastText ?? 'Нет сообщений'}</span>
          {chat.unread_count > 0 && (
            <span className='bg-accent shrink-0 rounded-full px-1.5 py-0.5 text-[10px] leading-none font-semibold text-white'>
              {chat.unread_count > 99 ? '99+' : chat.unread_count}
            </span>
          )}
        </div>
      </div>
    </button>
  );
}
