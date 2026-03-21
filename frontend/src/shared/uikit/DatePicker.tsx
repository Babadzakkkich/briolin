import { DatePicker } from '@ark-ui/react/date-picker';
import { Portal } from '@ark-ui/react/portal';
import { parseDate } from '@internationalized/date';
import { Calendar } from 'lucide-react';

function ViewControl() {
  return (
    <DatePicker.ViewControl className='mb-3 flex items-center justify-between'>
      <DatePicker.PrevTrigger
        className={[
          'cursor-pointer rounded-lg p-1.5 transition-colors',
          'text-secondary hover:bg-surface-secondary hover:text-primary',
          'data-[disabled]:cursor-not-allowed data-[disabled]:opacity-40',
        ].join(' ')}
      >
        <ChevronLeftIcon />
      </DatePicker.PrevTrigger>
      <DatePicker.ViewTrigger
        className={[
          'font-inter cursor-pointer text-[14px] font-medium transition-colors',
          'text-primary hover:text-accent',
        ].join(' ')}
      >
        <DatePicker.RangeText />
      </DatePicker.ViewTrigger>
      <DatePicker.NextTrigger
        className={[
          'cursor-pointer rounded-lg p-1.5 transition-colors',
          'text-secondary hover:bg-surface-secondary hover:text-primary',
          'data-[disabled]:cursor-not-allowed data-[disabled]:opacity-40',
        ].join(' ')}
      >
        <ChevronRightIcon />
      </DatePicker.NextTrigger>
    </DatePicker.ViewControl>
  );
}

interface DatePickerProps {
  label?: string;
  error?: string;
  value?: string;
  onChange?: (value: string) => void;
  min?: string;
  max?: string;
}

export function DatePickerField({ label, error, value, onChange, min, max }: DatePickerProps) {
  return (
    <DatePicker.Root
      locale='ru-RU'
      value={value ? [parseDate(value)] : undefined}
      min={min ? parseDate(min) : undefined}
      max={max ? parseDate(max) : undefined}
      onValueChange={(details) => {
        const selected = details.value[0];
        if (selected) onChange?.(selected.toString());
      }}
    >
      <div className='flex w-full flex-col gap-1.5'>
        {label && (
          <DatePicker.Label className='font-inter text-primary text-[12px] font-medium'>
            {label}
          </DatePicker.Label>
        )}

        <DatePicker.Control className='flex w-full items-center gap-1'>
          <DatePicker.Input
            className={[
              'w-full rounded-xl bg-white px-2 py-2',
              'font-inter text-primary placeholder:text-muted text-[14px] font-normal',
              'border transition-colors outline-none',
              error ? 'border-destructive' : 'border-border',
              'focus:border-accent',
            ].join(' ')}
          />
          <DatePicker.Trigger
            className={[
              'flex-shrink-0 cursor-pointer rounded-xl border bg-white p-2',
              'border-border text-secondary',
              'hover:border-accent hover:text-accent',
              'transition-colors',
            ].join(' ')}
          >
            <Calendar size={21} className='stroke-[1.5px]' />
          </DatePicker.Trigger>
        </DatePicker.Control>

        {error && (
          <span className='font-inter text-destructive text-[11px] font-normal'>{error}</span>
        )}
      </div>

      <Portal>
        <DatePicker.Positioner>
          <DatePicker.Content
            className={[
              'border-border z-50 rounded-xl border',
              'bg-white p-4 shadow-lg outline-none',
            ].join(' ')}
          >
            <DatePicker.View view='day'>
              <DatePicker.Context>
                {(datePicker) => (
                  <>
                    <DatePicker.ViewControl className='mb-3 flex items-center justify-between'>
                      <DatePicker.PrevTrigger
                        className={[
                          'cursor-pointer rounded-lg p-1.5 transition-colors',
                          'text-secondary hover:bg-surface-secondary hover:text-primary',
                          'data-[disabled]:cursor-not-allowed data-[disabled]:opacity-40',
                        ].join(' ')}
                      >
                        <ChevronLeftIcon />
                      </DatePicker.PrevTrigger>
                      <DatePicker.ViewTrigger
                        className={[
                          'font-inter cursor-pointer text-[14px] font-medium transition-colors',
                          'text-primary hover:text-accent',
                        ].join(' ')}
                      >
                        <DatePicker.RangeText />
                      </DatePicker.ViewTrigger>
                      <DatePicker.NextTrigger
                        className={[
                          'cursor-pointer rounded-lg p-1.5 transition-colors',
                          'text-secondary hover:bg-surface-secondary hover:text-primary',
                          'data-[disabled]:cursor-not-allowed data-[disabled]:opacity-40',
                        ].join(' ')}
                      >
                        <ChevronRightIcon />
                      </DatePicker.NextTrigger>
                    </DatePicker.ViewControl>
                    <DatePicker.Table className='w-full border-collapse'>
                      <DatePicker.TableHead>
                        <DatePicker.TableRow>
                          {datePicker.weekDays.map((weekDay, id) => (
                            <DatePicker.TableHeader
                              className='font-inter text-muted pb-2 text-[11px] font-medium'
                              key={id}
                            >
                              {weekDay.short}
                            </DatePicker.TableHeader>
                          ))}
                        </DatePicker.TableRow>
                      </DatePicker.TableHead>
                      <DatePicker.TableBody>
                        {datePicker.weeks.map((week, i) => (
                          <DatePicker.TableRow key={i}>
                            {week.map((day, j) => (
                              <DatePicker.TableCell key={j} value={day}>
                                <DatePicker.TableCellTrigger
                                  className={[
                                    'font-inter flex h-8 w-8 cursor-pointer items-center justify-center rounded-lg text-[13px] transition-colors',
                                    'hover:bg-surface-secondary',
                                    'data-[today]:text-accent data-[today]:font-semibold',
                                    'data-[selected]:bg-accent data-[selected]:text-white',
                                    'data-[selected]:hover:bg-accent',
                                    'data-[selected]:data-[today]:text-white',
                                    'data-[outside-range]:cursor-not-allowed data-[outside-range]:opacity-30',
                                    'data-[disabled]:cursor-not-allowed data-[disabled]:opacity-30',
                                  ].join(' ')}
                                >
                                  {day.day}
                                </DatePicker.TableCellTrigger>
                              </DatePicker.TableCell>
                            ))}
                          </DatePicker.TableRow>
                        ))}
                      </DatePicker.TableBody>
                    </DatePicker.Table>
                  </>
                )}
              </DatePicker.Context>
            </DatePicker.View>

            <DatePicker.View view='month'>
              <DatePicker.Context>
                {(datePicker) => (
                  <>
                    <ViewControl />
                    <DatePicker.Table>
                      <DatePicker.TableBody>
                        {datePicker
                          .getMonthsGrid({ columns: 4, format: 'short' })
                          .map((months, i) => (
                            <DatePicker.TableRow key={i}>
                              {months.map((month, j) => (
                                <DatePicker.TableCell key={j} value={month.value}>
                                  <DatePicker.TableCellTrigger
                                    className={[
                                      'font-inter w-full cursor-pointer rounded-lg px-3 py-2 text-[13px] transition-colors',
                                      'hover:bg-surface-secondary',
                                      'data-[selected]:bg-accent data-[selected]:text-white',
                                      'data-[selected]:hover:bg-accent',
                                      'data-[disabled]:cursor-not-allowed data-[disabled]:opacity-30',
                                    ].join(' ')}
                                  >
                                    {month.label}
                                  </DatePicker.TableCellTrigger>
                                </DatePicker.TableCell>
                              ))}
                            </DatePicker.TableRow>
                          ))}
                      </DatePicker.TableBody>
                    </DatePicker.Table>
                  </>
                )}
              </DatePicker.Context>
            </DatePicker.View>

            <DatePicker.View view='year'>
              <DatePicker.Context>
                {(datePicker) => (
                  <>
                    <ViewControl />
                    <DatePicker.Table>
                      <DatePicker.TableBody>
                        {datePicker.getYearsGrid({ columns: 4 }).map((years, i) => (
                          <DatePicker.TableRow key={i}>
                            {years.map((year, j) => (
                              <DatePicker.TableCell key={j} value={year.value}>
                                <DatePicker.TableCellTrigger
                                  className={[
                                    'cursor-pointer font-inter w-full rounded-lg px-3 py-2 text-center text-[13px] transition-colors',
                                    'hover:bg-surface-secondary',
                                    'data-[selected]:bg-accent data-[selected]:text-white',
                                    'data-[selected]:hover:bg-accent',
                                    'data-[disabled]:cursor-not-allowed data-[disabled]:opacity-30',
                                  ].join(' ')}
                                >
                                  {year.label}
                                </DatePicker.TableCellTrigger>
                              </DatePicker.TableCell>
                            ))}
                          </DatePicker.TableRow>
                        ))}
                      </DatePicker.TableBody>
                    </DatePicker.Table>
                  </>
                )}
              </DatePicker.Context>
            </DatePicker.View>
          </DatePicker.Content>
        </DatePicker.Positioner>
      </Portal>
    </DatePicker.Root>
  );
}

function ChevronLeftIcon() {
  return (
    <svg
      width='16'
      height='16'
      viewBox='0 0 24 24'
      fill='none'
      stroke='currentColor'
      strokeWidth='2'
      strokeLinecap='round'
      strokeLinejoin='round'
    >
      <path d='M15 18l-6-6 6-6' />
    </svg>
  );
}

function ChevronRightIcon() {
  return (
    <svg
      width='16'
      height='16'
      viewBox='0 0 24 24'
      fill='none'
      stroke='currentColor'
      strokeWidth='2'
      strokeLinecap='round'
      strokeLinejoin='round'
    >
      <path d='M9 18l6-6-6-6' />
    </svg>
  );
}
