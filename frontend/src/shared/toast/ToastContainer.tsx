import type { LucideProps } from 'lucide-react';
import { AlertCircle, AlertTriangle, CheckCircle, Info, X } from 'lucide-react';
import { useToastStore } from './toast';
import { Text } from '@/shared/uikit/Text';
import type { ToastItem, ToastType } from './toast';

const CONFIG: Record<
  ToastType,
  { bg: string; border: string; iconColor: string; Icon: React.ComponentType<LucideProps> }
> = {
  success: {
    bg: '#E8F5E9',
    border: '#C8E6C9',
    iconColor: '#5A9E6F',
    Icon: CheckCircle,
  },
  error: {
    bg: '#FDECEA',
    border: '#F5C6C2',
    iconColor: '#DC4C4C',
    Icon: AlertCircle,
  },
  warn: {
    bg: '#FFF3E0',
    border: '#FFE0B2',
    iconColor: '#E0A548',
    Icon: AlertTriangle,
  },
  info: {
    bg: '#F0EBE3',
    border: '#E8E0D6',
    iconColor: '#8A7B6B',
    Icon: Info,
  },
};

function Toast({ id, type, message }: ToastItem) {
  const remove = useToastStore((s) => s.remove);
  const { bg, border, iconColor, Icon } = CONFIG[type];

  return (
    <div
      className='animate-toast-in flex w-80 items-center justify-between gap-3 rounded-xl border px-4 py-3'
      style={{ backgroundColor: bg, borderColor: border }}
    >
      <div className='flex items-center gap-2'>
        <Icon size={20} color={iconColor} className='shrink-0' />
        <Text variant='p-sm' style={{ color: iconColor }}>
          {message}
        </Text>
      </div>
      <button
        onClick={() => remove(id)}
        className='text-muted hover:text-secondary mt-0.5 flex size-6 shrink-0 cursor-pointer items-center justify-center transition-colors'
      >
        <X size={14} />
      </button>
    </div>
  );
}

export function ToastContainer() {
  const toasts = useToastStore((s) => s.toasts);

  return (
    <div className='fixed right-6 bottom-6 z-50 flex flex-col gap-2'>
      {toasts.map((t) => (
        <Toast key={t.id} {...t} />
      ))}
    </div>
  );
}
