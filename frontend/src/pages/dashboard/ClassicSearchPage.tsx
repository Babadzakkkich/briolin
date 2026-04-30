import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, ChevronLeft, ChevronRight, AlertCircle } from 'lucide-react';
import { searchApi, ProfileCard, SearchSkeleton } from '@/entities/search';
import type { SearchResponse, ProfilePreview } from '@/entities/search';
import { profileApi } from '@/entities/profile';
import type { QuestionsStatus, ProfileQuestions } from '@/entities/profile';
import { LikeWithAnswersModal } from '@/features/matching/ui/LikeWithAnswersModal';
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

function QuestionsRequiredBanner({ count }: { count: number }) {
  const navigate = useNavigate();
  return (
    <div className='mb-4 flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-4'>
      <AlertCircle size={18} className='mt-0.5 shrink-0 text-amber-500' />
      <div className='flex-1'>
        <p className='text-[14px] font-medium text-amber-800'>
          Заполните вопросы для партнёра ({count}/5)
        </p>
        <p className='mt-0.5 text-[13px] text-amber-700'>
          Чтобы использовать поиск, необходимо заполнить все 5 вопросов в профиле.
        </p>
      </div>
      <button
        onClick={() => navigate('/dashboard/profile')}
        className='shrink-0 rounded-xl bg-amber-100 px-3 py-1.5 text-[13px] font-medium text-amber-800 hover:bg-amber-200 transition-colors'
      >
        Перейти
      </button>
    </div>
  );
}

interface LikeTarget {
  profile: ProfilePreview;
  questions: ProfileQuestions;
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
  const [page, setPage] = useState(1);

  const [questionsStatus, setQuestionsStatus] = useState<QuestionsStatus | null>(null);
  const [likeTarget, setLikeTarget] = useState<LikeTarget | null>(null);

  useEffect(() => {
    profileApi
      .getQuestionsStatus()
      .then((res) => setQuestionsStatus(res.data))
      .catch(() => {});
  }, []);

  const searchBlocked = questionsStatus !== null && !questionsStatus.can_receive_likes;

  const runSearch = useCallback(
    async (p: number) => {
      if (searchBlocked) return;
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
      } catch {
        toast.error('Ошибка поиска');
      } finally {
        setLoading(false);
      }
    },
    [gender, minAge, maxAge, city, searchBlocked],
  );

  async function handleLike(profile: ProfilePreview) {
    try {
      const res = await profileApi.getUserQuestions(profile.keycloak_id);
      setLikeTarget({ profile, questions: res.data });
    } catch {
      toast.error('Не удалось получить вопросы пользователя');
    }
  }

  const showPagination = result && result.pagination.total_pages > 1 && !loading;

  return (
    <div className='flex-1 overflow-y-auto px-8 py-8'>
      <div className='mx-auto max-w-4xl'>
        <div className='mb-6'>
          <h1 className='font-onest text-primary text-2xl font-medium'>Классический поиск</h1>
          <p className='text-secondary mt-1 text-[14px]'>
            Найдите анкеты по основным параметрам. Доступно без ограничений.
          </p>
        </div>

        {searchBlocked && (
          <QuestionsRequiredBanner count={questionsStatus?.questions_count ?? 0} />
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
          loading={loading || searchBlocked}
          onSubmit={() => runSearch(1)}
        />

        {(loading || searched) && (
          <div className='mt-6'>
            {loading ? (
              <SearchSkeleton />
            ) : result && result.profiles.length > 0 ? (
              <>
                <p className='text-secondary mb-4 text-[13px]'>
                  Найдено {result.pagination.total_results}{' '}
                  {result.pagination.total_results === 1
                    ? 'анкета'
                    : result.pagination.total_results < 5
                      ? 'анкеты'
                      : 'анкет'}
                </p>
                <div className='grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3'>
                  {result.profiles.map((p, i) => (
                    <ProfileCard
                      key={`${p.keycloak_id}-${i}`}
                      profile={p}
                      onLike={() => handleLike(p)}
                      onView={() =>
                        navigate('/dashboard/users/' + p.keycloak_id, { state: { profile: p } })
                      }
                    />
                  ))}
                </div>
                {showPagination && (
                  <Pagination
                    current={result.pagination.current_page}
                    total={result.pagination.total_pages}
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

      {likeTarget && (
        <LikeWithAnswersModal
          targetUserId={likeTarget.profile.keycloak_id}
          targetDisplayName={likeTarget.profile.display_name}
          questions={likeTarget.questions}
          onClose={() => setLikeTarget(null)}
          onMatched={(matchId) => {
            setLikeTarget(null);
            navigate('/dashboard/matches', { state: { newMatchId: matchId } });
          }}
        />
      )}
    </div>
  );
}
