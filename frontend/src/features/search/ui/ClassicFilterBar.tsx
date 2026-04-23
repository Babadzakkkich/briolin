import { useEffect, useState } from 'react';
import { Search } from 'lucide-react';
import { z } from 'zod';
import { Button } from '@/shared/uikit/Button';

const GENDERS = [
  { label: 'Любой', value: undefined },
  { label: 'Мужской', value: 'male' },
  { label: 'Женский', value: 'female' },
] as const;

const ageField = z
  .string()
  .refine((v) => v === '' || (Number.isInteger(Number(v)) && Number(v) >= 18 && Number(v) <= 100), {
    message: 'Возраст: 18—100',
  });

const schema = z
  .object({
    minAge: ageField,
    maxAge: ageField,
    city: z.string().max(200, 'Макс. 200 символов'),
  })
  .refine((d) => !(d.minAge && d.maxAge && Number(d.minAge) > Number(d.maxAge)), {
    message: 'Мин. возраст больше макс.',
    path: ['minAge'],
  });

type Errors = Partial<Record<'minAge' | 'maxAge' | 'city', string>>;

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
  const [errors, setErrors] = useState<Errors>({});

  useEffect(() => {
    if (Object.keys(errors).length > 0) setErrors({});
  }, [minAge, maxAge, city]);

  const handleSubmit = () => {
    const result = schema.safeParse({ minAge, maxAge, city });
    if (!result.success) {
      const errs: Errors = {};
      for (const issue of result.error.issues) {
        const key = issue.path[0] as keyof Errors;
        if (!errs[key]) errs[key] = issue.message;
      }
      setErrors(errs);
      return;
    }
    setErrors({});
    onSubmit();
  };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSubmit();
  };

  return (
    <div className='flex flex-wrap items-start justify-between gap-2'>
      <div className='flex flex-wrap items-start gap-1'>
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

        <div className='flex flex-col gap-0.5'>
          <div
            className={[
              'border-border flex items-center gap-1.5 rounded-full border px-3.5 py-1.5 transition-colors',
              errors.minAge || errors.maxAge ? 'border-destructive' : '',
            ].join(' ')}
          >
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
          {(errors.minAge || errors.maxAge) && (
            <span className='text-destructive px-3 text-[11px]'>
              {errors.minAge ?? errors.maxAge}
            </span>
          )}
        </div>

        <div className='flex flex-col gap-0.5'>
          <div
            className={[
              'border-border flex items-center rounded-full border px-3.5 py-1.5 transition-colors',
              errors.city ? 'border-destructive' : '',
            ].join(' ')}
          >
            <input
              type='text'
              value={city}
              onChange={(e) => onCityChange(e.target.value)}
              onKeyDown={handleKey}
              placeholder='Город'
              className='text-primary placeholder:text-muted w-24 bg-transparent text-[13px] font-medium outline-none'
            />
          </div>
          {errors.city && <span className='text-destructive px-3 text-[11px]'>{errors.city}</span>}
        </div>
      </div>

      <Button onClick={handleSubmit} disabled={loading} className='rounded-full!'>
        <Search size={14} />
        {loading ? 'Поиск...' : 'Найти'}
      </Button>
    </div>
  );
}
