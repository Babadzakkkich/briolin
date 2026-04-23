import { useEffect, useState } from 'react';
import { Search } from 'lucide-react';
import { z } from 'zod';
import { Button } from '@/shared/uikit/Button';
import { AgeRangeInput } from '@/shared/uikit/AgeRangeInput';

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

  return (
    <div className='rounded-2xl bg-white p-6'>
      <p className='text-primary mb-5 text-[15px] font-semibold'>Фильтры поиска</p>

      <div className='flex flex-col gap-5'>
        <div className='flex flex-wrap items-start gap-3'>
          <div className='flex flex-col gap-1.5'>
            <span className='text-secondary text-[12px] font-medium'>Пол</span>
            <div className='flex gap-1'>
              {GENDERS.map((opt) => (
                <button
                  key={opt.label}
                  type='button'
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
          </div>

          <AgeRangeInput
            minValue={minAge}
            maxValue={maxAge}
            onMinChange={onMinAgeChange}
            onMaxChange={onMaxAgeChange}
            error={errors.minAge ?? errors.maxAge}
          />
        </div>

        <div className='flex flex-col gap-1.5'>
          <label className='text-secondary text-[12px] font-medium'>Город</label>
          <div
            className={[
              'border-border focus-within:border-accent flex items-center rounded-xl border bg-white transition-colors',
              errors.city ? 'border-destructive! focus-within:border-destructive!' : '',
            ].join(' ')}
          >
            <input
              type='text'
              value={city}
              onChange={(e) => onCityChange(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
              placeholder='Например, Москва'
              className='text-primary placeholder:text-muted w-full rounded-xl bg-transparent px-3 py-2 text-[14px] outline-none'
            />
          </div>
          {errors.city && <span className='text-destructive text-[11px]'>{errors.city}</span>}
        </div>

        <div className='flex justify-end'>
          <Button onClick={handleSubmit} disabled={loading}>
            <Search size={15} />
            {loading ? 'Поиск...' : 'Найти'}
          </Button>
        </div>
      </div>
    </div>
  );
}
