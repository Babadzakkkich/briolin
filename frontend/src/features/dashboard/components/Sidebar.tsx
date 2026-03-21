import { Link, NavLink, useNavigate } from 'react-router-dom';
import { LogoIcon } from '@/shared/icons/Logo';
import { authApi } from '@/features/auth/api';
import { useAuthStore } from '@/shared/stores/authStore';
import {
  Briefcase,
  Dice5,
  LogOut,
  MessageCircle,
  Search,
  User,
  Zap,
  type LucideIcon,
} from 'lucide-react';

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
  const username = useAuthStore((s) => s.username);
  const clear = useAuthStore((s) => s.clear);
  const navigate = useNavigate();
  const initials = username ? username.slice(0, 2).toUpperCase() : '?';

  const handleLogout = async () => {
    await authApi.logout().catch(() => {});
    clear();
    navigate('/login');
  };

  return (
    <div className='flex items-center gap-2'>
      <div className='bg-accent/15 text-accent flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-semibold'>
        {initials}
      </div>
      <span className='text-primary truncate text-sm font-medium'>{username ?? '—'}</span>
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

export function Sidebar() {
  return (
    <nav className='border-border flex w-60 flex-col gap-10 border-r bg-white pt-10 pb-4'>
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
        <SidebarItem to='/dashboard/services' icon={Briefcase}>
          Услуги
        </SidebarItem>
        <SidebarItem to='/dashboard/search' icon={Search}>
          Поиск
        </SidebarItem>
        <SidebarItem to='/dashboard/cupidon' icon={Zap}>
          Купидон
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
