interface TypingIndicatorProps {
  names: string[];
}

export function TypingIndicator({ names }: TypingIndicatorProps) {
  if (names.length === 0) return null;
  return (
    <div className='flex items-center gap-2 px-1'>
      <div className='flex gap-0.5'>
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className='bg-muted/60 h-1.5 w-1.5 animate-bounce rounded-full'
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>
      <span className='text-secondary text-[12px]'>
        {names.length === 1 ? `${names[0]} печатает` : 'Несколько человек печатают'}
      </span>
    </div>
  );
}
