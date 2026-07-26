import { useState } from 'react';
import { X, Plus } from 'lucide-react';
import { Textarea } from '@/shared/uikit/Textarea';
import { SectionHeader } from './SectionHeader';
import type { ProfileDetailed } from '@/entities/profile';

function DetailField({ label, value }: { label: string; value?: string | null }) {
  return (
    <div>
      <p className='text-secondary mb-1 text-[12px] font-medium'>{label}</p>
      {value ? (
        <p className='text-primary text-[14px] leading-relaxed'>{value}</p>
      ) : (
        <p className='text-muted text-[14px]'>Не заполнено</p>
      )}
    </div>
  );
}

function RedFlagTag({ label, onRemove }: { label: string; onRemove?: () => void }) {
  return (
    <span className='inline-flex items-center gap-1 rounded-xl bg-red-50 px-3 py-1.5 text-[13px] text-red-600'>
      {label}
      {onRemove && (
        <button onClick={onRemove} className='ml-1 cursor-pointer opacity-60 hover:opacity-100'>
          <X size={12} />
        </button>
      )}
    </span>
  );
}

function RedFlagsInput({
  tags,
  onChange,
  error,
}: {
  tags: string[];
  onChange: (tags: string[]) => void;
  error?: string;
}) {
  const [inputValue, setInputValue] = useState('');

  function addTag() {
    const trimmed = inputValue.trim();
    if (!trimmed || tags.length >= 20 || trimmed.length > 200) return;
    if (tags.includes(trimmed)) {
      setInputValue('');
      return;
    }
    onChange([...tags, trimmed]);
    setInputValue('');
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') {
      e.preventDefault();
      addTag();
    }
  }

  function removeTag(index: number) {
    onChange(tags.filter((_, i) => i !== index));
  }

  return (
    <div>
      <p className='text-secondary mb-1 text-[12px] font-medium'>Не приемлю (красные флаги)</p>
      {tags.length > 0 && (
        <div className='mb-2 flex flex-wrap gap-1.5'>
          {tags.map((tag, i) => (
            <RedFlagTag key={i} label={tag} onRemove={() => removeTag(i)} />
          ))}
        </div>
      )}
      <div className='flex gap-2'>
        <input
          type='text'
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder='Введите и нажмите Enter...'
          maxLength={200}
          disabled={tags.length >= 20}
          className='text-primary placeholder:text-muted flex-1 rounded-xl border border-[#E8E0D8] bg-white px-3 py-2 text-[14px] outline-none focus:border-[#C4A882] disabled:opacity-50'
        />
        <button
          type='button'
          onClick={addTag}
          disabled={!inputValue.trim() || tags.length >= 20}
          className='bg-accent/10 text-accent hover:bg-accent/20 flex items-center gap-1 rounded-xl px-3 py-2 text-[13px] font-medium transition-colors disabled:pointer-events-none disabled:opacity-40'
        >
          <Plus size={14} />
          Добавить
        </button>
      </div>
      {error && <p className='mt-1 text-[12px] text-red-500'>{error}</p>}
      <p className='text-muted mt-1 text-[11px]'>{tags.length}/20 флагов</p>
    </div>
  );
}

type DetailedErrors = Partial<Record<'about_me' | 'education' | 'hobbies' | 'partner_preferences' | 'red_flags', string>>;

interface DetailedInfoSectionProps {
  detailed: ProfileDetailed | null | undefined;
  editing: boolean;
  saving: boolean;
  errors: DetailedErrors;
  aboutMe: string;
  education: string;
  hobbies: string;
  partnerPreferences: string;
  redFlags: string[];
  onEdit: () => void;
  onSave: () => void;
  onCancel: () => void;
  onAboutMeChange: (v: string) => void;
  onEducationChange: (v: string) => void;
  onHobbiesChange: (v: string) => void;
  onPartnerPreferencesChange: (v: string) => void;
  onRedFlagsChange: (v: string[]) => void;
}

export function DetailedInfoSection({
  detailed,
  editing,
  saving,
  errors,
  aboutMe,
  education,
  hobbies,
  partnerPreferences,
  redFlags,
  onEdit,
  onSave,
  onCancel,
  onAboutMeChange,
  onEducationChange,
  onHobbiesChange,
  onPartnerPreferencesChange,
  onRedFlagsChange,
}: DetailedInfoSectionProps) {
  return (
    <div className='rounded-2xl bg-white p-6'>
      <SectionHeader
        title='О себе'
        editing={editing}
        saving={saving}
        onEdit={onEdit}
        onSave={onSave}
        onCancel={onCancel}
      />

      {!editing ? (
        <div className='flex flex-col gap-5'>
          <DetailField label='О себе' value={detailed?.about_me} />
          <DetailField label='Образование' value={detailed?.education} />
          <DetailField label='Хобби и интересы' value={detailed?.hobbies} />
          <DetailField label='Ищу партнёра' value={detailed?.partner_preferences} />
          <div>
            <p className='text-secondary mb-1 text-[12px] font-medium'>Не приемлю</p>
            {detailed?.red_flags && detailed.red_flags.length > 0 ? (
              <div className='flex flex-wrap gap-1.5'>
                {detailed.red_flags.map((flag, i) => (
                  <RedFlagTag key={i} label={flag} />
                ))}
              </div>
            ) : (
              <p className='text-muted text-[14px]'>Не заполнено</p>
            )}
          </div>
        </div>
      ) : (
        <div className='flex flex-col gap-4'>
          <Textarea
            label='О себе'
            error={errors.about_me}
            value={aboutMe}
            onChange={onAboutMeChange}
            placeholder='Расскажите о себе...'
            rows={4}
          />
          <Textarea
            label='Образование'
            error={errors.education}
            value={education}
            onChange={onEducationChange}
            placeholder='Ваше образование...'
          />
          <Textarea
            label='Хобби и интересы'
            error={errors.hobbies}
            value={hobbies}
            onChange={onHobbiesChange}
            placeholder='Чем вы увлекаетесь?'
          />
          <Textarea
            label='Ищу партнёра'
            error={errors.partner_preferences}
            value={partnerPreferences}
            onChange={onPartnerPreferencesChange}
            placeholder='Опишите, кого вы ищете...'
            rows={4}
          />
          <RedFlagsInput
            tags={redFlags}
            onChange={onRedFlagsChange}
            error={errors.red_flags}
          />
        </div>
      )}
    </div>
  );
}
