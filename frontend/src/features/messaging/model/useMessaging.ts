import { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import { chatApi, getOtherParticipant } from '@/entities/chat';
import { messageApi } from '@/entities/message';
import { useAuthStore } from '@/entities/session';
import { toast } from '@/shared/toast/toast';
import { useChatSocket } from '../useChatSocket';
import type { Chat } from '@/entities/chat';
import type { Message, WsMessage } from '@/entities/message';

export function useMessaging(initialChatId: string | null) {
  const keycloakId = useAuthStore((s) => s.keycloakId);

  const [chats, setChats] = useState<Chat[]>([]);
  const [selectedChatId, setSelectedChatId] = useState<string | null>(initialChatId);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [search, setSearch] = useState('');
  const [isLoadingChats, setIsLoadingChats] = useState(true);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [typingMap, setTypingMap] = useState<Record<string, string[]>>({});
  const [onlineUsers, setOnlineUsers] = useState<Set<string>>(new Set());

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const typingTimers = useRef<Record<string, ReturnType<typeof setTimeout>>>({});
  const typingActive = useRef(false);
  const typingTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const subscribedChatsRef = useRef<Set<string>>(new Set());

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

    const controller = new AbortController();

    messageApi
      .getMessages(selectedChatId, { limit: 60 }, controller.signal)
      .then((data) => {
        const sorted = [...data.messages].sort(
          (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
        );
        setMessages(sorted);
        const unread = sorted.filter(
          (m) => !m.is_read_by_me && m.sender_keycloak_id !== keycloakId,
        );
        if (unread.length > 0) {
          messageApi.markReadBulk(selectedChatId, unread.map((m) => m.id)).catch(() => {});
          setChats((prev) =>
            prev.map((c) => (c.id === selectedChatId ? { ...c, unread_count: 0 } : c)),
          );
        }
      })
      .catch((err: unknown) => {
        if (axios.isCancel(err)) return;
        toast.error('Не удалось загрузить сообщения');
      })
      .finally(() => setIsLoadingMessages(false));

    return () => controller.abort();
  }, [selectedChatId, keycloakId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Один поллинг для всех чатов сразу (а не по одному запросу на открытый чат) —
  // покрывает и "точку онлайн" в открытом ChatView, и зелёные точки в списке чатов.
  // WS не шлёт user_online/user_offline клиенту (это внутренние RabbitMQ-события),
  // так что статус можно получить только через REST.
  useEffect(() => {
    const check = () => {
      chatApi
        .getOnlineUsers()
        .then((d) => setOnlineUsers(new Set(d.online_users)))
        .catch(() => {});
    };
    check();
    const timer = setInterval(check, 30_000);
    return () => clearInterval(timer);
  }, []);

  const handleWsMessage = useCallback(
    (msg: WsMessage) => {
      if (msg.type === 'message' && msg.message) {
        const incoming = msg.message;
        if (incoming.chat_id === selectedChatId) {
          setMessages((prev) => {
            if (prev.some((m) => m.id === incoming.id)) return prev;
            return [...prev, incoming];
          });
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
                    updated_at: incoming.created_at,
                    unread_count:
                      c.id === selectedChatId || incoming.sender_keycloak_id === keycloakId
                        ? 0
                        : c.unread_count + 1,
                  }
                : c,
            )
            .sort((a, b) => {
              const aTime = a.last_message?.created_at ?? a.updated_at;
              const bTime = b.last_message?.created_at ?? b.updated_at;
              return new Date(bTime).getTime() - new Date(aTime).getTime();
            }),
        );
      }

      if (msg.type === 'typing' && msg.chat_id && msg.sender_id && msg.sender_id !== keycloakId) {
        const chatId = msg.chat_id;
        const userId = msg.sender_id;
        // Backend nests display_name and is_typing inside msg.message for typing events
        const typingPayload = msg.message as unknown as
          | { display_name?: string; is_typing?: boolean }
          | undefined;
        const name = typingPayload?.display_name ?? msg.display_name ?? userId;
        const isTyping = typingPayload?.is_typing ?? msg.is_typing ?? false;

        setTypingMap((prev) => {
          const current = prev[chatId] ?? [];
          if (isTyping) {
            return { ...prev, [chatId]: [...current.filter((n) => n !== name), name] };
          }
          return { ...prev, [chatId]: current.filter((n) => n !== name) };
        });
        if (isTyping) {
          if (typingTimers.current[userId]) clearTimeout(typingTimers.current[userId]);
          typingTimers.current[userId] = setTimeout(() => {
            setTypingMap((prev) => ({
              ...prev,
              [chatId]: (prev[chatId] ?? []).filter((n) => n !== name),
            }));
          }, 4000);
        }
      }

      if (msg.type === 'message_updated' && msg.message) {
        setMessages((prev) => prev.map((m) => (m.id === msg.message!.id ? msg.message! : m)));
      }

      if (msg.type === 'message_deleted' && msg.message_id) {
        setMessages((prev) => prev.filter((m) => m.id !== msg.message_id));
      }

      if (msg.type === 'read_receipt') {
        const receipt = msg.message as unknown as { message_id?: string } | undefined;
        if (receipt?.message_id) {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === receipt.message_id ? { ...m, read_count: m.read_count + 1 } : m,
            ),
          );
        }
      }

      if (msg.type === 'bulk_read_receipt' && msg.message_ids) {
        const ids = new Set(msg.message_ids);
        setMessages((prev) =>
          prev.map((m) => (ids.has(m.id) ? { ...m, read_count: m.read_count + 1 } : m)),
        );
      }
    },
    [selectedChatId, keycloakId],
  );

  const { subscribe, unsubscribe, sendTyping } = useChatSocket({ onMessage: handleWsMessage });

  // Subscribe to all loaded chats so WS events are received for all, not just the selected one
  useEffect(() => {
    const toSubscribe = chats.filter((c) => !subscribedChatsRef.current.has(c.id));
    toSubscribe.forEach((c) => {
      subscribedChatsRef.current.add(c.id);
      subscribe(c.id);
    });
  }, [chats, subscribe]);

  // Unsubscribe all on unmount
  useEffect(() => {
    const ref = subscribedChatsRef;
    return () => {
      ref.current.forEach((id) => unsubscribe(id));
      ref.current.clear();
    };
  }, [unsubscribe]);

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
    inputRef.current?.focus();
    setInput('');
    setIsSending(true);
    if (typingTimeout.current) clearTimeout(typingTimeout.current);
    typingActive.current = false;
    sendTyping(selectedChatId, false);
    try {
      const msg = await messageApi.send(selectedChatId, content);
      setMessages((prev) => {
        if (prev.some((m) => m.id === msg.id)) return prev;
        return [...prev, msg];
      });
      setChats((prev) =>
        prev
          .map((c) =>
            c.id === selectedChatId
              ? { ...c, last_message: msg, updated_at: msg.created_at }
              : c,
          )
          .sort((a, b) => {
            const aTime = a.last_message?.created_at ?? a.updated_at;
            const bTime = b.last_message?.created_at ?? b.updated_at;
            return new Date(bTime).getTime() - new Date(aTime).getTime();
          }),
      );
    } catch {
      toast.error('Не удалось отправить сообщение');
      setInput((current) => current || content);
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleDeleteChat = useCallback(
    async (chatId: string) => {
      try {
        await chatApi.deleteChat(chatId);
        unsubscribe(chatId);
        subscribedChatsRef.current.delete(chatId);
        setChats((prev) => prev.filter((c) => c.id !== chatId));
        setSelectedChatId((prev) => (prev === chatId ? null : prev));
        toast.success('Чат удалён');
      } catch {
        toast.error('Не удалось удалить чат');
      }
    },
    [unsubscribe],
  );

  // Отметить весь чат прочитанным без открытия — например, по кнопке в списке.
  // Сообщений мы пока не загрузили, поэтому сначала тянем последнюю страницу,
  // чтобы получить id непрочитанных, и уже их шлём в /read/bulk.
  const handleMarkChatRead = useCallback(
    async (chatId: string) => {
      try {
        const data = await messageApi.getMessages(chatId, { limit: 100 });
        const unread = data.messages.filter(
          (m) => !m.is_read_by_me && m.sender_keycloak_id !== keycloakId,
        );
        if (unread.length > 0) {
          await messageApi.markReadBulk(chatId, unread.map((m) => m.id));
        }
        setChats((prev) => prev.map((c) => (c.id === chatId ? { ...c, unread_count: 0 } : c)));
      } catch {
        toast.error('Не удалось отметить чат прочитанным');
      }
    },
    [keycloakId],
  );

  const selectedChat = chats.find((c) => c.id === selectedChatId);
  const typingNames = typingMap[selectedChatId ?? ''] ?? [];
  const otherParticipantId = selectedChat ? getOtherParticipant(selectedChat, keycloakId)?.keycloak_id : undefined;
  const isOtherUserOnline = otherParticipantId ? onlineUsers.has(otherParticipantId) : false;

  return {
    chats,
    selectedChatId,
    setSelectedChatId,
    selectedChat,
    messages,
    input,
    search,
    setSearch,
    isLoadingChats,
    isLoadingMessages,
    isSending,
    typingNames,
    keycloakId,
    messagesEndRef,
    inputRef,
    isOtherUserOnline,
    onlineUsers,
    handleInputChange,
    handleSend,
    handleKeyDown,
    handleDeleteChat,
    handleMarkChatRead,
  };
}
