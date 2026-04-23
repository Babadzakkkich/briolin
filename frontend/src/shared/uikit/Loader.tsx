const DELAYS = [0, 200, 400];

const dotSize = {
  sm: 'h-1.5 w-1.5',
  md: 'h-2   w-2',
  lg: 'h-2.5 w-2.5',
};

const gap = {
  sm: 'gap-1',
  md: 'gap-1.5',
  lg: 'gap-2',
};

const labelSize = {
  sm: 'text-[11px]',
  md: 'text-[13px]',
  lg: 'text-[14px]',
};

interface LoaderProps {
  size?: 'sm' | 'md' | 'lg';
  label?: string;
  /** Centres the loader inside a flex-1 container */
  center?: boolean;
}

export function Loader({ size = 'md', label, center = false }: LoaderProps) {
  const dots = (
    <div className={`flex items-center ${gap[size]}`}>
      {DELAYS.map((delay) => (
        <span
          key={delay}
          className={`animate-loader-dot rounded-full bg-accent ${dotSize[size]}`}
          style={{ animationDelay: `${delay}ms` }}
        />
      ))}
    </div>
  );

  const inner = (
    <div className='flex flex-col items-center gap-3'>
      {dots}
      {label && (
        <span className={`text-muted font-medium ${labelSize[size]}`}>{label}</span>
      )}
    </div>
  );

  if (center) {
    return <div className='flex flex-1 items-center justify-center'>{inner}</div>;
  }

  return inner;
}
