interface AgeRangeInputProps {
  label?: string;
  minValue: string;
  maxValue: string;
  onMinChange: (v: string) => void;
  onMaxChange: (v: string) => void;
  error?: string;
}

export function AgeRangeInput({
  label = 'Возраст',
  minValue,
  maxValue,
  onMinChange,
  onMaxChange,
  error,
}: AgeRangeInputProps) {
  return (
    <div className='flex flex-col gap-1.5'>
      <span className='text-secondary text-[12px] font-medium'>{label}</span>
      <div
        className={[
          'border-border flex items-center gap-1 rounded-full border px-3 py-1 transition-colors',
          error ? 'border-destructive' : '',
        ].join(' ')}
      >
        <input
          type='number'
          min={18}
          max={100}
          value={minValue}
          onChange={(e) => onMinChange(e.target.value)}
          placeholder='18'
          className='text-primary placeholder:text-muted w-6 [appearance:textfield] bg-transparent text-[13px] font-medium outline-none [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none'
        />
        <span className='text-muted text-[12px]'>—</span>
        <input
          type='number'
          min={18}
          max={100}
          value={maxValue}
          onChange={(e) => onMaxChange(e.target.value)}
          placeholder='60'
          className='text-primary placeholder:text-muted ml-2 w-6 [appearance:textfield] bg-transparent text-[13px] font-medium outline-none [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none'
        />
        <span className='text-muted text-[12px]'>лет</span>
      </div>
      {error && <span className='text-destructive px-3 text-[11px]'>{error}</span>}
    </div>
  );
}
