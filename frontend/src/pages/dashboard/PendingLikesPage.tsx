import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MapPin, Heart, X, MessageCircle } from 'lucide-react';
import { matchingApi } from '@/entities/matching';
import type { PendingLike, LikeAnswers } from '@/entities/matching';
import { profileApi } from '@/entities/profile';
import type { ProfileQuestions } from '@/entities/profile';
import { LikeWithAnswersModal } from '@/features/matching/ui/LikeWithAnswersModal';
import { AuthImage } from '@/shared/uikit/AuthImage';
import { Button } from '@/shared/uikit/Button';
import { Loader } from '@/shared/uikit/Loader';
import { toast } from '@/shared/toast/toast';

const QUESTION_KEYS: (keyof LikeAnswers)[] = [
  'question_1',
  'question_2',
  'question_3',
  'question_4',
  'question_5',
];

function AvatarFallback({ name }: { name: string }) {
  const initials = name
    .split(' ')
    .slice(0, 2)
    .map((w) => w[0] ?? '')
    .join('')
    .toUpperCase();
  return (
    <div className='bg-accent/15 text-accent flex h-full w-full items-center justify-center text-2xl font-semibold'>
      {initials || '?'}
    </div>
  );
}

function PendingLikeCard({
  like,
  onAccept,
  onDecline,
}: {
  like: PendingLike;
  onAccept: () => void;
  onDecline: () => void;
}) {
  const navigate = useNavigate();
  const hobbies = like.from_user_hobbies
    ? like.from_user_hobbies.split(',').map((h) => h.trim()).filter(Boolean)
    : [];

  return (
    <div className='rounded-2xl border border-[#F0E9E0] bg-white'>
      <div className='flex gap-4 p-5'>
        <div className='relative h-20 w-20 shrink-0 overflow-hidden rounded-2xl'>
          {like.from_user_avatar ? (
            <AuthImage
              src={like.from_user_avatar}
              alt={like.from_user_display_name}
              className='h-full w-full object-cover'
              fallback={<AvatarFallback name={like.from_user_display_name} />}
            />
          ) : (
            <AvatarFallback name={like.from_user_display_name} />
          )}
        </div>
        <div className='min-w-0 flex-1'>
          <p className='font-onest text-primary text-[16px] font-medium'>
            {like.from_user_display_name}, {like.from_user_age}
          </p>
          <p className='text-secondary mt-0.5 flex items-center gap-1 text-[13px]'>
            <MapPin size={12} className='shrink-0' />
            {like.from_user_city}
          </p>
          {like.from_user_about_me && (
            <p className='text-secondary mt-2 text-[13px] leading-relaxed line-clamp-2'>
              {like.from_user_about_me}
            </p>
          )}
          {hobbies.length > 0 && (
            <div className='mt-2 flex flex-wrap gap-1'>
              {hobbies.slice(0, 4).map((h, i) => (
                <span key={i} className='bg-surface text-muted rounded-lg px-2 py-0.5 text-[11px]'>
                  {h}
                </span>
              ))}
            </div>
          )}
          {like.from_user_red_flags && like.from_user_red_flags.length > 0 && (
            <div className='mt-2 flex flex-wrap gap-1'>
              {like.from_user_red_flags.map((flag, i) => (
                <span key={i} className='rounded-lg bg-red-50 px-2 py-0.5 text-[11px] text-red-600'>
                  🚩 {flag}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className='border-t border-[#F0E9E0] px-5 py-4'>
        <p className='text-secondary mb-3 text-[12px] font-medium uppercase tracking-wide'>
          Ответы на ваши вопросы
        </p>
        <div className='flex flex-col gap-2'>
          {QUESTION_KEYS.map((key, i) => (
            <div key={key}>
              <p className='text-muted text-[11px]'>{like.questions[key] || `Вопрос ${i + 1}`}</p>
              <p className='text-primary mt-0.5 text-[13px]'>{like.answers[key] || '—'}</p>
            </div>
          ))}
        </div>
      </div>

      <div className='flex gap-2 border-t border-[#F0E9E0] px-5 py-4'>
        <Button
          variant='secondary'
          size='sm'
          onClick={() =>
            navigate('/dashboard/users/' + like.from_user_id, {
              state: {
                profile: {
                  keycloak_id: like.from_user_id,
                  display_name: like.from_user_display_name,
                  age: like.from_user_age,
                  city: like.from_user_city,
                  avatar_url: like.from_user_avatar,
                  about_me: like.from_user_about_me,
                  hobbies: like.from_user_hobbies,
                  partner_preferences: like.from_user_partner_preferences,
                  red_flags: like.from_user_red_flags,
                },
              },
            })
          }
          className='gap-1.5'
        >
          <MessageCircle size={13} />
          Профиль
        </Button>
        <Button
          variant='destructive'
          size='sm'
          onClick={onDecline}
          className='gap-1.5'
        >
          <X size={13} />
          Отклонить
        </Button>
        <Button size='sm' onClick={onAccept} className='flex-1 gap-1.5'>
          <Heart size={13} />
          Ответный лайк
        </Button>
      </div>
    </div>
  );
}

interface ReverseLikeTarget {
  like: PendingLike;
  questions: ProfileQuestions;
}

export function PendingLikesPage() {
  const navigate = useNavigate();
  const [likes, setLikes] = useState<PendingLike[]>([]);
  const [loading, setLoading] = useState(true);
  const [reverseLikeTarget, setReverseLikeTarget] = useState<ReverseLikeTarget | null>(null);

  useEffect(() => {
    matchingApi
      .getPendingLikes()
      .then((res) => setLikes(res.data))
      .catch(() => toast.error('Не удалось загрузить входящие лайки'))
      .finally(() => setLoading(false));
  }, []);

  async function handleAccept(like: PendingLike) {
    try {
      const res = await profileApi.getUserQuestions(like.from_user_id);
      setReverseLikeTarget({ like, questions: res.data });
    } catch {
      toast.error('Не удалось получить вопросы пользователя');
    }
  }

  async function handleDecline(like: PendingLike) {
    try {
      await matchingApi.declineLike(like.from_user_id);
      setLikes((prev) => prev.filter((l) => l.from_user_id !== like.from_user_id));
      toast.success('Лайк отклонён');
    } catch {
      toast.error('Ошибка при отклонении лайка');
    }
  }

  if (loading) return <Loader center label='Загружаем входящие лайки...' />;

  return (
    <div className='flex-1 overflow-y-auto px-8 py-8'>
      <div className='mx-auto max-w-2xl'>
        <div className='mb-6'>
          <h1 className='font-onest text-primary text-2xl font-medium'>Входящие лайки</h1>
          <p className='text-secondary mt-1 text-[14px]'>
            {likes.length > 0
              ? `${likes.length} ${likes.length === 1 ? 'человек' : likes.length < 5 ? 'человека' : 'человек'} хотят с вами познакомиться`
              : 'Пока никто не поставил вам лайк'}
          </p>
        </div>

        {likes.length === 0 ? (
          <div className='flex flex-col items-center gap-3 py-20'>
            <div className='bg-surface flex h-14 w-14 items-center justify-center rounded-2xl'>
              <Heart size={24} className='text-muted' strokeWidth={1.5} />
            </div>
            <p className='text-primary text-[15px] font-medium'>Входящих лайков нет</p>
            <p className='text-muted text-[13px]'>Появляйтесь в поиске и заполните профиль</p>
          </div>
        ) : (
          <div className='flex flex-col gap-4'>
            {likes.map((like) => (
              <PendingLikeCard
                key={like.from_user_id}
                like={like}
                onAccept={() => handleAccept(like)}
                onDecline={() => handleDecline(like)}
              />
            ))}
          </div>
        )}
      </div>

      {reverseLikeTarget && (
        <LikeWithAnswersModal
          targetUserId={reverseLikeTarget.like.from_user_id}
          targetDisplayName={reverseLikeTarget.like.from_user_display_name}
          questions={reverseLikeTarget.questions}
          onClose={() => setReverseLikeTarget(null)}
          onMatched={(matchId) => {
            setLikes((prev) =>
              prev.filter((l) => l.from_user_id !== reverseLikeTarget.like.from_user_id),
            );
            setReverseLikeTarget(null);
            navigate('/dashboard/matches', { state: { newMatchId: matchId } });
          }}
        />
      )}
    </div>
  );
}
