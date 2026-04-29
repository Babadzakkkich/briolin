import type { Question } from '@/entities/test-session';

const OPTION_BASE =
  'cursor-pointer rounded-xl border px-4 py-3 text-left text-[14px] transition-colors font-inter font-normal';
const OPTION_ACTIVE = 'border-accent bg-accent/10 text-accent';
const OPTION_IDLE = 'border-border text-primary hover:border-accent hover:bg-surface-secondary';

interface Props {
  question: Question;
  selected: string | number | null;
  onSelect: (value: string | number) => void;
}

function MultipleChoice({ question, selected, onSelect }: Props) {
  return (
    <div className='flex flex-col gap-2'>
      {question.options.map((option) => (
        <button
          key={option.id}
          type='button'
          onClick={() => onSelect(option.id)}
          className={[OPTION_BASE, selected === option.id ? OPTION_ACTIVE : OPTION_IDLE].join(' ')}
        >
          {option.text}
        </button>
      ))}
    </div>
  );
}

function TrueFalse({ question, selected, onSelect }: Props) {
  return (
    <div className='flex gap-3'>
      {question.options.map((option) => (
        <button
          key={option.id}
          type='button'
          onClick={() => onSelect(option.id)}
          className={[
            'flex-1 cursor-pointer rounded-xl border py-3 text-[14px] font-medium transition-colors font-inter',
            selected === option.id ? OPTION_ACTIVE : OPTION_IDLE,
          ].join(' ')}
        >
          {option.text}
        </button>
      ))}
    </div>
  );
}

function LikertScale({ question, selected, onSelect }: Props) {
  const min = question.min_value ?? 1;
  const max = question.max_value ?? 5;
  const values = Array.from({ length: max - min + 1 }, (_, i) => min + i);

  return (
    <div className='flex flex-col gap-2'>
      <div className='flex gap-2'>
        {values.map((val) => (
          <button
            key={val}
            type='button'
            onClick={() => onSelect(val)}
            className={[
              'flex h-10 flex-1 cursor-pointer items-center justify-center rounded-xl border text-[14px] font-medium transition-colors font-inter',
              selected === val ? OPTION_ACTIVE : OPTION_IDLE,
            ].join(' ')}
          >
            {val}
          </button>
        ))}
      </div>
      {question.labels && (
        <div className='flex justify-between'>
          <span className='font-inter text-muted text-[11px]'>{question.labels[String(min)]}</span>
          <span className='font-inter text-muted text-[11px]'>{question.labels[String(max)]}</span>
        </div>
      )}
    </div>
  );
}

export function QuestionOptions(props: Props) {
  if (props.question.question_type === 'multiple_choice') return <MultipleChoice {...props} />;
  if (props.question.question_type === 'true_false') return <TrueFalse {...props} />;
  if (props.question.question_type === 'likert_scale') return <LikertScale {...props} />;
  return null;
}
