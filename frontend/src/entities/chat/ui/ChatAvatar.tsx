import { AuthImage } from '@/shared/uikit/AuthImage';

interface ChatAvatarProps {
  name?: string;
  src?: string | null;
  size?: 'sm' | 'md' | 'lg';
  online?: boolean;
}

const sizeMap = {
  sm: 'h-8 w-8 text-[11px]',
  md: 'h-10 w-10 text-[13px]',
  lg: 'h-11 w-11 text-[13px]',
};

function getInitials(name?: string) {
  if (!name) return '?';
  return name
    .split(' ')
    .slice(0, 2)
    .map((w) => w[0] ?? '')
    .join('')
    .toUpperCase();
}

export function ChatAvatar({ name, src, size = 'md', online }: ChatAvatarProps) {
  const initials = getInitials(name);
  return (
    <div className={`relative shrink-0 overflow-hidden rounded-full ${sizeMap[size]}`}>
      {src ? (
        <AuthImage
          src={src}
          alt={name ?? ''}
          className='h-full w-full object-cover'
          fallback={
            <div className='bg-accent/15 text-accent flex h-full w-full items-center justify-center font-semibold'>
              {initials}
            </div>
          }
        />
      ) : (
        <div className='bg-accent/15 text-accent flex h-full w-full items-center justify-center font-semibold'>
          {initials}
        </div>
      )}
      {online && (
        <span className='absolute right-0 bottom-0 h-2.5 w-2.5 rounded-full bg-green-400 ring-2 ring-white' />
      )}
    </div>
  );
}
