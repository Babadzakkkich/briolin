import { Button } from './Button';

interface ConfirmDialogProps {
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  destructive?: boolean;
  loading?: boolean;
  onConfirm: () => void;
  onClose: () => void;
}

export function ConfirmDialog({
  title,
  description,
  confirmLabel = 'Подтвердить',
  cancelLabel = 'Отмена',
  destructive,
  loading,
  onConfirm,
  onClose,
}: ConfirmDialogProps) {
  return (
    <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4'>
      <div className='w-full max-w-sm rounded-2xl bg-white p-6 shadow-xl'>
        <h2 className='font-onest text-primary text-[17px] font-medium'>{title}</h2>
        {description && <p className='text-secondary mt-2 text-[13px] leading-relaxed'>{description}</p>}
        <div className='mt-6 flex justify-end gap-2'>
          <Button variant='ghost' size='sm' onClick={onClose} disabled={loading}>
            {cancelLabel}
          </Button>
          <Button
            variant={destructive ? 'destructive' : 'primary'}
            size='sm'
            onClick={onConfirm}
            disabled={loading}
          >
            {loading ? 'Подождите...' : confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}
