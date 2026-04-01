import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useLocation } from 'react-router-dom';
import { MessageCircle } from 'lucide-react';
import { chatApi } from '@/entities/chat';
import { messageApi } from '@/entities/message';
import { useChatSocket } from '@/features/messaging/useChatSocket';
import { ChatList } from '@/features/messaging/ui/ChatList';
import { ChatView } from '@/features/messaging/ui/ChatView';
import type { Chat } from '@/entities/chat';
import type { Message, WsMessage } from '@/entities/message';
import { useAuthStore } from '@/entities/session';
import { toast } from '@/shared/toast/toast';

function decodeKeycloakId(token: string | null): string | null {
  if (!token) return null;
  try {
    return (JSON.parse(atob(token.split('.')[1])) as { sub?: string }).sub ?? null;
  } catch {
    return null;
  }
}

function SelectChatPlaceholder() {
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

export function MessagesPage() {
  const location = useLocation();
  const accessToken = useAuthStore((s) => s.accessToken);
  const keycloakId = useMemo(() => decodeKeycloakId(accessToken), [accessToken]);

  const [chats, setChats] = useState<Chat[]>([]);
  const [selectedChatId, setSelectedChatId] = useState<string | null>(
    (location.state as { chatId?: string } | null)?.chatId ?? null,
  );
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

  useEffect(() => {
    chatApi
      .getChats({ limit: 100 })
      .then((data) => setChats(data.chats))
      .catch(() => toast.error('Не удалось загрузить чаты'))
      .finally(() => setIsLoadingChats(false));
  }, []);

  useEffect(() => {
    if (!selectedChatId) return;
    setMessages([]);
    setIsLoadingMessages(true);
    messageApi
      .getMessages(selectedChatId, { limit: 60 })
      .then((data) => {
        const sorted = [...data.messages].sort(
          (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
        );
        setMessages(sorted);
        const unread = sorted.filter((m) => !m.is_read_by_me && m.sender_keycloak_id !== keycloakId);
        if (unread.length > 0) {
          messageApi.markRead(selectedChatId, unread.map((m) => m.id)).catch(() => {});
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
            messageApi.markRead(incoming.chat_id, [incoming.id]).catch(() => {});
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
      const msg = await messageApi.send(selectedChatId, content);
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
  const typingNames = typingMap[selectedChatId ?? ''] ?? [];

  return (
    <div className='flex flex-1 overflow-hidden'>
      <ChatList
        chats={chats}
        selectedChatId={selectedChatId}
        search={search}
        isLoading={isLoadingChats}
        onSearch={setSearch}
        onSelect={setSelectedChatId}
      />

      {selectedChat ? (
        <ChatView
          chat={selectedChat}
          messages={messages}
          isLoading={isLoadingMessages}
          input={input}
          isSending={isSending}
          typingNames={typingNames}
          keycloakId={keycloakId}
          onInputChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onSend={handleSend}
          messagesEndRef={messagesEndRef}
          inputRef={inputRef}
        />
      ) : (
        <SelectChatPlaceholder />
      )}
    </div>
  );
}
