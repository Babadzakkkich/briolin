import { useEffect, useState } from 'react';
import { Search } from 'lucide-react';
import { z } from 'zod';
import { Button } from '@/shared/uikit/Button';

const textField = (max: number) => z.string().max(max, `Макс. ${max} символов`);

const rangeField = (lo: number, hi: number, label: string) =>
  z
    .string()
    .refine(
      (v) => v === '' || (Number.isInteger(Number(v)) && Number(v) >= lo && Number(v) <= hi),
      {
        message: `${label}: ${lo}—${hi}`,
      },
    );

const schema = z
  .object({
    hobbies: textField(500),
    education: textField(200),
    city: textField(200),
    minHeight: rangeField(100, 250, 'Рост'),
    maxHeight: rangeField(100, 250, 'Рост'),
    minWeight: rangeField(30, 200, 'Вес'),
    maxWeight: rangeField(30, 200, 'Вес'),
  })
  .refine((d) => !(d.minHeight && d.maxHeight && Number(d.minHeight) > Number(d.maxHeight)), {
    message: 'Мин. рост больше макс.',
    path: ['maxHeight'],
  })
  .refine((d) => !(d.minWeight && d.maxWeight && Number(d.minWeight) > Number(d.maxWeight)), {
    message: 'Мин. вес больше макс.',
    path: ['maxWeight'],
  });

type Errors = Partial<
  Record<
    'hobbies' | 'education' | 'city' | 'minHeight' | 'maxHeight' | 'minWeight' | 'maxWeight',
    string
  >
>;

interface TargetedFilterFormProps {
  hobbies: string;
  onHobbiesChange: (v: string) => void;
  education: string;
  onEducationChange: (v: string) => void;
  city: string;
  onCityChange: (v: string) => void;
  minHeight: string;
  onMinHeightChange: (v: string) => void;
  maxHeight: string;
  onMaxHeightChange: (v: string) => void;
  minWeight: string;
  onMinWeightChange: (v: string) => void;
  maxWeight: string;
  onMaxWeightChange: (v: string) => void;
  loading: boolean;
  onSubmit: () => void;
}

export function TargetedFilterForm({
  hobbies,
  onHobbiesChange,
  education,
  onEducationChange,
  city,
  onCityChange,
  minHeight,
  onMinHeightChange,
  maxHeight,
  onMaxHeightChange,
  minWeight,
  onMinWeightChange,
  maxWeight,
  onMaxWeightChange,
  loading,
  onSubmit,
}: TargetedFilterFormProps) {
  const [errors, setErrors] = useState<Errors>({});

  useEffect(() => {
    if (Object.keys(errors).length > 0) setErrors({});
  }, [hobbies, education, city, minHeight, maxHeight, minWeight, maxWeight]);

  const handleSubmit = () => {
    const result = schema.safeParse({
      hobbies,
      education,
      city,
      minHeight,
      maxHeight,
      minWeight,
      maxWeight,
    });
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
      <p className='text-primary mb-5 text-[15px] font-semibold'>Фильтры профиля</p>

      <div className='flex flex-col gap-4'>
        <div className='grid grid-cols-3 gap-3'>
          <FilterField
            label='Хобби'
            value={hobbies}
            onChange={onHobbiesChange}
            placeholder='Хобби'
            error={errors.hobbies}
          />
          <FilterField
            label='Образование'
            value={education}
            onChange={onEducationChange}
            placeholder='Высшее'
            error={errors.education}
          />
          <FilterField
            label='Темперамент'
            value=''
            onChange={() => {}}
            placeholder='Сангвиник'
            disabled
          />
        </div>

        <div className='grid grid-cols-3 gap-3'>
          <FilterField
            label='Город'
            value={city}
            onChange={onCityChange}
            placeholder='Санкт-Петербург'
            error={errors.city}
          />
          <RangeField
            label='Рост'
            unit='см'
            minValue={minHeight}
            maxValue={maxHeight}
            onMinChange={onMinHeightChange}
            onMaxChange={onMaxHeightChange}
            minPlaceholder='160'
            maxPlaceholder='190'
            error={errors.minHeight ?? errors.maxHeight}
          />
          <RangeField
            label='Вес'
            unit='кг'
            minValue={minWeight}
            maxValue={maxWeight}
            onMinChange={onMinWeightChange}
            onMaxChange={onMaxWeightChange}
            minPlaceholder='50'
            maxPlaceholder='90'
            error={errors.minWeight ?? errors.maxWeight}
          />
        </div>

        <Button onClick={handleSubmit} disabled={loading} className='w-fit'>
          <Search size={15} />
          {loading ? 'Поиск...' : 'Найти совпадение'}
        </Button>
      </div>
    </div>
  );
}

function FilterField({
  label,
  value,
  onChange,
  placeholder,
  disabled,
  error,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  disabled?: boolean;
  error?: string;
}) {
  return (
    <div className='flex flex-col gap-1.5'>
      <label className='text-secondary text-[12px] font-medium'>{label}</label>
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
          disabled={disabled}
          className='text-primary placeholder:text-muted w-full rounded-xl bg-transparent px-3 py-2 text-[14px] outline-none disabled:cursor-not-allowed disabled:opacity-40'
        />
      </div>
      {error && <span className='text-destructive text-[11px]'>{error}</span>}
    </div>
  );
}

function RangeField({
  label,
  unit,
  minValue,
  maxValue,
  onMinChange,
  onMaxChange,
  minPlaceholder,
  maxPlaceholder,
  error,
}: {
  label: string;
  unit: string;
  minValue: string;
  maxValue: string;
  onMinChange: (v: string) => void;
  onMaxChange: (v: string) => void;
  minPlaceholder?: string;
  maxPlaceholder?: string;
  error?: string;
}) {
  return (
    <div className='flex flex-col gap-1.5'>
      <label className='text-secondary text-[12px] font-medium'>{label}</label>
      <div
        className={[
          'border-border focus-within:border-accent flex items-center gap-1 rounded-xl border bg-white px-3 py-2 transition-colors',
          error ? 'border-destructive! focus-within:border-destructive!' : '',
        ].join(' ')}
      >
        <input
          type='number'
          value={minValue}
          onChange={(e) => onMinChange(e.target.value)}
          placeholder={minPlaceholder}
          className='text-primary placeholder:text-muted w-10 [appearance:textfield] bg-transparent text-[14px] outline-none [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none'
        />
        <span className='text-muted text-[13px]'>—</span>
        <input
          type='number'
          value={maxValue}
          onChange={(e) => onMaxChange(e.target.value)}
          placeholder={maxPlaceholder}
          className='text-primary placeholder:text-muted w-10 [appearance:textfield] bg-transparent text-[14px] outline-none [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none'
        />
        <span className='text-muted ml-auto text-[12px]'>{unit}</span>
      </div>
      {error && <span className='text-destructive text-[11px]'>{error}</span>}
    </div>
  );
}
