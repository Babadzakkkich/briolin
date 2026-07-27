import { useEffect, useState } from 'react';
import { Heart, X } from 'lucide-react';
import { chatApi } from '@/entities/chat';
import type { MatchWithAnswers, LikeAnswers } from '@/entities/matching';
import { ErrorState } from '@/shared/uikit/ErrorState';

const KEYS: (keyof LikeAnswers)[] = [
  'question_1',
  'question_2',
  'question_3',
  'question_4',
  'question_5',
];

interface MatchAnswersPanelProps {
  chatId: string;
  partnerName: string;
  onClose: () => void;
}

export function MatchAnswersPanel({ chatId, partnerName, onClose }: MatchAnswersPanelProps) {
  const [data, setData] = useState<MatchWithAnswers | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  function loadAnswers() {
    setLoading(true);
    setError(false);
    chatApi
      .getMatchAnswers(chatId)
      .then(setData)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    loadAnswers();
  }, [chatId]);

  return (
    <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4'>
      <div className='relative w-full max-w-lg rounded-2xl bg-white shadow-xl'>
        <div className='flex items-center justify-between border-b border-[#F0E9E0] p-5'>
          <h2 className='font-onest text-primary flex items-center gap-2 text-[17px] font-medium'>
            <Heart size={18} className='text-accent' />
            Почему вы совпали
          </h2>
          <button
            onClick={onClose}
            className='text-muted hover:text-primary rounded-lg p-1.5 transition-colors'
          >
            <X size={18} />
          </button>
        </div>

        <div className='max-h-[60vh] overflow-y-auto p-5'>
          {loading && !data ? (
            <div className='flex animate-pulse flex-col gap-5' role='status'>
              {[0, 1].map((section) => (
                <div key={section} className='space-y-3'>
                  <div className='bg-surface h-4 w-2/3 rounded-lg' />
                  {[0, 1, 2].map((item) => (
                    <div key={item} className='bg-surface h-14 rounded-xl' />
                  ))}
                </div>
              ))}
              <span className='sr-only'>Загружаем ответы</span>
            </div>
          ) : error && !data ? (
            <ErrorState title='Не удалось загрузить ответы' onRetry={loadAnswers} compact />
          ) : !data ? (
            <ErrorState
              title='Ответы недоступны'
              description='Для этого мэтча пока нет данных об ответах.'
              compact
            />
          ) : (
            <div
              className={[
                'flex flex-col gap-6 transition-opacity',
                loading ? 'opacity-60' : '',
              ].join(' ')}
            >
              <div>
                <h3 className='text-primary mb-3 text-[13px] font-semibold'>
                  Вопросы {partnerName} — ваши ответы
                </h3>
                <div className='flex flex-col gap-3'>
                  {KEYS.map((key) => (
                    <div key={key} className='bg-surface rounded-xl px-3 py-2.5'>
                      <p className='text-muted mb-1 text-[11px] font-medium'>
                        {data.partner_questions[key]}
                      </p>
                      <p className='text-primary text-[13px]'>{data.my_answers[key]}</p>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <h3 className='text-primary mb-3 text-[13px] font-semibold'>
                  Ваши вопросы — ответы {partnerName}
                </h3>
                <div className='flex flex-col gap-3'>
                  {KEYS.map((key) => (
                    <div key={key} className='bg-accent/10 rounded-xl px-3 py-2.5'>
                      <p className='text-muted mb-1 text-[11px] font-medium'>
                        {data.my_questions[key]}
                      </p>
                      <p className='text-primary text-[13px]'>{data.partner_answers[key]}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
