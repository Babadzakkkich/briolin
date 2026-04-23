import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, ChevronLeft, ChevronRight, Clock } from 'lucide-react';
import { searchApi, ProfileCard, SearchSkeleton, LockBanner } from '@/entities/search';
import type { SearchResponse, SearchLockInfo } from '@/entities/search';
import { ClassicFilterBar } from '@/features/search/ui/ClassicFilterBar';
import { Button } from '@/shared/uikit/Button';
import { toast } from '@/shared/toast/toast';

function EmptyState({ searched }: { searched: boolean }) {
  return (
    <div className='flex flex-col items-center justify-center gap-3 py-24'>
      <div className='bg-surface flex h-14 w-14 items-center justify-center rounded-2xl'>
        <Search size={24} className='text-muted' strokeWidth={1.5} />
      </div>
      <p className='text-primary text-[15px] font-medium'>
        {searched ? 'Никого не найдено' : 'Настройте фильтры и нажмите «Найти»'}
      </p>
      <p className='text-muted text-[13px]'>
        {searched ? 'Попробуйте изменить параметры' : 'Поиск анкет по заданным критериям'}
      </p>
    </div>
  );
}

function Pagination({
  current,
  total,
  onPrev,
  onNext,
}: {
  current: number;
  total: number;
  onPrev: () => void;
  onNext: () => void;
}) {
  return (
    <div className='mt-6 flex items-center justify-between'>
      <Button variant='secondary' size='sm' onClick={onPrev} disabled={current <= 1}>
        <ChevronLeft size={16} />
        Назад
      </Button>
      <span className='text-secondary text-[13px]'>
        Страница {current} из {total}
      </span>
      <Button variant='secondary' size='sm' onClick={onNext} disabled={current >= total}>
        Вперёд
        <ChevronRight size={16} />
      </Button>
    </div>
  );
}

export function ClassicSearchPage() {
  const navigate = useNavigate();
  const [gender, setGender] = useState<string | undefined>(undefined);
  const [minAge, setMinAge] = useState('');
  const [maxAge, setMaxAge] = useState('');
  const [city, setCity] = useState('');

  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [lockInfo, setLockInfo] = useState<SearchLockInfo | null>(null);
  const [page, setPage] = useState(1);

  const runSearch = useCallback(
    async (p: number) => {
      setLoading(true);
      try {
        const res = await searchApi.classic({
          gender,
          min_age: minAge ? Number(minAge) : undefined,
          max_age: maxAge ? Number(maxAge) : undefined,
          city: city.trim() || undefined,
          page: p,
          limit: 12,
        });
        setResult(res.data);
        setPage(p);
        setSearched(true);
      } catch (err: unknown) {
        const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data
          ?.detail;
        if (typeof detail === 'object' && detail !== null && 'message' in detail) {
          const lockErr = detail as { time_until_unlock?: number; profiles_viewed?: number };
          setLockInfo({
            search_type: 'classic',
            is_locked: true,
            profiles_viewed: lockErr.profiles_viewed ?? 0,
            time_until_unlock: lockErr.time_until_unlock,
          });
          toast.warn('Поиск временно заблокирован');
        } else {
          toast.error('Ошибка поиска');
        }
      } finally {
        setLoading(false);
      }
    },
    [gender, minAge, maxAge, city],
  );

  const showPagination = result && result.total_pages > 1 && !loading;

  return (
    <div className='flex-1 overflow-y-auto px-8 py-8'>
      <div className='mx-auto max-w-4xl'>
        <div className='mb-6'>
          <h1 className='font-onest text-primary text-2xl font-medium'>Классический поиск</h1>
          <p className='text-secondary mt-1 text-[14px]'>
            Найдите анкеты по основным параметрам. Доступно без ограничений.
          </p>
        </div>

        {lockInfo?.is_locked && (
          <div className='mb-4'>
            <LockBanner lockInfo={lockInfo} />
          </div>
        )}

        <ClassicFilterBar
          gender={gender}
          onGenderChange={setGender}
          minAge={minAge}
          onMinAgeChange={setMinAge}
          maxAge={maxAge}
          onMaxAgeChange={setMaxAge}
          city={city}
          onCityChange={setCity}
          loading={loading}
          onSubmit={() => runSearch(1)}
        />

        {(loading || searched) && (
          <div className='mt-6'>
            {loading ? (
              <SearchSkeleton />
            ) : result && result.profiles.length > 0 ? (
              <>
                <div className='mb-4 flex items-center justify-between'>
                  <p className='text-secondary text-[13px]'>
                    Найдено {result.total_results}{' '}
                    {result.total_results === 1
                      ? 'анкета'
                      : result.total_results < 5
                        ? 'анкеты'
                        : 'анкет'}
                  </p>
                  {result && (
                    <span className='text-muted flex items-center gap-1.5 text-[13px]'>
                      <Clock size={13} />
                      Сессия {result.search_session_id}
                    </span>
                  )}
                </div>
                <div className='grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3'>
                  {result.profiles.map((p, i) => (
                    <ProfileCard
                      key={i}
                      profile={p}
                      onLike={() => toast.info(`Лайк — ${p.first_name}`)}
                      onView={() =>
                        navigate('/dashboard/users/' + p.keycloak_id, { state: { profile: p } })
                      }
                    />
                  ))}
                </div>
                {showPagination && (
                  <Pagination
                    current={result.current_page}
                    total={result.total_pages}
                    onPrev={() => runSearch(page - 1)}
                    onNext={() => runSearch(page + 1)}
                  />
                )}
              </>
            ) : (
              <EmptyState searched={searched} />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
