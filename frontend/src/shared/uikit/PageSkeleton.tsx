type PageSkeletonVariant = 'cards' | 'list' | 'profile' | 'table';

interface PageSkeletonProps {
  variant?: PageSkeletonVariant;
  count?: number;
  className?: string;
  label?: string;
}

function Block({ className }: { className: string }) {
  return <div className={`bg-surface rounded-xl ${className}`} />;
}

function CardSkeleton() {
  return (
    <div className='border-border overflow-hidden rounded-2xl border bg-white'>
      <Block className='aspect-square w-full rounded-none!' />
      <div className='space-y-3 p-4'>
        <Block className='h-4 w-2/3' />
        <Block className='h-3 w-1/2' />
        <Block className='h-10 w-full' />
      </div>
    </div>
  );
}

function ListSkeleton() {
  return (
    <div className='border-border flex items-center gap-4 rounded-2xl border bg-white p-4'>
      <Block className='h-14 w-14 shrink-0 rounded-2xl' />
      <div className='flex-1 space-y-2'>
        <Block className='h-4 w-1/3' />
        <Block className='h-3 w-1/2' />
      </div>
      <Block className='h-9 w-24' />
    </div>
  );
}

function ProfileSkeleton() {
  return (
    <div className='mx-auto w-full max-w-3xl space-y-4'>
      <div className='mb-8 space-y-2'>
        <Block className='h-8 w-48' />
        <Block className='h-3 w-72 max-w-full' />
      </div>
      {[0, 1, 2].map((item) => (
        <div key={item} className='rounded-2xl bg-white p-6'>
          <div className='mb-6 flex items-center justify-between'>
            <Block className='h-5 w-40' />
            <Block className='h-8 w-20' />
          </div>
          <div className='grid gap-4 sm:grid-cols-2'>
            <Block className='h-12 w-full' />
            <Block className='h-12 w-full' />
            <Block className='h-12 w-full' />
            <Block className='h-12 w-full' />
          </div>
        </div>
      ))}
    </div>
  );
}

function TableSkeleton({ count }: { count: number }) {
  return (
    <div className='overflow-hidden rounded-2xl bg-white'>
      <div className='border-border grid grid-cols-5 gap-4 border-b px-5 py-4'>
        {Array.from({ length: 5 }).map((_, index) => (
          <Block key={index} className='h-3 w-full' />
        ))}
      </div>
      {Array.from({ length: count }).map((_, index) => (
        <div
          key={index}
          className='border-border grid grid-cols-5 gap-4 border-b px-5 py-4 last:border-0'
        >
          {Array.from({ length: 5 }).map((__, cell) => (
            <Block key={cell} className='h-3 w-full' />
          ))}
        </div>
      ))}
    </div>
  );
}

export function PageSkeleton({
  variant = 'list',
  count = 4,
  className,
  label = 'Загрузка данных',
}: PageSkeletonProps) {
  let content: React.ReactNode;

  if (variant === 'profile') {
    content = <ProfileSkeleton />;
  } else if (variant === 'table') {
    content = <TableSkeleton count={count} />;
  } else {
    const Item = variant === 'cards' ? CardSkeleton : ListSkeleton;
    content = (
      <div
        className={
          variant === 'cards'
            ? 'grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3'
            : 'flex flex-col gap-3'
        }
      >
        {Array.from({ length: count }).map((_, index) => (
          <Item key={index} />
        ))}
      </div>
    );
  }

  return (
    <div role='status' aria-label={label} className={['animate-pulse', className ?? ''].join(' ')}>
      {content}
      <span className='sr-only'>{label}</span>
    </div>
  );
}
