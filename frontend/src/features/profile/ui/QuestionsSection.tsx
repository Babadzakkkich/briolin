import { z } from 'zod';
import { Textarea } from '@/shared/uikit/Textarea';
import { SectionHeader } from './SectionHeader';
import type { ProfileQuestions } from '@/entities/profile';

const questionSchema = z.string().min(10, 'Минимум 10 символов').max(500, 'Максимум 500 символов');

type QuestionsErrors = Partial<Record<'question_1' | 'question_2' | 'question_3' | 'question_4' | 'question_5', string>>;

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
  onChange: (key: keyof Omit<ProfileQuestions, 'created_at' | 'updated_at'>, value: string) => void;
}

const QUESTION_LABELS = [
  'Вопрос 1',
  'Вопрос 2',
  'Вопрос 3',
  'Вопрос 4',
  'Вопрос 5',
] as const;

const QUESTION_KEYS = [
  'question_1',
  'question_2',
  'question_3',
  'question_4',
  'question_5',
] as const;

function QuestionField({ label, value }: { label: string; value?: string }) {
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

export function QuestionsSection({
  questions,
  editing,
  saving,
  errors,
  onEdit,
  onSave,
  onCancel,
  onChange,
}: QuestionsSectionProps) {
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
            <QuestionField key={key} label={QUESTION_LABELS[i]} value={questions[key]} />
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
