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

type DetailedErrors = Partial<Record<'about_me' | 'education' | 'hobbies' | 'partner_preferences', string>>;

interface DetailedInfoSectionProps {
  detailed: ProfileDetailed | null | undefined;
  editing: boolean;
  saving: boolean;
  errors: DetailedErrors;
  aboutMe: string;
  education: string;
  hobbies: string;
  partnerPreferences: string;
  onEdit: () => void;
  onSave: () => void;
  onCancel: () => void;
  onAboutMeChange: (v: string) => void;
  onEducationChange: (v: string) => void;
  onHobbiesChange: (v: string) => void;
  onPartnerPreferencesChange: (v: string) => void;
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
  onEdit,
  onSave,
  onCancel,
  onAboutMeChange,
  onEducationChange,
  onHobbiesChange,
  onPartnerPreferencesChange,
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
        </div>
      )}
    </div>
  );
}
