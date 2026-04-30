import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Zap, Lock, AlertCircle } from 'lucide-react';
import { searchApi, ProfileCard, SearchSkeleton } from '@/entities/search';
import type { SearchResponse, ProfilePreview } from '@/entities/search';
import { profileApi } from '@/entities/profile';
import type { QuestionsStatus, ProfileQuestions } from '@/entities/profile';
import { LikeWithAnswersModal } from '@/features/matching/ui/LikeWithAnswersModal';
import { Button } from '@/shared/uikit/Button';
import { toast } from '@/shared/toast/toast';

function formatUnlockTime(seconds?: number | null) {
  if (!seconds) return '';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 0) return `${h} ч ${m} мин`;
  return `${m} мин`;
}

function LockBanner({
  profilesViewed,
  timeUntilUnlock,
  dailyLimit,
}: {
  profilesViewed: number;
  timeUntilUnlock: number | null;
  dailyLimit: number;
}) {
  return (
    <div className='mb-6 flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-4'>
      <Lock size={18} className='mt-0.5 shrink-0 text-amber-600' strokeWidth={2} />
      <div>
        <p className='text-[14px] font-semibold text-amber-800'>
          Рекомендации временно недоступны
        </p>
        <p className='mt-0.5 text-[13px] text-amber-700'>
          Просмотрено {profilesViewed} из {dailyLimit} анкет.
          {timeUntilUnlock
            ? ` Разблокируется через ${formatUnlockTime(timeUntilUnlock)}.`
            : ''}
        </p>
      </div>
    </div>
  );
}

function QuestionsRequiredBanner({ count }: { count: number }) {
  const navigate = useNavigate();
  return (
    <div className='mb-6 flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-4'>
      <AlertCircle size={18} className='mt-0.5 shrink-0 text-amber-500' />
      <div className='flex-1'>
        <p className='text-[14px] font-medium text-amber-800'>
          Заполните вопросы для партнёра ({count}/5)
        </p>
        <p className='mt-0.5 text-[13px] text-amber-700'>
          Для AI-рекомендаций необходимо заполнить все 5 вопросов в профиле.
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

export function CupidonPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [loaded, setLoaded] = useState(false);
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
  const isLocked = result?.lock_info?.is_locked ?? false;

  const loadRecommendations = useCallback(async () => {
    if (searchBlocked || isLocked) return;
    setLoading(true);
    try {
      const res = await searchApi.recommendations();
      setResult(res.data);
      setLoaded(true);
    } catch {
      toast.error('Не удалось загрузить рекомендации');
    } finally {
      setLoading(false);
    }
  }, [searchBlocked, isLocked]);

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
          <h1 className='font-onest text-primary text-2xl font-medium'>Купидон</h1>
          <p className='text-secondary mt-1 text-[14px]'>
            AI-рекомендации на основе вашего профиля. До 100 просмотров в день.
          </p>
        </div>

        {searchBlocked && questionsStatus && (
          <QuestionsRequiredBanner count={questionsStatus.questions_count} />
        )}

        {!searchBlocked && result?.lock_info?.is_locked && (
          <LockBanner
            profilesViewed={result.lock_info.profiles_viewed}
            timeUntilUnlock={result.lock_info.time_until_unlock ?? null}
            dailyLimit={result.lock_info.daily_limit ?? 100}
          />
        )}

        {!loaded && !loading && !searchBlocked && !isLocked && (
          <div className='flex flex-col items-center gap-4 py-20'>
            <div className='bg-accent/15 flex h-16 w-16 items-center justify-center rounded-2xl'>
              <Zap size={28} className='text-accent' />
            </div>
            <p className='text-primary text-[15px] font-medium'>Умные рекомендации</p>
            <p className='text-muted text-center text-[13px]'>
              Алгоритм подберёт анкеты, которые наиболее подходят вам по интересам и предпочтениям.
              Входящие лайки показываются первыми.
            </p>
            <Button onClick={loadRecommendations}>
              <Zap size={15} />
              Показать рекомендации
            </Button>
          </div>
        )}

        {loading && <SearchSkeleton />}

        {loaded && !loading && result && !isLocked && (
          <>
            <div className='mb-4 flex items-center justify-between'>
              <p className='text-secondary text-[13px]'>
                Найдено {result.pagination.total_results} рекомендаций
                {result.sentiment_boost_applied && (
                  <span className='ml-1.5 rounded-full bg-violet-50 px-2 py-0.5 text-[11px] text-violet-600'>
                    AI-бустинг активен
                  </span>
                )}
              </p>
              {result.lock_info && (
                <span className='text-muted text-[12px]'>
                  Просмотрено: {result.lock_info.profiles_viewed}/{result.lock_info.daily_limit}
                </span>
              )}
            </div>

            {result.profiles.length === 0 ? (
              <div className='py-12 text-center'>
                <p className='text-primary text-[15px] font-medium'>Рекомендаций пока нет</p>
                <p className='text-muted mt-1 text-[13px]'>Заполните профиль подробнее</p>
              </div>
            ) : (
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
            )}

            <div className='mt-6 text-center'>
              <Button variant='secondary' onClick={loadRecommendations} disabled={loading}>
                Загрузить ещё
              </Button>
            </div>
          </>
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
