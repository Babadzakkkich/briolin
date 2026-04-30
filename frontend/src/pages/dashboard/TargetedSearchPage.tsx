import { useCallback, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle } from 'lucide-react';
import { searchApi, ProfileCard, SearchSkeleton } from '@/entities/search';
import type { SearchResponse, TargetedSearchRequest, ProfilePreview } from '@/entities/search';
import { profileApi } from '@/entities/profile';
import type { QuestionsStatus, ProfileQuestions } from '@/entities/profile';
import { LikeWithAnswersModal } from '@/features/matching/ui/LikeWithAnswersModal';
import { TargetedFilterForm } from '@/features/search/ui/TargetedFilterForm';
import { toast } from '@/shared/toast/toast';

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

export function TargetedSearchPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [result, setResult] = useState<SearchResponse | null>(null);

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
    async (filters: TargetedSearchRequest) => {
      if (searchBlocked) return;
      setLoading(true);
      try {
        const res = await searchApi.targeted(filters);
        setResult(res.data);
        setSearched(true);
      } catch {
        toast.error('Ошибка поиска');
      } finally {
        setLoading(false);
      }
    },
    [searchBlocked],
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
    <div className='flex-1 overflow-y-auto px-8 py-8'>
      <div className='mx-auto max-w-4xl'>
        <div className='mb-6'>
          <h1 className='font-onest text-primary text-2xl font-medium'>Таргетированный поиск</h1>
          <p className='text-secondary mt-1 text-[14px]'>
            Поиск с дополнительными фильтрами: образование, хобби, онлайн-статус.
          </p>
        </div>

        {searchBlocked && (
          <QuestionsRequiredBanner count={questionsStatus?.questions_count ?? 0} />
        )}

        <TargetedFilterForm loading={loading || searchBlocked} onSubmit={runSearch} />

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
