import { useState } from 'react';
import { z } from 'zod';
import { Pencil, Check, X } from 'lucide-react';
import { Textarea } from '@/shared/uikit/Textarea';
import { Button } from '@/shared/uikit/Button';
import { toast } from '@/shared/toast/toast';
import { profileApi } from '@/entities/profile';
import { SectionHeader } from './SectionHeader';
import type { ProfileQuestions } from '@/entities/profile';

const questionSchema = z.string().min(10, 'Минимум 10 символов').max(500, 'Максимум 500 символов');

type QuestionKey = 'question_1' | 'question_2' | 'question_3' | 'question_4' | 'question_5';
type QuestionsErrors = Partial<Record<QuestionKey, string>>;

export function validateQuestions(questions: Omit<ProfileQuestions, 'created_at' | 'updated_at'>): QuestionsErrors {
  const errors: QuestionsErrors = {};
  (['question_1', 'question_2', 'question_3', 'question_4', 'question_5'] as const).forEach((key) => {
    const result = questionSchema.safeParse(questions[key]);
    if (!result.success) errors[key] = result.error.issues[0].message;
  });
  return errors;
}

interface QuestionsSectionProps {
  questions: Omit<ProfileQuestions, 'created_at' | 'updated_at'>;
  editing: boolean;
  saving: boolean;
  errors: QuestionsErrors;
  onEdit: () => void;
  onSave: () => void;
  onCancel: () => void;
  onChange: (key: QuestionKey, value: string) => void;
  // Точечное редактирование одного вопроса (PATCH) — отдельно от полного edit-режима
  // выше (POST, нужен только при первом заполнении всех 5 сразу).
  onSaved: (key: QuestionKey, value: string) => void;
}

const QUESTION_LABELS = [
  'Вопрос 1',
  'Вопрос 2',
  'Вопрос 3',
  'Вопрос 4',
  'Вопрос 5',
] as const;

const QUESTION_KEYS: readonly QuestionKey[] = [
  'question_1',
  'question_2',
  'question_3',
  'question_4',
  'question_5',
];

function QuestionField({
  label,
  value,
  onSave,
}: {
  label: string;
  value?: string;
  onSave: (value: string) => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value ?? '');
  const [error, setError] = useState<string | undefined>();
  const [saving, setSaving] = useState(false);

  function startEdit() {
    setDraft(value ?? '');
    setError(undefined);
    setEditing(true);
  }

  async function handleSave() {
    const result = questionSchema.safeParse(draft);
    if (!result.success) {
      setError(result.error.issues[0].message);
      return;
    }
    setError(undefined);
    setSaving(true);
    try {
      await onSave(draft);
      setEditing(false);
    } catch {
      // toast уже показан вызывающей стороной
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <div className='mb-1 flex items-center justify-between gap-2'>
        <p className='text-secondary text-[12px] font-medium'>{label}</p>
        {!editing && value && (
          <button
            onClick={startEdit}
            className='text-muted hover:text-accent cursor-pointer transition-colors'
            title='Редактировать ответ'
          >
            <Pencil size={12} />
          </button>
        )}
      </div>

      {editing ? (
        <div className='flex flex-col gap-2'>
          <Textarea value={draft} onChange={setDraft} error={error} placeholder='Введите вопрос...' />
          <div className='flex justify-end gap-2'>
            <Button size='sm' variant='ghost' onClick={() => setEditing(false)} disabled={saving}>
              <X size={14} />
              Отмена
            </Button>
            <Button size='sm' onClick={handleSave} disabled={saving}>
              <Check size={14} />
              {saving ? 'Сохранение...' : 'Сохранить'}
            </Button>
          </div>
        </div>
      ) : value ? (
        <p className='text-primary text-[14px] leading-relaxed'>{value}</p>
      ) : (
        <p className='text-muted text-[14px]'>Не заполнено</p>
      )}
    </div>
  );
}

export function QuestionsSection({
  questions,
  editing,
  saving,
  errors,
  onEdit,
  onSave,
  onCancel,
  onChange,
  onSaved,
}: QuestionsSectionProps) {
  async function handleInlineSave(key: QuestionKey, value: string) {
    try {
      await profileApi.patchQuestion(key, value);
      onSaved(key, value);
      toast.success('Вопрос обновлён');
    } catch {
      toast.error('Не удалось сохранить ответ');
      throw new Error('patch failed');
    }
  }

  return (
    <div className='rounded-2xl bg-white p-6'>
      <SectionHeader
        title='Вопросы для партнёра'
        editing={editing}
        saving={saving}
        onEdit={onEdit}
        onSave={onSave}
        onCancel={onCancel}
      />

      {!editing ? (
        <div className='flex flex-col gap-5'>
          {QUESTION_KEYS.map((key, i) => (
            <QuestionField
              key={key}
              label={QUESTION_LABELS[i]}
              value={questions[key]}
              onSave={(value) => handleInlineSave(key, value)}
            />
          ))}
        </div>
      ) : (
        <div className='flex flex-col gap-4'>
          {QUESTION_KEYS.map((key, i) => (
            <Textarea
              key={key}
              label={QUESTION_LABELS[i]}
              error={errors[key]}
              value={questions[key]}
              onChange={(v) => onChange(key, v)}
              placeholder='Введите вопрос...'
            />
          ))}
        </div>
      )}
    </div>
  );
}
