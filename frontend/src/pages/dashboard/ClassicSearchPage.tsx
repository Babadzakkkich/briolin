import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, AlertCircle, ChevronDown } from 'lucide-react';
import { searchApi, ProfileCard, SearchSkeleton } from '@/entities/search';
import type { ProfilePreview } from '@/entities/search';
import { profileApi } from '@/entities/profile';
import type { QuestionsStatus, ProfileQuestions } from '@/entities/profile';
import { LikeWithAnswersModal } from '@/features/matching/ui/LikeWithAnswersModal';
import { ClassicFilterBar } from '@/features/search/ui/ClassicFilterBar';
import { Button } from '@/shared/uikit/Button';
import { toast } from '@/shared/toast/toast';

const SESSION_KEY = 'classic-search-state';

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
        className='shrink-0 cursor-pointer rounded-xl bg-amber-100 px-3 py-1.5 text-[13px] font-medium text-amber-800 transition-colors hover:bg-amber-200'
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

interface SavedState {
  gender: string | null;
  minAge: string;
  maxAge: string;
  city: string;
  profiles: ProfilePreview[];
  totalResults: number;
  hasMore: boolean;
  page: number;
}

export function ClassicSearchPage() {
  const navigate = useNavigate();
  const [gender, setGender] = useState<string | undefined>(undefined);
  const [minAge, setMinAge] = useState('');
  const [maxAge, setMaxAge] = useState('');
  const [city, setCity] = useState('');

  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [searched, setSearched] = useState(false);
  const [profiles, setProfiles] = useState<ProfilePreview[]>([]);
  const [totalResults, setTotalResults] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [page, setPage] = useState(1);

  const [questionsStatus, setQuestionsStatus] = useState<QuestionsStatus | null>(null);
  const [likeTarget, setLikeTarget] = useState<LikeTarget | null>(null);

  // Restore state from sessionStorage on mount
  useEffect(() => {
    const raw = sessionStorage.getItem(SESSION_KEY);
    if (!raw) return;
    try {
      const s: SavedState = JSON.parse(raw);
      setGender(s.gender ?? undefined);
      setMinAge(s.minAge || '');
      setMaxAge(s.maxAge || '');
      setCity(s.city || '');
      if (s.profiles?.length > 0) {
        setProfiles(s.profiles);
        setTotalResults(s.totalResults || 0);
        setHasMore(s.hasMore || false);
        setPage(s.page || 1);
        setSearched(true);
      }
    } catch {}
  }, []);

  useEffect(() => {
    profileApi
      .getQuestionsStatus()
      .then((res) => setQuestionsStatus(res.data))
      .catch(() => {});
  }, []);

  const searchBlocked = questionsStatus !== null && !questionsStatus.can_receive_likes;

  const runSearch = useCallback(
    async (p: number, append = false) => {
      if (searchBlocked) return;
      if (append) setLoadingMore(true);
      else setLoading(true);
      try {
        const res = await searchApi.classic({
          gender,
          min_age: minAge ? Number(minAge) : undefined,
          max_age: maxAge ? Number(maxAge) : undefined,
          city: city.trim() || undefined,
          page: p,
          limit: 12,
        });
        const newProfiles = append
          ? (prev: ProfilePreview[]) => [...prev, ...res.data.profiles]
          : res.data.profiles;
        const nextHasMore = p < res.data.pagination.total_pages;

        setProfiles(newProfiles);
        setTotalResults(res.data.pagination.total_results);
        setHasMore(nextHasMore);
        setPage(p);
        setSearched(true);

        // Persist to sessionStorage (only for fresh searches, not load-more)
        if (!append) {
          const state: SavedState = {
            gender: gender ?? null,
            minAge,
            maxAge,
            city,
            profiles: res.data.profiles,
            totalResults: res.data.pagination.total_results,
            hasMore: nextHasMore,
            page: p,
          };
          sessionStorage.setItem(SESSION_KEY, JSON.stringify(state));
        }
      } catch {
        toast.error('Ошибка поиска');
      } finally {
        setLoading(false);
        setLoadingMore(false);
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

  return (
    <div className='flex-1 overflow-y-auto px-4 py-8 md:px-8'>
      <div className='mx-auto max-w-4xl'>
        <div className='mb-6'>
          <h1 className='font-onest text-primary text-2xl font-medium'>Классический поиск</h1>
          <p className='text-secondary mt-1 text-[14px]'>
            Найдите анкеты по основным параметрам. Доступно без ограничений.
          </p>
        </div>

        {searchBlocked && <QuestionsRequiredBanner count={questionsStatus?.questions_count ?? 0} />}

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
            ) : profiles.length > 0 ? (
              <>
                <p className='text-secondary mb-4 text-[13px]'>
                  Найдено {totalResults}{' '}
                  {totalResults === 1 ? 'анкета' : totalResults < 5 ? 'анкеты' : 'анкет'}
                </p>
                <div className='grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3'>
                  {profiles.map((p, i) => (
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

                {hasMore && (
                  <div className='mt-6 flex justify-center'>
                    <Button
                      variant='secondary'
                      onClick={() => runSearch(page + 1, true)}
                      disabled={loadingMore}
                      className='gap-2'
                    >
                      <ChevronDown size={16} />
                      {loadingMore ? 'Загружаем...' : 'Загрузить ещё'}
                    </Button>
                  </div>
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
