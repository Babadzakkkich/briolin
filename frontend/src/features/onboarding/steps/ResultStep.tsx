import { Button } from '@/shared/uikit/Button';
import { Text } from '@/shared/uikit/Text';
import type { StepProps } from '@/features/onboarding/model/types';
import { CircleCheck, CircleX } from 'lucide-react';

interface TestResults {
  total_score: number;
  max_possible_score: number;
  percentage: number;
  passed: boolean;
}

export function ResultStep({ onNext, onRetry, data }: StepProps) {
  const results = data as TestResults | undefined;
  const passed = results?.passed ?? false;
  const percentage = results ? Math.round(results.percentage) : null;

  return (
    <div className='border-border flex w-120 flex-col gap-8 rounded-lg border bg-white px-8 py-8'>
      <div className='flex flex-col items-center gap-4 text-center'>
        <div
          className={[
            'flex h-20 w-20 items-center justify-center rounded-full text-4xl',
            passed ? 'bg-accent/10' : 'bg-destructive/10',
          ].join(' ')}
        >
          <div className='text-accent'>
            {passed ? <CircleCheck size={36} /> : <CircleX size={36} />}
          </div>
        </div>

        <div className='flex flex-col gap-1'>
          <Text variant='h2' as='h2'>
            {passed ? 'Тест пройден!' : 'Тест не пройден'}
          </Text>
          <Text variant='p' as='p'>
            {passed
              ? 'Отлично! Вы готовы к поиску совместимых людей.'
              : 'К сожалению, результат ниже необходимого порога.'}
          </Text>
        </div>

        {percentage !== null && (
          <div className='flex w-full flex-col gap-2'>
            <div className='flex justify-between'>
              <span className='font-inter text-secondary text-[12px]'>Результат</span>
              <span
                className={[
                  'font-inter text-[12px] font-medium',
                  passed ? 'text-accent' : 'text-destructive',
                ].join(' ')}
              >
                {percentage}%
              </span>
            </div>
            <div className='bg-border h-2 w-full rounded-full'>
              <div
                className={[
                  'h-full rounded-full transition-all',
                  passed ? 'bg-accent' : 'bg-destructive',
                ].join(' ')}
                style={{ width: `${percentage}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {passed ? (
        <Button onClick={() => onNext()}>Перейти в приложение</Button>
      ) : (
        <Button variant='outline' onClick={onRetry}>Пройти тест заново</Button>
      )}
    </div>
  );
}
