import { useEffect, useRef, useState } from 'react';
import { CheckCheck, MoreVertical, Trash2 } from 'lucide-react';

interface ChatActionsMenuProps {
  onDelete: () => void;
  onMarkRead?: () => void;
  className?: string;
}

// Кликабельное (не только hover) мини-меню — чтобы работало и на тач-устройствах.
export function ChatActionsMenu({ onDelete, onMarkRead, className }: ChatActionsMenuProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [open]);

  return (
    <div ref={ref} className={`relative ${className ?? ''}`}>
      <button
        onClick={(e) => {
          e.stopPropagation();
          setOpen((v) => !v);
        }}
        className='text-muted hover:text-primary hover:bg-muted/15 flex h-7 w-7 shrink-0 cursor-pointer items-center justify-center rounded-lg transition-colors'
      >
        <MoreVertical size={16} />
      </button>
      {open && (
        <div className='absolute top-full right-0 z-30 mt-1 w-52 rounded-xl border border-[#F0E9E0] bg-white py-1.5 shadow-lg'>
          {onMarkRead && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                setOpen(false);
                onMarkRead();
              }}
              className='text-secondary hover:bg-surface flex w-full cursor-pointer items-center gap-2 px-3 py-2 text-left text-[13px] transition-colors'
            >
              <CheckCheck size={14} />
              Отметить прочитанным
            </button>
          )}
          <button
            onClick={(e) => {
              e.stopPropagation();
              setOpen(false);
              onDelete();
            }}
            className='flex w-full cursor-pointer items-center gap-2 px-3 py-2 text-left text-[13px] text-red-500 transition-colors hover:bg-red-50'
          >
            <Trash2 size={14} />
            Удалить чат
          </button>
        </div>
      )}
    </div>
  );
}
