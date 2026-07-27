import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from './Button';

interface ErrorStateProps {
  title?: string;
  description?: string;
  retryLabel?: string;
  onRetry?: () => void;
  compact?: boolean;
}

export function ErrorState({
  title = 'Не удалось загрузить данные',
  description = 'Проверьте соединение и попробуйте ещё раз.',
  retryLabel = 'Повторить',
  onRetry,
  compact = false,
}: ErrorStateProps) {
  return (
    <div
      role='alert'
      className={[
        'flex flex-col items-center justify-center px-6 text-center',
        compact ? 'gap-2 py-10' : 'gap-3 py-20',
      ].join(' ')}
    >
      <div className='bg-error text-destructive flex h-14 w-14 items-center justify-center rounded-2xl'>
        <AlertCircle size={24} strokeWidth={1.8} />
      </div>
      <div>
        <p className='text-primary text-[15px] font-medium'>{title}</p>
        <p className='text-secondary mt-1 max-w-sm text-[13px] leading-5'>{description}</p>
      </div>
      {onRetry && (
        <Button variant='secondary' size='sm' onClick={onRetry} className='mt-1'>
          <RefreshCw size={14} />
          {retryLabel}
        </Button>
      )}
    </div>
  );
}
