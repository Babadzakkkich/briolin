import { useEffect, useRef, useCallback } from 'react';
import { useAuthStore } from '@/entities/session';
import type { WsMessage } from '@/entities/message';

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
const WS_BASE = API_URL.replace(/^https?/, (m: string) => (m === 'https' ? 'wss' : 'ws'));

interface Options {
  onMessage: (msg: WsMessage) => void;
  enabled?: boolean;
}

export function useChatSocket({ onMessage, enabled = true }: Options) {
  const ws = useRef<WebSocket | null>(null);
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;

  const send = useCallback((data: object) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(data));
    }
  }, []);

  const subscribe = useCallback(
    (chatId: string) => send({ type: 'subscribe', chat_id: chatId }),
    [send],
  );

  const unsubscribe = useCallback(
    (chatId: string) => send({ type: 'unsubscribe', chat_id: chatId }),
    [send],
  );

  const sendTyping = useCallback(
    (chatId: string, isTyping: boolean) =>
      send({ type: 'typing', chat_id: chatId, is_typing: isTyping }),
    [send],
  );

  useEffect(() => {
    if (!enabled) return;
    const token = useAuthStore.getState().accessToken;
    if (!token) return;

    const socket = new WebSocket(`${WS_BASE}/ws?token=${token}`);
    ws.current = socket;

    socket.onmessage = (event) => {
      try {
        const msg: WsMessage = JSON.parse(event.data as string);
        if (msg.type !== 'pong') onMessageRef.current(msg);
      } catch {
        // ignore malformed frames
      }
    };

    const ping = setInterval(() => {
      if (socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ type: 'ping' }));
    }, 30_000);

    socket.onclose = () => {
      ws.current = null;
      clearInterval(ping);
    };

    return () => {
      clearInterval(ping);
      socket.close();
    };
  }, [enabled]);

  return { subscribe, unsubscribe, sendTyping };
}
