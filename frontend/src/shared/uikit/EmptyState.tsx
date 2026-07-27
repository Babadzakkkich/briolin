import type { LucideIcon } from 'lucide-react';
import { Button } from './Button';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  compact?: boolean;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  actionLabel,
  onAction,
  compact = false,
}: EmptyStateProps) {
  return (
    <div
      className={[
        'flex flex-col items-center justify-center px-6 text-center',
        compact ? 'gap-2 py-10' : 'gap-3 py-20',
      ].join(' ')}
    >
      <div className='bg-surface text-muted flex h-14 w-14 items-center justify-center rounded-2xl'>
        <Icon size={24} strokeWidth={1.6} />
      </div>
      <div>
        <p className='text-primary text-[15px] font-medium'>{title}</p>
        {description && (
          <p className='text-muted mt-1 max-w-sm text-[13px] leading-5'>{description}</p>
        )}
      </div>
      {actionLabel && onAction && (
        <Button variant='secondary' size='sm' onClick={onAction} className='mt-1'>
          {actionLabel}
        </Button>
      )}
    </div>
  );
}
