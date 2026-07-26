import { useState } from 'react';
import { X, Heart } from 'lucide-react';
import { matchingApi } from '@/entities/matching';
import type { LikeAnswers } from '@/entities/matching';
import type { ProfileQuestions } from '@/entities/profile';
import { Button } from '@/shared/uikit/Button';
import { Textarea } from '@/shared/uikit/Textarea';
import { toast } from '@/shared/toast/toast';

const KEYS: (keyof LikeAnswers)[] = [
  'question_1',
  'question_2',
  'question_3',
  'question_4',
  'question_5',
];

interface LikeWithAnswersModalProps {
  targetUserId: string;
  targetDisplayName: string;
  questions: ProfileQuestions;
  onClose: () => void;
  onMatched: (matchId: number) => void;
}

export function LikeWithAnswersModal({
  targetUserId,
  targetDisplayName,
  questions,
  onClose,
  onMatched,
}: LikeWithAnswersModalProps) {
  const [answers, setAnswers] = useState<LikeAnswers>({
    question_1: '',
    question_2: '',
    question_3: '',
    question_4: '',
    question_5: '',
  });
  const [errors, setErrors] = useState<Partial<LikeAnswers>>({});
  const [submitting, setSubmitting] = useState(false);

  function validate(): boolean {
    const errs: Partial<LikeAnswers> = {};
    KEYS.forEach((k) => {
      if (!answers[k].trim()) errs[k] = 'Введите ответ';
    });
    setErrors(errs);
    return Object.keys(errs).length === 0;
  }

  async function handleSubmit() {
    if (!validate()) return;
    setSubmitting(true);
    try {
      const res = await matchingApi.likeWithAnswers(targetUserId, answers);
      if (res.data.status === 'matched' && res.data.match_id) {
        toast.success('Взаимный мэтч!');
        onMatched(res.data.match_id);
      } else {
        toast.success('Лайк отправлен!');
        onClose();
      }
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 429) toast.error('Дневной лимит лайков исчерпан (10/день)');
      else if (status === 409) toast.warn('Вы уже лайкали этого пользователя');
      else toast.error('Не удалось отправить лайк');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4'>
      <div className='relative w-full max-w-lg rounded-2xl bg-white shadow-xl'>
        <div className='flex items-center justify-between border-b border-[#F0E9E0] p-5'>
          <div>
            <h2 className='font-onest text-primary text-[17px] font-medium'>Ответьте на вопросы</h2>
            <p className='text-secondary mt-0.5 text-[13px]'>
              {targetDisplayName} ждёт ваших ответов
            </p>
          </div>
          <button
            onClick={onClose}
            className='text-muted hover:text-primary rounded-lg p-1.5 transition-colors'
          >
            <X size={18} />
          </button>
        </div>

        <div className='max-h-[60vh] overflow-y-auto p-5'>
          <div className='flex flex-col gap-4'>
            {KEYS.map((key, i) => (
              <Textarea
                key={key}
                label={questions[key] || `Вопрос ${i + 1}`}
                value={answers[key]}
                error={errors[key]}
                onChange={(v) => {
                  setAnswers((prev) => ({ ...prev, [key]: v }));
                  setErrors((prev) => ({ ...prev, [key]: undefined }));
                }}
                placeholder='Ваш ответ...'
                rows={2}
              />
            ))}
          </div>
        </div>

        <div className='flex gap-2 border-t border-[#F0E9E0] p-5'>
          <Button variant='secondary' onClick={onClose} disabled={submitting} className='flex-1'>
            Отмена
          </Button>
          <Button onClick={handleSubmit} disabled={submitting} className='flex-1'>
            <Heart size={15} />
            {submitting ? 'Отправляем...' : 'Лайкнуть'}
          </Button>
        </div>
      </div>
    </div>
  );
}
