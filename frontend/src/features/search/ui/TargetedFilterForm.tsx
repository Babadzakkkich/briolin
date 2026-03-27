import { Search } from 'lucide-react';
import { Button } from '@/shared/uikit/Button';

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
          />
          <FilterField
            label='Образование'
            value={education}
            onChange={onEducationChange}
            placeholder='Высшее'
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
          />
        </div>

        <Button onClick={onSubmit} disabled={loading} className='w-fit'>
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
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  disabled?: boolean;
}) {
  return (
    <div className='flex flex-col gap-1.5'>
      <label className='text-secondary text-[12px] font-medium'>{label}</label>
      <div className='border-border focus-within:border-accent flex items-center rounded-xl border bg-white transition-colors'>
        <input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          className='text-primary placeholder:text-muted w-full rounded-xl bg-transparent px-3 py-2 text-[14px] outline-none disabled:cursor-not-allowed disabled:opacity-40'
        />
      </div>
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
}: {
  label: string;
  unit: string;
  minValue: string;
  maxValue: string;
  onMinChange: (v: string) => void;
  onMaxChange: (v: string) => void;
  minPlaceholder?: string;
  maxPlaceholder?: string;
}) {
  return (
    <div className='flex flex-col gap-1.5'>
      <label className='text-secondary text-[12px] font-medium'>{label}</label>
      <div className='border-border focus-within:border-accent flex items-center gap-1 rounded-xl border bg-white px-3 py-2 transition-colors'>
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
    </div>
  );
}
