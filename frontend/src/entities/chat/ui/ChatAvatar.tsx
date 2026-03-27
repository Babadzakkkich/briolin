function getInitials(name?: string) {
  if (!name) return '?';
  return name
    .split(' ')
    .slice(0, 2)
    .map((w) => w[0])
    .join('')
    .toUpperCase();
}

interface ChatAvatarProps {
  name?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function ChatAvatar({ name, size = 'md' }: ChatAvatarProps) {
  const sz = { sm: 'h-8 w-8 text-[11px]', md: 'h-10 w-10 text-[13px]', lg: 'h-11 w-11 text-[14px]' }[size];
  return (
    <div className={`${sz} bg-accent/15 text-accent flex shrink-0 items-center justify-center rounded-full font-semibold`}>
      {getInitials(name)}
    </div>
  );
}
