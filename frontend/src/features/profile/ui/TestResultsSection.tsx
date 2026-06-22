import { useEffect, useState } from 'react';
import { Award, CalendarClock, ListChecks } from 'lucide-react';
import { testSessionApi } from '@/entities/test-session';
import type { TestHistoryItem, UserTestStatistics } from '@/entities/test-session';
import { Loader } from '@/shared/uikit/Loader';

function formatDate(dateStr: string | null) {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' });
}

function StatBlock({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className='flex items-center gap-3'>
      <div className='bg-surface flex h-9 w-9 shrink-0 items-center justify-center rounded-xl'>{icon}</div>
      <div>
        <p className='text-muted text-[11px] font-medium'>{label}</p>
        <p className='text-primary text-[14px] font-medium'>{value}</p>
      </div>
    </div>
  );
}

export function TestResultsSection() {
  const [stats, setStats] = useState<UserTestStatistics | null>(null);
  const [history, setHistory] = useState<TestHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([testSessionApi.getStatistics(), testSessionApi.getHistory()])
      .then(([statsRes, historyRes]) => {
        setStats(statsRes.data);
        setHistory(historyRes.data.history);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className='rounded-2xl bg-white p-6'><Loader /></div>;
  if (!stats) return null;

  return (
    <div className='rounded-2xl bg-white p-4 sm:p-6'>
      <h2 className='font-onest text-primary mb-5 text-[18px] font-medium'>Психологический тест</h2>

      <div className='grid grid-cols-1 gap-4 sm:grid-cols-3'>
        <StatBlock
          icon={<ListChecks size={18} className='text-accent' strokeWidth={2} />}
          label='Пройдено тестов'
          value={String(stats.total_tests_completed)}
        />
        <StatBlock
          icon={<Award size={18} className='text-accent' strokeWidth={2} />}
          label='Средний балл'
          value={`${Math.round(stats.average_score)}%`}
        />
        <StatBlock
          icon={<CalendarClock size={18} className='text-accent' strokeWidth={2} />}
          label='Последний тест'
          value={formatDate(stats.last_test_date)}
        />
      </div>

      {history.length > 0 && (
        <div className='mt-5 flex flex-col gap-3 border-t border-[#F0E9E0] pt-5'>
          {history.map((item) => (
            <div key={item.session_id} className='flex flex-col gap-1 text-[13px]'>
              <div className='flex items-center justify-between gap-3'>
                <span className='text-primary min-w-0 truncate font-medium'>{item.test_name}</span>
                <span
                  className={[
                    'shrink-0 rounded-xl px-2.5 py-1 text-[11px] font-medium',
                    item.passed ? 'bg-green-50 text-green-600' : 'bg-surface text-secondary',
                  ].join(' ')}
                >
                  {item.passed ? 'Пройден' : 'Не пройден'}
                </span>
              </div>
              <div className='text-secondary flex items-center gap-2'>
                <span>{formatDate(item.completed_at)}</span>
                <span>·</span>
                <span>{Math.round(item.percentage)}%</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
