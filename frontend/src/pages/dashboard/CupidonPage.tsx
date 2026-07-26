import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Zap, Lock, AlertCircle, X, Heart } from 'lucide-react';
import { searchApi } from '@/entities/search';
import type { SearchLockInfo, ProfilePreview } from '@/entities/search';
import { matchingApi } from '@/entities/matching';
import { profileApi } from '@/entities/profile';
import type { QuestionsStatus, ProfileQuestions } from '@/entities/profile';
import { LikeWithAnswersModal } from '@/widgets/matching/ui/LikeWithAnswersModal';
import {
  SwipeCard,
  type SwipeCardHandle,
  type SwipeDirection,
} from '@/widgets/matching/ui/SwipeCard';
import { Button } from '@/shared/uikit/Button';
import { Loader } from '@/shared/uikit/Loader';
import { toast } from '@/shared/toast/toast';

const LOW_WATERMARK = 3;
const MAX_EMPTY_FETCHES = 3;

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
        <p className='text-[14px] font-semibold text-amber-800'>Рекомендации временно недоступны</p>
        <p className='mt-0.5 text-[13px] text-amber-700'>
          Просмотрено {profilesViewed} из {dailyLimit} анкет.
          {timeUntilUnlock ? ` Разблокируется через ${formatUnlockTime(timeUntilUnlock)}.` : ''}
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
        className='shrink-0 cursor-pointer rounded-xl bg-amber-100 px-3 py-1.5 text-[13px] font-medium text-amber-800 transition-colors hover:bg-amber-200'
      >
        Перейти
      </button>
    </div>
  );
}

function DeckLoading({ label, absolute }: { label: string; absolute?: boolean }) {
  return (
    <div
      className={[
        'border-border flex items-center justify-center rounded-3xl border bg-white',
        absolute ? 'absolute inset-0' : 'mx-auto aspect-[3/4] w-full max-w-sm',
      ].join(' ')}
    >
      <Loader label={label} />
    </div>
  );
}

function EmptyDeckState({ onRetry }: { onRetry: () => void }) {
  return (
    <div className='border-border absolute inset-0 flex flex-col items-center justify-center gap-3 rounded-3xl border border-dashed bg-white p-6 text-center'>
      <div className='bg-accent/15 flex h-14 w-14 items-center justify-center rounded-2xl'>
        <Zap size={24} className='text-accent' />
      </div>
      <p className='text-primary text-[15px] font-medium'>Анкеты закончились</p>
      <p className='text-muted text-[13px]'>Загляните позже — мы подберём новые анкеты</p>
      <Button variant='secondary' onClick={onRetry}>
        Обновить
      </Button>
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
  const [loadingMore, setLoadingMore] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [queue, setQueue] = useState<ProfilePreview[]>([]);
  const [exhausted, setExhausted] = useState(false);
  const [lockInfo, setLockInfo] = useState<SearchLockInfo | null>(null);
  const [questionsStatus, setQuestionsStatus] = useState<QuestionsStatus | null>(null);
  const [likeTarget, setLikeTarget] = useState<LikeTarget | null>(null);
  const activeCardRef = useRef<SwipeCardHandle>(null);
  const seenIds = useRef<Set<string>>(new Set());
  const pageRef = useRef(1);
  const totalPagesRef = useRef(1);

  useEffect(() => {
    profileApi
      .getQuestionsStatus()
      .then((res) => setQuestionsStatus(res.data))
      .catch(() => {});
  }, []);

  const searchBlocked = questionsStatus !== null && !questionsStatus.can_receive_likes;
  const isLocked = lockInfo?.is_locked ?? false;

  const loadRecommendations = useCallback(async () => {
    if (searchBlocked) return;
    setLoading(true);
    setExhausted(false);
    try {
      const res = await searchApi.recommendations();
      seenIds.current = new Set(res.data.profiles.map((p) => p.keycloak_id));
      setQueue(res.data.profiles);
      pageRef.current = 1;
      totalPagesRef.current = res.data.pagination.total_pages;
      setLockInfo(res.data.lock_info ?? null);
      setLoaded(true);
    } catch {
      toast.error('Не удалось загрузить рекомендации');
    } finally {
      setLoading(false);
    }
  }, [searchBlocked]);

  const fetchMore = useCallback(async () => {
    if (loadingMore || isLocked) return;
    setLoadingMore(true);
    try {
      // Когда страницы заканчиваются, начинаем заново — рекомендательный API
      // не отдаёт повторно уже лайкнутые/пропущенные анкеты, поэтому это
      // ведёт себя как бесконечная лента, а не как тупик. Перебираем попытки
      // внутри одного вызова — иначе при "пустом" ответе никто не повторит
      // запрос, если в очереди не изменилось ничего, что могло бы перезапустить эффект.
      for (let attempt = 0; attempt < MAX_EMPTY_FETCHES; attempt++) {
        const nextPage = pageRef.current < totalPagesRef.current ? pageRef.current + 1 : 1;
        const res = await searchApi.recommendations({ page: nextPage });
        const fresh = res.data.profiles.filter((p) => !seenIds.current.has(p.keycloak_id));
        fresh.forEach((p) => seenIds.current.add(p.keycloak_id));
        pageRef.current = nextPage;
        totalPagesRef.current = res.data.pagination.total_pages;
        if (res.data.lock_info) setLockInfo(res.data.lock_info);

        if (res.data.lock_info?.is_locked) return;

        if (fresh.length > 0) {
          setQueue((q) => [...q, ...fresh]);
          return;
        }
      }
      setExhausted(true);
    } catch {
      // фоновая подгрузка — без тоста, чтобы не мешать просмотру
    } finally {
      setLoadingMore(false);
    }
  }, [loadingMore, isLocked]);

  useEffect(() => {
    if (loaded && !isLocked && !exhausted && queue.length <= LOW_WATERMARK) {
      fetchMore();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loaded, isLocked, exhausted, queue.length]);

  function removeFromQueue(keycloakId: string) {
    setQueue((q) => q.filter((p) => p.keycloak_id !== keycloakId));
  }

  function handleSwiped(direction: SwipeDirection, profile: ProfilePreview) {
    if (direction === 'left') {
      matchingApi.dislike(profile.keycloak_id).catch(() => {});
      removeFromQueue(profile.keycloak_id);
      return;
    }
    profileApi
      .getUserQuestions(profile.keycloak_id)
      .then((res) => setLikeTarget({ profile, questions: res.data }))
      .catch(() => toast.error('Не удалось получить вопросы пользователя'))
      .finally(() => removeFromQueue(profile.keycloak_id));
  }

  return (
    <div className='flex-1 overflow-y-auto px-4 py-6 md:px-8 md:py-8'>
      <div className='mx-auto max-w-xl'>
        <div className='mb-6'>
          <h1 className='font-onest text-primary text-2xl font-medium'>Купидон</h1>
          <p className='text-secondary mt-1 text-[14px]'>
            Свайпайте анкеты — вправо лайк, влево пропустить.
          </p>
        </div>

        {searchBlocked && questionsStatus && (
          <QuestionsRequiredBanner count={questionsStatus.questions_count} />
        )}

        {!searchBlocked && isLocked && lockInfo && (
          <LockBanner
            profilesViewed={lockInfo.profiles_viewed}
            timeUntilUnlock={lockInfo.time_until_unlock ?? null}
            dailyLimit={lockInfo.daily_limit ?? 100}
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
              Смотрите анкеты по одной и сразу решайте — лайк или пропустить.
            </p>
            <Button onClick={loadRecommendations}>
              <Zap size={15} />
              Показать рекомендации
            </Button>
          </div>
        )}

        {loading && <DeckLoading label='Загружаем анкеты...' />}

        {loaded && !loading && !searchBlocked && !isLocked && (
          <>
            <div className='mb-4 flex items-center justify-center'>
              {lockInfo && (
                <span className='text-muted text-[12px]'>
                  Просмотрено: {lockInfo.profiles_viewed}/{lockInfo.daily_limit ?? 100}
                </span>
              )}
            </div>

            <div className='relative mx-auto aspect-[3/4] w-full max-w-sm'>
              {queue.length === 0 ? (
                exhausted ? (
                  <EmptyDeckState onRetry={loadRecommendations} />
                ) : (
                  <DeckLoading label='Подбираем анкеты...' absolute />
                )
              ) : (
                queue
                  .slice(0, 3)
                  .map((profile, i) => (
                    <SwipeCard
                      key={profile.keycloak_id}
                      ref={i === 0 ? activeCardRef : undefined}
                      profile={profile}
                      active={i === 0}
                      stackIndex={i}
                      onSwiped={handleSwiped}
                      onInfo={() =>
                        navigate('/dashboard/users/' + profile.keycloak_id, { state: { profile } })
                      }
                    />
                  ))
              )}
            </div>

            <div className='mt-6 flex items-center justify-center gap-6'>
              <button
                onClick={() => activeCardRef.current?.swipe('left')}
                disabled={queue.length === 0}
                className='border-border text-secondary flex h-14 w-14 items-center justify-center rounded-full border bg-white transition-transform active:scale-90 disabled:opacity-40'
              >
                <X size={24} strokeWidth={2.5} />
              </button>
              <button
                onClick={() => activeCardRef.current?.swipe('right')}
                disabled={queue.length === 0}
                className='bg-accent flex h-16 w-16 items-center justify-center rounded-full text-white transition-transform active:scale-90 disabled:opacity-40'
              >
                <Heart size={26} strokeWidth={2.2} fill='currentColor' />
              </button>
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
