import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { profileApi, useProfileStore } from '@/entities/profile';
import type { ProfileResponse } from '@/entities/profile';
import { chatApi, ChatAvatar, getChatAvatarUrl, getChatDisplayName } from '@/entities/chat';
import type { Chat } from '@/entities/chat';
import { matchingApi } from '@/entities/matching';
import type { Match } from '@/entities/matching';
import { useAuthStore } from '@/entities/session';
import {
  Briefcase,
  Dice5,
  Heart,
  MessageCircle,
  Search,
  UserRound,
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
              className={['text-[15px] font-semibold', accent ? 'text-white' : 'text-primary'].join(
                ' ',
              )}
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
            className={['mt-1 text-[13px]', accent ? 'text-white/70' : 'text-secondary'].join(' ')}
          >
            {description}
          </p>
        </div>
      </div>
    </Link>
  );
}

function StatCard({ label, value, loading }: { label: string; value: number; loading: boolean }) {
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

interface NextAction {
  icon: LucideIcon;
  title: string;
  description: string;
  label: string;
  to: string;
  state?: { chatId?: string };
}

interface ProfileProgress {
  percentage: number;
  missing: string | null;
}

function getProfileProgress(
  profile: ProfileResponse | null,
  questionsComplete?: boolean,
): ProfileProgress | null {
  if (!profile) return null;

  const questions = profile.questions;
  const checks = [
    {
      complete: Boolean(profile.basic.avatar_url || profile.basic.thumbnail_url),
      label: 'фотографию',
    },
    {
      complete: Boolean(
        profile.basic.first_name.trim() &&
        profile.basic.last_name.trim() &&
        profile.basic.city.trim(),
      ),
      label: 'основную информацию',
    },
    {
      complete: Boolean(profile.detailed?.about_me?.trim()),
      label: 'рассказ о себе',
    },
    {
      complete: Boolean(profile.detailed?.education?.trim() && profile.detailed?.hobbies?.trim()),
      label: 'образование и интересы',
    },
    {
      complete: Boolean(profile.detailed?.partner_preferences?.trim()),
      label: 'пожелания к партнёру',
    },
    {
      complete:
        questionsComplete ??
        Boolean(
          questions &&
          [
            questions.question_1,
            questions.question_2,
            questions.question_3,
            questions.question_4,
            questions.question_5,
          ].every((answer) => answer?.trim()),
        ),
      label: 'вопросы для партнёра',
    },
  ];

  const completed = checks.filter((item) => item.complete).length;
  return {
    percentage: Math.round((completed / checks.length) * 100),
    missing: checks.find((item) => !item.complete)?.label ?? null,
  };
}

function formatRecentDate(date: string) {
  const value = new Date(date);
  const today = new Date();
  if (value.toDateString() === today.toDateString()) {
    return value.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
  }
  return value.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
}

function NextActionCard({ action, loading }: { action: NextAction | null; loading: boolean }) {
  if (loading || !action) {
    return (
      <div className='mb-6 animate-pulse rounded-2xl bg-white p-5' role='status'>
        <div className='flex items-center gap-4'>
          <div className='bg-surface h-11 w-11 shrink-0 rounded-xl' />
          <div className='flex-1 space-y-2'>
            <div className='bg-surface h-4 w-40 rounded-lg' />
            <div className='bg-surface h-3 w-64 max-w-full rounded-lg' />
          </div>
          <div className='bg-surface hidden h-9 w-24 rounded-xl sm:block' />
        </div>
        <span className='sr-only'>Подбираем следующее действие</span>
      </div>
    );
  }

  const Icon = action.icon;

  return (
    <div className='bg-accent mb-6 overflow-hidden rounded-2xl p-5 text-white'>
      <div className='flex flex-col gap-4 sm:flex-row sm:items-center'>
        <div className='flex min-w-0 flex-1 items-center gap-4'>
          <div className='flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white/15'>
            <Icon size={20} strokeWidth={2.2} />
          </div>
          <div className='min-w-0'>
            <p className='text-[11px] font-semibold text-white/65'>Что дальше?</p>
            <p className='mt-0.2 text-[15px] font-semibold'>{action.title}</p>
            <p className='mt-0.2 text-[12px] leading-5 text-white/75'>{action.description}</p>
          </div>
        </div>
        <Link
          to={action.to}
          state={action.state}
          className='group text-accent flex shrink-0 items-center justify-center gap-2 rounded-xl bg-white px-4 py-2.5 text-[12px] font-semibold transition-colors hover:bg-white/90'
        >
          {action.label}
          <ArrowRight
            size={14}
            className='transition-transform group-hover:translate-x-0.5'
            strokeWidth={2.4}
          />
        </Link>
      </div>
    </div>
  );
}

function RecentActivity({
  chats,
  matches,
  keycloakId,
}: {
  chats: Chat[];
  matches: Match[];
  keycloakId: string | null;
}) {
  const recentChats = [...chats]
    .sort((left, right) => Date.parse(right.updated_at) - Date.parse(left.updated_at))
    .slice(0, 3);

  if (recentChats.length > 0) {
    return (
      <div className='mb-6 rounded-2xl bg-white p-4'>
        <div className='mb-2 flex items-center justify-between'>
          <p className='text-primary text-[13px] font-semibold'>Недавние диалоги</p>
          <Link
            to='/dashboard/messages'
            className='text-accent hover:text-accent-hover text-[12px] transition-colors'
          >
            Все сообщения
          </Link>
        </div>
        <div className='flex flex-col'>
          {recentChats.map((chat) => {
            const name = getChatDisplayName(chat, keycloakId);
            return (
              <Link
                key={chat.id}
                to='/dashboard/messages'
                state={{ chatId: chat.id }}
                className='hover:bg-surface -mx-2 flex items-center gap-3 rounded-xl px-2 py-2 transition-colors'
              >
                <ChatAvatar name={name} src={getChatAvatarUrl(chat, keycloakId)} size='sm' />
                <div className='min-w-0 flex-1'>
                  <p className='text-primary truncate text-[13px] font-medium'>{name}</p>
                  <p className='text-muted truncate text-[11px]'>
                    {chat.last_message?.content ?? 'Откройте диалог'}
                  </p>
                </div>
                <div className='flex shrink-0 items-center gap-2'>
                  {chat.unread_count > 0 && (
                    <span className='bg-accent flex min-w-5 items-center justify-center rounded-full px-1.5 py-0.5 text-[10px] text-white'>
                      {chat.unread_count}
                    </span>
                  )}
                  <span className='text-muted text-[10px]'>
                    {formatRecentDate(chat.last_message?.created_at ?? chat.updated_at)}
                  </span>
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    );
  }

  const recentMatches = [...matches]
    .sort((left, right) => Date.parse(right.matched_at) - Date.parse(left.matched_at))
    .slice(0, 3);

  if (recentMatches.length === 0) return null;

  return (
    <div className='mb-6 rounded-2xl bg-white p-4'>
      <div className='mb-2 flex items-center justify-between'>
        <p className='text-primary text-[13px] font-semibold'>Последние мэтчи</p>
        <Link
          to='/dashboard/matches'
          className='text-accent hover:text-accent-hover text-[12px] transition-colors'
        >
          Все мэтчи
        </Link>
      </div>
      <div className='flex flex-col'>
        {recentMatches.map((match) => (
          <Link
            key={match.match_id}
            to={`/dashboard/users/${match.partner.keycloak_id}`}
            className='hover:bg-surface -mx-2 flex items-center gap-3 rounded-xl px-2 py-2 transition-colors'
          >
            <ChatAvatar
              name={match.partner.display_name}
              src={match.partner.avatar_url}
              size='sm'
            />
            <p className='text-primary min-w-0 flex-1 truncate text-[13px] font-medium'>
              {match.partner.display_name}
            </p>
            <span className='text-muted shrink-0 text-[10px]'>
              {formatRecentDate(match.matched_at)}
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}

export function DashboardHomePage() {
  const { firstName, lastName } = useProfileStore();
  const keycloakId = useAuthStore((state) => state.keycloakId);
  const [stats, setStats] = useState({ unread: 0, matches: 0, likes: 0 });
  const [chats, setChats] = useState<Chat[]>([]);
  const [matches, setMatches] = useState<Match[]>([]);
  const [profileProgress, setProfileProgress] = useState<ProfileProgress | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);

  useEffect(() => {
    Promise.allSettled([
      chatApi.getChats({ limit: 50 }),
      matchingApi.getMatches(),
      matchingApi.getPendingLikes(),
      profileApi.getMe(),
      profileApi.getQuestionsStatus(),
    ]).then(([chatsResult, matchesResult, likesResult, profileResult, questionsResult]) => {
      const loadedChats = chatsResult.status === 'fulfilled' ? chatsResult.value.chats : [];
      const loadedMatches = matchesResult.status === 'fulfilled' ? matchesResult.value.data : [];

      setChats(loadedChats);
      setMatches(loadedMatches);
      setProfileProgress(
        profileResult.status === 'fulfilled'
          ? getProfileProgress(
              profileResult.value.data,
              questionsResult.status === 'fulfilled'
                ? questionsResult.value.data.can_receive_likes
                : undefined,
            )
          : null,
      );
      setStats({
        unread: loadedChats.reduce((sum, chat) => sum + chat.unread_count, 0),
        matches: loadedMatches.length,
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

  const unreadChat = [...chats]
    .filter((chat) => chat.unread_count > 0)
    .sort((left, right) => Date.parse(right.updated_at) - Date.parse(left.updated_at))[0];

  let nextAction: NextAction;
  if (stats.unread > 0) {
    nextAction = {
      icon: MessageCircle,
      title:
        stats.unread === 1
          ? 'Ответьте на новое сообщение'
          : `Ответьте на ${stats.unread} непрочитанных сообщений`,
      description: unreadChat
        ? `Продолжите общение с ${getChatDisplayName(unreadChat, keycloakId)}.`
        : 'В диалогах вас ждут новые сообщения.',
      label: 'Ответить',
      to: '/dashboard/messages',
      state: unreadChat ? { chatId: unreadChat.id } : undefined,
    };
  } else if (stats.likes > 0) {
    nextAction = {
      icon: Heart,
      title: stats.likes === 1 ? 'У вас новый лайк' : `У вас ${stats.likes} новых лайков`,
      description: 'Посмотрите анкеты и решите, кому хотите ответить взаимностью.',
      label: 'Посмотреть',
      to: '/dashboard/likes',
    };
  } else if (profileProgress && profileProgress.percentage < 100) {
    nextAction = {
      icon: UserRound,
      title: `Профиль заполнен на ${profileProgress.percentage}%`,
      description: profileProgress.missing
        ? `Добавьте ${profileProgress.missing}, чтобы анкета рассказывала о вас больше.`
        : 'Дополните анкету, чтобы получать более подходящие рекомендации.',
      label: 'Дополнить',
      to: '/dashboard/profile',
    };
  } else {
    nextAction = {
      icon: Search,
      title: 'Найдите новое знакомство',
      description: 'Настройте параметры и посмотрите анкеты подходящих людей.',
      label: 'Начать поиск',
      to: '/dashboard/search/classic',
    };
  }

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
          <StatCard label='мэтчей' value={stats.matches} loading={statsLoading} />
          <StatCard label='Новых лайков' value={stats.likes} loading={statsLoading} />
        </div>

        <NextActionCard action={nextAction} loading={statsLoading} />

        {!statsLoading && (
          <RecentActivity chats={chats} matches={matches} keycloakId={keycloakId} />
        )}

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
