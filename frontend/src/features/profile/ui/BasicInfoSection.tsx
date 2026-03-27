import { MapPin, CalendarDays, Venus, User } from 'lucide-react';
import { Input } from '@/shared/uikit/Input';
import { RadioCardGroup } from '@/shared/uikit/RadioCardGroup';
import { DatePickerField } from '@/shared/uikit/DatePicker';
import { SectionHeader } from './SectionHeader';
import type { ProfileBasic } from '@/entities/profile';

const GENDER_OPTIONS = ['Мужской', 'Женский'];

export const genderToDisplay = (g: string) => (g === 'male' ? 'Мужской' : 'Женский');
export const displayToGender = (d: string) => (d === 'Мужской' ? 'male' : 'female');

function formatDate(dateStr: string) {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

function InfoRow({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className='flex items-center gap-3'>
      <div className='bg-surface flex h-9 w-9 shrink-0 items-center justify-center rounded-xl'>
        {icon}
      </div>
      <div>
        <p className='text-muted text-[11px] font-medium'>{label}</p>
        <p className='text-primary text-[14px] font-medium'>{value || '—'}</p>
      </div>
    </div>
  );
}

type BasicErrors = Partial<Record<'first_name' | 'last_name' | 'city' | 'date_of_birth', string>>;

interface BasicInfoSectionProps {
  basic: ProfileBasic;
  editing: boolean;
  saving: boolean;
  errors: BasicErrors;
  firstName: string;
  lastName: string;
  city: string;
  gender: string;
  birthDate: string;
  maxBirthDateStr: string;
  onEdit: () => void;
  onSave: () => void;
  onCancel: () => void;
  onFirstNameChange: (v: string) => void;
  onLastNameChange: (v: string) => void;
  onCityChange: (v: string) => void;
  onGenderChange: (v: string) => void;
  onBirthDateChange: (v: string) => void;
}

export function BasicInfoSection({
  basic,
  editing,
  saving,
  errors,
  firstName,
  lastName,
  city,
  gender,
  birthDate,
  maxBirthDateStr,
  onEdit,
  onSave,
  onCancel,
  onFirstNameChange,
  onLastNameChange,
  onCityChange,
  onGenderChange,
  onBirthDateChange,
}: BasicInfoSectionProps) {
  return (
    <div className='rounded-2xl bg-white p-6'>
      <SectionHeader
        title='Основная информация'
        editing={editing}
        saving={saving}
        onEdit={onEdit}
        onSave={onSave}
        onCancel={onCancel}
      />

      {!editing ? (
        <div className='grid grid-cols-2 gap-4'>
          <InfoRow icon={<User size={18} className='text-accent' strokeWidth={2} />} label='Имя' value={basic.first_name} />
          <InfoRow icon={<User size={18} className='text-accent' strokeWidth={2} />} label='Фамилия' value={basic.last_name} />
          <InfoRow icon={<MapPin size={18} className='text-accent' strokeWidth={2} />} label='Город' value={basic.city} />
          <InfoRow icon={<CalendarDays size={18} className='text-accent' strokeWidth={2} />} label='Дата рождения' value={formatDate(basic.date_of_birth)} />
          <InfoRow icon={<Venus size={18} className='text-accent' strokeWidth={2} />} label='Пол' value={genderToDisplay(basic.gender)} />
        </div>
      ) : (
        <div className='flex flex-col gap-4'>
          <div className='grid grid-cols-2 gap-4'>
            <Input
              label='Имя'
              error={errors.first_name}
              value={firstName}
              onChange={(e) => onFirstNameChange(e.target.value)}
              placeholder='Введите имя'
            />
            <Input
              label='Фамилия'
              error={errors.last_name}
              value={lastName}
              onChange={(e) => onLastNameChange(e.target.value)}
              placeholder='Введите фамилию'
            />
            <Input
              label='Город'
              error={errors.city}
              value={city}
              onChange={(e) => onCityChange(e.target.value)}
              placeholder='Например, Москва'
            />
            <DatePickerField
              label='Дата рождения'
              error={errors.date_of_birth}
              max={maxBirthDateStr}
              value={birthDate}
              onChange={onBirthDateChange}
            />
          </div>
          <div className='flex flex-col gap-2'>
            <label className='font-inter text-primary text-[12px] font-medium'>Пол</label>
            <RadioCardGroup items={GENDER_OPTIONS} value={gender} onChange={onGenderChange} />
          </div>
        </div>
      )}
    </div>
  );
}
