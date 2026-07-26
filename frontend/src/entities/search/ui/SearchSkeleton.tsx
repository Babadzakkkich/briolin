export function SearchSkeleton() {
  return (
    <div className='grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3'>
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className='animate-pulse overflow-hidden rounded-2xl border border-transparent bg-white'>
          <div className='bg-surface aspect-square w-full' />
          <div className='flex flex-col gap-3 p-4'>
            <div>
              <div className='bg-surface h-4 w-28 rounded' />
              <div className='bg-surface mt-1.5 h-3 w-20 rounded' />
            </div>
            <div className='flex gap-2'>
              <div className='bg-surface h-9 flex-1 rounded-xl' />
              <div className='bg-surface h-9 flex-1 rounded-xl' />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
