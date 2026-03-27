import { useState, useCallback } from 'react';
import { searchApi, ProfileCard, SearchSkeleton, LockBanner } from '@/entities/search';
import type { SearchResponse, SearchLockInfo } from '@/entities/search';
import { TargetedFilterForm } from '@/features/search/ui/TargetedFilterForm';
import { toast } from '@/shared/toast/toast';

export function TargetedSearchPage() {
  const [hobbies, setHobbies] = useState('');
  const [education, setEducation] = useState('');
  const [city, setCity] = useState('');
  const [minHeight, setMinHeight] = useState('');
  const [maxHeight, setMaxHeight] = useState('');
  const [minWeight, setMinWeight] = useState('');
  const [maxWeight, setMaxWeight] = useState('');

  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [lockInfo, setLockInfo] = useState<SearchLockInfo | null>(null);

  const runSearch = useCallback(async () => {
    setLoading(true);
    try {
      const res = await searchApi.targeted({
        city: city.trim() || undefined,
        education: education.trim() || undefined,
        hobbies_keywords: hobbies.trim()
          ? hobbies
              .split(',')
              .map((h) => h.trim())
              .filter(Boolean)
          : undefined,
        page: 1,
        limit: 12,
      });
      setResult(res.data);
      setSearched(true);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data
        ?.detail;
      if (typeof detail === 'object' && detail !== null && 'message' in detail) {
        const lockErr = detail as { time_until_unlock?: number; profiles_viewed?: number };
        setLockInfo({
          search_type: 'targeted',
          is_locked: true,
          profiles_viewed: lockErr.profiles_viewed ?? 0,
          time_until_unlock: lockErr.time_until_unlock,
        });
        toast.warn('Таргетированный поиск временно заблокирован');
      } else {
        toast.error('Ошибка поиска');
      }
    } finally {
      setLoading(false);
    }
  }, [hobbies, education, city]);

  return (
    <div className='flex-1 overflow-y-auto px-8 py-8'>
      <div className='mx-auto max-w-4xl'>
        <div className='mb-6'>
          <h1 className='font-onest text-primary text-2xl font-medium'>Таргетированный поиск</h1>
          <p className='text-secondary mt-1 text-[14px]'>
            Введите подробные характеристики для поиска. Найдётся 5 анкет, потом 1 в день.
          </p>
        </div>

        {lockInfo?.is_locked && (
          <div className='mb-4'>
            <LockBanner lockInfo={lockInfo} />
          </div>
        )}

        <TargetedFilterForm
          hobbies={hobbies}
          onHobbiesChange={setHobbies}
          education={education}
          onEducationChange={setEducation}
          city={city}
          onCityChange={setCity}
          minHeight={minHeight}
          onMinHeightChange={setMinHeight}
          maxHeight={maxHeight}
          onMaxHeightChange={setMaxHeight}
          minWeight={minWeight}
          onMinWeightChange={setMinWeight}
          maxWeight={maxWeight}
          onMaxWeightChange={setMaxWeight}
          loading={loading}
          onSubmit={runSearch}
        />

        {(loading || searched) && (
          <div className='mt-6'>
            {loading ? (
              <SearchSkeleton />
            ) : result && result.profiles.length > 0 ? (
              <>
                <p className='text-secondary mb-4 text-[13px]'>
                  Найдено {result.total_results}{' '}
                  {result.total_results === 1
                    ? 'анкета'
                    : result.total_results < 5
                      ? 'анкеты'
                      : 'анкет'}
                </p>
                <div className='grid grid-cols-1 gap-4 sm:grid-cols-2'>
                  {result.profiles.map((p, i) => (
                    <ProfileCard
                      key={i}
                      profile={p}
                      onLike={() => toast.info(`Байс — ${p.first_name}`)}
                      onView={() => toast.info(`Профиль: ${p.first_name} ${p.last_name}`)}
                    />
                  ))}
                </div>
                <p className='text-muted mt-6 text-center text-[13px]'>
                  Отправленные тобой свайпы недоступны — профайлы из лайк-листа
                </p>
              </>
            ) : (
              <div className='py-12 text-center'>
                <p className='text-primary text-[15px] font-medium'>Никого не найдено</p>
                <p className='text-muted mt-1 text-[13px]'>Попробуйте изменить параметры поиска</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
