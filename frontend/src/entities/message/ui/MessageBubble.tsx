import { CheckCheck } from 'lucide-react';
import type { Message } from '../model/types';

function formatTime(dateStr: string) {
  const date = new Date(dateStr);
  const now = new Date();
  const isToday = date.toDateString() === now.toDateString();
  if (isToday) return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
  return date.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' });
}

interface MessageBubbleProps {
  message: Message;
  isOwn: boolean;
}

export function MessageBubble({ message, isOwn }: MessageBubbleProps) {
  return (
    <div className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[68%] flex flex-col gap-1 ${isOwn ? 'items-end' : 'items-start'}`}>
        {!isOwn && (
          <span className='text-secondary ml-1 text-[11px] font-medium'>
            {message.sender_display_name}
          </span>
        )}
        <div
          className={[
            'rounded-2xl px-4 py-2.5 text-[14px] leading-relaxed',
            isOwn
              ? 'bg-accent rounded-br-sm text-white'
              : 'text-primary border-border rounded-bl-sm border bg-white',
          ].join(' ')}
        >
          {message.content}
          {message.is_edited && (
            <span className={`ml-2 text-[11px] ${isOwn ? 'text-white/60' : 'text-muted'}`}>
              изм.
            </span>
          )}
        </div>
        <div className={`mx-1 flex items-center gap-1 ${isOwn ? 'flex-row-reverse' : ''}`}>
          <span className='text-muted text-[11px]'>{formatTime(message.created_at)}</span>
          {isOwn && (
            <CheckCheck
              size={13}
              className={message.read_count > 0 ? 'text-accent' : 'text-muted'}
              strokeWidth={2.5}
            />
          )}
        </div>
      </div>
    </div>
  );
}
