import { useEffect, useState } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import { LogoIcon } from '@/shared/icons/Logo';
import { useAuthStore } from '@/entities/session';
import { profileApi, useProfileStore } from '@/entities/profile';
import { AuthImage } from '@/shared/uikit/AuthImage';
import {
  Briefcase,
  Dice5,
  Heart,
  LogOut,
  MessageCircle,
  MoreHorizontal,
  SlidersHorizontal,
  Target,
  User,
  Users,
  X,
  Zap,
  type LucideIcon,
} from 'lucide-react';
import { useAuth } from '@/features/auth/useAuth';

export function SidebarItem({
  to,
  icon: Icon,
  children,
}: {
  to: string;
  icon: LucideIcon;
  children: string;
}) {
  return (
    <NavLink to={to}>
      {({ isActive }) => (
        <button
          className={[
            'flex w-full cursor-pointer items-center gap-2 px-4 py-3',
            'text-secondary hover:bg-muted/15 rounded-xl transition-colors duration-75',
            isActive && 'text-accent! bg-accent/15 hover:bg-accent/20!',
          ]
            .filter(Boolean)
            .join(' ')}
        >
          <Icon className='stroke-[2.2px]' size={20} />
          <span className='text-[14px] leading-none'>{children}</span>
        </button>
      )}
    </NavLink>
  );
}

function UserCard() {
  const firstName = useProfileStore((p) => p.firstName);
  const lastName = useProfileStore((p) => p.lastName);
  const thumbnailUrl = useProfileStore((p) => p.thumbnailUrl);
  const setProfile = useProfileStore((p) => p.setProfile);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const { logout } = useAuth();

  useEffect(() => {
    if (isAuthenticated && !firstName) {
      profileApi
        .getMe()
        .then((res) => setProfile({ ...res.data.basic, thumbnail_url: res.data.basic.thumbnail_url }))
        .catch(() => {});
    }
  }, [isAuthenticated, firstName, setProfile]);

  const initials =
    firstName && lastName
      ? `${firstName[0]}${lastName[0]}`.toUpperCase()
      : firstName
        ? firstName[0].toUpperCase()
        : '?';

  const handleLogout = async () => {
    await logout();
  };

  return (
    <div className='flex items-center gap-2'>
      <div className='h-9 w-9 shrink-0 overflow-hidden rounded-full'>
        {thumbnailUrl ? (
          <AuthImage
            src={thumbnailUrl}
            alt={firstName ?? ''}
            className='h-full w-full object-cover'
            fallback={
              <div className='bg-accent/15 text-accent flex h-full w-full items-center justify-center text-xs font-semibold'>
                {initials}
              </div>
            }
          />
        ) : (
          <div className='bg-accent/15 text-accent flex h-full w-full items-center justify-center text-xs font-semibold'>
            {initials}
          </div>
        )}
      </div>
      <div className='min-w-0 flex-1'>
        {firstName ? (
          <span className='text-primary block truncate text-sm font-medium'>
            {lastName ? `${firstName} ${lastName}` : firstName}
          </span>
        ) : (
          <div className='bg-surface h-3.5 w-24 animate-pulse rounded' />
        )}
      </div>
      <button
        onClick={handleLogout}
        className='text-secondary hover:text-primary hover:bg-muted/15 ml-auto cursor-pointer rounded-lg p-1.5 transition-colors duration-75'
        title='Выйти'
      >
        <LogOut size={12} className='stroke-[2.2px]' />
      </button>
    </div>
  );
}

const MAIN_NAV = [
  { to: '/dashboard/profile', icon: User, label: 'Профиль' },
  { to: '/dashboard/messages', icon: MessageCircle, label: 'Сообщения' },
  { to: '/dashboard/search/classic', icon: SlidersHorizontal, label: 'Поиск' },
  { to: '/dashboard/likes', icon: Heart, label: 'Лайки' },
] as const;

const MORE_NAV = [
  { to: '/dashboard/matches', icon: Users, label: 'Матчи' },
  { to: '/dashboard/search/targeted', icon: Target, label: 'Таргетированный поиск' },
  { to: '/dashboard/cupidon', icon: Zap, label: 'Купидон' },
  { to: '/dashboard/services', icon: Briefcase, label: 'Услуги' },
  { to: '/dashboard/fortune', icon: Dice5, label: 'Фортуна' },
] as const;

export function BottomNav() {
  const [open, setOpen] = useState(false);
  const location = useLocation();

  const isMoreActive = MORE_NAV.some((item) => location.pathname === item.to);

  return (
    <>
      {/* Backdrop */}
      <div
        className={[
          'fixed inset-0 z-40 bg-black/30 transition-opacity duration-300 md:hidden',
          open ? 'opacity-100' : 'pointer-events-none opacity-0',
        ].join(' ')}
        onClick={() => setOpen(false)}
      />

      {/* Slide-up sheet */}
      <div
        className={[
          'fixed right-0 left-0 z-50 rounded-t-2xl bg-white shadow-xl transition-transform duration-300 ease-in-out md:hidden',
          'bottom-[60px]',
          open ? 'translate-y-0' : 'translate-y-full',
        ].join(' ')}
      >
        <div className='flex items-center justify-between border-b border-border px-5 py-4'>
          <span className='font-onest text-primary text-[15px] font-medium'>Ещё</span>
          <button
            onClick={() => setOpen(false)}
            className='text-secondary hover:bg-muted/10 flex h-7 w-7 cursor-pointer items-center justify-center rounded-lg transition-colors'
          >
            <X size={16} strokeWidth={2.2} />
          </button>
        </div>
        <div className='flex flex-col gap-0.5 px-3 py-3'>
          {MORE_NAV.map(({ to, icon: Icon, label }) => (
            <NavLink key={to} to={to} onClick={() => setOpen(false)}>
              {({ isActive }) => (
                <div
                  className={[
                    'flex items-center gap-3 rounded-xl px-4 py-3 transition-colors',
                    isActive
                      ? 'text-accent bg-accent/10'
                      : 'text-secondary hover:bg-muted/10',
                  ].join(' ')}
                >
                  <Icon size={20} strokeWidth={2.2} />
                  <span className='text-[14px]'>{label}</span>
                </div>
              )}
            </NavLink>
          ))}
        </div>
      </div>

      {/* Bottom nav bar */}
      <nav className='border-border fixed right-0 bottom-0 left-0 z-50 flex border-t bg-white md:hidden'>
        {MAIN_NAV.map(({ to, icon: Icon, label }) => (
          <NavLink key={to} to={to} className='flex-1' onClick={() => setOpen(false)}>
            {({ isActive }) => (
              <div
                className={[
                  'flex flex-col items-center gap-1 py-3',
                  isActive ? 'text-accent' : 'text-secondary',
                ].join(' ')}
              >
                <Icon size={22} className='stroke-[2.2px]' />
                <span className='text-[10px] leading-none'>{label}</span>
              </div>
            )}
          </NavLink>
        ))}

        <button className='flex-1 cursor-pointer' onClick={() => setOpen((v) => !v)}>
          <div
            className={[
              'flex flex-col items-center gap-1 py-3',
              isMoreActive || open ? 'text-accent' : 'text-secondary',
            ].join(' ')}
          >
            <MoreHorizontal size={22} className='stroke-[2.2px]' />
            <span className='text-[10px] leading-none'>Ещё</span>
          </div>
        </button>
      </nav>
    </>
  );
}

export function Sidebar() {
  return (
    <nav className='border-border hidden h-screen w-70 shrink-0 flex-col gap-10 border-r bg-white pt-10 pb-4 md:flex'>
      <Link to='/'>
        <div className='flex items-center justify-center gap-2'>
          <LogoIcon />
          <span className='font-onest text-primary text-xl font-medium'>Бриолин</span>
        </div>
      </Link>
      <div className='flex flex-col gap-2 px-4'>
        <SidebarItem to='/dashboard/profile' icon={User}>
          Профиль
        </SidebarItem>
        <SidebarItem to='/dashboard/messages' icon={MessageCircle}>
          Сообщения
        </SidebarItem>
        <SidebarItem to='/dashboard/likes' icon={Heart}>
          Входящие лайки
        </SidebarItem>
        <SidebarItem to='/dashboard/matches' icon={Users}>
          Матчи
        </SidebarItem>
        <SidebarItem to='/dashboard/search/classic' icon={SlidersHorizontal}>
          Классический поиск
        </SidebarItem>
        <SidebarItem to='/dashboard/search/targeted' icon={Target}>
          Таргетированный поиск
        </SidebarItem>
        <SidebarItem to='/dashboard/cupidon' icon={Zap}>
          Купидон
        </SidebarItem>
        <SidebarItem to='/dashboard/services' icon={Briefcase}>
          Услуги
        </SidebarItem>
        <SidebarItem to='/dashboard/fortune' icon={Dice5}>
          Фортуна
        </SidebarItem>
      </div>
      <div className='border-border mt-auto border-t px-4 pt-4'>
        <UserCard />
      </div>
    </nav>
  );
}
