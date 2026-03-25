import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { MessageCircle, Send, Search, Users, CheckCheck } from 'lucide-react';
import { chatApi } from '@/features/chat/api';
import { useChatSocket } from '@/features/chat/useChatSocket';
import type { Chat, Message, WsMessage } from '@/features/chat/types';
import { useAuthStore } from '@/shared/stores/authStore';
import { Button } from '@/shared/uikit/Button';
import { toast } from '@/shared/toast/toast';

function getInitials(name?: string) {
  if (!name) return '?';
  return name
    .split(' ')
    .slice(0, 2)
    .map((w) => w[0])
    .join('')
    .toUpperCase();
}

function formatTime(dateStr: string) {
  const date = new Date(dateStr);
  const now = new Date();
  const isToday = date.toDateString() === now.toDateString();
  if (isToday) return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
  return date.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' });
}

function decodeKeycloakId(token: string | null): string | null {
  if (!token) return null;
  try {
    return (JSON.parse(atob(token.split('.')[1])) as { sub?: string }).sub ?? null;
  } catch {
    return null;
  }
}

function ChatAvatar({ name, size = 'md' }: { name?: string; size?: 'sm' | 'md' | 'lg' }) {
  const sz = {
    sm: 'h-8 w-8 text-[11px]',
    md: 'h-10 w-10 text-[13px]',
    lg: 'h-11 w-11 text-[14px]',
  }[size];
  return (
    <div
      className={`${sz} bg-accent/15 text-accent flex shrink-0 items-center justify-center rounded-full font-semibold`}
    >
      {getInitials(name)}
    </div>
  );
}

function ChatItem({
  chat,
  isSelected,
  onClick,
}: {
  chat: Chat;
  isSelected: boolean;
  onClick: () => void;
}) {
  const lastText = chat.last_message?.content;
  const lastTime = chat.last_message?.created_at;

  return (
    <button
      onClick={onClick}
      className={[
        'flex w-full items-center gap-3 px-4 py-3 text-left transition-colors duration-75',
        isSelected ? 'bg-accent/10' : 'hover:bg-surface',
      ].join(' ')}
    >
      <ChatAvatar name={chat.name} />
      <div className='min-w-0 flex-1'>
        <div className='flex items-center justify-between gap-2'>
          <span
            className={`truncate text-[14px] font-medium ${isSelected ? 'text-accent' : 'text-primary'}`}
          >
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

function MessageBubble({ message, isOwn }: { message: Message; isOwn: boolean }) {
  return (
    <div className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[68%] ${isOwn ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
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

function TypingIndicator({ names }: { names: string[] }) {
  if (names.length === 0) return null;
  return (
    <div className='flex items-center gap-2 px-1'>
      <div className='flex gap-0.5'>
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className='bg-muted/60 h-1.5 w-1.5 animate-bounce rounded-full'
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>
      <span className='text-secondary text-[12px]'>
        {names.length === 1 ? `${names[0]} печатает` : 'Несколько человек печатают'}
      </span>
    </div>
  );
}

function EmptyState() {
  return (
    <div className='flex flex-1 flex-col items-center justify-center gap-3 px-8 text-center'>
      <div className='bg-accent/10 flex h-16 w-16 items-center justify-center rounded-2xl'>
        <MessageCircle size={28} className='text-accent' strokeWidth={2} />
      </div>
      <div>
        <p className='text-primary text-[15px] font-medium'>Выберите чат</p>
        <p className='text-secondary mt-1 text-[13px]'>
          Выберите беседу из списка слева, чтобы начать общение
        </p>
      </div>
    </div>
  );
}

function EmptyChatList() {
  return (
    <div className='flex flex-col items-center justify-center gap-2 px-6 py-12 text-center'>
      <Users size={24} className='text-muted' strokeWidth={1.8} />
      <p className='text-secondary text-[13px]'>Нет активных чатов</p>
    </div>
  );
}

// ─── Main Page ───────────────────────────────────────────────────────────────

export function MessagesPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const keycloakId = useMemo(() => decodeKeycloakId(accessToken), [accessToken]);

  const [chats, setChats] = useState<Chat[]>([]);
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [search, setSearch] = useState('');
  const [isLoadingChats, setIsLoadingChats] = useState(true);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [typingMap, setTypingMap] = useState<Record<string, string[]>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const typingTimers = useRef<Record<string, ReturnType<typeof setTimeout>>>({});
  const inputRef = useRef<HTMLInputElement>(null);

  // Load chats
  useEffect(() => {
    chatApi
      .getChats({ limit: 100 })
      .then((data) => setChats(data.chats))
      .catch(() => toast.error('Не удалось загрузить чаты'))
      .finally(() => setIsLoadingChats(false));
  }, []);

  // Load messages when chat changes
  useEffect(() => {
    if (!selectedChatId) return;
    setMessages([]);
    setIsLoadingMessages(true);
    chatApi
      .getMessages(selectedChatId, { limit: 60 })
      .then((data) => {
        const sorted = [...data.messages].sort(
          (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
        );
        setMessages(sorted);
        // Mark unread as read
        const unread = sorted.filter(
          (m) => !m.is_read_by_me && m.sender_keycloak_id !== keycloakId,
        );
        if (unread.length > 0) {
          chatApi
            .markRead(
              selectedChatId,
              unread.map((m) => m.id),
            )
            .catch(() => {});
          setChats((prev) =>
            prev.map((c) => (c.id === selectedChatId ? { ...c, unread_count: 0 } : c)),
          );
        }
      })
      .catch(() => toast.error('Не удалось загрузить сообщения'))
      .finally(() => setIsLoadingMessages(false));
  }, [selectedChatId, keycloakId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleWsMessage = useCallback(
    (msg: WsMessage) => {
      if (msg.type === 'message' && msg.message) {
        const incoming = msg.message;
        if (incoming.chat_id === selectedChatId) {
          setMessages((prev) => [...prev, incoming]);
          if (incoming.sender_keycloak_id !== keycloakId) {
            chatApi.markRead(incoming.chat_id, [incoming.id]).catch(() => {});
          }
        }
        setChats((prev) =>
          prev
            .map((c) =>
              c.id === incoming.chat_id
                ? {
                    ...c,
                    last_message: incoming,
                    unread_count:
                      c.id === selectedChatId || incoming.sender_keycloak_id === keycloakId
                        ? 0
                        : c.unread_count + 1,
                  }
                : c,
            )
            .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()),
        );
      }

      if (msg.type === 'typing' && msg.chat_id && msg.sender_id && msg.sender_id !== keycloakId) {
        const chatId = msg.chat_id;
        const userId = msg.sender_id;
        const name = msg.display_name ?? userId;

        setTypingMap((prev) => {
          const current = prev[chatId] ?? [];
          if (msg.is_typing) {
            return { ...prev, [chatId]: [...current.filter((n) => n !== name), name] };
          }
          return { ...prev, [chatId]: current.filter((n) => n !== name) };
        });

        if (msg.is_typing) {
          if (typingTimers.current[userId]) clearTimeout(typingTimers.current[userId]);
          typingTimers.current[userId] = setTimeout(() => {
            setTypingMap((prev) => ({
              ...prev,
              [chatId]: (prev[chatId] ?? []).filter((n) => n !== name),
            }));
          }, 4000);
        }
      }

      if (msg.type === 'message_update' && msg.message) {
        setMessages((prev) => prev.map((m) => (m.id === msg.message!.id ? msg.message! : m)));
      }
    },
    [selectedChatId, keycloakId],
  );

  const { subscribe, unsubscribe, sendTyping } = useChatSocket({ onMessage: handleWsMessage });

  useEffect(() => {
    if (!selectedChatId) return;
    subscribe(selectedChatId);
    return () => unsubscribe(selectedChatId);
  }, [selectedChatId, subscribe, unsubscribe]);

  const typingActive = useRef(false);
  const typingTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value);
    if (!selectedChatId) return;
    if (!typingActive.current) {
      typingActive.current = true;
      sendTyping(selectedChatId, true);
    }
    if (typingTimeout.current) clearTimeout(typingTimeout.current);
    typingTimeout.current = setTimeout(() => {
      typingActive.current = false;
      if (selectedChatId) sendTyping(selectedChatId, false);
    }, 2000);
  };

  const handleSend = async () => {
    const content = input.trim();
    if (!content || !selectedChatId || isSending) return;
    setInput('');
    setIsSending(true);
    if (typingTimeout.current) clearTimeout(typingTimeout.current);
    typingActive.current = false;
    sendTyping(selectedChatId, false);
    try {
      const msg = await chatApi.sendMessage(selectedChatId, content);
      setMessages((prev) => [...prev, msg]);
      setChats((prev) =>
        prev.map((c) => (c.id === selectedChatId ? { ...c, last_message: msg } : c)),
      );
    } catch {
      toast.error('Не удалось отправить сообщение');
      setInput(content);
    } finally {
      setIsSending(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const selectedChat = chats.find((c) => c.id === selectedChatId);
  const filteredChats = chats.filter((c) =>
    (c.name ?? '').toLowerCase().includes(search.toLowerCase()),
  );
  const typingNames = typingMap[selectedChatId ?? ''] ?? [];

  return (
    <div className='flex flex-1 overflow-hidden' style={{ height: '100vh' }}>
      {/* ── Left panel: chat list ── */}
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
              onChange={(e) => setSearch(e.target.value)}
              placeholder='Поиск...'
              className='border-border focus:border-accent font-inter text-primary placeholder:text-muted w-full rounded-xl border bg-white py-2 pr-3 pl-8 text-[13px] transition-colors outline-none'
            />
          </div>
        </div>

        <div className='flex-1 overflow-y-auto'>
          {isLoadingChats ? (
            <div className='flex flex-col gap-2 p-4'>
              {[...Array(5)].map((_, i) => (
                <div key={i} className='bg-surface h-14 animate-pulse rounded-xl' />
              ))}
            </div>
          ) : filteredChats.length === 0 ? (
            <EmptyChatList />
          ) : (
            filteredChats.map((chat) => (
              <ChatItem
                key={chat.id}
                chat={chat}
                isSelected={chat.id === selectedChatId}
                onClick={() => setSelectedChatId(chat.id)}
              />
            ))
          )}
        </div>
      </div>

      {selectedChat ? (
        <div className='flex flex-1 flex-col overflow-hidden'>
          <div className='border-border flex shrink-0 items-center gap-3 border-b bg-white px-6 py-4'>
            <ChatAvatar name={selectedChat.name} size='lg' />
            <div className='min-w-0 flex-1'>
              <p className='text-primary truncate text-[15px] font-semibold'>
                {selectedChat.name ?? 'Чат'}
              </p>
              <p className='text-secondary text-[12px]'>
                {selectedChat.type === 'GROUP'
                  ? `${selectedChat.participants.length} участников`
                  : 'Личный чат'}
              </p>
            </div>
          </div>

          <div className='flex flex-1 flex-col gap-3 overflow-y-auto px-6 py-5'>
            {isLoadingMessages ? (
              <div className='flex flex-1 items-center justify-center'>
                <div className='bg-surface border-accent h-8 w-8 animate-spin rounded-full border-2 border-t-transparent' />
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
            <TypingIndicator names={typingNames} />
            <div ref={messagesEndRef} />
          </div>
          <div className='border-border shrink-0 border-t bg-white px-6 py-4'>
            <div className='flex items-center gap-2'>
              <input
                ref={inputRef}
                value={input}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder='Напишите сообщение...'
                disabled={isSending}
                className='border-border focus:border-accent font-inter text-primary placeholder:text-muted flex-1 rounded-xl border bg-white px-4 py-3 text-[14px] transition-colors outline-none disabled:opacity-50'
              />
              <Button
                size='md'
                onClick={handleSend}
                disabled={!input.trim() || isSending}
                className='shrink-0 px-4!'
              >
                <Send size={16} strokeWidth={2.2} />
              </Button>
            </div>
          </div>
        </div>
      ) : (
        <EmptyState />
      )}
    </div>
  );
}
