import { useState } from 'react';
import { Search } from 'lucide-react';
import { z } from 'zod';
import { Button } from '@/shared/uikit/Button';
import { AgeRangeInput } from '@/shared/uikit/AgeRangeInput';
import type { TargetedSearchRequest } from '@/entities/search';

const GENDERS = [
  { label: 'Любой', value: '' },
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
    gender: z.string(),
    minAge: ageField,
    maxAge: ageField,
    city: z.string().max(200, 'Макс. 200 символов'),
    education: z.string().max(200, 'Макс. 200 символов'),
    hobbies: z.string().max(500, 'Макс. 500 символов'),
    partnerPreferences: z.string().max(1000, 'Макс. 1000 символов'),
    onlineOnly: z.boolean(),
  })
  .refine((d) => !(d.minAge && d.maxAge && Number(d.minAge) > Number(d.maxAge)), {
    message: 'Мин. возраст больше макс.',
    path: ['minAge'],
  });

type FormErrors = Partial<
  Record<'minAge' | 'maxAge' | 'city' | 'education' | 'hobbies' | 'partnerPreferences', string>
>;

interface TargetedFilterFormProps {
  loading: boolean;
  onSubmit: (data: TargetedSearchRequest) => void;
}

export function TargetedFilterForm({ loading, onSubmit }: TargetedFilterFormProps) {
  const [gender, setGender] = useState('');
  const [minAge, setMinAge] = useState('');
  const [maxAge, setMaxAge] = useState('');
  const [city, setCity] = useState('');
  const [education, setEducation] = useState('');
  const [hobbies, setHobbies] = useState('');
  const [partnerPreferences, setPartnerPreferences] = useState('');
  const [onlineOnly, setOnlineOnly] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});

  const clearError = (field: keyof FormErrors) =>
    setErrors((prev) => ({ ...prev, [field]: undefined }));

  const handleSubmit = () => {
    const parsed = schema.safeParse({
      gender,
      minAge,
      maxAge,
      city,
      education,
      hobbies,
      partnerPreferences,
      onlineOnly,
    });

    if (!parsed.success) {
      const errs: FormErrors = {};
      for (const issue of parsed.error.issues) {
        const key = issue.path[0] as keyof FormErrors;
        if (!errs[key]) errs[key] = issue.message;
      }
      setErrors(errs);
      return;
    }

    setErrors({});
    const d = parsed.data;

    onSubmit({
      gender: d.gender || undefined,
      min_age: d.minAge ? Number(d.minAge) : undefined,
      max_age: d.maxAge ? Number(d.maxAge) : undefined,
      city: d.city.trim() || undefined,
      education: d.education.trim() || undefined,
      hobbies_keywords: d.hobbies.trim()
        ? d.hobbies
            .split(',')
            .map((h) => h.trim())
            .filter(Boolean)
        : undefined,
      online_only: d.onlineOnly || undefined,
      page: 1,
      limit: 12,
    });
  };

  return (
    <div className='rounded-2xl bg-white p-6'>
      <p className='text-primary mb-5 text-[15px] font-semibold'>Фильтры профиля</p>

      <div className='flex flex-col gap-5'>
        <div className='flex flex-wrap items-start gap-3'>
          <div className='flex flex-col gap-1.5'>
            <span className='text-secondary text-[12px] font-medium'>Пол</span>
            <div className='flex gap-1'>
              {GENDERS.map((opt) => (
                <button
                  key={opt.label}
                  type='button'
                  onClick={() => setGender(opt.value)}
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
            onMinChange={(v) => {
              setMinAge(v);
              clearError('minAge');
            }}
            onMaxChange={(v) => {
              setMaxAge(v);
              clearError('maxAge');
            }}
            error={errors.minAge ?? errors.maxAge}
          />
        </div>

        <div className='grid grid-cols-2 gap-3'>
          <FilterField
            label='Город'
            value={city}
            onChange={(v) => {
              setCity(v);
              clearError('city');
            }}
            placeholder='Санкт-Петербург'
            error={errors.city}
          />
          <FilterField
            label='Образование'
            value={education}
            onChange={(v) => {
              setEducation(v);
              clearError('education');
            }}
            placeholder='Высшее'
            error={errors.education}
          />
        </div>

        <FilterField
          label='Хобби'
          hint='через запятую'
          value={hobbies}
          onChange={(v) => {
            setHobbies(v);
            clearError('hobbies');
          }}
          placeholder='путешествия, музыка, спорт'
          error={errors.hobbies}
        />

        <FilterField
          label='Ищу партнёра'
          value={partnerPreferences}
          onChange={(v) => {
            setPartnerPreferences(v);
            clearError('partnerPreferences');
          }}
          placeholder='Опишите, кого вы ищете...'
          error={errors.partnerPreferences}
        />

        <div className='flex items-center justify-between'>
          <label className='flex cursor-pointer items-center gap-2.5'>
            <button
              type='button'
              role='switch'
              aria-checked={onlineOnly}
              onClick={() => setOnlineOnly((v) => !v)}
              className={[
                'relative h-5 w-9 cursor-pointer rounded-full transition-colors',
                onlineOnly ? 'bg-accent' : 'bg-border',
              ].join(' ')}
            >
              <span
                className={[
                  'absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-transform',
                  onlineOnly ? '' : '-translate-x-4',
                ].join(' ')}
              />
            </button>
            <span className='text-secondary text-[13px] font-medium'>Только онлайн</span>
          </label>

          <Button onClick={handleSubmit} disabled={loading}>
            <Search size={15} />
            {loading ? 'Поиск...' : 'Найти совпадение'}
          </Button>
        </div>
      </div>
    </div>
  );
}

function FilterField({
  label,
  hint,
  value,
  onChange,
  placeholder,
  error,
}: {
  label: string;
  hint?: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  error?: string;
}) {
  return (
    <div className='flex flex-col gap-1.5'>
      <div className='flex items-baseline gap-1.5'>
        <label className='text-secondary text-[12px] font-medium'>{label}</label>
        {hint && <span className='text-muted text-[11px]'>{hint}</span>}
      </div>
      <div
        className={[
          'border-border focus-within:border-accent flex items-center rounded-xl border bg-white transition-colors',
          error ? 'border-destructive! focus-within:border-destructive!' : '',
        ].join(' ')}
      >
        <input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className='text-primary placeholder:text-muted w-full rounded-xl bg-transparent px-3 py-2 text-[14px] outline-none'
        />
      </div>
      {error && <span className='text-destructive text-[11px]'>{error}</span>}
    </div>
  );
}
