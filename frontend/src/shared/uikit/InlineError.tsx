import { AlertCircle, RefreshCw } from 'lucide-react';

interface InlineErrorProps {
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export function InlineError({
  message = 'Не удалось обновить данные.',
  onRetry,
  className,
}: InlineErrorProps) {
  return (
    <div
      role='alert'
      className={[
        'border-destructive/20 bg-error text-destructive flex items-center gap-2 rounded-xl border px-3 py-2.5',
        className ?? '',
      ].join(' ')}
    >
      <AlertCircle size={16} className='shrink-0' />
      <p className='flex-1 text-[12px] leading-5'>{message}</p>
      {onRetry && (
        <button
          type='button'
          onClick={onRetry}
          className='hover:bg-destructive/10 flex shrink-0 cursor-pointer items-center gap-1 rounded-lg px-2 py-1 text-[12px] font-medium transition-colors'
        >
          <RefreshCw size={12} />
          Повторить
        </button>
      )}
    </div>
  );
}
