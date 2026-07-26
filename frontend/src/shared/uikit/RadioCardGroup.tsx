interface Props {
  items: string[];
  value: string;
  onChange: (value: string) => void;
}

export function RadioCardGroup({ items, value, onChange }: Props) {
  return (
    <div className='flex w-full gap-3'>
      {items.map((item) => {
        const selected = item === value;
        return (
          <button
            key={item}
            type='button'
            onClick={() => onChange(item)}
            className={[
              'flex h-12 flex-1 cursor-pointer items-center justify-center rounded-xl border text-sm font-medium transition-colors',
              selected
                ? 'border-accent text-accent bg-accent/5'
                : 'border-border text-muted bg-white font-normal',
            ].join(' ')}
          >
            {item}
          </button>
        );
      })}
    </div>
  );
}
