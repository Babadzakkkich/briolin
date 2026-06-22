import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useProfileStore } from '@/entities/profile';
import { chatApi } from '@/entities/chat';
import { matchingApi } from '@/entities/matching';
import {
  Briefcase,
  Dice5,
  MessageCircle,
  Search,
  Zap,
  ArrowRight,
  type LucideIcon,
} from 'lucide-react';

interface FeatureCardProps {
  to: string;
  icon: LucideIcon;
  title: string;
  description: string;
  accent?: boolean;
}

function FeatureCard({ to, icon: Icon, title, description, accent }: FeatureCardProps) {
  return (
    <Link to={to}>
      <div
        className={[
          'group flex h-full flex-col justify-between rounded-2xl p-5 transition-all duration-150',
          accent
            ? 'bg-accent hover:bg-accent-hover text-white'
            : 'hover:border-border border border-transparent bg-white',
        ].join(' ')}
      >
        <div
          className={[
            'mb-8 flex h-10 w-10 items-center justify-center rounded-xl',
            accent ? 'bg-white/20' : 'bg-surface',
          ].join(' ')}
        >
          <Icon size={20} className={accent ? 'text-white' : 'text-accent'} strokeWidth={2.2} />
        </div>
        <div>
          <div className='flex items-center justify-between'>
            <span
              className={[
                'text-[15px] font-semibold',
                accent ? 'text-white' : 'text-primary',
              ].join(' ')}
            >
              {title}
            </span>
            <ArrowRight
              size={16}
              strokeWidth={2.2}
              className={[
                'transition-transform duration-150 group-hover:translate-x-0.5',
                accent ? 'text-white/70' : 'text-muted',
              ].join(' ')}
            />
          </div>
          <p
            className={['mt-1 text-[13px]', accent ? 'text-white/70' : 'text-secondary'].join(
              ' ',
            )}
          >
            {description}
          </p>
        </div>
      </div>
    </Link>
  );
}

function StatCard({
  label,
  value,
  loading,
}: {
  label: string;
  value: number;
  loading: boolean;
}) {
  return (
    <div className='rounded-2xl bg-white px-4 py-4'>
      <p className='text-secondary truncate text-[11px]'>{label}</p>
      {loading ? (
        <div className='bg-surface mt-1.5 h-7 w-10 animate-pulse rounded-lg' />
      ) : (
        <p className='text-primary mt-0.5 text-2xl font-semibold'>{value}</p>
      )}
    </div>
  );
}

export function DashboardHomePage() {
  const { firstName, lastName } = useProfileStore();
  const [stats, setStats] = useState({ unread: 0, matches: 0, likes: 0 });
  const [statsLoading, setStatsLoading] = useState(true);

  useEffect(() => {
    Promise.allSettled([
      chatApi.getChats({ limit: 50 }),
      matchingApi.getMatches(),
      matchingApi.getPendingLikes(),
    ]).then(([chatsResult, matchesResult, likesResult]) => {
      setStats({
        unread:
          chatsResult.status === 'fulfilled'
            ? chatsResult.value.chats.reduce((s, c) => s + c.unread_count, 0)
            : 0,
        matches: matchesResult.status === 'fulfilled' ? matchesResult.value.data.length : 0,
        likes: likesResult.status === 'fulfilled' ? likesResult.value.data.length : 0,
      });
      setStatsLoading(false);
    });
  }, []);

  const greeting = () => {
    const hour = new Date().getHours();
    if (hour < 6) return 'Доброй ночи';
    if (hour < 12) return 'Доброе утро';
    if (hour < 18) return 'Добрый день';
    return 'Добрый вечер';
  };

  return (
    <div className='flex-1 overflow-y-auto px-4 py-8 md:px-8 md:py-10'>
      <div className='mx-auto max-w-3xl'>
        <div className='mb-8'>
          <p className='text-secondary text-sm'>{greeting()}</p>
          {firstName ? (
            <h1 className='font-onest text-primary mt-0.5 text-3xl font-medium'>
              {lastName ? `${firstName} ${lastName}` : firstName}
            </h1>
          ) : (
            <div className='bg-surface mt-2 h-9 w-48 animate-pulse rounded-xl' />
          )}
        </div>

        <div className='mb-6 grid grid-cols-3 gap-3'>
          <StatCard label='Непрочитано' value={stats.unread} loading={statsLoading} />
          <StatCard label='Матчей' value={stats.matches} loading={statsLoading} />
          <StatCard label='Новых лайков' value={stats.likes} loading={statsLoading} />
        </div>

        <div className='grid grid-cols-2 gap-3'>
          <FeatureCard
            to='/dashboard/cupidon'
            icon={Zap}
            title='Купидон'
            description='Найди свою пару'
            accent
          />
          <FeatureCard
            to='/dashboard/messages'
            icon={MessageCircle}
            title='Сообщения'
            description='Общайся с другими'
          />
          <FeatureCard
            to='/dashboard/search/classic'
            icon={Search}
            title='Поиск'
            description='Ищи по параметрам'
          />
          <FeatureCard
            to='/dashboard/services'
            icon={Briefcase}
            title='Услуги'
            description='Дополнительные возможности'
          />
          <FeatureCard
            to='/dashboard/fortune'
            icon={Dice5}
            title='Фортуна'
            description='Случайная встреча'
          />
        </div>
      </div>
    </div>
  );
}
