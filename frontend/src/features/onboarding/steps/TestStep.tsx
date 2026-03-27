import { useEffect, useState } from 'react';
import { Button } from '@/shared/uikit/Button';
import { Text } from '@/shared/uikit/Text';
import { testSessionApi, type Question } from '@/entities/test-session';
import { toast } from '@/shared/toast/toast';
import type { StepProps } from '../OnboardingPage';

export function TestStep({ onNext }: StepProps<unknown>) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<string | number | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    testSessionApi
      .start()
      .then(({ data }) => {
        setSessionId(data.session_id);
        setQuestions(data.questions);
      })
      .catch(() => toast.error('Не удалось загрузить тест'))
      .finally(() => setLoading(false));
  }, []);

  const current = questions[currentIndex];
  const isLast = currentIndex === questions.length - 1;

  async function handleNext() {
    if (!sessionId || selectedAnswer === null) return;

    setSubmitting(true);
    try {
      await testSessionApi.submitAnswer(sessionId, current.id, selectedAnswer);

      if (isLast) {
        const { data: result } = await testSessionApi.complete(sessionId);
        onNext(result.results);
      } else {
        setCurrentIndex((i) => i + 1);
        setSelectedAnswer(null);
      }
    } catch {
      toast.error('Ошибка при отправке ответа');
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className='border-border flex w-120 items-center justify-center rounded-lg border bg-white px-8 py-16'>
        <Text variant='p' as='p'>
          Загрузка теста...
        </Text>
      </div>
    );
  }

  return (
    <div className='border-border flex w-120 flex-col gap-6 rounded-lg border bg-white px-8 py-8'>
      <div className='flex flex-col gap-2 text-center'>
        <Text variant='h2' as='h2'>
          Тест совместимости
        </Text>
        <Text variant='p-sm' as='p'>
          Вопрос {currentIndex + 1} из {questions.length}
        </Text>
      </div>

      <div className='bg-border h-1.5 w-full rounded-full'>
        <div
          className='bg-accent h-full rounded-full transition-all'
          style={{ width: `${((currentIndex + 1) / questions.length) * 100}%` }}
        />
      </div>

      <Text variant='p' as='p'>
        {current.text}
      </Text>

      {current.question_type === 'multiple_choice' && (
        <div className='flex flex-col gap-2'>
          {current.options.map((option) => (
            <button
              key={option.id}
              type='button'
              onClick={() => setSelectedAnswer(option.id)}
              className={[
                'cursor-pointer rounded-xl border px-4 py-3 text-left text-[14px] transition-colors',
                'font-inter font-normal',
                selectedAnswer === option.id
                  ? 'border-accent bg-accent/10 text-accent'
                  : 'border-border text-primary hover:border-accent hover:bg-surface-secondary',
              ].join(' ')}
            >
              {option.text}
            </button>
          ))}
        </div>
      )}

      {current.question_type === 'true_false' && (
        <div className='flex gap-3'>
          {current.options.map((option) => (
            <button
              key={option.id}
              type='button'
              onClick={() => setSelectedAnswer(option.id)}
              className={[
                'flex-1 cursor-pointer rounded-xl border py-3 text-[14px] font-medium transition-colors',
                'font-inter',
                selectedAnswer === option.id
                  ? 'border-accent bg-accent/10 text-accent'
                  : 'border-border text-primary hover:border-accent hover:bg-surface-secondary',
              ].join(' ')}
            >
              {option.text}
            </button>
          ))}
        </div>
      )}

      {current.question_type === 'likert_scale' && (
        <div className='flex flex-col gap-2'>
          <div className='flex gap-2'>
            {Array.from(
              { length: (current.max_value ?? 5) - (current.min_value ?? 1) + 1 },
              (_, i) => (current.min_value ?? 1) + i,
            ).map((val) => (
              <button
                key={val}
                type='button'
                onClick={() => setSelectedAnswer(val)}
                className={[
                  'flex h-10 flex-1 cursor-pointer items-center justify-center rounded-xl border text-[14px] font-medium transition-colors',
                  'font-inter',
                  selectedAnswer === val
                    ? 'border-accent bg-accent/10 text-accent'
                    : 'border-border text-primary hover:border-accent hover:bg-surface-secondary',
                ].join(' ')}
              >
                {val}
              </button>
            ))}
          </div>
          {current.labels && (
            <div className='flex justify-between'>
              <span className='font-inter text-muted text-[11px]'>
                {current.labels[String(current.min_value ?? 1)]}
              </span>
              <span className='font-inter text-muted text-[11px]'>
                {current.labels[String(current.max_value ?? 5)]}
              </span>
            </div>
          )}
        </div>
      )}

      <Button onClick={handleNext} disabled={selectedAnswer === null || submitting}>
        {isLast ? 'Завершить' : 'Далее'}
      </Button>
    </div>
  );
}
