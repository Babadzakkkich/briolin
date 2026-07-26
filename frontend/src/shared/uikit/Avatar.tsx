import { Camera } from 'lucide-react';
import { useRef } from 'react';

function getInitials(name?: string) {
  if (!name) return '?';
  return name
    .split(' ')
    .slice(0, 2)
    .map((w) => w[0] ?? '')
    .join('')
    .toUpperCase();
}

const sizeClasses = {
  sm: 'h-8 w-8 text-[11px]',
  md: 'h-10 w-10 text-[13px]',
  lg: 'h-11 w-11 text-[14px]',
  xl: 'h-14 w-14 text-base',
  '2xl': 'h-20 w-20 text-2xl',
} as const;

const cameraSizes: Record<keyof typeof sizeClasses, number> = {
  sm: 12,
  md: 14,
  lg: 16,
  xl: 18,
  '2xl': 22,
};

export interface AvatarProps {
  src?: string | null;
  name?: string;
  size?: keyof typeof sizeClasses;
  /** circle (default) — rounded-full; square — no border-radius */
  shape?: 'circle' | 'square';
  online?: boolean;
  uploadable?: boolean;
  onUpload?: (file: File) => void;
  className?: string;
}

export function Avatar({
  src,
  name,
  size = 'md',
  shape = 'circle',
  online,
  uploadable,
  onUpload,
  className = '',
}: AvatarProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const hasContent = !!(src || name);

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) onUpload?.(file);
    e.target.value = '';
  };

  const containerClass = [
    sizeClasses[size],
    'relative shrink-0 flex items-center justify-center font-semibold overflow-hidden',
    shape === 'circle' ? 'rounded-full' : '',
    hasContent ? 'bg-accent/15 text-accent' : 'bg-surface border border-border',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={containerClass}>
      {src ? (
        <img src={src} alt={name ?? 'avatar'} className='h-full w-full object-cover' />
      ) : name ? (
        <span>{getInitials(name)}</span>
      ) : null}

      {uploadable && (
        <label
          className={[
            'absolute inset-0 flex cursor-pointer items-center justify-center',
            shape === 'circle' ? 'rounded-full' : '',
            hasContent
              ? 'bg-black/30 opacity-0 transition-opacity hover:opacity-100'
              : 'transition-colors hover:bg-muted/25',
          ].join(' ')}
        >
          <Camera
            size={cameraSizes[size]}
            className={hasContent ? 'text-white' : 'text-muted'}
          />
          <input
            ref={inputRef}
            type='file'
            accept='image/png,image/jpeg'
            className='hidden'
            onChange={handleFile}
          />
        </label>
      )}

      {online && (
        <span className='absolute right-0 bottom-0 h-2.5 w-2.5 rounded-full bg-green-400 ring-2 ring-white' />
      )}
    </div>
  );
}
