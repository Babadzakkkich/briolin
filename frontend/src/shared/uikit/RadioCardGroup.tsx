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
                                ? 'border-[#DC4C4C] bg-[#DC4C4C15] text-[#DC4C4C]'
                                : 'border-[#E8E0D6] bg-white font-normal text-[#8A7B6B]',
                        ].join(' ')}
                    >
                        {item}
                    </button>
                );
            })}
        </div>
    );
}
