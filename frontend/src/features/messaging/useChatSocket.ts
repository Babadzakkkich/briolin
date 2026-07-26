import { useEffect, useRef, useCallback } from 'react';
import { useAuthStore } from '@/entities/session';
import { isRefreshTokenRejected, refreshAccessToken } from '@/shared/api/client';
import type { WsMessage } from '@/entities/message';

const API_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

const WS_URL = (() => {
  try {
    const { protocol, host } = new URL(API_URL);
    return `${protocol === 'https:' ? 'wss' : 'ws'}://${host}/ws`;
  } catch {
    return 'ws://localhost:8000/ws';
  }
})();

interface Options {
  onMessage: (msg: WsMessage) => void;
  enabled?: boolean;
}

export function useChatSocket({ onMessage, enabled = true }: Options) {
  const ws = useRef<WebSocket | null>(null);
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;

  // Re-run the effect when the access token changes so we reconnect with a fresh token
  const accessToken = useAuthStore((s) => s.accessToken);

  const subscribedChats = useRef<Set<string>>(new Set());

  const send = useCallback((data: object) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(data));
    }
  }, []);

  const subscribe = useCallback(
    (chatId: string) => {
      subscribedChats.current.add(chatId);
      send({ type: 'subscribe', chat_id: chatId });
    },
    [send],
  );

  const unsubscribe = useCallback(
    (chatId: string) => {
      subscribedChats.current.delete(chatId);
      send({ type: 'unsubscribe', chat_id: chatId });
    },
    [send],
  );

  const sendTyping = useCallback(
    (chatId: string, isTyping: boolean) =>
      send({ type: 'typing', chat_id: chatId, is_typing: isTyping }),
    [send],
  );

  useEffect(() => {
    if (!enabled || !accessToken) return;

    let active = true;
    let retryTimeout: ReturnType<typeof setTimeout> | null = null;
    let retryDelay = 1000;
    let currentSocket: WebSocket | null = null;

    function connect() {
      if (!active) return;

      // Always read the latest token when connecting
      const token = useAuthStore.getState().accessToken;
      if (!token) return;

      const socket = new WebSocket(`${WS_URL}?token=${token}`);
      currentSocket = socket;
      ws.current = socket;

      const ping = setInterval(() => {
        if (socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ type: 'ping' }));
      }, 30_000);

      socket.onopen = () => {
        if (!active) {
          socket.close();
          return;
        }
        retryDelay = 1000;
        subscribedChats.current.forEach((chatId) => {
          socket.send(JSON.stringify({ type: 'subscribe', chat_id: chatId }));
        });
      };

      socket.onmessage = (event) => {
        if (!active) return;
        try {
          const msg: WsMessage = JSON.parse(event.data as string);
          if (msg.type !== 'pong') onMessageRef.current(msg);
        } catch {}
      };

      socket.onerror = () => {
        socket.close();
      };

      socket.onclose = (event) => {
        clearInterval(ping);
        if (ws.current === socket) ws.current = null;
        currentSocket = null;

        if (!active) return;

        if (event.code === 1008) {
          // Auth error: refresh the token then reconnect immediately
          refreshAccessToken()
            .then(() => {
              if (active) {
                retryDelay = 1000;
                retryTimeout = setTimeout(connect, 200);
              }
            })
            .catch((error: unknown) => {
              if (isRefreshTokenRejected(error)) {
                useAuthStore.getState().clear();
                window.location.href = '/login';
                return;
              }

              retryTimeout = setTimeout(connect, retryDelay);
              retryDelay = Math.min(retryDelay * 2, 30_000);
            });
        } else {
          retryTimeout = setTimeout(connect, retryDelay);
          retryDelay = Math.min(retryDelay * 2, 30_000);
        }
      };
    }

    connect();

    return () => {
      active = false;
      if (retryTimeout) clearTimeout(retryTimeout);
      if (currentSocket) {
        const s = currentSocket;
        currentSocket = null;
        s.onclose = null;
        s.onerror = null;
        if (s.readyState === WebSocket.CONNECTING) {
          s.onopen = () => s.close();
        } else {
          s.close();
        }
        if (ws.current === s) ws.current = null;
      }
    };
  }, [enabled, accessToken]);

  return { subscribe, unsubscribe, sendTyping };
}
