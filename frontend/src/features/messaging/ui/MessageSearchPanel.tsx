import { useEffect, useRef, useState } from 'react';
import { Search, TextSearch, X } from 'lucide-react';
import { chatApi, getChatDisplayName } from '@/entities/chat';
import type { Chat } from '@/entities/chat';
import type { Message } from '@/entities/message';
import { ErrorState } from '@/shared/uikit/ErrorState';
import { InlineError } from '@/shared/uikit/InlineError';

interface MessageSearchPanelProps {
  chats: Chat[];
  keycloakId: string | null;
  onSelectChat: (chatId: string) => void;
  onClose: () => void;
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function MessageSearchPanel({
  chats,
  keycloakId,
  onSelectChat,
  onClose,
}: MessageSearchPanelProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  function searchMessages(term: string) {
    setLoading(true);
    setError(false);
    chatApi
      .searchMessages({ query: term })
      .then((data) => setResults(data.messages))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    const trimmed = query.trim();
    if (!trimmed) {
      setResults([]);
      setError(false);
      return;
    }
    debounceRef.current = setTimeout(() => {
      searchMessages(trimmed);
    }, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query]);

  function chatNameFor(chatId: string) {
    const chat = chats.find((c) => c.id === chatId);
    return chat ? getChatDisplayName(chat, keycloakId) : 'Чат';
  }

  return (
    <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4'>
      <div className='relative flex max-h-[70vh] w-full max-w-lg flex-col rounded-2xl bg-white shadow-xl'>
        <div className='flex items-center justify-between border-b border-[#F0E9E0] p-5'>
          <h2 className='font-onest text-primary flex items-center gap-2 text-[17px] font-medium'>
            <TextSearch size={18} className='text-accent' />
            Поиск по сообщениям
          </h2>
          <button
            onClick={onClose}
            className='text-muted hover:text-primary rounded-lg p-1.5 transition-colors'
          >
            <X size={18} />
          </button>
        </div>

        <div className='border-b border-[#F0E9E0] p-4'>
          <div className='relative'>
            <Search
              size={14}
              className='text-muted pointer-events-none absolute top-1/2 left-3 -translate-y-1/2'
            />
            <input
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder='Введите текст сообщения...'
              className='border-border focus:border-accent font-inter text-primary placeholder:text-muted w-full rounded-xl border bg-white py-2.5 pr-3 pl-8 text-[14px] transition-colors outline-none'
            />
          </div>
        </div>

        <div className='flex-1 overflow-y-auto p-2'>
          {!query.trim() ? (
            <p className='text-secondary p-4 text-center text-[13px]'>
              Начните вводить текст для поиска
            </p>
          ) : loading && results.length === 0 ? (
            <div className='flex animate-pulse flex-col gap-2 p-2' role='status'>
              {Array.from({ length: 4 }).map((_, index) => (
                <div key={index} className='bg-surface h-14 rounded-xl' />
              ))}
              <span className='sr-only'>Ищем сообщения</span>
            </div>
          ) : error && results.length === 0 ? (
            <ErrorState
              title='Не удалось выполнить поиск'
              onRetry={() => searchMessages(query.trim())}
              compact
            />
          ) : results.length === 0 ? (
            <p className='text-secondary p-4 text-center text-[13px]'>Ничего не найдено</p>
          ) : (
            <>
              {error && (
                <InlineError
                  message='Не удалось обновить результаты поиска.'
                  onRetry={() => searchMessages(query.trim())}
                  className='m-2'
                />
              )}
              <div className={loading ? 'opacity-60' : ''} aria-busy={loading}>
                {results.map((msg) => (
                  <button
                    key={msg.id}
                    onClick={() => {
                      onSelectChat(msg.chat_id);
                      onClose();
                    }}
                    className='hover:bg-surface flex w-full flex-col gap-0.5 rounded-xl px-3 py-2.5 text-left transition-colors'
                  >
                    <div className='flex items-center justify-between gap-2'>
                      <span className='text-primary text-[13px] font-medium'>
                        {chatNameFor(msg.chat_id)}
                      </span>
                      <span className='text-muted shrink-0 text-[11px]'>
                        {formatDate(msg.created_at)}
                      </span>
                    </div>
                    <span className='text-secondary truncate text-[13px]'>{msg.content}</span>
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
