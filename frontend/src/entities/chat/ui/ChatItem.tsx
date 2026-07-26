import { useState } from 'react';
import { ChatAvatar } from './ChatAvatar';
import { ChatActionsMenu } from './ChatActionsMenu';
import { getChatDisplayName, getChatAvatarUrl } from '../model/helpers';
import { ConfirmDialog } from '@/shared/uikit/ConfirmDialog';
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
  keycloakId: string | null;
  online?: boolean;
  onClick: () => void;
  onDelete: () => void;
  onMarkRead: () => void;
}

export function ChatItem({ chat, isSelected, keycloakId, online, onClick, onDelete, onMarkRead }: ChatItemProps) {
  const displayName = getChatDisplayName(chat, keycloakId);
  const avatarUrl = getChatAvatarUrl(chat, keycloakId);
  const lastText = chat.last_message?.content;
  const lastTime = chat.last_message?.created_at;
  const [confirmDelete, setConfirmDelete] = useState(false);

  return (
    <div
      className={[
        'group relative flex w-full items-center gap-3 px-4 py-3 text-left transition-colors duration-75',
        isSelected ? 'bg-accent/10' : 'hover:bg-surface',
      ].join(' ')}
    >
      <button onClick={onClick} className='flex min-w-0 flex-1 cursor-pointer items-center gap-3 text-left'>
        <ChatAvatar name={displayName} src={avatarUrl} online={online} />
        <div className='min-w-0 flex-1'>
          <div className='flex items-center justify-between gap-2'>
            <span
              className={`truncate text-[14px] font-medium ${isSelected ? 'text-accent' : 'text-primary'}`}
            >
              {displayName}
            </span>
            {lastTime && (
              <span className='text-muted shrink-0 text-[11px]'>{formatTime(lastTime)}</span>
            )}
          </div>
          <div className='mt-0.5 flex items-center justify-between gap-2'>
            <span className='text-secondary truncate text-[12px]'>
              {lastText ?? 'Нет сообщений'}
            </span>
            {chat.unread_count > 0 && (
              <span className='bg-accent shrink-0 rounded-full px-1.5 py-0.5 text-[10px] leading-none font-semibold text-white'>
                {chat.unread_count > 99 ? '99+' : chat.unread_count}
              </span>
            )}
          </div>
        </div>
      </button>

      <ChatActionsMenu
        onDelete={() => setConfirmDelete(true)}
        onMarkRead={chat.unread_count > 0 ? onMarkRead : undefined}
        className='opacity-100 transition-opacity md:opacity-0 md:group-hover:opacity-100 md:focus-within:opacity-100'
      />

      {confirmDelete && (
        <ConfirmDialog
          title='Удалить чат?'
          description='Чат будет удалён для обоих собеседников без возможности восстановления.'
          confirmLabel='Удалить'
          destructive
          onConfirm={() => {
            setConfirmDelete(false);
            onDelete();
          }}
          onClose={() => setConfirmDelete(false)}
        />
      )}
    </div>
  );
}
