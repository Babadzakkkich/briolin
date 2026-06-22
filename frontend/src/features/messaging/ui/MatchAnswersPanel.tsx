import { useEffect, useState } from 'react';
import { Heart, X } from 'lucide-react';
import { chatApi } from '@/entities/chat';
import type { MatchWithAnswers, LikeAnswers } from '@/entities/matching';
import { Loader } from '@/shared/uikit/Loader';
import { toast } from '@/shared/toast/toast';

const KEYS: (keyof LikeAnswers)[] = ['question_1', 'question_2', 'question_3', 'question_4', 'question_5'];

interface MatchAnswersPanelProps {
  chatId: string;
  partnerName: string;
  onClose: () => void;
}

export function MatchAnswersPanel({ chatId, partnerName, onClose }: MatchAnswersPanelProps) {
  const [data, setData] = useState<MatchWithAnswers | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    chatApi
      .getMatchAnswers(chatId)
      .then(setData)
      .catch(() => toast.error('Не удалось загрузить ответы'))
      .finally(() => setLoading(false));
  }, [chatId]);

  return (
    <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4'>
      <div className='relative w-full max-w-lg rounded-2xl bg-white shadow-xl'>
        <div className='flex items-center justify-between border-b border-[#F0E9E0] p-5'>
          <h2 className='font-onest text-primary flex items-center gap-2 text-[17px] font-medium'>
            <Heart size={18} className='text-accent' />
            Почему вы совпали
          </h2>
          <button onClick={onClose} className='text-muted hover:text-primary rounded-lg p-1.5 transition-colors'>
            <X size={18} />
          </button>
        </div>

        <div className='max-h-[60vh] overflow-y-auto p-5'>
          {loading ? (
            <Loader center />
          ) : !data ? (
            <p className='text-secondary text-center text-[13px]'>Нет данных об ответах</p>
          ) : (
            <div className='flex flex-col gap-6'>
              <div>
                <h3 className='text-primary mb-3 text-[13px] font-semibold'>Вопросы {partnerName} — ваши ответы</h3>
                <div className='flex flex-col gap-3'>
                  {KEYS.map((key) => (
                    <div key={key} className='rounded-xl bg-surface px-3 py-2.5'>
                      <p className='text-muted mb-1 text-[11px] font-medium'>{data.partner_questions[key]}</p>
                      <p className='text-primary text-[13px]'>{data.my_answers[key]}</p>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <h3 className='text-primary mb-3 text-[13px] font-semibold'>Ваши вопросы — ответы {partnerName}</h3>
                <div className='flex flex-col gap-3'>
                  {KEYS.map((key) => (
                    <div key={key} className='bg-accent/10 rounded-xl px-3 py-2.5'>
                      <p className='text-muted mb-1 text-[11px] font-medium'>{data.my_questions[key]}</p>
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
