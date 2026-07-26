interface TextareaProps {
  label?: string;
  error?: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  rows?: number;
}

export function Textarea({ label, error, value, onChange, placeholder, rows = 3 }: TextareaProps) {
  return (
    <div className='flex flex-col gap-1.5'>
      {label && (
        <label className='font-inter text-primary text-[12px] font-medium'>{label}</label>
      )}
      <textarea
        rows={rows}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className={[
          'w-full resize-none rounded-xl border bg-white px-3 py-2',
          'font-inter text-primary placeholder:text-muted text-[14px]',
          'transition-colors outline-none',
          error ? 'border-destructive' : 'border-border focus:border-accent',
        ].join(' ')}
      />
      {error && <span className='text-destructive text-[11px]'>{error}</span>}
    </div>
  );
}
