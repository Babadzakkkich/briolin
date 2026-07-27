import { useEffect, useState } from 'react';
import axios from 'axios';
import { Button } from '@/shared/uikit/Button';
import { Text } from '@/shared/uikit/Text';
import { ErrorState } from '@/shared/uikit/ErrorState';
import { testSessionApi, type Question } from '@/entities/test-session';
import { useAuthStore } from '@/entities/session';
import { toast } from '@/shared/toast/toast';
import type { StepProps } from '@/features/onboarding/model/types';
import { QuestionOptions } from '@/features/onboarding/ui/QuestionOptions';

const CARD_CLASS =
  'border-border flex w-120 items-center justify-center rounded-lg border bg-white px-8 py-16';

export function TestStep({ onNext }: StepProps<unknown>) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<string | number | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [loadAttempt, setLoadAttempt] = useState(0);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setLoadError(false);

    const load = async () => {
      try {
        const { data } = await testSessionApi.start(controller.signal);
        setSessionId(data.session_id);
        setQuestions(data.questions);
      } catch (err) {
        if (axios.isCancel(err)) return;

        if (axios.isAxiosError(err) && err.response?.status === 409) {
          try {
            const { data } = await testSessionApi.getCurrent(controller.signal);
            setSessionId(data.session_id);
            setQuestions(data.questions);
            setCurrentIndex(data.total_answered ?? 0);
            setSelectedAnswer(null);
          } catch (resumeErr) {
            if (!axios.isCancel(resumeErr)) setLoadError(true);
          }
          return;
        }

        setLoadError(true);
      } finally {
        setLoading(false);
      }
    };

    load();

    return () => controller.abort();
  }, [loadAttempt]);

  const current = questions[currentIndex];
  const isLast = questions.length > 0 && currentIndex === questions.length - 1;

  async function handleNext() {
    if (!sessionId || selectedAnswer === null || !current) return;

    setSubmitting(true);
    try {
      await testSessionApi.submitAnswer(sessionId, current.id, selectedAnswer);

      if (isLast) {
        const { data: result } = await testSessionApi.complete(sessionId);
        useAuthStore.getState().setTestPassed(result.results.passed);
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

  if (loading && questions.length === 0) {
    return (
      <div className={CARD_CLASS}>
        <div className='flex w-full animate-pulse flex-col gap-5' role='status'>
          <div className='bg-surface mx-auto h-6 w-48 rounded-lg' />
          <div className='bg-surface h-2 w-full rounded-full' />
          <div className='bg-surface h-4 w-4/5 rounded-lg' />
          {[0, 1, 2, 3].map((item) => (
            <div key={item} className='bg-surface h-11 w-full rounded-xl' />
          ))}
          <span className='sr-only'>Загружаем тест</span>
        </div>
      </div>
    );
  }

  if (loadError && questions.length === 0) {
    return (
      <div className='border-border w-120 rounded-lg border bg-white'>
        <ErrorState
          title='Не удалось загрузить тест'
          onRetry={() => setLoadAttempt((attempt) => attempt + 1)}
          compact
        />
      </div>
    );
  }

  if (!current) {
    return (
      <div className={CARD_CLASS}>
        <Text variant='p' as='p'>
          Ошибка загрузки вопроса
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

      <QuestionOptions question={current} selected={selectedAnswer} onSelect={setSelectedAnswer} />

      <Button onClick={handleNext} disabled={selectedAnswer === null || submitting}>
        {isLast ? 'Завершить' : 'Далее'}
      </Button>
    </div>
  );
}
