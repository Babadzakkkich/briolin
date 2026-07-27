import { useState } from 'react';
import { ArrowLeft, Heart, MessageCircle, Send } from 'lucide-react';
import { MessageBubble } from '@/entities/message';
import { ChatAvatar, ChatActionsMenu, getChatDisplayName, getChatAvatarUrl } from '@/entities/chat';
import { Button } from '@/shared/uikit/Button';
import { ConfirmDialog } from '@/shared/uikit/ConfirmDialog';
import { MatchAnswersPanel } from './MatchAnswersPanel';
import type { Message } from '@/entities/message';
import type { Chat } from '@/entities/chat';

interface ChatViewProps {
  chat: Chat;
  messages: Message[];
  isLoading: boolean;
  input: string;
  isSending: boolean;
  typingNames: string[];
  keycloakId: string | null;
  online?: boolean;
  onInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onKeyDown: (e: React.KeyboardEvent<HTMLInputElement>) => void;
  onSend: () => void;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
  inputRef: React.RefObject<HTMLInputElement | null>;
  onBack?: () => void;
  onDeleteChat: (chatId: string) => void;
}

export function ChatView({
  chat,
  messages,
  isLoading,
  input,
  isSending,
  typingNames,
  keycloakId,
  onInputChange,
  onKeyDown,
  onSend,
  online,
  messagesEndRef,
  inputRef,
  onBack,
  onDeleteChat,
}: ChatViewProps) {
  const displayName = getChatDisplayName(chat, keycloakId);
  const avatarUrl = getChatAvatarUrl(chat, keycloakId);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [showMatchAnswers, setShowMatchAnswers] = useState(false);

  return (
    <div className='flex flex-1 flex-col overflow-hidden'>
      <div className='border-border flex shrink-0 items-center gap-3 border-b bg-white px-4 py-4 md:px-6'>
        {onBack && (
          <button
            onClick={onBack}
            className='text-secondary hover:text-primary hover:bg-muted/10 -ml-1 flex h-9 w-9 shrink-0 cursor-pointer items-center justify-center rounded-xl transition-colors md:hidden'
          >
            <ArrowLeft size={20} strokeWidth={2.2} />
          </button>
        )}
        <ChatAvatar name={displayName} src={avatarUrl} size='lg' online={online} />
        <div className='min-w-0 flex-1'>
          <p className='text-primary truncate text-[15px] font-semibold'>{displayName}</p>
          {typingNames.length > 0 ? (
            <span className='text-accent flex items-center gap-1.5 text-[12px]'>
              <span className='flex gap-0.5'>
                {[0, 1, 2].map((i) => (
                  <span
                    key={i}
                    className='bg-accent h-1 w-1 animate-bounce rounded-full'
                    style={{ animationDelay: `${i * 0.15}s` }}
                  />
                ))}
              </span>
              {typingNames.length === 1
                ? `${typingNames[0]} печатает`
                : 'Несколько человек печатают'}
            </span>
          ) : online ? (
            <p className='text-[12px] text-green-500'>В сети</p>
          ) : (
            <p className='text-secondary text-[12px]'>
              {chat.type === 'GROUP' ? `${chat.participants.length} участников` : 'Личный чат'}
            </p>
          )}
        </div>

        {chat.match_id != null && (
          <button
            onClick={() => setShowMatchAnswers(true)}
            title='Почему вы совпали'
            className='text-accent hover:bg-accent/10 flex h-9 w-9 shrink-0 cursor-pointer items-center justify-center rounded-xl transition-colors'
          >
            <Heart size={18} strokeWidth={2.2} />
          </button>
        )}
        <ChatActionsMenu onDelete={() => setConfirmDelete(true)} />
      </div>

      <div className='flex flex-1 flex-col gap-3 overflow-y-auto px-6 py-5'>
        {isLoading ? (
          <div className='flex animate-pulse flex-col gap-3' role='status'>
            {[40, 58, 46, 65, 38].map((width, index) => (
              <div
                key={index}
                className={[
                  'bg-surface h-12 rounded-2xl',
                  index % 2 === 0 ? 'self-start' : 'self-end',
                ].join(' ')}
                style={{ width: `${width}%` }}
              />
            ))}
            <span className='sr-only'>Загружаем сообщения</span>
          </div>
        ) : messages.length === 0 ? (
          <div className='flex flex-1 flex-col items-center justify-center gap-2 text-center'>
            <MessageCircle size={24} className='text-muted' strokeWidth={1.8} />
            <p className='text-secondary text-[13px]'>Нет сообщений. Напишите первым!</p>
          </div>
        ) : (
          messages.map((msg) => (
            <MessageBubble
              key={msg.id}
              message={msg}
              isOwn={msg.sender_keycloak_id === keycloakId}
            />
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className='border-border shrink-0 border-t bg-white px-6 py-4'>
        <div className='flex items-center gap-2'>
          <input
            ref={inputRef}
            value={input}
            onChange={onInputChange}
            onKeyDown={onKeyDown}
            placeholder='Напишите сообщение...'
            className='border-border focus:border-accent font-inter text-primary placeholder:text-muted flex-1 rounded-xl border bg-white px-4 py-3 text-[14px] transition-colors outline-none'
          />
          <Button
            size='md'
            onClick={onSend}
            onMouseDown={(event) => event.preventDefault()}
            disabled={!input.trim() || isSending}
            className='shrink-0 px-4!'
          >
            <Send size={16} strokeWidth={2.2} />
          </Button>
        </div>
      </div>

      {confirmDelete && (
        <ConfirmDialog
          title='Удалить чат?'
          description='Чат будет удалён для обоих собеседников без возможности восстановления.'
          confirmLabel='Удалить'
          destructive
          onConfirm={() => {
            setConfirmDelete(false);
            onDeleteChat(chat.id);
          }}
          onClose={() => setConfirmDelete(false)}
        />
      )}

      {showMatchAnswers && (
        <MatchAnswersPanel
          chatId={chat.id}
          partnerName={displayName}
          onClose={() => setShowMatchAnswers(false)}
        />
      )}
    </div>
  );
}
