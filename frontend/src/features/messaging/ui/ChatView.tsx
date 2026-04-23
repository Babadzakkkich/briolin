import { MessageCircle, Send } from 'lucide-react';
import { MessageBubble, TypingIndicator } from '@/entities/message';
import { ChatAvatar } from '@/entities/chat';
import { Button } from '@/shared/uikit/Button';
import { Loader } from '@/shared/uikit/Loader';
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
  onInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onKeyDown: (e: React.KeyboardEvent<HTMLInputElement>) => void;
  onSend: () => void;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
  inputRef: React.RefObject<HTMLInputElement | null>;
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
  messagesEndRef,
  inputRef,
}: ChatViewProps) {
  return (
    <div className='flex flex-1 flex-col overflow-hidden'>
      <div className='border-border flex shrink-0 items-center gap-3 border-b bg-white px-6 py-4'>
        <ChatAvatar name={chat.name} size='lg' />
        <div className='min-w-0 flex-1'>
          <p className='text-primary truncate text-[15px] font-semibold'>{chat.name ?? 'Чат'}</p>
          <p className='text-secondary text-[12px]'>
            {chat.type === 'GROUP' ? `${chat.participants.length} участников` : 'Личный чат'}
          </p>
        </div>
      </div>
      <div className='flex flex-1 flex-col gap-3 overflow-y-auto px-6 py-5'>
        {isLoading ? (
          <Loader center />
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
        <TypingIndicator names={typingNames} />
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
            disabled={isSending}
            className='border-border focus:border-accent font-inter text-primary placeholder:text-muted flex-1 rounded-xl border bg-white px-4 py-3 text-[14px] transition-colors outline-none disabled:opacity-50'
          />
          <Button
            size='md'
            onClick={onSend}
            disabled={!input.trim() || isSending}
            className='shrink-0 px-4!'
          >
            <Send size={16} strokeWidth={2.2} />
          </Button>
        </div>
      </div>
    </div>
  );
}
