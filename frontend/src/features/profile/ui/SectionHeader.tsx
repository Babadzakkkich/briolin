import { Pencil, X, Check } from 'lucide-react';
import { Button } from '@/shared/uikit/Button';

interface SectionHeaderProps {
  title: string;
  editing: boolean;
  saving?: boolean;
  onEdit: () => void;
  onSave: () => void;
  onCancel: () => void;
}

export function SectionHeader({ title, editing, saving, onEdit, onSave, onCancel }: SectionHeaderProps) {
  return (
    <div className='mb-5 flex items-center justify-between'>
      <h2 className='font-onest text-primary text-[18px] font-medium'>{title}</h2>
      {!editing ? (
        <button
          onClick={onEdit}
          className='text-secondary hover:text-primary flex cursor-pointer items-center gap-1.5 text-[13px] transition-colors'
        >
          <Pencil size={14} strokeWidth={2} />
          Редактировать
        </button>
      ) : (
        <div className='flex items-center gap-2'>
          <Button size='sm' variant='ghost' onClick={onCancel} disabled={saving}>
            <X size={14} />
            Отмена
          </Button>
          <Button size='sm' onClick={onSave} disabled={saving}>
            <Check size={14} />
            {saving ? 'Сохранение...' : 'Сохранить'}
          </Button>
        </div>
      )}
    </div>
  );
}
