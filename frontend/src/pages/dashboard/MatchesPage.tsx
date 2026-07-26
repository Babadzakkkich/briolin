import { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { MessageCircle, Heart, Users } from 'lucide-react';
import { matchingApi } from '@/entities/matching';
import type { Match } from '@/entities/matching';
import { chatApi } from '@/entities/chat';
import { AuthImage } from '@/shared/uikit/AuthImage';
import { Button } from '@/shared/uikit/Button';
import { Loader } from '@/shared/uikit/Loader';
import { toast } from '@/shared/toast/toast';

function AvatarFallback({ name }: { name: string }) {
  const initials = name
    .split(' ')
    .slice(0, 2)
    .map((w) => w[0] ?? '')
    .join('')
    .toUpperCase();
  return (
    <div className='bg-accent/15 text-accent flex h-full w-full items-center justify-center text-lg font-semibold'>
      {initials || '?'}
    </div>
  );
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

function MatchCard({ match }: { match: Match }) {
  const navigate = useNavigate();
  const [starting, setStarting] = useState(false);

  async function handleMessage() {
    setStarting(true);
    try {
      const chat = await chatApi.createDirectChat(match.partner.keycloak_id);
      navigate('/dashboard/messages', { state: { chatId: chat.id } });
    } catch {
      toast.error('Не удалось открыть чат');
    } finally {
      setStarting(false);
    }
  }

  return (
    <div className='flex items-center gap-4 rounded-2xl border border-[#F0E9E0] bg-white p-4'>
      <div className='relative h-14 w-14 shrink-0 overflow-hidden rounded-2xl'>
        {match.partner.avatar_url ? (
          <AuthImage
            src={match.partner.avatar_url}
            alt={match.partner.display_name}
            className='h-full w-full object-cover'
            fallback={<AvatarFallback name={match.partner.display_name} />}
          />
        ) : (
          <AvatarFallback name={match.partner.display_name} />
        )}
      </div>
      <div className='min-w-0 flex-1'>
        <p className='text-primary text-[15px] font-semibold'>{match.partner.display_name}</p>
        <p className='text-muted mt-0.5 text-[12px]'>Мэтч {formatDate(match.matched_at)}</p>
      </div>
      <Button size='sm' onClick={handleMessage} disabled={starting} className='shrink-0 gap-1.5'>
        <MessageCircle size={14} />
        {starting ? '...' : 'Написать'}
      </Button>
    </div>
  );
}

export function MatchesPage() {
  const location = useLocation();
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);

  const newMatchId = location.state?.newMatchId as number | undefined;

  useEffect(() => {
    matchingApi
      .getMatches()
      .then((res) => setMatches(res.data))
      .catch(() => toast.error('Не удалось загрузить мэтчи'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Loader center label='Загружаем мэтчи...' />;

  return (
    <div className='flex-1 overflow-y-auto px-4 py-8 md:px-8'>
      <div className='mx-auto max-w-2xl'>
        <div className='mb-6'>
          <h1 className='font-onest text-primary text-2xl font-medium'>мэтчи</h1>
          <p className='text-secondary mt-1 text-[14px]'>
            {matches.length > 0
              ? `${matches.length} взаимных симпатий`
              : 'Взаимных симпатий пока нет'}
          </p>
        </div>

        {newMatchId && (
          <div className='mb-4 flex items-center gap-3 rounded-2xl border border-green-200 bg-green-50 p-4'>
            <Heart size={18} className='shrink-0 text-green-600' />
            <p className='text-[14px] font-medium text-green-800'>
              Поздравляем с новым мэтчем! 🎉 Теперь вы можете написать друг другу.
            </p>
          </div>
        )}

        {matches.length === 0 ? (
          <div className='flex flex-col items-center gap-3 py-20'>
            <div className='bg-surface flex h-14 w-14 items-center justify-center rounded-2xl'>
              <Users size={24} className='text-muted' strokeWidth={1.5} />
            </div>
            <p className='text-primary text-[15px] font-medium'>мэтчей пока нет</p>
            <p className='text-muted text-center text-[13px]'>
              Заполните профиль и ищите анкеты — взаимные лайки создают мэтч
            </p>
          </div>
        ) : (
          <div className='flex flex-col gap-3'>
            {matches.map((match) => (
              <MatchCard key={match.match_id} match={match} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
