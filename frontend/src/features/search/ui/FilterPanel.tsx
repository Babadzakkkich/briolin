import { Search, Wifi, Target, SlidersHorizontal, GraduationCap, Heart, Clock } from 'lucide-react';
import { Button } from '@/shared/uikit/Button';
import { Input } from '@/shared/uikit/Input';
import type { SearchResponse } from '@/entities/search';

const GENDER_OPTIONS = [
  { label: 'Любой', value: undefined },
  { label: 'Мужской', value: 'male' },
  { label: 'Женский', value: 'female' },
] as const;

type SearchMode = 'classic' | 'targeted';

interface FilterPanelProps {
  mode: SearchMode;
  onModeChange: (m: SearchMode) => void;
  gender: string | undefined;
  onGenderChange: (v: string | undefined) => void;
  minAge: string;
  onMinAgeChange: (v: string) => void;
  maxAge: string;
  onMaxAgeChange: (v: string) => void;
  city: string;
  onCityChange: (v: string) => void;
  education: string;
  onEducationChange: (v: string) => void;
  hobbiesRaw: string;
  onHobbiesChange: (v: string) => void;
  partnerPrefs: string;
  onPartnerPrefsChange: (v: string) => void;
  onlineOnly: boolean;
  onOnlineOnlyChange: (v: boolean) => void;
  loading: boolean;
  onSubmit: () => void;
  result: SearchResponse | null;
}

export function FilterPanel({
  mode,
  onModeChange,
  gender,
  onGenderChange,
  minAge,
  onMinAgeChange,
  maxAge,
  onMaxAgeChange,
  city,
  onCityChange,
  education,
  onEducationChange,
  hobbiesRaw,
  onHobbiesChange,
  partnerPrefs,
  onPartnerPrefsChange,
  onlineOnly,
  onOnlineOnlyChange,
  loading,
  onSubmit,
  result,
}: FilterPanelProps) {
  return (
    <div className='border-border shrink-0 border-b bg-white px-8 py-5'>
      {/* Title row */}
      <div className='mb-4 flex items-center justify-between'>
        <div>
          <h1 className='font-onest text-primary text-2xl font-medium'>Поиск</h1>
          {result && !loading && (
            <p className='text-secondary mt-0.5 text-[13px]'>
              Найдено {result.total_results}{' '}
              {result.total_results === 1
                ? 'анкета'
                : result.total_results < 5
                  ? 'анкеты'
                  : 'анкет'}
            </p>
          )}
        </div>
        <div className='flex items-center gap-2'>
          {result && !loading && (
            <span className='text-muted mr-2 flex items-center gap-1.5 text-[12px]'>
              <Clock size={12} />
              Сессия #{result.search_session_id}
            </span>
          )}
          <ModeButton active={mode === 'classic'} icon={<SlidersHorizontal size={14} />} onClick={() => onModeChange('classic')}>
            Классический
          </ModeButton>
          <ModeButton active={mode === 'targeted'} icon={<Target size={14} />} onClick={() => onModeChange('targeted')}>
            Таргет
          </ModeButton>
        </div>
      </div>

      {/* Base filters */}
      <div className='flex flex-wrap items-end gap-3'>
        <div className='flex flex-col gap-1.5'>
          <span className='text-primary text-[12px] font-medium'>Пол</span>
          <div className='flex gap-1.5'>
            {GENDER_OPTIONS.map((opt) => (
              <button
                key={opt.label}
                onClick={() => onGenderChange(opt.value)}
                className={[
                  'cursor-pointer rounded-xl border px-3 py-1.5 text-[13px] font-medium transition-colors',
                  gender === opt.value
                    ? 'border-accent bg-accent/10 text-accent'
                    : 'border-border text-secondary hover:bg-surface',
                ].join(' ')}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <div className='h-8 w-px bg-[#E8E0D6]' />

        <div className='flex items-end gap-2'>
          <div className='w-24'>
            <Input
              label='Возраст от'
              type='number'
              min={18}
              max={100}
              value={minAge}
              onChange={(e) => onMinAgeChange(e.target.value)}
              placeholder='18'
            />
          </div>
          <span className='text-secondary mb-2.5 text-[13px]'>—</span>
          <div className='w-24'>
            <Input
              label='до'
              type='number'
              min={18}
              max={100}
              value={maxAge}
              onChange={(e) => onMaxAgeChange(e.target.value)}
              placeholder='60'
            />
          </div>
        </div>

        <div className='h-8 w-px bg-[#E8E0D6]' />

        <div className='w-44'>
          <Input
            label='Город'
            value={city}
            onChange={(e) => onCityChange(e.target.value)}
            placeholder='Москва'
          />
        </div>

        <div className='ml-auto'>
          <Button onClick={onSubmit} disabled={loading}>
            <Search size={15} />
            {loading ? 'Поиск...' : 'Найти'}
          </Button>
        </div>
      </div>

      {/* Targeted extras */}
      {mode === 'targeted' && (
        <div className='border-border mt-4 flex flex-wrap items-end gap-3 border-t pt-4'>
          <div className='w-44'>
            <TextFilterField
              label={<><GraduationCap size={12} /> Образование</>}
              value={education}
              onChange={onEducationChange}
              placeholder='Высшее, техническое...'
            />
          </div>

          <div className='w-52'>
            <div className='flex flex-col gap-1.5'>
              <label className='text-primary text-[12px] font-medium'>Интересы</label>
              <input
                value={hobbiesRaw}
                onChange={(e) => onHobbiesChange(e.target.value)}
                placeholder='Спорт, музыка, кино'
                className='border-border focus:border-accent font-inter text-primary placeholder:text-muted w-full rounded-xl border bg-white px-3 py-2 text-[14px] transition-colors outline-none'
              />
              <span className='text-muted text-[11px]'>Через запятую</span>
            </div>
          </div>

          <div className='w-52'>
            <TextFilterField
              label={<><Heart size={12} /> Ищет партнёра</>}
              value={partnerPrefs}
              onChange={onPartnerPrefsChange}
              placeholder='Опишите предпочтения...'
            />
          </div>

          <label className='mb-1 flex cursor-pointer items-center gap-2'>
            <Checkbox checked={onlineOnly} onChange={onOnlineOnlyChange} />
            <div className='flex items-center gap-1.5'>
              <Wifi size={14} className='text-secondary' />
              <span className='text-primary text-[13px] font-medium'>Только онлайн</span>
            </div>
          </label>
        </div>
      )}
    </div>
  );
}

function ModeButton({
  active,
  icon,
  children,
  onClick,
}: {
  active: boolean;
  icon: React.ReactNode;
  children: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={[
        'flex cursor-pointer items-center gap-1.5 rounded-xl border px-3.5 py-2 text-[13px] font-medium transition-colors',
        active
          ? 'border-accent bg-accent/10 text-accent'
          : 'border-border text-secondary hover:bg-surface',
      ].join(' ')}
    >
      {icon}
      {children}
    </button>
  );
}

function TextFilterField({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: React.ReactNode;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <div className='flex flex-col gap-1.5'>
      <label className='text-primary flex items-center gap-1 text-[12px] font-medium'>
        {label}
      </label>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className='border-border focus:border-accent font-inter text-primary placeholder:text-muted w-full rounded-xl border bg-white px-3 py-2 text-[14px] transition-colors outline-none'
      />
    </div>
  );
}

function Checkbox({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <div className='relative'>
      <input
        type='checkbox'
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className='peer sr-only'
      />
      <div className='peer-checked:bg-accent peer-checked:border-accent h-5 w-5 rounded-md border-2 border-[#E8E0D6] bg-white transition-colors' />
      {checked && (
        <svg
          className='pointer-events-none absolute inset-0 m-auto h-3 w-3'
          fill='none'
          viewBox='0 0 12 12'
          stroke='white'
          strokeWidth={2.5}
        >
          <path d='M2 6l3 3 5-5' strokeLinecap='round' strokeLinejoin='round' />
        </svg>
      )}
    </div>
  );
}
