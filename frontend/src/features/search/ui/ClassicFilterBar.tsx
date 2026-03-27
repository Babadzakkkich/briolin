import { Search } from 'lucide-react';
import { Button } from '@/shared/uikit/Button';

const GENDERS = [
  { label: 'Любой', value: undefined },
  { label: 'Мужской', value: 'male' },
  { label: 'Женский', value: 'female' },
] as const;

interface ClassicFilterBarProps {
  gender: string | undefined;
  onGenderChange: (v: string | undefined) => void;
  minAge: string;
  onMinAgeChange: (v: string) => void;
  maxAge: string;
  onMaxAgeChange: (v: string) => void;
  city: string;
  onCityChange: (v: string) => void;
  loading: boolean;
  onSubmit: () => void;
}

export function ClassicFilterBar({
  gender,
  onGenderChange,
  minAge,
  onMinAgeChange,
  maxAge,
  onMaxAgeChange,
  city,
  onCityChange,
  loading,
  onSubmit,
}: ClassicFilterBarProps) {
  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') onSubmit();
  };

  return (
    <div className='flex flex-wrap items-center justify-between gap-2'>
      <div className='flex gap-1'>
        <div className='flex gap-1'>
          {GENDERS.map((opt) => (
            <button
              key={opt.label}
              onClick={() => onGenderChange(opt.value)}
              className={[
                'cursor-pointer rounded-full border px-3.5 py-1.5 text-[13px] font-medium transition-colors',
                gender === opt.value
                  ? 'border-accent bg-accent text-white'
                  : 'border-border text-secondary hover:border-muted hover:bg-surface',
              ].join(' ')}
            >
              {opt.label}
            </button>
          ))}
        </div>

        <div className='border-border flex items-center gap-1.5 rounded-full border px-3.5 py-1.5'>
          <input
            type='number'
            min={18}
            max={100}
            value={minAge}
            onChange={(e) => onMinAgeChange(e.target.value)}
            onKeyDown={handleKey}
            placeholder='18'
            className='text-primary placeholder:text-muted w-8 [appearance:textfield] bg-transparent text-[13px] font-medium outline-none [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none'
          />
          <span className='text-muted text-[12px]'>—</span>
          <input
            type='number'
            min={18}
            max={100}
            value={maxAge}
            onChange={(e) => onMaxAgeChange(e.target.value)}
            onKeyDown={handleKey}
            placeholder='60'
            className='text-primary placeholder:text-muted w-8 [appearance:textfield] bg-transparent text-[13px] font-medium outline-none [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none'
          />
          <span className='text-muted text-[12px]'>лет</span>
        </div>

        <div className='border-border flex items-center rounded-full border px-3.5 py-1.5'>
          <input
            type='text'
            value={city}
            onChange={(e) => onCityChange(e.target.value)}
            onKeyDown={handleKey}
            placeholder='Город'
            className='text-primary placeholder:text-muted w-24 bg-transparent text-[13px] font-medium outline-none'
          />
        </div>
      </div>

      <Button onClick={onSubmit} disabled={loading} className='rounded-full!'>
        <Search size={14} />
        {loading ? 'Поиск...' : 'Найти'}
      </Button>
    </div>
  );
}
